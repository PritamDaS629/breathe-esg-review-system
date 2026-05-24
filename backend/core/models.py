from django.conf import settings
from django.db import models
from django.utils import timezone


class Tenant(models.Model):
    name = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Facility(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="facilities")
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=160)
    country = models.CharField(max_length=2, default="US")

    class Meta:
        unique_together = ("tenant", "code")

    def __str__(self):
        return f"{self.code} - {self.name}"


class DataSource(models.Model):
    SOURCE_TYPES = [
        ("sap", "SAP fuel/procurement"),
        ("utility", "Utility electricity"),
        ("travel", "Corporate travel"),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="sources")
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    name = models.CharField(max_length=160)
    ingestion_mode = models.CharField(max_length=80)
    owner = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class UploadBatch(models.Model):
    STATUS = [
        ("received", "Received"),
        ("processed", "Processed"),
        ("failed", "Failed"),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="batches")
    source = models.ForeignKey(DataSource, on_delete=models.PROTECT, related_name="batches")
    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS, default="received")
    total_rows = models.PositiveIntegerField(default=0)
    accepted_rows = models.PositiveIntegerField(default=0)
    failed_rows = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)


class EmissionFactor(models.Model):
    scope = models.CharField(max_length=10)
    category = models.CharField(max_length=80)
    unit = models.CharField(max_length=20)
    kg_co2e_per_unit = models.DecimalField(max_digits=12, decimal_places=6)
    geography = models.CharField(max_length=40, default="global")
    valid_from = models.DateField(default="2024-01-01")
    source = models.CharField(max_length=160)

    class Meta:
        unique_together = ("scope", "category", "unit", "geography", "valid_from")


class NormalizedActivity(models.Model):
    REVIEW_STATUS = [
        ("needs_review", "Needs review"),
        ("flagged", "Flagged"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="activities")
    source = models.ForeignKey(DataSource, on_delete=models.PROTECT, related_name="activities")
    batch = models.ForeignKey(UploadBatch, on_delete=models.PROTECT, related_name="activities")
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)
    source_row_id = models.CharField(max_length=120)
    source_payload = models.JSONField(default=dict)
    activity_date = models.DateField()
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    scope = models.CharField(max_length=10)
    category = models.CharField(max_length=80)
    activity_type = models.CharField(max_length=120)
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    unit = models.CharField(max_length=20)
    normalized_quantity = models.DecimalField(max_digits=14, decimal_places=4)
    normalized_unit = models.CharField(max_length=20)
    emission_factor = models.ForeignKey(EmissionFactor, on_delete=models.PROTECT, null=True, blank=True)
    calculated_kg_co2e = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    review_status = models.CharField(max_length=20, choices=REVIEW_STATUS, default="needs_review")
    flags = models.JSONField(default=list)
    edited = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "review_status"]),
            models.Index(fields=["tenant", "source", "source_row_id"]),
        ]
        unique_together = ("tenant", "source", "source_row_id")

    def lock(self, user=None):
        self.review_status = "approved"
        self.locked_at = timezone.now()
        self.approved_by = user
        self.save(update_fields=["review_status", "locked_at", "approved_by", "updated_at"])


class AuditEvent(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="audit_events")
    activity = models.ForeignKey(NormalizedActivity, on_delete=models.CASCADE, related_name="audit_events", null=True, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=80)
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
