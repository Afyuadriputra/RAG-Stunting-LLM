import re
import uuid
import logging
from pypdf import PdfReader

from tqdm import tqdm
from .embeddings import embed, get_device_info
from .chroma_client import get_collection

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def pdf_to_text(
    pdf_path: str,
    max_pages: int | None = 50,
    max_chars: int = 300_000,
) -> str:
    logger.info(f"[PDF] Reading: {pdf_path}")

    reader = PdfReader(pdf_path)
    parts = []
    pages = reader.pages[:max_pages] if max_pages else reader.pages

    total = 0
    for i, page in enumerate(pages, start=1):
        txt = page.extract_text() or ""
        if not txt:
            continue

        txt = re.sub(r"\n{3,}", "\n\n", txt)
        txt = re.sub(r"[ \t]+\n", "\n", txt)

        parts.append(txt)
        total += len(txt)

        if i % 5 == 0:
            logger.info(f"[PDF]  extracted page {i}, chars={total}")

        if total >= max_chars:
            logger.warning(f"[PDF]  reached max_chars={max_chars}, stopping extraction")
            break

    text = "\n".join(parts).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)

    logger.info(f"[PDF] Finished extraction, total chars={len(text)}")
    return text


def chunk_text_iter(text: str, max_chars: int = 1800, overlap: int = 200):
    """
    Generator chunk yang aman:
    - selalu maju
    - pasti berhenti
    """
    if overlap >= max_chars:
        raise ValueError("overlap harus lebih kecil dari max_chars")

    i = 0
    n = len(text)

    while i < n:
        j = min(i + max_chars, n)
        c = text[i:j].strip()
        if c:
            yield c

        if j >= n:
            break  # penting: stop di akhir teks

        i = j - overlap  # geser dengan overlap
        if i < 0:
            i = 0


def upsert_pdf(pdf_path: str, paper_meta: dict, batch_size: int = 64) -> int:
    logger.info(f"[INGEST] Start PDF: {paper_meta.get('title')} ({pdf_path})")
    logger.info(f"[EMBED] Device: {get_device_info()}")

    text = pdf_to_text(pdf_path, max_pages=50, max_chars=300_000)
    if len(text) < 500:
        logger.warning("[INGEST] Text too short, skipping PDF")
        return 0

    col = get_collection()
    total_inserted = 0

    batch_docs, batch_ids, batch_metas = [], [], []
    chunk_index = 0

    # progress bar tanpa total (anti hang, tetap bergerak)
    pbar = tqdm(
        desc=f"Ingest {paper_meta.get('title')}",
        unit="chunk",
        dynamic_ncols=True,
    )

    for chunk in chunk_text_iter(text, max_chars=1800, overlap=200):
        batch_docs.append(chunk)
        batch_ids.append(str(uuid.uuid4()))
        batch_metas.append(
            {
                "paper_id": paper_meta.get("paper_id"),
                "title": paper_meta.get("title"),
                "year": paper_meta.get("year"),
                "doi": paper_meta.get("doi"),
                "source": paper_meta.get("source", "oa"),
                "pdf_url": paper_meta.get("pdf_url"),
                "landing_url": paper_meta.get("landing_url") or paper_meta.get("url"),
                "chunk_index": chunk_index,
            }
        )
        chunk_index += 1
        pbar.update(1)

        if len(batch_docs) >= batch_size:
            logger.info(f"[EMBED] Embedding+Upsert batch. total={total_inserted + len(batch_docs)}")
            embs = embed(batch_docs, show_progress=False)
            col.upsert(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas,
                embeddings=embs,
            )
            total_inserted += len(batch_docs)
            batch_docs, batch_ids, batch_metas = [], [], []

    # flush sisa batch
    if batch_docs:
        logger.info(f"[EMBED] Embedding+Upsert final batch. total={total_inserted + len(batch_docs)}")
        embs = embed(batch_docs, show_progress=False)
        col.upsert(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_metas,
            embeddings=embs,
        )
        total_inserted += len(batch_docs)

    pbar.close()

    logger.info(f"[DONE] PDF ingested: {paper_meta.get('title')} → {total_inserted} chunks")
    return total_inserted
