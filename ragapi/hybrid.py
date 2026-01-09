import os
import tempfile
import httpx
import json

from .retrieval import retrieve
from .gating import evidence_is_weak
from .pdf_ingest import upsert_pdf
from .sources_pmc import pmc_search, pmc_fetch_summary
from .sources_semantic_scholar import s2_search, s2_fetch_summary
from .sources_openalex import openalex_search, openalex_fetch_summary
from .prompts import system_prompt, build_context
from .openrouter_client import chat


def build_retrieval_query(c) -> str:
    # bisa kamu upgrade nanti (keyword expansion, include vision_findings, dsb.)
    vision = ""
    if c.vision_findings:
        try:
            vision = json.dumps(c.vision_findings, ensure_ascii=True)
        except Exception:
            vision = str(c.vision_findings)
    return (
        f"Topik: pencegahan stunting / gizi anak dan remaja.\n"
        f"Mode: {c.mode}.\n"
        f"Umur: {c.age_value} {c.age_unit}. Gender: {c.sex}.\n"
        f"BB: {c.weight_kg} kg. TB/PB: {c.height_cm} cm.\n"
        f"Pertanyaan: {c.user_question}\n"
        f"Temuan visual (jika ada): {vision}\n"
    )


def _download_pdf(url: str, out_path: str):
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)


def _build_external_query(query: str, max_len: int = 400) -> str:
    """
    Batasi query untuk provider eksternal agar tidak terlalu panjang.
    """
    if len(query) <= max_len:
        return query
    return query[:max_len]


def autofetch_oa_and_ingest(query: str, max_papers: int = 3) -> int:
    """
    On-demand: cari OA paper dari PMC/Semantic Scholar/OpenAlex → download PDF → ingest ke Chroma.
    """
    external_query = _build_external_query(query)
    pmcids = pmc_search(external_query, retmax=max_papers)
    metas = pmc_fetch_summary(pmcids)
    metas += s2_fetch_summary(s2_search(external_query, limit=max_papers))
    metas += openalex_fetch_summary(openalex_search(external_query, per_page=max_papers))

    inserted_total = 0
    with tempfile.TemporaryDirectory() as td:
        for meta in metas:
            pdf_url = meta.get("pdf_url")
            if not pdf_url:
                continue

            pdf_path = os.path.join(td, f"{meta['paper_id']}.pdf")
            try:
                _download_pdf(pdf_url, pdf_path)
                inserted = upsert_pdf(pdf_path, paper_meta=meta)
                inserted_total += inserted
            except Exception:
                # skip jika ada yang gagal
                continue

    return inserted_total


def _format_sources(hits):
    lines = []
    for i, h in enumerate(hits, start=1):
        m = h.get("meta") or {}
        title = m.get("title") or m.get("paper_id") or "-"
        parts = [title]

        year = m.get("year")
        if year:
            parts.append(str(year))

        doi = m.get("doi")
        if doi:
            parts.append(f"DOI:{doi}")

        source = m.get("source")
        if source:
            parts.append(f"SOURCE:{source}")

        pdf_url = m.get("pdf_url")
        landing_url = m.get("landing_url") or m.get("url")
        if pdf_url:
            parts.append(f"PDF:{pdf_url}")
        if landing_url:
            parts.append(f"URL:{landing_url}")

        lines.append(f"[S{i}] " + " | ".join(parts))
    return "\n".join(lines)


def answer_hybrid(c, k: int = 8):
    """
    Hybrid RAG:
    1) retrieve dari Chroma
    2) jika bukti lemah → autofetch OA PMC + ingest
    3) retrieve ulang
    4) LLM jawab grounded + sitasi
    """
    query = build_retrieval_query(c)

    hits = retrieve(query=query, k=k)
    did_autofetch = False

    if evidence_is_weak(hits):
        inserted = autofetch_oa_and_ingest(query, max_papers=3)
        if inserted > 0:
            did_autofetch = True
            hits = retrieve(query=query, k=k)

    context = build_context(hits)
    if not context.strip():
        answer = (
            "Mohon maaf, informasi detail (CONTEXT) yang Anda lampirkan kosong. "
            "Berdasarkan aturan ketat yang diberikan, saya tidak dapat memberikan edukasi "
            "berdasarkan kutipan jurnal atau guideline spesifik karena informasi tidak ditemukan "
            "pada sumber yang tersedia.\n\n"
            "Silakan coba lagi setelah menambahkan sumber atau melakukan ingest dokumen."
        )
        return {"answer": answer, "hits": hits, "did_autofetch": did_autofetch}

    user_prompt = f"""
DATA USER:
- mode: {c.mode}
- umur: {c.age_value} {c.age_unit}
- gender: {c.sex}
- BB: {c.weight_kg} kg
- TB/PB: {c.height_cm} cm ({c.measurement_type})
- pertanyaan: {c.user_question}
 - temuan visual (jika ada): {c.vision_findings}

CONTEXT:
{context}

Tulis jawaban terstruktur:
1) Ringkasan singkat berbasis data (tanpa diagnosis berlebihan)
2) Rekomendasi praktis (poin-poin)
3) Kapan harus ke tenaga kesehatan (red flags)
Catatan: sumber akan ditambahkan otomatis, tapi tetap gunakan [S#] pada klaim penting.

Jika CONTEXT tidak cukup, katakan 'tidak ditemukan pada sumber yang tersedia' dan sarankan langkah aman.
""".strip()

    answer = chat(
        messages=[
            {"role": "system", "content": system_prompt()},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1000,
    )

    sources = _format_sources(hits)
    if sources:
        answer = f"{answer}\n\n### 4) Sumber (otomatis)\n{sources}"

    return {"answer": answer, "hits": hits, "did_autofetch": did_autofetch}
