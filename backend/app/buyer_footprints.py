from __future__ import annotations

import re
from collections import Counter
from datetime import date
from statistics import mean
from typing import Any

from .disposition_engine import haversine_miles, parse_date, safe_float

RADIUS_BUCKETS = (1, 3, 5, 10, 25)
TREND_BUCKETS = (30, 90, 180, 365)
LEGAL_SUFFIXES = {
    "llc",
    "l.l.c",
    "inc",
    "incorporated",
    "corp",
    "corporation",
    "company",
    "co",
    "ltd",
    "limited",
    "lp",
    "llp",
}
BUILDER_WORDS = {"builder", "builders", "homes", "construction", "custom", "communities"}
INVESTOR_WORDS = {"investment", "investments", "capital", "holdings", "properties", "realty", "land", "ventures"}
STREET_SUFFIXES = {
    "st",
    "street",
    "dr",
    "drive",
    "rd",
    "road",
    "ln",
    "lane",
    "ave",
    "avenue",
    "ct",
    "court",
    "blvd",
    "boulevard",
    "trl",
    "trail",
    "way",
    "pl",
    "place",
    "cir",
    "circle",
}


def build_buyer_footprints(transactions: list[dict[str, Any]], subject: dict[str, Any]) -> dict[str, dict[str, Any]]:
    groups = group_transactions_by_identity(transactions)
    footprints: dict[str, dict[str, Any]] = {}
    for normalized_name, buyer_transactions in groups.items():
        if not normalized_name or normalized_name == "unidentified buyer":
            continue
        footprints[normalized_name] = build_buyer_footprint(normalized_name, buyer_transactions, subject)
    return footprints


def build_buyer_footprint(normalized_name: str, transactions: list[dict[str, Any]], subject: dict[str, Any]) -> dict[str, Any]:
    sorted_transactions = sorted(transactions, key=lambda item: item.get("saleDate") or "", reverse=True)
    first = sorted_transactions[0] if sorted_transactions else {}
    sale_dates = [parse_date(item.get("saleDate")) for item in sorted_transactions]
    usable_dates = [item for item in sale_dates if item]
    verified_transactions = [item for item in sorted_transactions if is_verified_transaction(item)]
    source_confidences = [safe_float(item.get("confidence"), 0) for item in sorted_transactions if safe_float(item.get("confidence"), 0) > 0]
    same_street = same_street_transactions(sorted_transactions, subject)
    adjacent_blocks = adjacent_block_transactions(sorted_transactions, subject)
    purchases_by_radius = radius_counts(sorted_transactions)
    trend = activity_trend(sorted_transactions)
    aliases = alias_matches(sorted_transactions, normalized_name)
    corridor_signals = detect_corridor_signals(sorted_transactions, subject, same_street, adjacent_blocks, purchases_by_radius)
    intent_signals = classify_buyer_intent(sorted_transactions, same_street, purchases_by_radius, trend, corridor_signals)

    return {
        "entityName": first.get("buyerName") or normalized_name.title(),
        "normalizedBuyerName": normalized_name,
        "aliases": aliases,
        "sourceConfidence": round(mean(source_confidences)) if source_confidences else 0,
        "verifiedPurchaseCount": len(verified_transactions),
        "transactionCount": len(sorted_transactions),
        "purchasesByRadius": purchases_by_radius,
        "latestPurchaseDate": max(usable_dates).isoformat() if usable_dates else "",
        "firstKnownPurchaseDate": min(usable_dates).isoformat() if usable_dates else "",
        "averageAcreage": round_average([safe_float(item.get("acreage"), 0) for item in sorted_transactions], digits=2),
        "averagePurchasePrice": round(round_average([safe_float(item.get("salePrice"), 0) for item in sorted_transactions])),
        "averagePricePerAcre": round(round_average([safe_float(item.get("pricePerAcre"), 0) for item in sorted_transactions])),
        "preferredZipCodes": preferred_zip_codes(sorted_transactions),
        "preferredPropertyTypes": preferred_values(sorted_transactions, "propertyType"),
        "cashPurchasePercentage": cash_purchase_percentage(sorted_transactions),
        "activityTrend": trend,
        "streetLevelSignals": build_street_level_signals(sorted_transactions, subject, same_street, adjacent_blocks),
        "corridorSignals": corridor_signals,
        "intentSignals": intent_signals,
        "matchExplanation": build_match_explanation(first.get("buyerName") or normalized_name.title(), same_street, purchases_by_radius, trend),
        "contact": {
            "mailingAddress": first.get("buyerMailingAddress") or "",
            "phone": first.get("phone") or "",
            "email": first.get("email") or "",
            "source": first.get("sourceName") or first.get("source") or "",
        },
        "transactions": sorted_transactions,
    }


