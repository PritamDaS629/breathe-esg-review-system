# Tradeoffs

## 1. No direct upstream API connections

I did not build live SAP, utility, or Concur API integrations. Real credentials, tenant-specific authorization, and network access would dominate the four-day prototype. File ingestion lets the data model and review workflow be tested while still matching realistic export shapes.

## 2. No production emission factor library

The app uses placeholder factors with clear source labels. A production system should version official factor sets by geography, year, category, and methodology. I kept the factor model in place, but did not pretend a small hard-coded demo list is audit-grade.

## 3. No advanced allocation engine

Utility billing periods can cross reporting months, and travel rows can span multi-leg itineraries. I store period boundaries and flags, but I do not allocate partial periods into reporting months or reconstruct complete trips. That logic matters, but it should be built after the PM confirms the auditor's reporting rules.
