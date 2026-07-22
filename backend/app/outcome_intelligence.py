from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from statistics import mean
from typing import Any

SCHEMA_VERSION = "outcome-intelligence-v1"
LEARNING_MANTRA = "We measure before we predict."

CLOSED_RESULTS = {"buyer_purchased", "assigned", "closed"}
FAILED_RESULTS = {"seller_declined", "price_too_high", "buyer_passed", "contract_canceled"}
CHANGED_RESULTS = {"repriced"}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def first_text(*values: Any) -> str:
    for value in values:
        text = safe_text(value)
        if text:
            return text
    return ""


def safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^0-9.\-]", "", str(value))
    if cleaned in {"", ".", "-", "-."}:
        return default
    try:
        return float(cleaned)
    except ValueError:
        return default


def safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return safe_text(value).lower() in {"1", "true", "yes", "y"}

def safe_int(value: Any, default: int = 0) -> int:
    number = safe_float(value, default)
    return int(round(number))


def parse_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode("utf-8")
    if isinstance(payload, str):
        return json.loads(payload)
    return json.loads(str(payload))


def normalize_entity_name(value: Any) -> str:
    text = safe_text(value).upper()
    text = re.sub(r"[^A-Z0-9 ]+", " ", text)
    stop_words = {
        "LLC",
        "L L C",
        "INC",
        "CORP",
        "CORPORATION",
        "COMPANY",
        "CO",
        "LP",
        "LTD",
        "THE",
    }
    words = [word for word in text.split() if word not in stop_words]
    return " ".join(words).strip()


def parse_datetime(value: Any) -> datetime | None:
    text = safe_text(value)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def evaluate_recommendation(recommended_buyer: Any, final_buyer: Any, disposition_result: str = "") -> str:
    recommended = normalize_entity_name(recommended_buyer)
    actual = normalize_entity_name(final_buyer)
    result = safe_text(disposition_result).lower()

    if not actual:
        return "unknown" if result not in CLOSED_RESULTS else "missing_actual_buyer"
    if not recommended:
        return "unknown"
    if recommended == actual:
        return "yes"

    recommended_tokens = set(recommended.split())
    actual_tokens = set(actual.split())
    if recommended_tokens and actual_tokens and len(recommended_tokens & actual_tokens) >= 2:
        return "partial"

    return "no"


def classify_assignment_performance(assignment_fee: Any) -> str:
    fee = safe_float(assignment_fee)
    if fee >= 20000:
        return "excellent"
    if fee >= 10000:
        return "strong"
    if fee > 0:
        return "thin"
    return "missing"


def classify_buyer_response_speed(hours: Any) -> str:
    response_hours = safe_float(hours, default=-1)
    if response_hours < 0:
        return "unknown"
    if response_hours <= 4:
        return "fast"
    if response_hours <= 24:
        return "same_day"
    if response_hours <= 72:
        return "slow"
    return "very_slow"


def classify_confidence_accuracy(recommendation_correct: str, confidence: Any) -> str:
    score = safe_float(confidence)
    if recommendation_correct == "yes":
        return "accurate" if score >= 75 else "underconfident"
    if recommendation_correct == "partial":
        return "partially_accurate"
    if recommendation_correct == "no":
        return "overconfident" if score >= 75 else "missed"
    return "not_measured"


def classify_outcome_type(disposition_result: str) -> str:
    result = safe_text(disposition_result).lower()
    if result in CLOSED_RESULTS:
        return "closed"
    if result in FAILED_RESULTS:
        return "failed"
    if result in CHANGED_RESULTS:
        return "changed"
    return "unknown"


def calculate_days_from_recommendation(recommendation_timestamp: Any, outcome_date: Any, fallback_days: Any) -> int:
    explicit_days = safe_int(fallback_days)
    if explicit_days > 0:
        return explicit_days

    recommended_at = parse_datetime(recommendation_timestamp)
    closed_at = parse_datetime(outcome_date)
    if not recommended_at or not closed_at:
        return 0

    return max((closed_at - recommended_at).days, 0)


