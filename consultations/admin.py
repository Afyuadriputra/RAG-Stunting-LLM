from django.contrib import admin
from .models import Consultation, ChildPhoto


class ChildPhotoInline(admin.TabularInline):
    model = ChildPhoto
    extra = 0


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ("id", "mode", "age_value", "age_unit", "sex", "created_at")
    list_filter = ("mode", "sex", "created_at")
    search_fields = ("user_question",)
    inlines = [ChildPhotoInline]


@admin.register(ChildPhoto)
class ChildPhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "photo_id", "context", "consent", "created_at")
    list_filter = ("context", "consent", "created_at")
