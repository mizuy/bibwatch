"""PubMed search via NCBI E-utilities."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any
from xml.etree import ElementTree as ET

import httpx

from bibwatch.models import Abstract, Author, Journal, Paper
from bibwatch.store import normalize_doi, paper_id_from_ids

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def _ncbi_params(**extra: Any) -> dict[str, str]:
    params = {"tool": "bibwatch", "email": "support@example.com"}
    key = os.environ.get("NCBI_API_KEY", "").strip()
    if key:
        params["api_key"] = key
    for k, v in extra.items():
        if v is not None:
            params[k] = str(v)
    return params


def _text(el: ET.Element | None) -> str | None:
    if el is None or el.text is None:
        return None
    return el.text.strip() or None


def _pub_date(article: ET.Element) -> str | None:
    pub = article.find("./Journal/JournalIssue/PubDate")
    if pub is None:
        pub = article.find("./ArticleDate")
    if pub is None:
        return None
    year = _text(pub.find("Year"))
    if not year:
        medline = _text(pub.find("MedlineDate"))
        return medline[:10] if medline else None
    month_raw = (_text(pub.find("Month")) or "1").lower()[:3]
    month = _MONTHS.get(month_raw, int(month_raw) if month_raw.isdigit() else 1)
    day = _text(pub.find("Day")) or "1"
    try:
        return datetime(int(year), int(month), int(day)).date().isoformat()
    except ValueError:
        return year


def authors_from_article(article: ET.Element) -> list[Author]:
    authors: list[Author] = []
    for au in article.findall("./AuthorList/Author"):
        collective = _text(au.find("CollectiveName"))
        if collective:
            authors.append(Author(name=collective))
            continue
        last = _text(au.find("LastName"))
        first = _text(au.find("ForeName"))
        initials = _text(au.find("Initials"))
        name = " ".join(p for p in (last, first) if p) or initials
        if not name:
            continue
        authors.append(Author(name=name, last=last, first=first, initials=initials))
    return authors


def authors_from_pubmed_xml(xml_text: str) -> list[Author]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    article = root.find(".//Article")
    if article is None:
        return []
    return authors_from_article(article)


def _abstract(article: ET.Element) -> str | None:
    parts: list[str] = []
    for node in article.findall("./Abstract/AbstractText"):
        label = node.get("Label")
        text = "".join(node.itertext()).strip()
        if not text:
            continue
        parts.append(f"{label}: {text}" if label else text)
    return " ".join(parts) or None


def paper_from_pubmed_article(article_el: ET.Element, watch_id: str) -> Paper | None:
    medline = article_el.find("MedlineCitation")
    if medline is None:
        return None
    article = medline.find("Article")
    if article is None:
        return None
    pmid = _text(medline.find("PMID"))
    title_el = article.find("ArticleTitle")
    title = "".join(title_el.itertext()).strip() if title_el is not None else ""
    doi = None
    for aid in article_el.findall("./PubmedData/ArticleIdList/ArticleId"):
        if aid.get("IdType") == "doi" and aid.text:
            doi = aid.text.strip()
            break
    if not doi:
        doi = _text(article.find("./ELocationID[@EIdType='doi']"))

    journal_el = article.find("Journal")
    issn = _text(journal_el.find("ISSN")) if journal_el is not None else None
    journal = Journal(
        name=_text(journal_el.find("Title")) if journal_el is not None else None,
        iso_abbrev=_text(journal_el.find("ISOAbbreviation")) if journal_el is not None else None,
        issn=issn,
        volume=_text(journal_el.find("./JournalIssue/Volume")) if journal_el is not None else None,
        issue=_text(journal_el.find("./JournalIssue/Issue")) if journal_el is not None else None,
        published=_pub_date(article),
        type="journal",
    )

    paper_id = paper_id_from_ids(doi=doi, pmid=pmid, title=title)
    ids: dict[str, str] = {}
    if doi:
        ids["doi"] = normalize_doi(doi) or doi
    if pmid:
        ids["pmid"] = pmid
    urls: dict[str, str] = {}
    if pmid:
        urls["landing"] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    if doi:
        norm = normalize_doi(doi)
        if norm:
            urls["doi"] = f"https://doi.org/{norm}"

    return Paper(
        id=paper_id,
        title=title,
        watch_ids=[watch_id],
        authors=authors_from_article(article),
        journal=journal,
        abstract=Abstract(original=_abstract(article)),
        urls=urls,
        ids=ids,
        fetched_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )


def search_pmids(query: str, *, retmax: int = 30, client: httpx.Client | None = None) -> list[str]:
    own = client is None
    client = client or httpx.Client(follow_redirects=True, timeout=30.0)
    try:
        resp = client.get(
            f"{EUTILS}/esearch.fcgi",
            params=_ncbi_params(db="pubmed", term=query, retmax=retmax, sort="date", retmode="json"),
            headers={"User-Agent": "bibwatch/0.1"},
        )
        resp.raise_for_status()
        return list(resp.json().get("esearchresult", {}).get("idlist") or [])
    finally:
        if own:
            client.close()


def fetch_pubmed_articles(pmids: list[str], *, client: httpx.Client | None = None) -> ET.Element:
    own = client is None
    client = client or httpx.Client(follow_redirects=True, timeout=45.0)
    try:
        resp = client.get(
            f"{EUTILS}/efetch.fcgi",
            params=_ncbi_params(db="pubmed", id=",".join(pmids), rettype="abstract", retmode="xml"),
            headers={"User-Agent": "bibwatch/0.1"},
        )
        resp.raise_for_status()
        return ET.fromstring(resp.content)
    finally:
        if own:
            client.close()


def poll_pubmed_search(watch_id: str, feed: dict[str, Any]) -> list[Paper]:
    query = (feed.get("query") or "").strip()
    if not query:
        raise ValueError(f"{watch_id}: pubmed_search feed missing query")
    retmax = int(feed.get("retmax") or 30)
    with httpx.Client(follow_redirects=True, timeout=45.0) as client:
        pmids = search_pmids(query, retmax=retmax, client=client)
        if not pmids:
            return []
        time.sleep(0.12)
        root = fetch_pubmed_articles(pmids, client=client)
    papers: list[Paper] = []
    for article in root.findall("PubmedArticle"):
        paper = paper_from_pubmed_article(article, watch_id)
        if paper:
            papers.append(paper)
    return papers
