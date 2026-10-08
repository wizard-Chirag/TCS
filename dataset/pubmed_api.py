import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from .normalizer import normalize_paper

MONTH_MAP = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
    'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
}

BASE_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
BASE_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

def clean_element_text(elem) -> str:
    if elem is None:
        return ""
    raw = "".join(elem.itertext())
    text = html.unescape(raw)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[ \t\r\f\v]+', ' ', text)
    text = re.sub(r' \n', '\n', text)
    text = re.sub(r'\n ', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def parse_xml_date(article: ET.Element) -> Optional[str]:
    # 1. ArticleDate
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

    # 2. JournalIssue/PubDate
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
            return clean_element_text(pd)

    # 3. History
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

    return None

def parse_xml_abstract(article: ET.Element) -> Optional[str]:
    abstract_elem = article.find('.//Abstract')
    if abstract_elem is None:
        return None

    texts = abstract_elem.findall('AbstractText')
    if not texts:
        full = clean_element_text(abstract_elem)
        return full if full else None

    sections = []
    for at in texts:
        label = (at.get('Label') or at.get('NlmCategory') or '').strip()
        text = clean_element_text(at)
        if not text:
            continue
        if label:
            sections.append(f"{label.upper()}: {text}")
        else:
            sections.append(text)

    joined = "\n\n".join(sections).strip()
    return joined if joined else None

def parse_xml_authors(article: ET.Element) -> List[str]:
    authors: List[str] = []
    for a in article.findall('.//AuthorList/Author'):
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

def fetch_pubmed_by_ids(pmids: List[str], timeout: int = 15) -> List[Dict[str, Any]]:
    """
    Fetches XML metadata for given PMIDs from NCBI E-Fetch and returns normalized papers.
    """
    clean_pmids = [str(p).strip() for p in pmids if str(p).strip()]
    if not clean_pmids:
        return []

    params = {
        'db': 'pubmed',
        'id': ','.join(clean_pmids),
        'retmode': 'xml'
    }
    url = f"{BASE_EFETCH}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'PubMed-Dataset-Retriever/1.0'})

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        xml_bytes = resp.read()

    root = ET.fromstring(xml_bytes)
    papers: List[Dict[str, Any]] = []

    for article in root.findall('.//PubmedArticle'):
        pmid_elem = article.find('.//MedlineCitation/PMID')
        pmid = pmid_elem.text.strip() if (pmid_elem is not None and pmid_elem.text) else None
        if not pmid:
            continue

        title_elem = article.find('.//ArticleTitle')
        title = clean_element_text(title_elem) if title_elem is not None else None

        abstract = parse_xml_abstract(article)
        authors = parse_xml_authors(article)
        date = parse_xml_date(article)

        raw_record = {
            "pmid": pmid,
            "title": title,
            "authors": authors,
            "date": date,
            "abstract": abstract
        }
        papers.append(normalize_paper(raw_record, source="PubMed"))

    return papers

def search_pubmed(query: str, max_results: int = 10, timeout: int = 15) -> List[Dict[str, Any]]:
    """
    Searches PubMed for articles matching query and returns normalized papers.
    """
    params = {
        'db': 'pubmed',
        'term': f"{query} AND hasabstract[Filter]",
        'retmax': str(max_results),
        'sort': 'pub_date',
        'retmode': 'json'
    }
    url = f"{BASE_ESEARCH}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'PubMed-Dataset-Retriever/1.0'})

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        search_data = json.loads(resp.read().decode('utf-8'))

    id_list = search_data.get('esearchresult', {}).get('idlist', [])
    if not id_list:
        return []

    return fetch_pubmed_by_ids(id_list, timeout=timeout)
