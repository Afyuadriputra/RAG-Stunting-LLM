import base64
import json
from typing import List, Dict

import httpx

from .openrouter_client import chat_vision


def _to_data_url(url: str, max_bytes: int = 3_000_000) -> str | None:
    """
    Unduh gambar dan ubah ke data URL agar bisa diproses LLM vision.
    """
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            r = client.get(url)
            r.raise_for_status()
            content = r.content
            if len(content) > max_bytes:
                return None
            content_type = r.headers.get("content-type", "image/jpeg")
    except Exception:
        return None

    b64 = base64.b64encode(content).decode("ascii")
    return f"data:{content_type};base64,{b64}"


def analyze_images(image_items: List[Dict[str, str]]) -> dict | None:
    """
    Jalankan analisis visual untuk daftar gambar.
    image_items: [{"url": "...", "context": "..."}]
    """
    if not image_items:
        return None

    vision_prompt = (
        "Anda adalah asisten konsultasi gizi anak. "
        "Analisis gambar hanya berdasarkan observasi visual yang jelas, tanpa diagnosis medis. "
        "Fokuskan pada hal terkait gizi/pertumbuhan/pola makan bila terlihat. "
        "Keluarkan JSON valid dengan struktur:\n"
        "{"
        "\"summary\": string, "
        "\"observations\": [string], "
        "\"possible_concerns\": [string], "
        "\"red_flags\": [string], "
        "\"confidence\": \"low\"|\"medium\"|\"high\""
        "}"
    )

    content = [{"type": "text", "text": vision_prompt}]
    for item in image_items:
        data_url = _to_data_url(item["url"])
        if not data_url:
            continue
        label = item.get("context") or "gambar"
        content.append({"type": "text", "text": f"Konteks: {label}"})
        content.append({"type": "image_url", "image_url": {"url": data_url}})

    if len(content) == 1:
        return None

    raw = chat_vision(
        messages=[
            {"role": "system", "content": "Anda adalah asisten yang patuh pada format JSON."},
            {"role": "user", "content": content},
        ],
        max_tokens=600,
    )

    raw_text = str(raw).strip()
    json_block = None

    if "```" in raw_text.lower():
        start = raw_text.lower().find("```json")
        if start != -1:
            end = raw_text.lower().find("```", start + 6)
            if end != -1:
                json_block = raw_text[start + 7:end].strip()
    if not json_block:
        first = raw_text.find("{")
        last = raw_text.rfind("}")
        if first != -1 and last != -1 and last > first:
            json_block = raw_text[first:last + 1]

    if json_block:
        try:
            return json.loads(json_block)
        except Exception:
            pass

    return {"summary": raw_text, "observations": [], "possible_concerns": [], "red_flags": [], "confidence": "low"}
