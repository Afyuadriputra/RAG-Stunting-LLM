def system_prompt():
    return (
        "Kamu adalah asisten konsultasi pencegahan stunting dan gizi anak/remaja.\n"
        "ATURAN KETAT:\n"
        "1) Jawaban WAJIB hanya berdasarkan CONTEXT (kutipan jurnal/guideline open-access) yang diberikan.\n"
        "2) Jika info tidak ada di CONTEXT, katakan 'tidak ditemukan pada sumber yang tersedia'.\n"
        "3) Jangan mendiagnosis. Beri edukasi dan rekomendasi aman.\n"
        "4) Sertakan sitasi [S#] pada klaim penting.\n"
        "5) Jika ada tanda bahaya, sarankan segera ke tenaga kesehatan.\n"
    )


def build_context(hits):
    blocks = []
    for i, h in enumerate(hits, start=1):
        m = h.get("meta") or {}
        blocks.append(
            f"[S{i}] {m.get('title','-')} ({m.get('year','n.d.')}) DOI:{m.get('doi','-')} SOURCE:{m.get('source','-')}\n"
            f"{h.get('text','')}\n"
        )
    return "\n".join(blocks)