def group_transactions_by_identity(transactions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for transaction in transactions:
        buyer_name = transaction.get("buyerName") or "Unidentified Buyer"
        normalized = normalize_entity_name(buyer_name)
        if not normalized:
            continue
        matched_key = find_existing_identity(normalized, groups.keys())
        groups.setdefault(matched_key or normalized, []).append(transaction)
    return groups


def find_existing_identity(candidate: str, existing_names: Any) -> str:
    for existing in existing_names:
        match = alias_confidence(candidate, existing)
        if match["confidence"] >= 90:
            return existing
    return ""


def normalize_entity_name(value: Any) -> str:
    text = str(value or "").lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    raw_tokens = [token for token in text.split() if token not in LEGAL_SUFFIXES]
    tokens: list[str] = []
    index = 0
    while index < len(raw_tokens):
        if len(raw_tokens[index]) == 1 and raw_tokens[index].isalnum():
            acronym_parts: list[str] = []
            while index < len(raw_tokens) and len(raw_tokens[index]) == 1 and raw_tokens[index].isalnum():
                acronym_parts.append(raw_tokens[index])
                index += 1
            tokens.append("".join(acronym_parts))
            continue
        tokens.append(raw_tokens[index])
        index += 1
    clean_tokens = [token for token in tokens if token not in LEGAL_SUFFIXES]
    return " ".join(clean_tokens)


def alias_confidence(candidate: Any, existing: Any) -> dict[str, Any]:
    candidate_normalized = normalize_entity_name(candidate)
    existing_normalized = normalize_entity_name(existing)
    if not candidate_normalized or not existing_normalized:
        return {"confidence": 0, "reason": "Missing entity name"}
    if candidate_normalized == existing_normalized:
        return {"confidence": 100, "reason": "Exact normalized entity match"}

    candidate_tokens = set(candidate_normalized.split())
    existing_tokens = set(existing_normalized.split())
    overlap = len(candidate_tokens & existing_tokens)
    max_tokens = max(len(candidate_tokens), len(existing_tokens), 1)
    score = round((overlap / max_tokens) * 100)
    if overlap >= 2 and score >= 80:
        return {"confidence": score, "reason": "Strong token overlap"}
    if candidate_normalized in existing_normalized or existing_normalized in candidate_normalized:
        return {"confidence": 82, "reason": "One entity name contains the other"}
    return {"confidence": min(score, 74), "reason": "Low-confidence alias; not merged"}


def alias_matches(transactions: list[dict[str, Any]], normalized_name: str) -> list[dict[str, Any]]:
    aliases: dict[str, dict[str, Any]] = {}
    for transaction in transactions:
        alias = str(transaction.get("buyerName") or "").strip()
        if not alias:
            continue
        match = alias_confidence(alias, normalized_name)
        aliases[alias] = {
            "alias": alias,
            "normalizedAlias": normalize_entity_name(alias),
            "confidence": match["confidence"],
            "reason": match["reason"],
        }
    return sorted(aliases.values(), key=lambda item: item["confidence"], reverse=True)


def radius_counts(transactions: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for radius in RADIUS_BUCKETS:
        counts[str(radius)] = len([item for item in transactions if safe_float(item.get("distanceMiles"), 999) <= radius])
    return counts


def activity_trend(transactions: list[dict[str, Any]], today: date | None = None) -> dict[str, int]:
    today = today or date.today()
    trend: dict[str, int] = {}
    for days in TREND_BUCKETS:
        trend[str(days)] = len(
            [
                item
                for item in transactions
                if parse_date(item.get("saleDate")) and (today - parse_date(item.get("saleDate"))).days <= days
            ]
        )
    return trend


def same_street_transactions(transactions: list[dict[str, Any]], subject: dict[str, Any]) -> list[dict[str, Any]]:
    subject_street = street_name(subject.get("address"))
    if not subject_street:
        return []
    return [item for item in transactions if street_name(item.get("address")) == subject_street]


def adjacent_block_transactions(transactions: list[dict[str, Any]], subject: dict[str, Any]) -> list[dict[str, Any]]:
    subject_number = street_number(subject.get("address"))
    subject_street = street_name(subject.get("address"))
    if not subject_number or not subject_street:
        return []
    adjacent: list[dict[str, Any]] = []
    for transaction in transactions:
        if street_name(transaction.get("address")) != subject_street:
            continue
        transaction_number = street_number(transaction.get("address"))
        if transaction_number and abs(transaction_number - subject_number) <= 300:
            adjacent.append(transaction)
    return adjacent


def street_number(address: Any) -> int:
    match = re.match(r"\s*(\d+)", str(address or ""))
    return int(match.group(1)) if match else 0


def street_name(address: Any) -> str:
    text = str(address or "").split(",")[0].lower()
    text = re.sub(r"^\s*\d+\s+", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [token for token in text.split() if token not in STREET_SUFFIXES]
    return " ".join(tokens)


def build_street_level_signals(
    transactions: list[dict[str, Any]],
    subject: dict[str, Any],
    same_street: list[dict[str, Any]],
    adjacent_blocks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    if same_street:
        signals.append(
            {
                "label": "Same-street buyer",
                "detail": f"{len(same_street)} purchase{'s' if len(same_street) != 1 else ''} on {street_name(subject.get('address')).title()}.",
                "transactionIds": [item.get("id") for item in same_street],
            }
        )
    if adjacent_blocks:
        signals.append(
            {
                "label": "Adjacent-block activity",
                "detail": f"{len(adjacent_blocks)} purchase{'s' if len(adjacent_blocks) != 1 else ''} within roughly 300 street numbers of the subject.",
                "transactionIds": [item.get("id") for item in adjacent_blocks],
            }
        )
    if repeated_tight_radius(transactions):
        signals.append(
            {
                "label": "Tight-radius repeat activity",
                "detail": "Multiple purchases are clustered inside one mile of the subject.",
                "transactionIds": [item.get("id") for item in transactions if safe_float(item.get("distanceMiles"), 999) <= 1],
            }
        )
    return signals


def detect_corridor_signals(
    transactions: list[dict[str, Any]],
    subject: dict[str, Any],
    same_street: list[dict[str, Any]],
    adjacent_blocks: list[dict[str, Any]],
    purchases_by_radius: dict[str, int],
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    one_mile_transactions = [item for item in transactions if safe_float(item.get("distanceMiles"), 999) <= 1]
    recent_transactions = [item for item in transactions if days_since_sale(item) <= 180]

    if len(one_mile_transactions) >= 3:
        signals.append(
            {
                "label": "Possible acquisition corridor",
                "confidence": 86,
                "detail": f"{len(one_mile_transactions)} related purchases are within one mile of the subject.",
                "transactionIds": [item.get("id") for item in one_mile_transactions],
            }
        )
    if len(same_street) >= 2:
        signals.append(
            {
                "label": "Possible same-street assembly",
                "confidence": 82,
                "detail": f"{len(same_street)} purchases are on the same street as the subject.",
                "transactionIds": [item.get("id") for item in same_street],
            }
        )
    if len(recent_transactions) >= 2 and safe_float(purchases_by_radius.get("5"), 0) >= 2:
        signals.append(
            {
                "label": "Recent nearby acquisition pattern",
                "confidence": 78,
                "detail": f"{len(recent_transactions)} purchases happened within the last 180 days near this deal.",
                "transactionIds": [item.get("id") for item in recent_transactions],
            }
        )
    if adjacent_blocks and not signals:
        signals.append(
            {
                "label": "Early corridor watch",
                "confidence": 68,
                "detail": "Adjacent block activity exists, but more evidence is needed before calling this an active corridor.",
                "transactionIds": [item.get("id") for item in adjacent_blocks],
            }
        )
    return signals


def classify_buyer_intent(
    transactions: list[dict[str, Any]],
    same_street: list[dict[str, Any]],
    purchases_by_radius: dict[str, int],
    trend: dict[str, int],
    corridor_signals: list[dict[str, Any]],
) -> list[str]:
    signals: list[str] = []
    buyer_type = most_common([str(item.get("buyerType") or "unknown") for item in transactions])
    buyer_names = " ".join(str(item.get("buyerName") or "") for item in transactions).lower()

    if purchases_by_radius.get("1", 0) or purchases_by_radius.get("3", 0) >= 2:
        signals.append("Active nearby buyer")
    if len(transactions) >= 2:
        signals.append("Repeat buyer")
    if same_street:
        signals.append("Same-street buyer")
    if buyer_type == "builder" or any(word in buyer_names for word in BUILDER_WORDS):
        signals.append("Possible builder")
    if corridor_signals:
        signals.append("Possible land assembler")
    if not trend.get("180") and transactions:
        signals.append("Recently inactive")
    if not signals:
        signals.append("Insufficient evidence")
    return signals


def build_deal_intelligence_summary(
    footprints: dict[str, dict[str, Any]],
    buyer_matches: list[dict[str, Any]],
    transactions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    same_street_buyers = [item for item in footprints.values() if any(signal["label"] == "Same-street buyer" for signal in item["streetLevelSignals"])]
    verified_one_mile = [item for item in footprints.values() if item["purchasesByRadius"].get("1", 0) and item["verifiedPurchaseCount"]]
    repeat_five_mile = [item for item in footprints.values() if item["purchasesByRadius"].get("5", 0) >= 2]
    active_builders = [item for item in footprints.values() if "Possible builder" in item["intentSignals"] and item["purchasesByRadius"].get("5", 0)]
    latest_transaction = most_recent_transaction(transactions)
    strongest_match = buyer_matches[0] if buyer_matches else None

    return [
        {
            "label": "Same-street buyers",
            "value": len(same_street_buyers),
            "detail": buyer_names(same_street_buyers) or "No same-street buyer evidence yet.",
        },
        {
            "label": "Verified buyers within 1 mile",
            "value": len(verified_one_mile),
            "detail": buyer_names(verified_one_mile) or "No verified one-mile buyers yet.",
        },
        {
            "label": "Repeat buyers within 5 miles",
            "value": len(repeat_five_mile),
            "detail": buyer_names(repeat_five_mile) or "No repeat five-mile buyer pattern yet.",
        },
        {
            "label": "Active builders nearby",
            "value": len(active_builders),
            "detail": buyer_names(active_builders) or "No nearby builder pattern yet.",
        },
        {
            "label": "Most recent nearby acquisition",
            "value": latest_transaction.get("saleDate") if latest_transaction else "None",
            "detail": latest_transaction.get("buyerName") if latest_transaction else "No nearby transaction in the selected filters.",
        },
        {
            "label": "Strongest buyer match",
            "value": f"{strongest_match.get('score')}%" if strongest_match else "None",
            "detail": strongest_match.get("buyerName") if strongest_match else "Run buyer activity to create matches.",
        },
    ]


def build_match_explanation(buyer_name: str, same_street: list[dict[str, Any]], purchases_by_radius: dict[str, int], trend: dict[str, int]) -> str:
    pieces = []
    if same_street:
        pieces.append(f"{buyer_name} purchased {len(same_street)} parcel{'s' if len(same_street) != 1 else ''} on the same street")
    if purchases_by_radius.get("1"):
        pieces.append(f"{purchases_by_radius['1']} within 1 mile")
    if trend.get("180"):
        pieces.append(f"{trend['180']} during the last 180 days")
    return "; ".join(pieces) + "." if pieces else "Not enough evidence yet to explain a strong footprint."


def preferred_zip_codes(transactions: list[dict[str, Any]]) -> list[str]:
    zips: list[str] = []
    for transaction in transactions:
        text = " ".join(
            str(transaction.get(key) or "")
            for key in ["address", "buyerMailingAddress"]
        )
        zips.extend(re.findall(r"\b\d{5}\b", text))
    return [zip_code for zip_code, _count in Counter(zips).most_common(5)]


def preferred_values(transactions: list[dict[str, Any]], key: str) -> list[str]:
    values = [str(item.get(key) or "").strip() for item in transactions if str(item.get(key) or "").strip()]
    return [value for value, _count in Counter(values).most_common(5)]


def cash_purchase_percentage(transactions: list[dict[str, Any]]) -> int:
    if not transactions:
        return 0
    cash_count = len([item for item in transactions if item.get("cashSale")])
    return round((cash_count / len(transactions)) * 100)


def repeated_tight_radius(transactions: list[dict[str, Any]]) -> bool:
    return len([item for item in transactions if safe_float(item.get("distanceMiles"), 999) <= 1]) >= 2


def days_since_sale(transaction: dict[str, Any], today: date | None = None) -> int:
    today = today or date.today()
    sale_date = parse_date(transaction.get("saleDate"))
    return (today - sale_date).days if sale_date else 99999


def is_verified_transaction(transaction: dict[str, Any]) -> bool:
    quality = str(transaction.get("dataQuality") or "").lower()
    if quality:
        return quality == "verified"
    return bool(transaction.get("buyerName") and transaction.get("salePrice") and transaction.get("saleDate"))


def round_average(values: list[float], digits: int = 0) -> float:
    usable_values = [value for value in values if value > 0]
    if not usable_values:
        return 0
    return round(mean(usable_values), digits)


def most_common(values: list[str]) -> str:
    clean_values = [value for value in values if value]
    if not clean_values:
        return "unknown"
    return Counter(clean_values).most_common(1)[0][0]


def most_recent_transaction(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    dated_transactions = [item for item in transactions if parse_date(item.get("saleDate"))]
    if not dated_transactions:
        return {}
    return max(dated_transactions, key=lambda item: parse_date(item.get("saleDate")) or date.min)


def buyer_names(footprints: list[dict[str, Any]]) -> str:
    names = [item.get("entityName") for item in footprints if item.get("entityName")]
    return ", ".join(names[:3])