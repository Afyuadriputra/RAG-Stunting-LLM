from django.urls import path
from .views import IngestPDFView

urlpatterns = [
    path("rag/ingest/", IngestPDFView.as_view()),
]
