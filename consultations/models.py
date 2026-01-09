import uuid
from django.db import models


class Consultation(models.Model):
    class Mode(models.TextChoices):
        BALITA = "balita", "Balita (0–59 bulan)"
        ANAK_SEKOLAH = "anak_sekolah", "Anak sekolah (5–9 tahun)"
        REMAJA = "remaja", "Remaja (10–19 tahun)"

    class Sex(models.TextChoices):
        MALE = "male", "Laki-laki"
        FEMALE = "female", "Perempuan"

    class MeasurementType(models.TextChoices):
        LENGTH = "length", "Panjang badan (PB, telentang)"
        HEIGHT = "height", "Tinggi badan (TB, berdiri)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    mode = models.CharField(max_length=20, choices=Mode.choices)

    # usia terstruktur
    age_value = models.PositiveIntegerField()
    age_unit = models.CharField(max_length=10)  # "months" atau "years"

    sex = models.CharField(max_length=10, choices=Sex.choices)

    # antropometri
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1)
    measurement_type = models.CharField(max_length=10, choices=MeasurementType.choices)

    user_question = models.TextField()

    # hasil pipeline (opsional)
    vision_findings = models.JSONField(null=True, blank=True)
    rag_citations = models.JSONField(null=True, blank=True)
    answer_text = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.mode} | {self.age_value}{self.age_unit} | {self.created_at:%Y-%m-%d %H:%M}"


class ChildPhoto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consultation = models.ForeignKey(
        Consultation, related_name="child_photos", on_delete=models.CASCADE
    )

    photo_id = models.CharField(max_length=50)
    url = models.URLField()

    captured_at = models.DateTimeField(null=True, blank=True)
    context = models.CharField(max_length=100)
    consent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.photo_id} | {self.context}"
