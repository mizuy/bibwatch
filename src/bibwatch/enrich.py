"""Enrich papers with journal and affiliation metadata."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import httpx

from bibwatch.models import Affiliation, Author, Journal, Paper
from bibwatch.pubmed import authors_from_article, authors_from_pubmed_xml, fetch_pubmed_articles
from bibwatch.store import list_papers, normalize_doi, save_paper

COUNTRY_JA = {
    "US": "アメリカ",
    "USA": "アメリカ",
    "JP": "日本",
    "Japan": "日本",
    "CN": "中国",
    "China": "中国",
    "GB": "イギリス",
    "UK": "イギリス",
    "DE": "ドイツ",
    "Germany": "ドイツ",
    "FR": "フランス",
    "France": "フランス",
    "KR": "韓国",
    "CA": "カナダ",
    "AU": "オーストラリア",
    "CH": "スイス",
    "NL": "オランダ",
    "SE": "スウェーデン",
    "SG": "シンガポール",
    "TW": "台湾",
    "IT": "イタリア",
    "ES": "スペイン",
    "AR": "アルゼンチン",
    "RS": "セルビア",
    "BR": "ブラジル",
    "IN": "インド",
    "BE": "ベルギー",
    "DK": "デンマーク",
    "NO": "ノルウェー",
    "FI": "フィンランド",
    "AT": "オーストリア",
    "PT": "ポルトガル",
    "PL": "ポーランド",
    "CZ": "チェコ",
    "GR": "ギリシャ",
    "IL": "イスラエル",
    "TR": "トルコ",
    "MX": "メキシコ",
    "NZ": "ニュージーランド",
    "IE": "アイルランド",
    "HK": "香港",
}


def country_display(code_or_name: str | None) -> str | None:
    if not code_or_name:
        return None
    return COUNTRY_JA.get(code_or_name, code_or_name)


def _openalex_work(client: httpx.Client, paper: Paper) -> dict[str, Any] | None:
    doi = normalize_doi(paper.ids.get("doi"))
    if doi:
        url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    elif pmid := paper.ids.get("pmid"):
        url = f"https://api.openalex.org/works/pmid:{pmid}"
    else:
        return None
    resp = client.get(url, headers={"User-Agent": "bibwatch/0.1 (mailto:support@example.com)"})
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def _authors_from_openalex(data: dict[str, Any]) -> list[Author]:
    out: list[Author] = []
    for authorship in data.get("authorships") or []:
        name = ((authorship.get("author") or {}).get("display_name") or "").strip()
        if name:
            out.append(Author(name=name))
    return out


def _affiliations_from_openalex(data: dict[str, Any]) -> list[Affiliation]:
    seen: set[tuple[str, str | None]] = set()
    out: list[Affiliation] = []
    for authorship in data.get("authorships") or []:
        for inst in authorship.get("institutions") or []:
            name = inst.get("display_name")
            if not name:
                continue
            cc = inst.get("country_code")
            key = (name, cc)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                Affiliation(
                    institution=name,
                    country=country_display(cc),
                    country_code=cc,
                )
            )
    return out


def _journal_from_openalex(data: dict[str, Any]) -> Journal | None:
    src = data.get("primary_location", {}).get("source") or {}
    if not src.get("display_name"):
        return None
    bib = data.get("biblio") or {}
    return Journal(
        name=src.get("display_name"),
        issn=(src.get("issn_l") or (src.get("issn") or [None])[0]),
        volume=str(bib["volume"]) if bib.get("volume") else None,
        issue=str(bib["issue"]) if bib.get("issue") else None,
        published=(data.get("publication_date") or data.get("published_date")),
        type="journal",
    )


def _pubmed_efetch(client: httpx.Client, pmid: str) -> dict[str, Any] | None:
    api_key = os.environ.get("NCBI_API_KEY", "")
    params = {"db": "pubmed", "id": pmid, "retmode": "xml"}
    if api_key:
        params["api_key"] = api_key
    resp = client.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi", params=params)
    if resp.status_code != 200:
        return None
    return {"xml": resp.text}


def _parse_pubmed_xml(xml_text: str) -> tuple[Journal | None, list[Affiliation], str | None, list[Author]]:
    journal = None
    affiliations: list[Affiliation] = []
    abstract_parts: list[str] = []

    jname = re.search(r"<Title>([^<]+)</Title>", xml_text)
    iso = re.search(r"<ISOAbbreviation>([^<]+)</ISOAbbreviation>", xml_text)
    issn = re.search(r"<ISSN[^>]*>([^<]+)</ISSN>", xml_text)
    pub_date = re.search(r"<PubDate>.*?<Year>(\d{4})</Year>", xml_text, re.S)
    if jname:
        journal = Journal(
            name=jname.group(1).strip(),
            iso_abbrev=iso.group(1).strip() if iso else None,
            issn=issn.group(1).strip() if issn else None,
            published=pub_date.group(1) if pub_date else None,
            type="journal",
        )

    for match in re.finditer(r"<AffiliationInfo>.*?<Affiliation>([^<]+)</Affiliation>", xml_text, re.S):
        aff_text = match.group(1).strip()
        country = _guess_country_from_affiliation(aff_text)
        inst = aff_text.split(",")[0].strip()
        affiliations.append(Affiliation(institution=inst, country=country_display(country), country_code=country))

    for match in re.finditer(r"<AbstractText[^>]*>([^<]+)</AbstractText>", xml_text):
        abstract_parts.append(match.group(1).strip())
    abstract = " ".join(abstract_parts) if abstract_parts else None

    # dedupe affiliations
    seen: set[tuple[str, str | None]] = set()
    deduped: list[Affiliation] = []
    for a in affiliations:
        key = (a.institution, a.country_code)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(a)

    authors = authors_from_pubmed_xml(xml_text)
    return journal, deduped, abstract, authors


def _guess_country_from_affiliation(text: str) -> str | None:
    for token in reversed(re.split(r"[,;]", text)):
        t = token.strip()
        if len(t) == 2 and t.isalpha():
            return t.upper()
        if t in COUNTRY_JA:
            return t
    return None


def enrich_paper(paper: Paper) -> Paper:
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        oa = _openalex_work(client, paper)
        if oa:
            j = _journal_from_openalex(oa)
            if j and j.name:
                paper.journal = j
            affs = _affiliations_from_openalex(oa)
            if affs:
                paper.affiliations = affs
            if not paper.authors:
                oa_authors = _authors_from_openalex(oa)
                if oa_authors:
                    paper.authors = oa_authors
            oa_doi = normalize_doi(oa.get("doi"))
            if oa_doi:
                paper.ids["doi"] = oa_doi
                paper.urls["doi"] = f"https://doi.org/{oa_doi}"
            if not paper.abstract.original:
                inv = oa.get("abstract_inverted_index")
                if isinstance(inv, dict):
                    paper.abstract.original = _reconstruct_openalex_abstract(inv)

        if pmid := paper.ids.get("pmid"):
            raw = _pubmed_efetch(client, pmid)
            if raw and raw.get("xml"):
                j, affs, abstract, authors = _parse_pubmed_xml(raw["xml"])
                if j and j.name and (not paper.journal.name or paper.journal.type == "preprint"):
                    paper.journal = j
                if affs and not paper.affiliations:
                    paper.affiliations = affs
                if authors:
                    paper.authors = authors
                if abstract and len(abstract) > len(paper.abstract.original or ""):
                    paper.abstract.original = abstract

    return paper


def _reconstruct_openalex_abstract(inverted: dict[str, list[int]]) -> str:
    if not inverted:
        return ""
    max_idx = max(i for indices in inverted.values() for i in indices)
    words = [""] * (max_idx + 1)
    for word, indices in inverted.items():
        for i in indices:
            words[i] = word
    return " ".join(words)


def fill_missing_authors(root: Path) -> int:
    """Backfill author lists from PubMed for stored papers that lack them."""
    import time

    need = [p for p in list_papers(root) if not p.authors and p.ids.get("pmid")]
    updated = 0
    for i in range(0, len(need), 50):
        batch = need[i : i + 50]
        pmids = [p.ids["pmid"] for p in batch]
        xml_root = fetch_pubmed_articles(pmids)
        by_pmid: dict[str, list[Author]] = {}
        for article_el in xml_root.findall("PubmedArticle"):
            medline = article_el.find("MedlineCitation")
            article = medline.find("Article") if medline is not None else None
            if medline is None or article is None:
                continue
            pmid_el = medline.find("PMID")
            pmid = (pmid_el.text or "").strip() if pmid_el is not None else ""
            if not pmid:
                continue
            authors = authors_from_article(article)
            if authors:
                by_pmid[pmid] = authors
        for paper in batch:
            authors = by_pmid.get(paper.ids.get("pmid") or "")
            if not authors:
                continue
            paper.authors = authors
            save_paper(root, paper)
            updated += 1
        if i + 50 < len(need):
            time.sleep(0.34)
    return updated
