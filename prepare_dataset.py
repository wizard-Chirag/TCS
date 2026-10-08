import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import csv
import re
import html
import os
import sys

MONTH_MAP = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
    'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
}

def clean_text(text):
    if not text:
        return ""
    text = html.unescape(text)
    # Remove XML/HTML tags if any remain
    text = re.sub(r'<[^>]+>', ' ', text)
    # Normalize multiple whitespace characters
    text = re.sub(r'[ \t\r\f\v]+', ' ', text)
    text = re.sub(r' \n', '\n', text)
    text = re.sub(r'\n ', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_element_full_text(elem):
    if elem is None:
        return ""
    full_text = "".join(elem.itertext())
    return clean_text(full_text)

def parse_date(article):
    # 1. Check ArticleDate (electronic publication date)
    for ad in article.findall('.//ArticleDate'):
        y = (ad.findtext('Year') or '').strip()
        m = (ad.findtext('Month') or '').strip()
        d = (ad.findtext('Day') or '').strip()
        if y:
            m_norm = MONTH_MAP.get(m.lower()[:3], m)
            if m_norm.isdigit():
                m_norm = m_norm.zfill(2)
            if d.isdigit():
                d = d.zfill(2)
            if y and m_norm and d and len(y) == 4 and len(m_norm) == 2 and len(d) == 2:
                return f"{y}-{m_norm}-{d}"
            elif y and m_norm and len(y) == 4 and len(m_norm) == 2:
                return f"{y}-{m_norm}"
            elif y and len(y) == 4:
                return y

    # 2. Check JournalIssue/PubDate
    pd = article.find('.//JournalIssue/PubDate')
    if pd is not None:
        y = (pd.findtext('Year') or '').strip()
        m = (pd.findtext('Month') or '').strip()
        d = (pd.findtext('Day') or '').strip()
        if y:
            m_norm = MONTH_MAP.get(m.lower()[:3], m)
            if m_norm.isdigit():
                m_norm = m_norm.zfill(2)
            if d.isdigit():
                d = d.zfill(2)
            if y and m_norm and d and len(y) == 4 and len(m_norm) == 2 and len(d) == 2:
                return f"{y}-{m_norm}-{d}"
            elif y and m_norm and len(y) == 4 and len(m_norm) == 2:
                return f"{y}-{m_norm}"
            elif y and len(y) == 4:
                return y
        medline_date = (pd.findtext('MedlineDate') or '').strip()
        if medline_date:
            return clean_text(medline_date)

    # 3. Check PubMedPubDate with PubStatus="pubmed"
    for hist in article.findall('.//History/PubMedPubDate'):
        if hist.get('PubStatus') == 'pubmed':
            y = (hist.findtext('Year') or '').strip()
            m = (hist.findtext('Month') or '').strip()
            d = (hist.findtext('Day') or '').strip()
            if y:
                m_norm = MONTH_MAP.get(m.lower()[:3], m)
                if m_norm.isdigit():
                    m_norm = m_norm.zfill(2)
                if d.isdigit():
                    d = d.zfill(2)
                if y and m_norm and d and len(y) == 4 and len(m_norm) == 2 and len(d) == 2:
                    return f"{y}-{m_norm}-{d}"
                elif y and m_norm and len(y) == 4 and len(m_norm) == 2:
                    return f"{y}-{m_norm}"
                elif y and len(y) == 4:
                    return y

    return ""

def parse_abstract(article):
    abstract_elem = article.find('.//Abstract')
    if abstract_elem is None:
        return ""

    abstract_texts = abstract_elem.findall('AbstractText')
    if not abstract_texts:
        return extract_element_full_text(abstract_elem)

    sections = []
    for at in abstract_texts:
        label = at.get('Label') or at.get('NlmCategory') or ''
        label = label.strip()
        text = extract_element_full_text(at)
        if not text:
            continue
        if label:
            sections.append(f"{label.upper()}: {text}")
        else:
            sections.append(text)

    return "\n\n".join(sections).strip()

def parse_authors(article):
    authors = []
    author_list = article.findall('.//AuthorList/Author')
    for a in author_list:
        last = (a.findtext('LastName') or '').strip()
        fore = (a.findtext('ForeName') or '').strip()
        collective = (a.findtext('CollectiveName') or '').strip()
        if fore and last:
            authors.append(f"{fore} {last}")
        elif last:
            authors.append(last)
        elif collective:
            authors.append(collective)
    return authors

def fetch_pubmed_records(target_count=100):
    base_esearch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    base_efetch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    # Query for medical research articles: clinical trials, therapy trials, randomized trials
    query = '(clinical trial[Publication Type] OR randomized controlled trial[Publication Type]) AND hasabstract[Filter] AND english[Language]'
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': str(int(target_count * 1.3)), # Fetch ~130 to guarantee at least 100 after filtering
        'sort': 'pub_date',
        'retmode': 'json'
    }

    url = f"{base_esearch}?{urllib.parse.urlencode(params)}"
    print(f"Querying NCBI PubMed E-Search API: {url}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'TCS-Hackathon-Dataset-Builder/1.0 (chiragsm0706@gmail.com)'})
    with urllib.request.urlopen(req) as resp:
        search_res = json.loads(resp.read().decode('utf-8'))

    pmids = search_res.get('esearchresult', {}).get('idlist', [])
    print(f"Retrieved {len(pmids)} candidate PMIDs from NCBI E-Search.")

    if not pmids:
        raise RuntimeError("No PMIDs returned from search query.")

    # Fetch XML records in chunks
    fetch_params = {
        'db': 'pubmed',
        'id': ','.join(pmids),
        'retmode': 'xml'
    }
    fetch_url = f"{base_efetch}?{urllib.parse.urlencode(fetch_params)}"
    print(f"Fetching PubMed XML for {len(pmids)} PMIDs (approx ~350-500 KB)...")
    req = urllib.request.Request(fetch_url, headers={'User-Agent': 'TCS-Hackathon-Dataset-Builder/1.0 (chiragsm0706@gmail.com)'})
    with urllib.request.urlopen(req) as resp:
        xml_data = resp.read()

    print(f"Fetched {len(xml_data):,} bytes of PubMed XML data.")
    root = ET.fromstring(xml_data)

    records = []
    seen_pmids = set()
    malformed_count = 0
    duplicate_count = 0
    missing_abstract_count = 0

    for article in root.findall('.//PubmedArticle'):
        pmid_elem = article.find('.//MedlineCitation/PMID')
        if pmid_elem is None or not pmid_elem.text or not pmid_elem.text.strip():
            malformed_count += 1
            continue

        pmid = str(pmid_elem.text.strip())

        if pmid in seen_pmids:
            duplicate_count += 1
            continue

        title_elem = article.find('.//ArticleTitle')
        title = extract_element_full_text(title_elem)
        if not title:
            malformed_count += 1
            continue

        abstract = parse_abstract(article)
        if not abstract:
            missing_abstract_count += 1
            continue

        authors = parse_authors(article)
        date = parse_date(article)

        record = {
            "pmid": pmid,
            "title": title,
            "authors": authors,
            "date": date,
            "abstract": abstract
        }

        seen_pmids.add(pmid)
        records.append(record)

        if len(records) >= target_count:
            break

    print(f"Successfully processed {len(records)} valid records.")
    print(f"Duplicates filtered: {duplicate_count}, Missing abstract filtered: {missing_abstract_count}, Malformed: {malformed_count}")
    return records

def validate_dataset(records):
    total = len(records)
    unique_pmids = len(set(r["pmid"] for r in records))
    with_title = sum(1 for r in records if r.get("title") and r["title"].strip())
    with_abstract = sum(1 for r in records if r.get("abstract") and r["abstract"].strip())
    with_authors = sum(1 for r in records if len(r.get("authors", [])) > 0)
    with_date = sum(1 for r in records if r.get("date") and r["date"].strip())
    duplicate_pmids = total - unique_pmids

    malformed = 0
    for r in records:
        if not isinstance(r.get("pmid"), str) or not r["pmid"].strip():
            malformed += 1
        elif not isinstance(r.get("title"), str) or not r["title"].strip():
            malformed += 1
        elif not isinstance(r.get("authors"), list):
            malformed += 1
        elif not isinstance(r.get("date"), str):
            malformed += 1
        elif not isinstance(r.get("abstract"), str) or not r["abstract"].strip():
            malformed += 1

    report = {
        "total_records": total,
        "unique_pmids": unique_pmids,
        "records_with_title": with_title,
        "records_with_abstract": with_abstract,
        "records_with_authors": with_authors,
        "records_with_date": with_date,
        "duplicate_pmid_count": duplicate_pmids,
        "malformed_record_count": malformed
    }
    return report

def main():
    target_count = 100
    records = fetch_pubmed_records(target_count=target_count)

    output_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(output_dir, "pubmed_sample.json")
    csv_path = os.path.join(output_dir, "pubmed_sample.csv")

    # Write JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"Wrote JSON dataset to: {json_path}")

    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["pmid", "title", "authors", "date", "abstract"])
        for r in records:
            # authors formatted as semicolon-separated string for clean CSV representation
            authors_str = "; ".join(r["authors"])
            writer.writerow([r["pmid"], r["title"], authors_str, r["date"], r["abstract"]])
    print(f"Wrote CSV dataset to: {csv_path}")

    # Validation
    report = validate_dataset(records)
    print("\n--- VALIDATION REPORT ---")
    for k, v in report.items():
        print(f"{k}: {v}")

    # Also verify reading JSON back
    with open(json_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
        assert len(loaded) == len(records), "Verification failed: JSON record count mismatch"
        print("\nJSON file verification: Successfully re-parsed and validated against schema.")

if __name__ == "__main__":
    main()
