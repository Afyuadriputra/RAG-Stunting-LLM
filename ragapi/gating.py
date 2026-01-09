def evidence_is_weak(hits, min_hits=4, dist_threshold=0.35, min_unique_papers=2):
    """
    Heuristik sederhana:
    - jika hits sedikit
    - atau distance terbaik jelek (semakin kecil semakin mirip)
    - atau sumber unik terlalu sedikit
    """
    if not hits or len(hits) < min_hits:
        return True

    best_dist = hits[0].get("distance", 1.0)
    if best_dist is None:
        best_dist = 1.0
    if best_dist > dist_threshold:
        return True

    paper_keys = set()
    for h in hits:
        meta = h.get("meta") or {}
        key = meta.get("paper_id") or meta.get("doi") or meta.get("pdf_url") or meta.get("title")
        if key:
            paper_keys.add(key)

    if len(paper_keys) < min_unique_papers:
        return True

    return False
