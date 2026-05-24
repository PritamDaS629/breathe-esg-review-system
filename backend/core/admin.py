from django.contrib import admin

from .models import AuditEvent, DataSource, EmissionFactor, Facility, NormalizedActivity, Tenant, UploadBatch

admin.site.register([Tenant, Facility, DataSource, UploadBatch, EmissionFactor, NormalizedActivity, AuditEvent])
