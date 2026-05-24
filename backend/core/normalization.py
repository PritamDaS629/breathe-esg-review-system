import csv
import io
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from dateutil import parser as date_parser


UNIT_ALIASES = {
    "l": "L",
    "liter": "L",
    "litre": "L",
    "liters": "L",
    "litres": "L",
    "gal": "gal",
    "gallon": "gal",
    "gallons": "gal",
    "kwh": "kWh",
    "mwh": "MWh",
    "mi": "mile",
    "mile": "mile",
    "miles": "mile",
    "km": "km",
    "kilometer": "km",
    "kilometers": "km",
    "night": "night",
    "nights": "night",
    "usd": "USD",
}

CONVERSIONS = {
    ("gal", "L"): Decimal("3.78541"),
    ("MWh", "kWh"): Decimal("1000"),
    ("km", "mile"): Decimal("0.621371"),
}

PLANT_LOOKUP = {
    "1000": {"code": "1000", "name": "Detroit Assembly Plant", "country": "US"},
    "2000": {"code": "2000", "name": "Bangalore Components Plant", "country": "IN"},
    "DE01": {"code": "DE01", "name": "Hamburg Distribution Center", "country": "DE"},
}

AIRPORT_DISTANCE_MILES = {
    ("JFK", "LHR"): 3451,
    ("SFO", "SEA"): 679,
    ("BLR", "DEL"): 1060,
    ("FRA", "JFK"): 3852,
}


@dataclass
class ParsedRow:
    source_row_id: str
    payload: dict
    activity_date: date
    period_start: date | None
    period_end: date | None
    scope: str
    category: str
    activity_type: str
    quantity: Decimal
    unit: str
    normalized_quantity: Decimal
    normalized_unit: str
    facility_code: str | None
    factor_category: str
    flags: list[str]
    confidence: Decimal


def read_csv_bytes(file_bytes):
    text = file_bytes.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def first_value(row, *names):
    lower_map = {k.strip().lower(): v for k, v in row.items()}
    for name in names:
        value = lower_map.get(name.lower())
        if value not in (None, ""):
            return str(value).strip()
    return ""


def parse_decimal(value):
    try:
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        raise ValueError(f"Invalid number: {value}")


def parse_date(value):
    if not value:
        raise ValueError("Missing date")
    return date_parser.parse(value, dayfirst=False).date()


def normalize_unit(quantity, unit, target_unit):
    unit = UNIT_ALIASES.get(str(unit).strip().lower(), str(unit).strip())
    if unit == target_unit:
        return quantity, unit
    factor = CONVERSIONS.get((unit, target_unit))
    if not factor:
        raise ValueError(f"No conversion from {unit} to {target_unit}")
    return quantity * factor, target_unit


def parse_sap(rows):
    parsed = []
    for idx, row in enumerate(rows, start=1):
        flags = []
        row_id = first_value(row, "Material Document", "Materialbeleg", "MAT_DOC", "document_id") or f"sap-{idx}"
        posting_date = parse_date(first_value(row, "Posting Date", "Buchungsdatum", "BUDAT", "date"))
        plant = first_value(row, "Plant", "Werk", "WERKS", "plant")
        material = first_value(row, "Material", "MATNR", "material")
        movement = first_value(row, "Movement Type", "BWART", "movement_type")
        qty = parse_decimal(first_value(row, "Quantity", "Menge", "MENGE", "qty"))
        unit = first_value(row, "Unit", "MEINS", "Einheit", "uom")
        normalized, normalized_unit = normalize_unit(qty, unit, "L")
        if plant and plant not in PLANT_LOOKUP:
            flags.append("unknown_plant_code")
        if movement not in {"201", "261", "101"}:
            flags.append("unexpected_movement_type")
        if normalized <= 0:
            flags.append("non_positive_quantity")
        parsed.append(ParsedRow(
            row_id, row, posting_date, None, None, "Scope 1", "stationary_combustion",
            f"SAP fuel issue {material or 'unknown material'}", qty, UNIT_ALIASES.get(unit.lower(), unit),
            normalized, normalized_unit, plant or None, "diesel_liters", flags,
            Decimal("0.65") if flags else Decimal("0.92"),
        ))
    return parsed


