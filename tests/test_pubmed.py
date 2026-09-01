from xml.etree import ElementTree as ET

from bibwatch.pubmed import paper_from_pubmed_article


SAMPLE = """
<PubmedArticle>
  <MedlineCitation>
    <PMID>42393851</PMID>
    <Article>
      <Journal>
        <ISSN IssnType="Electronic">1532-0979</ISSN>
        <JournalIssue>
          <Volume>1</Volume>
          <PubDate><Year>2026</Year><Month>Jul</Month><Day>03</Day></PubDate>
        </JournalIssue>
        <Title>The American journal of surgical pathology</Title>
        <ISOAbbreviation>Am J Surg Pathol</ISOAbbreviation>
      </Journal>
      <AuthorList>
        <Author>
          <LastName>Sekine</LastName>
          <ForeName>Shigeki</ForeName>
          <Initials>S</Initials>
        </Author>
        <Author>
          <LastName>Saito</LastName>
          <ForeName>Yutaka</ForeName>
          <Initials>Y</Initials>
        </Author>
      </AuthorList>
      <ArticleTitle>TSA and <i>RSPO</i> fusion</ArticleTitle>
      <ELocationID EIdType="doi">10.1097/PAS.0000000000002586</ELocationID>
      <Abstract>
        <AbstractText Label="BACKGROUND">SuSA and RSPO.</AbstractText>
      </Abstract>
    </Article>
  </MedlineCitation>
  <PubmedData>
    <ArticleIdList>
      <ArticleId IdType="pubmed">42393851</ArticleId>
      <ArticleId IdType="doi">10.1097/PAS.0000000000002586</ArticleId>
    </ArticleIdList>
  </PubmedData>
</PubmedArticle>
"""


def test_paper_from_pubmed_article():
    el = ET.fromstring(SAMPLE)
    paper = paper_from_pubmed_article(el, "w-test")
    assert paper is not None
    assert paper.ids["pmid"] == "42393851"
    assert paper.ids["doi"] == "10.1097/pas.0000000000002586"
    assert paper.journal.iso_abbrev == "Am J Surg Pathol"
    assert paper.journal.published == "2026-07-03"
    assert "RSPO" in paper.title
    assert [a.name for a in paper.authors] == ["Sekine Shigeki", "Saito Yutaka"]
    assert paper.abstract.original and paper.abstract.original.startswith("BACKGROUND")
