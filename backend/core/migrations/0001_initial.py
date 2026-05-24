# Generated for the Breathe ESG internship prototype.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, unique=True)),
                ("slug", models.SlugField(unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="EmissionFactor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scope", models.CharField(max_length=10)),
                ("category", models.CharField(max_length=80)),
                ("unit", models.CharField(max_length=20)),
                ("kg_co2e_per_unit", models.DecimalField(decimal_places=6, max_digits=12)),
                ("geography", models.CharField(default="global", max_length=40)),
                ("valid_from", models.DateField(default="2024-01-01")),
                ("source", models.CharField(max_length=160)),
            ],
            options={"unique_together": {("scope", "category", "unit", "geography", "valid_from")}},
        ),
        migrations.CreateModel(
            name="DataSource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_type", models.CharField(choices=[("sap", "SAP fuel/procurement"), ("utility", "Utility electricity"), ("travel", "Corporate travel")], max_length=20)),
                ("name", models.CharField(max_length=160)),
                ("ingestion_mode", models.CharField(max_length=80)),
                ("owner", models.CharField(blank=True, max_length=160)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sources", to="core.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="Facility",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=40)),
                ("name", models.CharField(max_length=160)),
                ("country", models.CharField(default="US", max_length=2)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="facilities", to="core.tenant")),
            ],
            options={"unique_together": {("tenant", "code")}},
        ),
        migrations.CreateModel(
            name="UploadBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("filename", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("received", "Received"), ("processed", "Processed"), ("failed", "Failed")], default="received", max_length=20)),
                ("total_rows", models.PositiveIntegerField(default=0)),
                ("accepted_rows", models.PositiveIntegerField(default=0)),
                ("failed_rows", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="batches", to="core.datasource")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="batches", to="core.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="NormalizedActivity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_row_id", models.CharField(max_length=120)),
                ("source_payload", models.JSONField(default=dict)),
                ("activity_date", models.DateField()),
                ("period_start", models.DateField(blank=True, null=True)),
                ("period_end", models.DateField(blank=True, null=True)),
                ("scope", models.CharField(max_length=10)),
                ("category", models.CharField(max_length=80)),
                ("activity_type", models.CharField(max_length=120)),
                ("quantity", models.DecimalField(decimal_places=4, max_digits=14)),
                ("unit", models.CharField(max_length=20)),
                ("normalized_quantity", models.DecimalField(decimal_places=4, max_digits=14)),
                ("normalized_unit", models.CharField(max_length=20)),
                ("calculated_kg_co2e", models.DecimalField(decimal_places=4, default=0, max_digits=14)),
                ("confidence", models.DecimalField(decimal_places=2, default=1, max_digits=5)),
                ("review_status", models.CharField(choices=[("needs_review", "Needs review"), ("flagged", "Flagged"), ("approved", "Approved"), ("rejected", "Rejected")], default="needs_review", max_length=20)),
                ("flags", models.JSONField(default=list)),
                ("edited", models.BooleanField(default=False)),
                ("locked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="activities", to="core.uploadbatch")),
                ("emission_factor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="core.emissionfactor")),
                ("facility", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.facility")),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="activities", to="core.datasource")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activities", to="core.tenant")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["tenant", "review_status"], name="core_normal_tenant__2f67b7_idx"),
                    models.Index(fields=["tenant", "source", "source_row_id"], name="core_normal_tenant__7057cf_idx"),
                ],
                "unique_together": {("tenant", "source", "source_row_id")},
            },
        ),
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=80)),
                ("before", models.JSONField(blank=True, default=dict)),
                ("after", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("activity", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="audit_events", to="core.normalizedactivity")),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audit_events", to="core.tenant")),
            ],
        ),
    ]
