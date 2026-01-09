from .chroma_client import get_collection
from .embeddings import embed


def retrieve(query: str, k: int = 8, where: dict | None = None):
    col = get_collection()
    q_emb = embed([query])[0]

    res = col.query(
        query_embeddings=[q_emb],
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        hits.append({"text": doc, "meta": meta, "distance": dist})
    return hits
