# Data Model

## Core shape

The prototype uses a normalized `NormalizedActivity` table as the review and audit boundary. Every row points back to:

- `Tenant`: company boundary for multi-tenancy.
- `DataSource`: the upstream system and ingestion mode.
- `UploadBatch`: the specific file/import event that produced the row.
- `source_row_id`: stable upstream identifier for idempotent re-ingestion.
- `source_payload`: raw source row JSON, retained for traceability.
- `EmissionFactor`: the factor used for the current calculation.
- `AuditEvent`: append-only record of ingest, re-ingest, approve, and reject actions.

This gives analysts one queue across Scope 1, Scope 2, and Scope 3 while keeping the source lineage intact.

## Multi-tenancy

Each operational table carries `tenant_id`. In a production version, this would be enforced in middleware from the authenticated user's organization and by database row-level security. The prototype defaults to one demo tenant, `Acme Manufacturing`, but the schema is tenant-scoped.

## Source-of-truth tracking

`DataSource` records the source type and chosen ingestion mechanism. `UploadBatch` records filename, timestamps, accepted rows, and failed rows. `NormalizedActivity.source_payload` preserves the original row exactly as received, so auditors can compare the normalized row with the source export. Re-ingestion updates the existing normalized row by `(tenant, source, source_row_id)` rather than duplicating it.

## Unit normalization

The app stores both source and normalized values:

- `quantity` and `unit`: value from the source.
- `normalized_quantity` and `normalized_unit`: value used for calculation.

Examples:

- SAP fuel gallons become liters.
- Utility MWh becomes kWh.
- Travel kilometers become passenger miles when a travel row needs a mileage factor.

Rows that cannot be normalized are rejected at ingestion and reported on the batch. Rows that normalize but look risky receive flags and lower confidence.

## Scope categorization

- SAP fuel issues become `Scope 1 / stationary_combustion`.
- Utility electricity becomes `Scope 2 / purchased_electricity`.
- Flights, hotels, and ground transport become `Scope 3 / business_travel`.

The categorization is explicit on `NormalizedActivity` because downstream audit packages should not need to infer scope from source type.

## Review and audit lock

Rows start as `needs_review` or `flagged`. Approval sets `review_status=approved`, records `locked_at`, and creates an `AuditEvent`. The prototype does not hard-block all edits to approved rows at the database layer; in production I would add an immutable approval table or database trigger so audit locks cannot be bypassed by application code.

## Why this model

The model is intentionally activity-centric. SAP, utilities, and travel all have different source schemas, but the analyst needs one consistent review queue: date, source, scope, activity, normalized quantity, emissions, flags, and status. Keeping raw payloads plus normalized fields avoids overfitting the relational model to every possible upstream export while preserving enough evidence for audit.
