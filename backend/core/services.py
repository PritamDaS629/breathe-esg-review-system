from decimal import Decimal

from django.utils import timezone

from .models import AuditEvent, DataSource, EmissionFactor, Facility, NormalizedActivity, UploadBatch
from .normalization import PARSERS, PLANT_LOOKUP, read_csv_bytes


def default_source_name(source_type):
    return {
        "sap": "SAP MM material movement CSV",
        "utility": "Green Button-style utility portal CSV",
        "travel": "Concur-style travel expense export",
    }[source_type]


def default_ingestion_mode(source_type):
    return {
        "sap": "scheduled CSV export from SAP MM/OData extract",
        "utility": "monthly portal CSV upload from facilities team",
        "travel": "expense report CSV export mirroring Concur categories",
    }[source_type]


def resolve_facility(tenant, code):
    if not code:
        return None
    info = PLANT_LOOKUP.get(code, {"code": code, "name": f"Unmapped facility {code}", "country": "US"})
    facility, _ = Facility.objects.get_or_create(
        tenant=tenant,
        code=info["code"],
        defaults={"name": info["name"], "country": info["country"]},
    )
    return facility


def factor_for(parsed):
    return EmissionFactor.objects.filter(
        category=parsed.factor_category,
        unit=parsed.normalized_unit,
    ).order_by("-valid_from").first()


def ingest_csv_bytes(tenant, source_type, filename, file_bytes, actor=None):
    if source_type not in PARSERS:
        raise ValueError("Unknown source type")
    source, _ = DataSource.objects.get_or_create(
        tenant=tenant,
        source_type=source_type,
        defaults={
            "name": default_source_name(source_type),
            "ingestion_mode": default_ingestion_mode(source_type),
            "owner": "Demo integration",
        },
    )
    batch = UploadBatch.objects.create(tenant=tenant, source=source, filename=filename)
    failures = []
    accepted = 0
    rows = read_csv_bytes(file_bytes)
    parser = PARSERS[source_type]
    for parsed in parser(rows):
        try:
            facility = resolve_facility(tenant, parsed.facility_code)
            factor = factor_for(parsed)
            kg = (parsed.normalized_quantity * factor.kg_co2e_per_unit) if factor else Decimal("0")
            status = "flagged" if parsed.flags else "needs_review"
            was_existing = NormalizedActivity.objects.filter(
                tenant=tenant,
                source=source,
                source_row_id=parsed.source_row_id,
            ).exists()
            activity, created = NormalizedActivity.objects.update_or_create(
                tenant=tenant,
                source=source,
                source_row_id=parsed.source_row_id,
                defaults={
                    "batch": batch,
                    "facility": facility,
                    "source_payload": parsed.payload,
                    "activity_date": parsed.activity_date,
                    "period_start": parsed.period_start,
                    "period_end": parsed.period_end,
                    "scope": parsed.scope,
                    "category": parsed.category,
                    "activity_type": parsed.activity_type,
                    "quantity": parsed.quantity,
                    "unit": parsed.unit,
                    "normalized_quantity": parsed.normalized_quantity,
                    "normalized_unit": parsed.normalized_unit,
                    "emission_factor": factor,
                    "calculated_kg_co2e": kg,
                    "confidence": parsed.confidence,
                    "review_status": status,
                    "flags": parsed.flags,
                    "edited": was_existing,
                },
            )
            AuditEvent.objects.create(
                tenant=tenant,
                activity=activity,
                actor=actor,
                action="ingested" if created else "reingested_update",
                after={"batch": batch.id, "flags": parsed.flags},
            )
            accepted += 1
        except Exception as exc:
            failures.append(str(exc))
    batch.total_rows = len(rows)
    batch.accepted_rows = accepted
    batch.failed_rows = len(failures)
    batch.status = "processed" if not failures else "failed"
    batch.notes = "\n".join(failures[:10])
    batch.processed_at = timezone.now()
    batch.save()
    return batch
