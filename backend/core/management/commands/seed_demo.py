from pathlib import Path

from django.core.management.base import BaseCommand

from core.models import DataSource, EmissionFactor, Facility, Tenant
from core.services import ingest_csv_bytes
from core.views import create_demo_user


class Command(BaseCommand):
    help = "Seed demo tenant, sources, factors, and sample ingested rows."

    def handle(self, *args, **options):
        tenant, _ = Tenant.objects.get_or_create(name="Acme Manufacturing", slug="acme")
        Facility.objects.get_or_create(tenant=tenant, code="1000", defaults={"name": "Detroit Assembly Plant", "country": "US"})
        Facility.objects.get_or_create(tenant=tenant, code="2000", defaults={"name": "Bangalore Components Plant", "country": "IN"})
        Facility.objects.get_or_create(tenant=tenant, code="DE01", defaults={"name": "Hamburg Distribution Center", "country": "DE"})
        self.seed_factors()
        self.seed_sources(tenant)
        create_demo_user()
        self.seed_samples(tenant)
        self.stdout.write(self.style.SUCCESS("Seeded Breathe ESG demo data."))

    def seed_factors(self):
        factors = [
            ("Scope 1", "diesel_liters", "L", "2.680000", "EPA-style stationary diesel placeholder"),
            ("Scope 2", "electricity_kwh_us", "kWh", "0.386000", "US grid average placeholder"),
            ("Scope 3", "flight_miles", "mile", "0.158000", "DEFRA-style passenger flight placeholder"),
            ("Scope 3", "hotel_nights", "night", "15.000000", "Hotel night average placeholder"),
            ("Scope 3", "ground_miles", "mile", "0.192000", "Passenger vehicle placeholder"),
        ]
        for scope, category, unit, kg, source in factors:
            EmissionFactor.objects.get_or_create(
                scope=scope,
                category=category,
                unit=unit,
                geography="global" if scope == "Scope 3" else "US",
                valid_from="2024-01-01",
                defaults={"kg_co2e_per_unit": kg, "source": source},
            )

    def seed_sources(self, tenant):
        DataSource.objects.get_or_create(
            tenant=tenant,
            source_type="sap",
            defaults={"name": "SAP MM material movement CSV", "ingestion_mode": "scheduled CSV export", "owner": "ERP team"},
        )
        DataSource.objects.get_or_create(
            tenant=tenant,
            source_type="utility",
            defaults={"name": "Green Button-style utility portal CSV", "ingestion_mode": "monthly file upload", "owner": "Facilities"},
        )
        DataSource.objects.get_or_create(
            tenant=tenant,
            source_type="travel",
            defaults={"name": "Concur-style travel expense export", "ingestion_mode": "CSV export", "owner": "Travel ops"},
        )

    def seed_samples(self, tenant):
        root = Path(__file__).resolve().parents[4] / "sample_data"
        files = {
            "sap": "sap_material_movements.csv",
            "utility": "utility_green_button_style.csv",
            "travel": "concur_travel_segments.csv",
        }
        for source_type, filename in files.items():
            path = root / filename
            if path.exists():
                ingest_csv_bytes(tenant, source_type, filename, path.read_bytes())
