const { XMLParser } = require("fast-xml-parser");


// =====================================================
// Search PubMed
// =====================================================

async function searchPubMed(question) {

    // ---------------------------------------------
    // Number of papers we want
    // ---------------------------------------------

    const maxResults = 10;


    // ---------------------------------------------
    // PubMed ESearch API
    // ---------------------------------------------

    const searchUrl =
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi" +
        `?db=pubmed` +
        `&term=${encodeURIComponent(question)}` +
        `&retmode=json` +
        `&retmax=${maxResults}`;


    // Add API key if available
    const finalSearchUrl =
        process.env.PUBMED_API_KEY
            ? searchUrl +
              `&api_key=${process.env.PUBMED_API_KEY}`
            : searchUrl;


    const searchResponse =
        await fetch(finalSearchUrl);


    if (!searchResponse.ok) {

        throw new Error(
            "PubMed search request failed"
        );

    }


    const searchData =
        await searchResponse.json();


    // ---------------------------------------------
    // Get PMIDs
    // ---------------------------------------------

    const ids =
        searchData
            ?.esearchresult
            ?.idlist || [];


    if (ids.length === 0) {

        return [];

    }


    // ---------------------------------------------
    // Fetch complete article information
    // ---------------------------------------------

    return await fetchPubMedArticles(ids);

}



// =====================================================
// Fetch PubMed articles
// =====================================================

async function fetchPubMedArticles(ids) {

    const fetchUrl =
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi" +
        `?db=pubmed` +
        `&id=${ids.join(",")}` +
        `&retmode=xml`;


    const finalFetchUrl =
        process.env.PUBMED_API_KEY
            ? fetchUrl +
              `&api_key=${process.env.PUBMED_API_KEY}`
            : fetchUrl;


    const fetchResponse =
        await fetch(finalFetchUrl);


    if (!fetchResponse.ok) {

        throw new Error(
            "PubMed article retrieval failed"
        );

    }


    const xml =
        await fetchResponse.text();


    return parsePubMedXML(xml);

}



// =====================================================
// Parse PubMed XML
// =====================================================

function parsePubMedXML(xml) {

    const parser =
        new XMLParser({
            ignoreAttributes: false,
            textNodeName: "#text"
        });


    const data =
        parser.parse(xml);


    let articles =
        data
            ?.PubmedArticleSet
            ?.PubmedArticle || [];


    // If there is only one article,
    // XML parser may return an object
    // instead of an array.

    if (!Array.isArray(articles)) {

        articles = [articles];

    }


    return articles
        .map(parseArticle)
        .filter(article => article !== null);

}



// =====================================================
// Parse individual article
// =====================================================

function parseArticle(article) {

    try {

        const medlineCitation =
            article.MedlineCitation;


        const articleData =
            medlineCitation.Article;


        // ---------------------------------------------
        // PMID
        // ---------------------------------------------

        const pmid =
            getText(
                medlineCitation.PMID
            );


        // ---------------------------------------------
        // Title
        // ---------------------------------------------

        const title =
            getText(
                articleData.ArticleTitle
            );


        // ---------------------------------------------
        // Authors
        // ---------------------------------------------

        const authors =
            extractAuthors(
                articleData.AuthorList
            );


        // ---------------------------------------------
        // Publication date
        // ---------------------------------------------

        const date =
            extractPublicationDate(
                articleData.Journal
            );


        // ---------------------------------------------
        // Abstract
        // ---------------------------------------------

        const abstract =
            extractAbstract(
                articleData.Abstract
            );


        // ---------------------------------------------
        // Return standard structure
        // ---------------------------------------------

        return {

            pmid,

            title,

            authors,

            date,

            abstract

        };

    }

    catch (error) {

        console.error(
            "Failed to parse PubMed article:",
            error.message
        );

        return null;

    }

}



// =====================================================
// Extract authors
// =====================================================

function extractAuthors(authorList) {

    if (!authorList) {

        return [];

    }


    let authors =
        authorList.Author || [];


    if (!Array.isArray(authors)) {

        authors = [authors];

    }


    return authors
        .map(author => {

            // Some PubMed records contain
            // CollectiveName instead of
            // FirstName/LastName.

            if (author.CollectiveName) {

                return getText(
                    author.CollectiveName
                );

            }


            const firstName =
                getText(
                    author.ForeName
                );


            const lastName =
                getText(
                    author.LastName
                );


            return `${firstName} ${lastName}`
                .trim();

        })
        .filter(name => name !== "");

}



// =====================================================
// Extract publication date
// =====================================================

function extractPublicationDate(journal) {

    const pubDate =
        journal
            ?.JournalIssue
            ?.PubDate;


    if (!pubDate) {

        return "";

    }


    // Example:
    // Year = 2025
    // Month = Jan
    // Day = 15

    const year =
        getText(pubDate.Year);


    const month =
        getText(pubDate.Month);


    const day =
        getText(pubDate.Day);


    if (year) {

        return [
            year,
            month,
            day
        ]
            .filter(Boolean)
            .join("-");

    }


    // Some articles have
    // MedlineDate instead.

    return getText(
        pubDate.MedlineDate
    );

}



// =====================================================
// Extract abstract
// =====================================================

function extractAbstract(abstractObject) {

    if (!abstractObject) {

        return "";

    }


    let abstractText =
        abstractObject.AbstractText || [];


    if (!Array.isArray(abstractText)) {

        abstractText = [abstractText];

    }


    return abstractText
        .map(section => {

            // Plain text
            if (typeof section === "string") {

                return section;

            }


            // Section with label
            const label =
                section["@_Label"] ||
                section["@_NlmCategory"] ||
                "";


            const text =
                getText(section);


            if (label && text) {

                return `${label}: ${text}`;

            }


            return text;

        })
        .filter(Boolean)
        .join(" ");

}



// =====================================================
// Generic XML text extractor
// =====================================================

function getText(value) {

    if (
        value === undefined ||
        value === null
    ) {

        return "";

    }


    if (typeof value === "string") {

        return value;

    }


    if (
        typeof value === "number" ||
        typeof value === "boolean"
    ) {

        return String(value);

    }


    if (
        typeof value === "object" &&
        value["#text"] !== undefined
    ) {

        return String(
            value["#text"]
        );

    }


    return "";

}



// =====================================================
// Export
// =====================================================

module.exports = {
    searchPubMed
};