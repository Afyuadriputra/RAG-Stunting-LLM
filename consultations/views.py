import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Consultation
from .serializers import ConsultationSerializer
from ragapi.vision import analyze_images


class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = Consultation.objects.all().order_by("-created_at")
    serializer_class = ConsultationSerializer

    @action(detail=True, methods=["POST"])
    def process(self, request, pk=None):
        c: Consultation = self.get_object()

        try:
            # lazy import supaya startup cepat
            from ragapi.hybrid import answer_hybrid  # type: ignore

            if c.vision_findings is None:
                images = [
                    {"url": p.url, "context": p.context}
                    for p in c.child_photos.all()
                    if p.url
                ]
                if images:
                    c.vision_findings = analyze_images(images)
                    c.save()

            result = answer_hybrid(c, k=8)
            c.rag_citations = [h["meta"] for h in result.get("hits", [])]
            c.answer_text = result.get("answer")
            c.save()

            data = self.get_serializer(c).data
            data["did_autofetch"] = result.get("did_autofetch", False)
            return Response(data, status=status.HTTP_200_OK)

        except ModuleNotFoundError:
            c.answer_text = "RAG pipeline belum dihubungkan (ragapi.hybrid belum tersedia)."
            c.rag_citations = []
            c.save()
            return Response(self.get_serializer(c).data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Gagal memproses konsultasi", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UploadPhotoView(APIView):
    """
    POST /api/photos/upload/
    Form-data:
      - file: image file
    Response:
      { "photo_id": "...", "url": "..." }
    """

    def post(self, request):
        upload = request.FILES.get("file")
        if not upload:
            return Response({"error": "file wajib diisi"}, status=status.HTTP_400_BAD_REQUEST)

        ext = os.path.splitext(upload.name)[1].lower()
        if not ext or len(ext) > 10:
            ext = ".jpg"

        photo_id = uuid.uuid4().hex
        file_path = f"child_photos/{photo_id}{ext}"
        saved_path = default_storage.save(file_path, upload)

        url = default_storage.url(saved_path)
        if url.startswith(settings.MEDIA_URL):
            url = request.build_absolute_uri(url)

        return Response({"photo_id": photo_id, "url": url}, status=status.HTTP_201_CREATED)
