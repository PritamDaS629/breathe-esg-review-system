from django.contrib.auth.models import User
from django.db.models import Count, Sum
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import AuditEvent, DataSource, NormalizedActivity, Tenant, UploadBatch
from .serializers import ActivitySerializer, DataSourceSerializer, TenantSerializer, UploadBatchSerializer
from .services import ingest_csv_bytes


def default_tenant():
    tenant, _ = Tenant.objects.get_or_create(name="Acme Manufacturing", slug="acme")
    return tenant


def factor_for(parsed):
    return EmissionFactor.objects.filter(
        category=parsed.factor_category,
        unit=parsed.normalized_unit,
    ).order_by("-valid_from").first()


@api_view(["GET"])
def bootstrap(request):
    tenant = default_tenant()
    sources = DataSource.objects.filter(tenant=tenant).order_by("source_type")
    return Response({
        "tenant": TenantSerializer(tenant).data,
        "sources": DataSourceSerializer(sources, many=True).data,
        "counts": dashboard_counts(tenant),
    })


def dashboard_counts(tenant):
    by_status = dict(NormalizedActivity.objects.filter(tenant=tenant).values_list("review_status").annotate(Count("id")))
    by_scope = list(NormalizedActivity.objects.filter(tenant=tenant).values("scope").annotate(count=Count("id"), kg=Sum("calculated_kg_co2e")).order_by("scope"))
    return {
        "needs_review": by_status.get("needs_review", 0) + by_status.get("flagged", 0),
        "approved": by_status.get("approved", 0),
        "rejected": by_status.get("rejected", 0),
        "total_kg_co2e": NormalizedActivity.objects.filter(tenant=tenant).aggregate(total=Sum("calculated_kg_co2e"))["total"] or 0,
        "by_scope": by_scope,
    }


@api_view(["GET"])
def activities(request):
    tenant = default_tenant()
    status_filter = request.GET.get("status")
    qs = NormalizedActivity.objects.filter(tenant=tenant).select_related("source", "facility", "batch").order_by("-activity_date", "-id")
    if status_filter and status_filter != "all":
        qs = qs.filter(review_status=status_filter)
    return Response(ActivitySerializer(qs[:200], many=True).data)


@api_view(["GET"])
def batches(request):
    tenant = default_tenant()
    qs = UploadBatch.objects.filter(tenant=tenant).select_related("source").order_by("-created_at")
    return Response(UploadBatchSerializer(qs[:50], many=True).data)


@api_view(["POST"])
def upload_source(request, source_type):
    tenant = default_tenant()
    upload = request.FILES.get("file")
    if not upload:
        return Response({"error": "Attach a CSV file as 'file'."}, status=400)
    try:
        batch = ingest_csv_bytes(
            tenant,
            source_type,
            upload.name,
            upload.read(),
            request.user if request.user.is_authenticated else None,
        )
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    return Response(UploadBatchSerializer(batch).data, status=201)


@api_view(["POST"])
def approve_activity(request, pk):
    tenant = default_tenant()
    activity = NormalizedActivity.objects.get(tenant=tenant, pk=pk)
    before = {"review_status": activity.review_status, "locked_at": activity.locked_at.isoformat() if activity.locked_at else None}
    activity.lock(request.user if request.user.is_authenticated else None)
    AuditEvent.objects.create(
        tenant=tenant,
        activity=activity,
        actor=request.user if request.user.is_authenticated else None,
        action="approved_locked",
        before=before,
        after={"review_status": activity.review_status, "locked_at": activity.locked_at.isoformat()},
    )
    return Response(ActivitySerializer(activity).data)


@api_view(["POST"])
def reject_activity(request, pk):
    tenant = default_tenant()
    activity = NormalizedActivity.objects.get(tenant=tenant, pk=pk)
    before = {"review_status": activity.review_status}
    reason = request.data.get("reason", "Rejected by analyst")
    activity.review_status = "rejected"
    activity.save(update_fields=["review_status", "updated_at"])
    AuditEvent.objects.create(
        tenant=tenant,
        activity=activity,
        actor=request.user if request.user.is_authenticated else None,
        action="rejected",
        before=before,
        after={"review_status": "rejected", "reason": reason},
    )
    return Response(ActivitySerializer(activity).data)


def create_demo_user():
    if not User.objects.filter(username="analyst@acme.example").exists():
        User.objects.create_user("analyst@acme.example", "analyst@acme.example", "breathe-demo")
