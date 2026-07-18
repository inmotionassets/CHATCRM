from __future__ import annotations

from datetime import date, datetime
from math import asin, cos, radians, sin, sqrt
from statistics import mean
from typing import Any


EARTH_RADIUS_MILES = 3958.8


MOCK_TRANSACTION_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "sale-001",
        "address": "1214 Cedar Crest Blvd",
        "apn": "00000481291000000",
        "saleDate": "2026-06-24",
        "salePrice": 72000,
        "acreage": 1.25,
        "propertyType": "Vacant Land",
        "cashSale": True,
        "buyerName": "DFW Land Partners LLC",
        "buyerMailingAddress": "325 N Saint Paul St, Dallas, TX",
        "buyerType": "investor",
        "northMiles": 0.8,
        "eastMiles": 0.9,
        "relationshipTier": "B",
    },
    {
        "id": "sale-002",
        "address": "1340 Pleasant Vista Dr",
        "apn": "00000650128000000",
        "saleDate": "2026-06-05",
        "salePrice": 63500,
        "acreage": 1.1,
        "propertyType": "Vacant Land",
        "cashSale": True,
        "buyerName": "DFW Land Partners LLC",
        "buyerMailingAddress": "325 N Saint Paul St, Dallas, TX",
        "buyerType": "investor",
        "northMiles": -1.4,
        "eastMiles": 1.2,
        "relationshipTier": "B",
    },
    {
        "id": "sale-003",
        "address": "1881 Oak Gate Ln",
        "apn": "00000783114000000",
        "saleDate": "2026-05-18",
        "salePrice": 81000,
        "acreage": 1.7,
        "propertyType": "Residential Lot",
        "cashSale": False,
        "buyerName": "Lone Star Custom Homes LLC",
        "buyerMailingAddress": "4301 Alpha Rd, Dallas, TX",
        "buyerType": "builder",
        "northMiles": 2.2,
        "eastMiles": -0.8,
        "relationshipTier": "A",
    },
    {
        "id": "sale-004",
        "address": "901 Prairie Bend Rd",
        "apn": "00000319045000000",
        "saleDate": "2026-04-26",
        "salePrice": 54500,
        "acreage": 0.95,
        "propertyType": "Vacant Land",
        "cashSale": True,
        "buyerName": "Texas Dirt Investments LLC",
        "buyerMailingAddress": "1409 S Lamar St, Dallas, TX",
        "buyerType": "investor",
        "northMiles": -2.6,
        "eastMiles": -1.5,
        "relationshipTier": "C",
    },
    {
        "id": "sale-005",
        "address": "2300 Walker Creek Trl",
        "apn": "00000477862000000",
        "saleDate": "2026-03-14",
        "salePrice": 58000,
        "acreage": 1.05,
        "propertyType": "Vacant Land",
        "cashSale": True,
        "buyerName": "Texas Dirt Investments LLC",
        "buyerMailingAddress": "1409 S Lamar St, Dallas, TX",
        "buyerType": "investor",
        "northMiles": -4.1,
        "eastMiles": 0.7,
        "relationshipTier": "C",
    },
    {
        "id": "sale-006",
        "address": "4114 Harbor View Ct",
        "apn": "00000911230000000",
        "saleDate": "2026-02-02",
        "salePrice": 124000,
        "acreage": 2.35,
        "propertyType": "Residential Lot",
        "cashSale": False,
        "buyerName": "Metro Infill Builders LLC",
        "buyerMailingAddress": "2100 Ross Ave, Dallas, TX",
        "buyerType": "builder",
        "northMiles": 6.8,
        "eastMiles": 2.1,
        "relationshipTier": "A",
    },
    {
        "id": "sale-007",
        "address": "7710 Garden Grove Rd",
        "apn": "00000220491000000",
        "saleDate": "2025-12-19",
        "salePrice": 39500,
        "acreage": 0.7,
        "propertyType": "Vacant Land",
        "cashSale": True,
        "buyerName": "Oakline Property Holdings LLC",
        "buyerMailingAddress": "5950 Berkshire Ln, Dallas, TX",
        "buyerType": "investor",
        "northMiles": -7.9,
        "eastMiles": -3.2,
        "relationshipTier": "C",
    },
    {
        "id": "sale-008",
        "address": "1551 Monarch Fields Dr",
        "apn": "00000539001000000",
        "saleDate": "2025-11-08",
        "salePrice": 151000,
        "acreage": 3.2,
        "propertyType": "Acreage",
        "cashSale": True,
        "buyerName": "Cedar Ridge Development Group",
        "buyerMailingAddress": "5005 Lyndon B Johnson Fwy, Dallas, TX",
        "buyerType": "developer",
        "northMiles": 9.4,
        "eastMiles": -4.7,
        "relationshipTier": "B",
    },
    {
        "id": "sale-009",
        "address": "3617 Millhouse Way",
        "apn": "00000887330000000",
        "saleDate": "2025-08-22",
        "salePrice": 68000,
        "acreage": 1.4,
        "propertyType": "Vacant Land",
        "cashSale": True,
        "buyerName": "DFW Land Partners LLC",
        "buyerMailingAddress": "325 N Saint Paul St, Dallas, TX",
        "buyerType": "investor",
        "northMiles": 12.1,
        "eastMiles": 5.8,
        "relationshipTier": "B",
    },
    {
        "id": "sale-010",
        "address": "4880 Horizon Ridge Ave",
        "apn": "00000188274000000",
        "saleDate": "2025-07-30",
        "salePrice": 99000,
        "acreage": 1.85,
        "propertyType": "Residential Lot",
        "cashSale": False,
        "buyerName": "Lone Star Custom Homes LLC",
        "buyerMailingAddress": "4301 Alpha Rd, Dallas, TX",
        "buyerType": "builder",
        "northMiles": 14.6,
        "eastMiles": -7.4,
        "relationshipTier": "A",
    },
]


