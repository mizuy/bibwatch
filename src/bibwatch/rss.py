"""Build RSS 2.0 feeds for GitHub Pages."""

from __future__ import annotations

import html
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from bibwatch.journals import ListedJournal, match_journal
from bibwatch.models import Paper


def _pub_date(paper: Paper) -> str:
    raw = paper.journal.published or paper.fetched_at
    if raw:
        try:
            if len(raw) == 4:
                dt = datetime(int(raw), 1, 1, tzinfo=timezone.utc)
            elif len(raw) >= 10:
                dt = datetime.fromisoformat(raw[:10]).replace(tzinfo=timezone.utc)
            else:
                dt = datetime.now(timezone.utc)
            return format_datetime(dt)
        except (ValueError, TypeError):
            pass
    return format_datetime(datetime.now(timezone.utc))


def _item_link(paper: Paper) -> str:
    if paper.urls.get("doi"):
        return paper.urls["doi"]
    if paper.urls.get("landing"):
        return paper.urls["landing"]
    return paper.urls.get("pdf", "https://example.invalid/")


def _if_label(listed: ListedJournal | None) -> str | None:
    if listed is None or listed.if_2025 is None:
        return None
    text = f"IF 2025 {listed.if_2025:g}"
    if listed.if_2025_flag:
        text += listed.if_2025_flag
    return text


def _description_html(paper: Paper, listed: ListedJournal | None = None) -> str:
    parts: list[str] = ['<div class="paper-meta">']

    parts.append('<section class="journal"><h4>掲載誌</h4>')
    j = paper.journal
    if j.name:
        jtype = "プレプリント" if j.type == "preprint" else j.name
        line = f"<p><strong>{html.escape(jtype)}</strong>"
        if j.published:
            line += f" ({html.escape(str(j.published))})"
        line += "</p>"
        parts.append(line)
        meta_bits = []
        if j.volume:
            meta_bits.append(f"Vol.{html.escape(j.volume)}")
        if j.issue:
            meta_bits.append(f"No.{html.escape(j.issue)}")
        if j.issn:
            meta_bits.append(f"ISSN {html.escape(j.issn)}")
        if_bit = _if_label(listed)
        if if_bit:
            meta_bits.append(html.escape(if_bit))
        if meta_bits:
            parts.append(f"<p>{' · '.join(meta_bits)}</p>")
    else:
        parts.append("<p>不明</p>")
    parts.append("</section>")

    parts.append('<section class="affiliations"><h4>所属・国</h4>')
    if paper.affiliations:
        parts.append("<ul>")
        for aff in paper.affiliations:
            country = html.escape(aff.country or "不明")
            inst = html.escape(aff.institution)
            parts.append(f"<li>{inst} — <strong>{country}</strong></li>")
        parts.append("</ul>")
    else:
        parts.append("<p>取得できず</p>")
    parts.append("</section>")

    if paper.abstract.ja:
        parts.append('<section class="abstract-ja"><h4>要旨（訳）</h4>')
        parts.append(f"<p>{html.escape(paper.abstract.ja)}</p></section>")

    if paper.abstract.original:
        parts.append('<section class="abstract-en"><h4>Abstract (original)</h4>')
        parts.append(f"<p>{html.escape(paper.abstract.original)}</p></section>")

    id_bits = []
    if paper.ids.get("doi"):
        doi = html.escape(paper.ids["doi"])
        id_bits.append(f'DOI: <a href="https://doi.org/{doi}">{doi}</a>')
    if paper.ids.get("pmid"):
        pmid = html.escape(paper.ids["pmid"])
        id_bits.append(
            f'PMID: <a href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/">{pmid}</a>'
        )
    if paper.ids.get("arxiv"):
        arx = html.escape(paper.ids["arxiv"])
        id_bits.append(
            f'arXiv: <a href="https://arxiv.org/abs/{arx}">{arx}</a>'
        )
    if id_bits:
        parts.append(f'<section class="ids"><p>{" · ".join(id_bits)}</p></section>')

    parts.append("</div>")
    return "".join(parts)


def build_rss(
    papers: list[Paper],
    *,
    feed_title: str,
    feed_link: str,
    feed_description: str,
    journal_catalog: list[ListedJournal] | None = None,
) -> str:
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = feed_title
    ET.SubElement(channel, "link").text = feed_link
    ET.SubElement(channel, "description").text = feed_description
    ET.SubElement(channel, "generator").text = "bibwatch"

    for paper in papers:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = paper.title
        ET.SubElement(item, "link").text = _item_link(paper)
        ET.SubElement(item, "guid", attrib={"isPermaLink": "false"}).text = paper.id
        ET.SubElement(item, "pubDate").text = _pub_date(paper)
        desc = ET.SubElement(item, "description")
        desc.text = _description_html(paper, match_journal(paper, journal_catalog))

    ET.indent(rss, space="  ")
    body = ET.tostring(rss, encoding="unicode", xml_declaration=False)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n"


def write_feed(path: Path, xml: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(xml, encoding="utf-8")
    return path
