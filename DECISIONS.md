# Decisions

## SAP source

Chosen subset: SAP MM material movement export for fuel issues, represented as a CSV extract with columns commonly mapped from material document fields: material document, posting date, plant, material, movement type, quantity, and unit.

Why: The assignment mentions fuel and procurement. For fuel consumed by company-controlled equipment, material movements are a realistic source because they include plant, material, movement type, posting date, quantity, and unit. I chose a file extract instead of direct OData/BAPI calls because enterprise onboarding often starts before VPN/API access is available.

Handled:

- German/English header variants.
- Multiple date formats.
- Liters and gallons.
- Plant code lookup.
- Movement type sanity check.

Ignored:

- Full IDoc segment parsing.
- Purchase order line enrichment.
- Material master unit conversion tables.
- Reversal documents and document chains.

PM question: Which SAP module and transaction is the client actually using as the fuel source of truth: MM material documents, FI invoices, PM equipment fueling logs, or something custom?

## Utility electricity source

Chosen subset: Green Button-style utility portal CSV uploaded monthly by facilities.

Why: Many utility portals provide either CSV or XML exports, and facilities teams frequently send portal downloads before API authorization is in place. Billing periods do not always align to calendar months, so the model stores service start and service end separately from activity date.

Handled:

- kWh and MWh.
- Meter IDs.
- Facility mapping.
- Billing period length flags.
- Missing tariff flags.

Ignored:

- Green Button XML parsing.
- Interval reads at 15-minute granularity.
- Demand charges and tiered tariff calculations.
- Supplier-specific renewable contracts.

PM question: Do auditors need billed kWh only, or interval-level data to allocate usage across reporting months?

## Corporate travel source

Chosen subset: Concur-style expense export with flight, hotel, and ground transport rows.

Why: Travel systems expose expense categories and itinerary/segment data, but distance is not always present. Airport-code based distance fallback is enough to show the right design pressure without building a full routing service.

Handled:

- Flights with origin/destination airport codes.
- Flight distance fallback for known airport pairs.
- Hotel nights.
- Ground transport distance.
- Missing distance flags.

Ignored:

- Direct Concur API OAuth.
- Cabin class multipliers.
- Radiative forcing.
- Employee home office/privacy constraints.
- Multi-leg trip reconstruction.

PM question: Should emissions be calculated from booked itinerary, expensed receipt, or approved travel request when those disagree?

## Analyst UX

I kept the dashboard focused on one operational loop: upload source file, see what normalized, inspect suspicious rows, approve or reject. I did not add generic CRUD pages because they would dilute the assignment's review workflow.

## Deployment

The repository includes Render config. The frontend builds into static assets and Django serves the app so the deployed service is one web process. This is simpler than deploying separate frontend and backend services for a prototype.