def build_disposition_workspace(
    lead_payload: dict[str, Any],
    radius_miles: float = 5,
    sold_within_days: int = 365,
    vacant_land_only: bool = False,
    cash_only: bool = False,
    buyer_types: list[str] | None = None,
    today: date | None = None,
    transactions: list[dict[str, Any]] | None = None,
    provider_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    today = today or date.today()
    subject = build_subject_property(lead_payload)
    transaction_source = transactions if transactions is not None else build_mock_transactions(subject)
    filtered_transactions = filter_transactions(
        transaction_source,
        subject,
        radius_miles=radius_miles,
        sold_within_days=sold_within_days,
        vacant_land_only=vacant_land_only,
        cash_only=cash_only,
        buyer_types=buyer_types or [],
        today=today,
    )
    buyer_groups = group_transactions_by_buyer(filtered_transactions)
    buyer_matches = [
        score_buyer_match(buyer_name, buyer_transactions, subject)
        for buyer_name, buyer_transactions in buyer_groups.items()
    ]
    buyer_matches.sort(key=lambda item: item["score"], reverse=True)

    price_per_acre_values = [safe_float(item.get("pricePerAcre"), 0) for item in filtered_transactions if safe_float(item.get("pricePerAcre"), 0) > 0]
    average_price_per_acre = mean(price_per_acre_values) if price_per_acre_values else 0
    suggested_buyer_price = int(average_price_per_acre * safe_float(subject.get("acreage"), 1)) if average_price_per_acre else 0
    contract_price = safe_float(subject.get("contractPrice"), 0)

    return {
        "subject": subject,
        "filters": {
            "radiusMiles": radius_miles,
            "soldWithinDays": sold_within_days,
            "vacantLandOnly": vacant_land_only,
            "cashOnly": cash_only,
            "buyerTypes": buyer_types or [],
        },
        "readiness": build_deal_readiness(lead_payload),
        "transactions": filtered_transactions,
        "buyerMatches": buyer_matches,
        "source": build_source_status(provider_result),
        "overview": {
            "verifiedNearbyBuyers": len(buyer_groups),
            "highMatchBuyers": len([item for item in buyer_matches if item["score"] >= 80]),
            "activeBuilders": len([item for item in buyer_matches if item["buyerType"] == "builder"]),
            "recentSimilarSales": len(filtered_transactions),
            "averagePricePerAcre": round(average_price_per_acre),
            "suggestedBuyerAskingPrice": suggested_buyer_price,
            "estimatedAssignmentSpread": max(0, suggested_buyer_price - int(contract_price)) if suggested_buyer_price else 0,
        },
    }


def build_source_status(provider_result: dict[str, Any] | None = None) -> dict[str, Any]:
    provider_result = provider_result or {}
    return {
        "provider": provider_result.get("provider") or "mock",
        "sourceName": provider_result.get("sourceName") or "Mock buyer activity",
        "lastRefreshAt": provider_result.get("lastRefreshAt") or "",
        "errors": provider_result.get("errors") or [],
    }


def build_subject_property(lead_payload: dict[str, Any]) -> dict[str, Any]:
    coordinates = subject_coordinates(lead_payload)
    contract_price = first_number(lead_payload.get("contractPrice"), lead_payload.get("purchasePrice"), lead_payload.get("estimatedArv"))
    target_assignment_price = first_number(lead_payload.get("targetAssignmentPrice"), lead_payload.get("askingPrice"))
    assignment_fee = first_number(lead_payload.get("assignmentFee"))
    if not target_assignment_price and contract_price and assignment_fee:
        target_assignment_price = contract_price + assignment_fee

    return {
        "leadId": str(lead_payload.get("id") or ""),
        "address": str(lead_payload.get("address") or "Address needed"),
        "coordinates": coordinates,
        "apn": str(lead_payload.get("parcelNumber") or ""),
        "acreage": parse_acreage(lead_payload.get("lotSize")) or 1.2,
        "propertyType": infer_property_type(lead_payload),
        "county": str(lead_payload.get("county") or "Dallas"),
        "zoning": str(lead_payload.get("zoning") or ""),
        "floodZone": str(lead_payload.get("floodZone") or ""),
        "utilities": str(lead_payload.get("utilities") or ""),
        "sellerAskingPrice": first_number(lead_payload.get("sellerAskingPrice")),
        "contractPrice": contract_price or 45000,
        "targetAssignmentPrice": target_assignment_price or 57500,
        "projectedSpread": (target_assignment_price - contract_price) if target_assignment_price and contract_price else assignment_fee or 12500,
    }


def build_deal_readiness(lead_payload: dict[str, Any]) -> list[dict[str, Any]]:
    stage = str(lead_payload.get("stage") or "").lower()
    notes = str(lead_payload.get("notes") or "").lower()
    return [
        {"label": "Under contract", "complete": "contract" in stage},
        {"label": "Title opened", "complete": "title" in notes},
        {"label": "Photos uploaded", "complete": "photo" in notes},
        {"label": "Survey available", "complete": "survey" in notes},
        {"label": "Access confirmed", "complete": "access" in notes},
        {"label": "Taxes verified", "complete": "tax" in notes},
        {"label": "Restrictions reviewed", "complete": "restriction" in notes},
    ]


def build_mock_transactions(subject: dict[str, Any]) -> list[dict[str, Any]]:
    subject_lat = float(subject["coordinates"]["lat"])
    subject_lng = float(subject["coordinates"]["lng"])
    transactions: list[dict[str, Any]] = []

    for template in MOCK_TRANSACTION_TEMPLATES:
        lat, lng = offset_coordinate(subject_lat, subject_lng, template["northMiles"], template["eastMiles"])
        price_per_acre = round(template["salePrice"] / max(float(template["acreage"]), 0.01))
        marker_type = marker_type_for_transaction(template)
        transaction = {
            **{key: value for key, value in template.items() if key not in {"northMiles", "eastMiles"}},
            "coordinates": {"lat": round(lat, 6), "lng": round(lng, 6)},
            "distanceMiles": round(haversine_miles(subject_lat, subject_lng, lat, lng), 2),
            "pricePerAcre": price_per_acre,
            "markerType": marker_type,
        }
        transactions.append(transaction)

    return transactions


def filter_transactions(
    transactions: list[dict[str, Any]],
    subject: dict[str, Any],
    radius_miles: float,
    sold_within_days: int,
    vacant_land_only: bool,
    cash_only: bool,
    buyer_types: list[str],
    today: date,
) -> list[dict[str, Any]]:
    normalized_buyer_types = {str(item).lower().strip() for item in buyer_types if str(item).strip()}
    subject_type = str(subject.get("propertyType") or "").lower()
    filtered: list[dict[str, Any]] = []

    for transaction in transactions:
        if float(transaction["distanceMiles"]) > radius_miles:
            continue
        sale_date = parse_date(transaction.get("saleDate"))
        if not sale_date or (today - sale_date).days > sold_within_days:
            continue
        if vacant_land_only and "land" not in str(transaction.get("propertyType") or "").lower() and "lot" not in subject_type:
            continue
        if cash_only and not transaction.get("cashSale"):
            continue
        if normalized_buyer_types and str(transaction.get("buyerType") or "").lower() not in normalized_buyer_types:
            continue
        filtered.append(transaction)

    return filtered


def group_transactions_by_buyer(transactions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for transaction in transactions:
        key = normalize_buyer_name(transaction.get("buyerName"))
        groups.setdefault(key, []).append(transaction)
    return groups


def score_buyer_match(buyer_key: str, transactions: list[dict[str, Any]], subject: dict[str, Any]) -> dict[str, Any]:
    nearest_distance = min(float(item["distanceMiles"]) for item in transactions)
    latest_sale = max(parse_date(item["saleDate"]) or date.min for item in transactions)
    avg_price = safe_average([safe_float(item.get("salePrice"), 0) for item in transactions])
    avg_acreage = safe_average([safe_float(item.get("acreage"), 0) for item in transactions])
    avg_price_per_acre = safe_average([safe_float(item.get("pricePerAcre"), 0) for item in transactions])
    subject_acreage = safe_float(subject.get("acreage"), 1)
    target_price = safe_float(subject.get("targetAssignmentPrice"), 0)
    buyer_type = most_common([str(item.get("buyerType") or "unknown") for item in transactions])
    first = transactions[0]

    distance_score = score_distance(nearest_distance)
    property_score = score_property_fit(transactions, subject)
    acreage_score = score_acreage_fit(avg_acreage, subject_acreage)
    recency_score = score_recency(latest_sale)
    price_score = score_price_fit(avg_price, target_price)
    repeat_score = min(5, max(1, len(transactions) * 2))
    relationship_score = {"A": 5, "B": 3, "C": 1}.get(str(first.get("relationshipTier") or "C").upper(), 1)
    total_score = round(
        distance_score
        + property_score
        + acreage_score
        + recency_score
        + price_score
        + repeat_score
        + relationship_score
    )

    return {
        "buyerName": first.get("buyerName"),
        "normalizedBuyerName": buyer_key,
        "buyerType": buyer_type,
        "buyerMailingAddress": first.get("buyerMailingAddress"),
        "score": clamp_score(total_score),
        "scoreBreakdown": {
            "nearbyActivity": round(distance_score),
            "propertyFit": round(property_score),
            "acreageFit": round(acreage_score),
            "recency": round(recency_score),
            "priceFit": round(price_score),
            "repeatActivity": round(repeat_score),
            "relationship": round(relationship_score),
        },
        "reasons": build_match_reasons(transactions, nearest_distance, buyer_type, latest_sale),
        "totalVerifiedPurchases": len([item for item in transactions if is_verified_transaction(item)]),
        "nearbyPurchases": len([item for item in transactions if float(item["distanceMiles"]) <= 5]),
        "latestPurchaseDate": latest_sale.isoformat() if latest_sale != date.min else "",
        "averagePurchasePrice": round(avg_price),
        "averageAcreage": round(avg_acreage, 2),
        "averagePricePerAcre": round(avg_price_per_acre),
        "transactions": sorted(transactions, key=lambda item: item["saleDate"], reverse=True),
    }


def score_distance(distance_miles: float) -> float:
    if distance_miles <= 1:
        return 30
    if distance_miles <= 3:
        return 26
    if distance_miles <= 5:
        return 22
    if distance_miles <= 10:
        return 16
    if distance_miles <= 25:
        return 10
    return 0


def score_property_fit(transactions: list[dict[str, Any]], subject: dict[str, Any]) -> float:
    subject_type = str(subject.get("propertyType") or "").lower()
    matching = [
        item
        for item in transactions
        if str(item.get("propertyType") or "").lower() in subject_type
        or subject_type in str(item.get("propertyType") or "").lower()
        or ("land" in subject_type and "land" in str(item.get("propertyType") or "").lower())
        or ("lot" in subject_type and "lot" in str(item.get("propertyType") or "").lower())
    ]
    return 20 if matching else 12


def score_acreage_fit(average_acreage: float, subject_acreage: float) -> float:
    if subject_acreage <= 0 or average_acreage <= 0:
        return 8
    ratio = average_acreage / subject_acreage
    if 0.75 <= ratio <= 1.35:
        return 15
    if 0.5 <= ratio <= 2:
        return 11
    return 6


def score_recency(latest_sale: date) -> float:
    if latest_sale == date.min:
        return 0
    days_old = (date.today() - latest_sale).days
    if days_old <= 30:
        return 15
    if days_old <= 90:
        return 12
    if days_old <= 180:
        return 8
    if days_old <= 365:
        return 5
    return 1


def score_price_fit(average_price: float, target_price: float) -> float:
    if average_price <= 0 or target_price <= 0:
        return 6
    ratio = average_price / target_price
    if 0.85 <= ratio <= 1.4:
        return 10
    if 0.65 <= ratio <= 1.75:
        return 7
    return 3


def build_match_reasons(transactions: list[dict[str, Any]], nearest_distance: float, buyer_type: str, latest_sale: date) -> list[str]:
    verified_count = len([item for item in transactions if is_verified_transaction(item)])
    quality_label = "verified" if verified_count else "estimated"
    reasons = [
        f"{len(transactions)} {quality_label} purchase{'s' if len(transactions) != 1 else ''}",
        f"Nearest purchase {nearest_distance:.1f} miles away",
        f"{buyer_type.title()} activity",
    ]
    if latest_sale != date.min:
        reasons.append(f"Last purchase {latest_sale.strftime('%b %d, %Y')}")
    if len(transactions) >= 3:
        reasons.append("Repeat buyer pattern")
    if any(item.get("cashSale") for item in transactions):
        reasons.append("Cash purchase history")
    if any(str(item.get("dataQuality") or "").lower() in {"incomplete", "estimated"} for item in transactions):
        reasons.append("Source data needs review")
    return reasons


def is_verified_transaction(transaction: dict[str, Any]) -> bool:
    quality = str(transaction.get("dataQuality") or "").lower()
    if quality:
        return quality == "verified"
    return bool(transaction.get("buyerName") and transaction.get("salePrice") and transaction.get("saleDate"))


def subject_coordinates(lead_payload: dict[str, Any]) -> dict[str, float]:
    address = str(lead_payload.get("address") or "")
    seed = sum(ord(char) for char in address)
    lat = 32.7767 + ((seed % 35) - 17) / 1000
    lng = -96.7970 + (((seed // 3) % 35) - 17) / 1000
    return {"lat": round(lat, 6), "lng": round(lng, 6)}


def offset_coordinate(lat: float, lng: float, north_miles: float, east_miles: float) -> tuple[float, float]:
    new_lat = lat + north_miles / 69
    lng_scale = max(cos(radians(lat)) * 69, 1)
    new_lng = lng + east_miles / lng_scale
    return new_lat, new_lng


def haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    value = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * asin(sqrt(value))


def marker_type_for_transaction(transaction: dict[str, Any]) -> str:
    if transaction.get("buyerType") == "builder":
        return "builder"
    if transaction.get("buyerType") == "developer":
        return "repeat"
    if transaction.get("cashSale"):
        return "cash"
    return "standard"


def normalize_buyer_name(value: Any) -> str:
    text = str(value or "").lower()
    for token in [",", ".", " llc", " l.l.c", " inc", " company", " co", " ltd"]:
        text = text.replace(token, "")
    return " ".join(text.split())


def parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def parse_acreage(value: Any) -> float | None:
    text = str(value or "").lower().replace(",", "")
    numbers = []
    for piece in text.replace("/", " ").split():
        try:
            numbers.append(float(piece))
        except ValueError:
            continue
    return numbers[0] if numbers else None


def first_number(*values: Any) -> int:
    for value in values:
        if value in (None, ""):
            continue
        text = str(value).replace("$", "").replace(",", "").strip()
        try:
            return int(float(text))
        except ValueError:
            continue
    return 0


def safe_float(value: Any, default: float = 0) -> float:
    try:
        return float(str(value).replace("$", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def safe_average(values: list[float]) -> float:
    usable_values = [value for value in values if value > 0]
    return mean(usable_values) if usable_values else 0


def infer_property_type(lead_payload: dict[str, Any]) -> str:
    text = " ".join(
        str(lead_payload.get(key) or "")
        for key in ["propertyType", "source", "notes", "lotSize"]
    ).lower()
    if "acre" in text:
        return "Acreage"
    if "lot" in text or "land" in text or not text.strip():
        return "Vacant Land"
    return "Residential Lot"


def most_common(values: list[str]) -> str:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return max(counts, key=counts.get) if counts else "unknown"


def clamp_score(value: int) -> int:
    return max(0, min(100, value))
