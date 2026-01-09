import httpx

OPENALEX_API = "https://api.openalex.org"


def openalex_search(query: str, per_page: int = 5):
    """
    Cari karya open-access via OpenAlex dan ambil daftar metadata.
    """
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            r = client.get(
                f"{OPENALEX_API}/works",
                params={
                    "search": query,
                    "per_page": per_page,
                    "filter": "is_oa:true",
                },
            )
            r.raise_for_status()
            data = r.json()
        return data.get("results", [])
    except Exception:
        return []


def openalex_fetch_summary(results):
    """
    Ambil metadata dan URL PDF dari hasil OpenAlex.
    """
    metas = []
    for item in results or []:
        title = item.get("title") or "Untitled"
        year = item.get("publication_year")
        doi = item.get("doi")
        primary = item.get("primary_location") or {}
        landing_url = primary.get("landing_page_url")
        best_oa = item.get("best_oa_location") or {}
        pdf_url = best_oa.get("pdf_url") or None

        if not pdf_url:
            continue

        metas.append(
            {
                "paper_id": item.get("id"),
                "title": title,
                "year": year,
                "doi": doi,
                "source": "openalex",
                "pdf_url": pdf_url,
                "landing_url": landing_url,
            }
        )
    return metas
