import httpx

S2_API = "https://api.semanticscholar.org/graph/v1"


def s2_search(query: str, limit: int = 5):
    """
    Cari paper di Semantic Scholar dan ambil paperId.
    """
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            r = client.get(
                f"{S2_API}/paper/search",
                params={"query": query, "limit": limit, "fields": "paperId,title,year,openAccessPdf,url"},
            )
            r.raise_for_status()
            data = r.json()
    except Exception:
        return []

    papers = data.get("data", [])
    return [p.get("paperId") for p in papers if p.get("paperId")]


def s2_fetch_summary(paper_ids: list[str]):
    """
    Ambil metadata open access PDF dari Semantic Scholar.
    """
    if not paper_ids:
        return []

    ids = ",".join(paper_ids)
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            r = client.get(
                f"{S2_API}/paper/batch",
                params={
                    "ids": ids,
                    "fields": "paperId,title,year,doi,openAccessPdf,url",
                },
            )
            r.raise_for_status()
            data = r.json()
    except Exception:
        return []

    metas = []
    for item in data or []:
        pdf = (item or {}).get("openAccessPdf") or {}
        pdf_url = pdf.get("url")
        if not pdf_url:
            continue
        metas.append(
            {
                "paper_id": item.get("paperId"),
                "title": item.get("title") or "Untitled",
                "year": item.get("year"),
                "doi": item.get("doi"),
                "source": "semantic_scholar",
                "pdf_url": pdf_url,
                "landing_url": item.get("url"),
            }
        )
    return metas