def build_data_quality_flags(actual_result: dict[str, Any], recommendation: dict[str, Any]) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    result = safe_text(actual_result.get("dispositionResult")).lower()

    if result in CLOSED_RESULTS and not safe_text(actual_result.get("finalBuyer")):
        flags.append({"level": "needs_review", "label": "Final buyer missing"})
    if result in CLOSED_RESULTS and safe_float(actual_result.get("assignmentFee")) <= 0:
        flags.append({"level": "incomplete", "label": "Assignment fee missing"})
    if result in CLOSED_RESULTS and safe_int(actual_result.get("daysToClose")) <= 0:
        flags.append({"level": "incomplete", "label": "Days to close missing"})
    if safe_text(actual_result.get("contractReassigned")).lower() in {"true", "yes", "1"}:
        flags.append({"level": "changed", "label": "Contract was reassigned"})
    if safe_text(actual_result.get("priceChanged")).lower() in {"true", "yes", "1"}:
        flags.append({"level": "changed", "label": "Price changed during disposition"})
    if not safe_text(recommendation.get("recommendedBuyer")):
        flags.append({"level": "incomplete", "label": "Original recommended buyer missing"})
    if not flags:
        flags.append({"level": "verified", "label": "Outcome ready for learning"})

    return flags


def build_outcome_record(
    record_id: str,
    lead_payload: dict[str, Any],
    payload: dict[str, Any],
    created_at: str | None = None,
) -> dict[str, Any]:
    created_at = created_at or utc_timestamp()
    lead_id = first_text(payload.get("leadId"), lead_payload.get("id"))
    disposition_result = safe_text(payload.get("dispositionResult") or "unknown").lower()

    property_payload = {
        "propertyId": first_text(payload.get("propertyId"), lead_payload.get("id")),
        "leadId": lead_id,
        "address": first_text(payload.get("address"), lead_payload.get("address")),
        "apn": first_text(payload.get("apn"), lead_payload.get("parcelNumber")),
        "county": first_text(payload.get("county"), lead_payload.get("county")),
    }
    recommendation = {
        "originalOpportunityScore": safe_int(payload.get("originalOpportunityScore")),
        "recommendedAction": safe_text(payload.get("recommendedAction")),
        "recommendedBuyer": safe_text(payload.get("recommendedBuyer")),
        "confidence": safe_int(payload.get("confidence")),
        "recommendationTimestamp": safe_text(payload.get("recommendationTimestamp") or created_at),
    }
    actual_result = {
        "finalBuyer": safe_text(payload.get("finalBuyer")),
        "assignmentFee": safe_float(payload.get("assignmentFee")),
        "daysToClose": safe_int(payload.get("daysToClose")),
        "purchasePrice": safe_float(payload.get("purchasePrice")),
        "dispositionResult": disposition_result,
        "sellerOutcome": safe_text(payload.get("sellerOutcome")),
        "buyerResponseHours": safe_float(payload.get("buyerResponseHours"), default=-1),
        "outcomeDate": safe_text(payload.get("outcomeDate") or created_at),
        "contractReassigned": safe_bool(payload.get("contractReassigned", False)),
        "priceChanged": safe_bool(payload.get("priceChanged", False)),
        "notes": safe_text(payload.get("notes")),
    }
    recommendation_correct = evaluate_recommendation(
        recommendation.get("recommendedBuyer"),
        actual_result.get("finalBuyer"),
        disposition_result,
    )
    days_from_recommendation = calculate_days_from_recommendation(
        recommendation.get("recommendationTimestamp"),
        actual_result.get("outcomeDate"),
        actual_result.get("daysToClose"),
    )

    return {
        "id": record_id,
        "schemaVersion": SCHEMA_VERSION,
        "leadId": lead_id,
        "property": property_payload,
        "recommendation": recommendation,
        "actualResult": actual_result,
        "intelligence": {
            "outcomeType": classify_outcome_type(disposition_result),
            "recommendationCorrect": recommendation_correct,
            "daysFromRecommendationToClosing": days_from_recommendation,
            "buyerResponseSpeed": classify_buyer_response_speed(actual_result.get("buyerResponseHours")),
            "assignmentPerformance": classify_assignment_performance(actual_result.get("assignmentFee")),
            "confidenceAccuracy": classify_confidence_accuracy(recommendation_correct, recommendation.get("confidence")),
        },
        "dataQuality": build_data_quality_flags(actual_result, recommendation),
        "createdAt": created_at,
        "updatedAt": created_at,
    }


