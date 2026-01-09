from rest_framework import serializers
from .models import Consultation, ChildPhoto


ALLOWED_CONTEXTS = {
    "wajah",
    "tubuh tampak depan",
    "tubuh tampak samping",
    "anak sedang makan",
    "porsi makanan",
    "lingkungan makan",
}


class ChildPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildPhoto
        fields = ["photo_id", "url", "captured_at", "context", "consent"]

    def validate_context(self, v: str) -> str:
        if v not in ALLOWED_CONTEXTS:
            raise serializers.ValidationError(
                f"context harus salah satu dari: {sorted(ALLOWED_CONTEXTS)}"
            )
        return v

    def validate(self, attrs):
        if attrs.get("consent") is not True:
            raise serializers.ValidationError("consent harus true untuk memproses foto.")
        return attrs


class ConsultationSerializer(serializers.ModelSerializer):
    child_photos = ChildPhotoSerializer(many=True, required=False)

    class Meta:
        model = Consultation
        fields = [
            "id",
            "mode",
            "age_value",
            "age_unit",
            "sex",
            "weight_kg",
            "height_cm",
            "measurement_type",
            "user_question",
            "child_photos",
            "vision_findings",
            "rag_citations",
            "answer_text",
            "created_at",
        ]
        read_only_fields = ["vision_findings", "rag_citations", "answer_text", "created_at"]

    def validate(self, attrs):
        mode = attrs["mode"]
        age_value = attrs["age_value"]
        age_unit = attrs["age_unit"]

        # Rules per mode
        if mode == Consultation.Mode.BALITA:
            if age_unit != "months" or not (0 <= age_value <= 59):
                raise serializers.ValidationError("Balita: age_unit=months, rentang 0–59.")
            # PB/TB rule
            if age_value < 24 and attrs["measurement_type"] != Consultation.MeasurementType.LENGTH:
                raise serializers.ValidationError("Balita <24 bulan: measurement_type harus length (PB).")
            if age_value >= 24 and attrs["measurement_type"] != Consultation.MeasurementType.HEIGHT:
                raise serializers.ValidationError("Balita ≥24 bulan: measurement_type harus height (TB).")

        elif mode == Consultation.Mode.ANAK_SEKOLAH:
            if age_unit != "years" or not (5 <= age_value <= 9):
                raise serializers.ValidationError("Anak sekolah: age_unit=years, rentang 5–9.")

        elif mode == Consultation.Mode.REMAJA:
            if age_unit != "years" or not (10 <= age_value <= 19):
                raise serializers.ValidationError("Remaja: age_unit=years, rentang 10–19.")

        # Sanity check angka
        w = float(attrs["weight_kg"])
        h = float(attrs["height_cm"])
        if not (1.0 <= w <= 200.0):
            raise serializers.ValidationError("weight_kg tidak masuk akal.")
        if not (30.0 <= h <= 230.0):
            raise serializers.ValidationError("height_cm tidak masuk akal.")

        return attrs

    def create(self, validated_data):
        photos = validated_data.pop("child_photos", [])
        c = Consultation.objects.create(**validated_data)

        for p in photos:
            ChildPhoto.objects.create(consultation=c, **p)

        return c
