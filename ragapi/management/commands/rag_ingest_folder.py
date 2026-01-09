import os
from django.core.management.base import BaseCommand, CommandError
from ragapi.pdf_ingest import upsert_pdf


class Command(BaseCommand):
    help = "Ingest semua file PDF dalam sebuah folder ke ChromaDB (RAG corpus)."

    def add_arguments(self, parser):
        parser.add_argument("--folder", required=True, help="Path folder yang berisi PDF")
        parser.add_argument("--source", default="core", help="Tag sumber (default: core)")
        parser.add_argument("--year", default=None, help="Tahun default jika tidak ada metadata")
        parser.add_argument("--recursive", action="store_true", help="Scan subfolder juga")

    def handle(self, *args, **opts):
        folder = opts["folder"]
        source = opts["source"]
        year = opts["year"]
        recursive = opts["recursive"]

        if not os.path.isdir(folder):
            raise CommandError(f"Folder tidak ditemukan: {folder}")

        pdf_files = []
        if recursive:
            for root, _, files in os.walk(folder):
                for fn in files:
                    if fn.lower().endswith(".pdf"):
                        pdf_files.append(os.path.join(root, fn))
        else:
            for fn in os.listdir(folder):
                if fn.lower().endswith(".pdf"):
                    pdf_files.append(os.path.join(folder, fn))

        if not pdf_files:
            raise CommandError("Tidak ada file PDF di folder tersebut.")

        total_chunks = 0
        for path in sorted(pdf_files):
            filename = os.path.basename(path)
            title = os.path.splitext(filename)[0]

            paper_meta = {
                "paper_id": filename,
                "title": title,
                "year": int(year) if year else None,
                "doi": None,
                "source": source,
                "pdf_url": None,
            }

            inserted = upsert_pdf(path, paper_meta)
            total_chunks += inserted
            self.stdout.write(self.style.SUCCESS(f"[OK] {filename}: inserted_chunks={inserted}"))

        self.stdout.write(self.style.SUCCESS(f"DONE. Total inserted_chunks={total_chunks}"))
