from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConsultationViewSet, UploadPhotoView

router = DefaultRouter()
router.register(r"consultations", ConsultationViewSet, basename="consultation")

urlpatterns = [
    path("", include(router.urls)),
    path("photos/upload/", UploadPhotoView.as_view()),
]