def build_learning_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    clean_records = [parse_payload(record) for record in records]
    closed_records = [
        record
        for record in clean_records
        if (record.get("intelligence") or {}).get("outcomeType") == "closed"
    ]
    evaluated_records = [
        record
        for record in clean_records
        if (record.get("intelligence") or {}).get("recommendationCorrect") in {"yes", "no", "partial"}
    ]
    correct = sum(1 for record in evaluated_records if (record.get("intelligence") or {}).get("recommendationCorrect") == "yes")
    partial = sum(1 for record in evaluated_records if (record.get("intelligence") or {}).get("recommendationCorrect") == "partial")
    accuracy = round(((correct + (partial * 0.5)) / len(evaluated_records)) * 100) if evaluated_records else 0
    days_to_close = [
        safe_int((record.get("actualResult") or {}).get("daysToClose"))
        for record in closed_records
        if safe_int((record.get("actualResult") or {}).get("daysToClose")) > 0
    ]
    assignment_fees = [
        safe_float((record.get("actualResult") or {}).get("assignmentFee"))
        for record in closed_records
        if safe_float((record.get("actualResult") or {}).get("assignmentFee")) > 0
    ]

    return {
        "engine": "LEGACY Learning Engine",
        "version": "outcome-intelligence-v1",
        "mantra": LEARNING_MANTRA,
        "totalOutcomes": len(clean_records),
        "closedDeals": len(closed_records),
        "evaluatedRecommendations": len(evaluated_records),
        "correctRecommendations": correct,
        "partialRecommendations": partial,
        "recommendationAccuracyRate": accuracy,
        "averageDaysToClose": round(mean(days_to_close), 1) if days_to_close else 0,
        "averageAssignmentFee": round(mean(assignment_fees), 2) if assignment_fees else 0,
        "buyerPerformance": build_buyer_performance(clean_records),
        "recentOutcomes": sorted(clean_records, key=lambda record: record.get("createdAt") or "", reverse=True)[:5],
        "predictionStatus": "Not active. Outcome Intelligence records and measures before prediction.",
    }


def build_buyer_performance(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        buyer = safe_text((record.get("actualResult") or {}).get("finalBuyer"))
        if not buyer:
            continue
        key = normalize_entity_name(buyer) or buyer.upper()
        grouped.setdefault(key, []).append(record)

    performance = []
    for key, buyer_records in grouped.items():
        closed_records = [
            record
            for record in buyer_records
            if (record.get("intelligence") or {}).get("outcomeType") == "closed"
        ]
        days = [
            safe_int((record.get("actualResult") or {}).get("daysToClose"))
            for record in closed_records
            if safe_int((record.get("actualResult") or {}).get("daysToClose")) > 0
        ]
        fees = [
            safe_float((record.get("actualResult") or {}).get("assignmentFee"))
            for record in closed_records
            if safe_float((record.get("actualResult") or {}).get("assignmentFee")) > 0
        ]
        matches = sum(
            1
            for record in buyer_records
            if (record.get("intelligence") or {}).get("recommendationCorrect") == "yes"
        )
        display_name = first_text((buyer_records[0].get("actualResult") or {}).get("finalBuyer"), key.title())
        performance.append(
            {
                "buyerName": display_name,
                "outcomes": len(buyer_records),
                "closedDeals": len(closed_records),
                "recommendationMatches": matches,
                "acceptanceRate": round((len(closed_records) / len(buyer_records)) * 100) if buyer_records else 0,
                "averageDaysToClose": round(mean(days), 1) if days else 0,
                "averageAssignmentFee": round(mean(fees), 2) if fees else 0,
            }
        )

    return sorted(performance, key=lambda item: (item["closedDeals"], item["averageAssignmentFee"]), reverse=True)[:10]
