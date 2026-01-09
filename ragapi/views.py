from django.shortcuts import render

# Create your views here.
import os
import tempfile
import httpx

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .pdf_ingest import upsert_pdf


class IngestPDFView(APIView):
    """
    POST /api/rag/ingest/
    Body:
      {
        "pdf_url": "...",
        "title": "...",
        "year": 2021,
        "doi": "...",
        "source": "core|pmc|doaj|..."
      }
    """
    def post(self, request):
        pdf_url = request.data.get("pdf_url")
        if not pdf_url:
            return Response({"error": "pdf_url wajib"}, status=status.HTTP_400_BAD_REQUEST)

        paper_meta = {
            "paper_id": request.data.get("paper_id") or pdf_url,
            "title": request.data.get("title") or "Unknown title",
            "year": request.data.get("year"),
            "doi": request.data.get("doi"),
            "source": request.data.get("source", "oa"),
            "pdf_url": pdf_url,
        }

        with tempfile.TemporaryDirectory() as td:
            pdf_path = os.path.join(td, "paper.pdf")
            with httpx.Client(timeout=60, follow_redirects=True) as client:
                r = client.get(pdf_url)
                r.raise_for_status()
                with open(pdf_path, "wb") as f:
                    f.write(r.content)

            inserted = upsert_pdf(pdf_path, paper_meta)

        return Response({"inserted_chunks": inserted, "paper_meta": paper_meta}, status=status.HTTP_200_OK)
