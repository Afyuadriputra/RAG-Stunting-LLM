from __future__ import annotations

from typing import Optional, Sequence, List

_MODEL = None
_DEVICE_LABEL: Optional[str] = None
_DEVICE_NAME: Optional[str] = None  # "cuda" atau "cpu"


def _detect_device():
    """
    Deteksi device terbaik (CUDA jika tersedia).
    Return: (device_name, device_label)
      - device_name: "cuda" / "cpu"
      - device_label: "cuda (RTX ...)" / "cpu"
    """
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            return "cuda", f"cuda ({name})"
    except Exception:
        pass
    return "cpu", "cpu"


def get_device_info() -> str:
    """
    Untuk logging: 'cuda (NVIDIA GeForce ...)' atau 'cpu'
    """
    global _DEVICE_LABEL, _DEVICE_NAME
    if _DEVICE_LABEL is None or _DEVICE_NAME is None:
        _DEVICE_NAME, _DEVICE_LABEL = _detect_device()
    return _DEVICE_LABEL


def get_embedder(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """
    Lazy-load SentenceTransformer dan cache di proses.
    """
    global _MODEL, _DEVICE_LABEL, _DEVICE_NAME

    if _MODEL is None:
        # lazy import supaya startup Django cepat
        from sentence_transformers import SentenceTransformer

        if _DEVICE_NAME is None or _DEVICE_LABEL is None:
            _DEVICE_NAME, _DEVICE_LABEL = _detect_device()

        _MODEL = SentenceTransformer(model_name, device=_DEVICE_NAME)

    return _MODEL


def embed(
    texts: Sequence[str],
    show_progress: bool = False,
    batch_size: Optional[int] = None,
) -> List[List[float]]:
    """
    Buat embeddings normalized untuk list teks.
    """
    model = get_embedder()

    global _DEVICE_NAME, _DEVICE_LABEL
    if _DEVICE_NAME is None or _DEVICE_LABEL is None:
        _DEVICE_NAME, _DEVICE_LABEL = _detect_device()

    if batch_size is None:
        batch_size = 64 if _DEVICE_NAME == "cuda" else 16

    vecs = model.encode(
        list(texts),
        normalize_embeddings=True,
        batch_size=batch_size,
        show_progress_bar=show_progress,
    )
    return [v.tolist() for v in vecs]
