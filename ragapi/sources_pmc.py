import re
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def _get_json(url, params):
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        return r.json()


def pmc_search(query: str, retmax: int = 5):
    """
    Cari kandidat artikel di PubMed Central (db=pmc).
    Return list PMCIDs format 'PMC1234567'.
    """
    data = _get_json(
        f"{EUTILS}/esearch.fcgi",
        {"db": "pmc", "term": query, "retmode": "json", "retmax": retmax},
    )
    ids = data.get("esearchresult", {}).get("idlist", [])
    return [f"PMC{i}" for i in ids]


def pmc_fetch_summary(pmcids: list[str]):
    """
    Ambil ringkasan (judul, tahun) via esummary.
    """
    if not pmcids:
        return []

    numeric_ids = [re.sub(r"^PMC", "", x) for x in pmcids]
    data = _get_json(
        f"{EUTILS}/esummary.fcgi",
        {"db": "pmc", "id": ",".join(numeric_ids), "retmode": "json"},
    )

    result = []
    for nid in numeric_ids:
        item = data.get("result", {}).get(nid)
        if not item:
            continue

        title = item.get("title") or "Untitled"
        pubdate = item.get("pubdate") or ""
        year = None
        m = re.search(r"\b(19|20)\d{2}\b", pubdate)
        if m:
            year = int(m.group(0))

        result.append(
            {
                "paper_id": f"PMC{nid}",
                "title": title,
                "year": year,
                "doi": None,
                "source": "pmc",
                "landing_url": f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{nid}/",
                "pdf_url": f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{nid}/pdf/",
            }
        )
    return result