def parse_utility(rows):
    parsed = []
    for idx, row in enumerate(rows, start=1):
        flags = []
        meter = first_value(row, "Meter ID", "meter", "meter_number") or "unknown-meter"
        start = parse_date(first_value(row, "Service Start", "billing_start", "period_start", "from"))
        end = parse_date(first_value(row, "Service End", "billing_end", "period_end", "to"))
        usage = parse_decimal(first_value(row, "Usage", "kWh", "USAGE", "energy"))
        unit = first_value(row, "Unit", "uom") or "kWh"
        normalized, normalized_unit = normalize_unit(usage, unit, "kWh")
        facility_code = first_value(row, "Facility", "site", "plant")
        tariff = first_value(row, "Tariff", "rate")
        if (end - start).days not in range(25, 37):
            flags.append("billing_period_not_month_like")
        if not tariff:
            flags.append("missing_tariff")
        if normalized <= 0:
            flags.append("non_positive_usage")
        parsed.append(ParsedRow(
            f"utility-{meter}-{start.isoformat()}-{idx}", row, end, start, end, "Scope 2",
            "purchased_electricity", f"Electricity meter {meter}", usage,
            UNIT_ALIASES.get(unit.lower(), unit), normalized, normalized_unit,
            facility_code or None, "electricity_kwh_us", flags,
            Decimal("0.70") if flags else Decimal("0.95"),
        ))
    return parsed


def parse_travel(rows):
    parsed = []
    for idx, row in enumerate(rows, start=1):
        flags = []
        expense_id = first_value(row, "Expense ID", "transaction_id", "id") or f"travel-{idx}"
        travel_date = parse_date(first_value(row, "Transaction Date", "date", "start_date"))
        category = first_value(row, "Category", "expense_type", "type").lower()
        raw_distance = first_value(row, "Distance", "distance_miles", "miles")
        unit = first_value(row, "Unit", "distance_unit") or "mile"
        factor_category = "ground_miles"
        normalized_unit = "mile"
        if "flight" in category or "air" in category:
            origin = first_value(row, "Origin", "from_airport")
            destination = first_value(row, "Destination", "to_airport")
            if raw_distance:
                qty = parse_decimal(raw_distance)
            else:
                key = (origin.upper(), destination.upper())
                reverse_key = (destination.upper(), origin.upper())
                distance = AIRPORT_DISTANCE_MILES.get(key) or AIRPORT_DISTANCE_MILES.get(reverse_key)
                if distance is None:
                    flags.append("missing_flight_distance")
                    distance = 0
                qty = Decimal(distance)
                unit = "mile"
            normalized, normalized_unit = normalize_unit(qty, unit, "mile")
            factor_category = "flight_miles"
            activity_type = f"Flight {origin or '?'}-{destination or '?'}"
        elif "hotel" in category:
            qty = parse_decimal(first_value(row, "Nights", "quantity", "nights") or "1")
            normalized = qty
            normalized_unit = "night"
            factor_category = "hotel_nights"
            activity_type = "Hotel stay"
        else:
            qty = parse_decimal(raw_distance or first_value(row, "Quantity", "quantity") or "0")
            normalized, normalized_unit = normalize_unit(qty, unit, "mile")
            activity_type = "Ground transport"
        if normalized <= 0:
            flags.append("non_positive_activity")
        parsed.append(ParsedRow(
            expense_id, row, travel_date, None, None, "Scope 3", "business_travel",
            activity_type, qty, UNIT_ALIASES.get(unit.lower(), unit), normalized,
            normalized_unit, None, factor_category, flags,
            Decimal("0.60") if flags else Decimal("0.90"),
        ))
    return parsed


PARSERS = {
    "sap": parse_sap,
    "utility": parse_utility,
    "travel": parse_travel,
}
