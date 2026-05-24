from rest_framework import serializers

from .models import AuditEvent, DataSource, Facility, NormalizedActivity, Tenant, UploadBatch


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "slug"]


class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ["id", "code", "name", "country"]


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ["id", "source_type", "name", "ingestion_mode", "owner", "created_at"]


class UploadBatchSerializer(serializers.ModelSerializer):
    source = DataSourceSerializer()

    class Meta:
        model = UploadBatch
        fields = ["id", "source", "filename", "status", "total_rows", "accepted_rows", "failed_rows", "created_at", "processed_at", "notes"]


class ActivitySerializer(serializers.ModelSerializer):
    source = DataSourceSerializer()
    facility = FacilitySerializer()

    class Meta:
        model = NormalizedActivity
        fields = [
            "id", "source", "batch_id", "facility", "source_row_id", "source_payload",
            "activity_date", "period_start", "period_end", "scope", "category",
            "activity_type", "quantity", "unit", "normalized_quantity", "normalized_unit",
            "calculated_kg_co2e", "confidence", "review_status", "flags", "edited",
            "locked_at", "created_at", "updated_at",
        ]


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = ["id", "activity_id", "action", "before", "after", "created_at"]
