from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .buyer_footprints import build_buyer_footprints, build_deal_intelligence_summary, normalize_entity_name
from .disposition_engine import build_disposition_workspace, build_subject_property, safe_float
from .disposition_providers import get_provider


@dataclass
class MarketIntelligenceFilters:
    radius_miles: float = 5
    sold_within_days: int = 365
    vacant_land_only: bool = False
    cash_only: bool = False
    buyer_types: list[str] = field(default_factory=list)

    def to_provider_payload(self) -> dict[str, Any]:
        return {
            "radiusMiles": self.radius_miles,
            "soldWithinDays": self.sold_within_days,
            "vacantLandOnly": self.vacant_land_only,
            "cashOnly": self.cash_only,
            "buyerTypes": self.buyer_types,
        }


class MarketIntelligenceService:
    def build_snapshot(
        self,
        lead_payload: dict[str, Any],
        filters: MarketIntelligenceFilters | None = None,
        provider_name: str = "",
    ) -> dict[str, Any]:
        filters = filters or MarketIntelligenceFilters()
        subject = build_subject_property(lead_payload)
        provider_result = self.load_provider_result(subject, filters, provider_name=provider_name)
        disposition_workspace = build_disposition_workspace(
            lead_payload,
            radius_miles=filters.radius_miles,
            sold_within_days=filters.sold_within_days,
            vacant_land_only=filters.vacant_land_only,
            cash_only=filters.cash_only,
            buyer_types=filters.buyer_types,
            transactions=provider_result.get("transactions") or [],
            provider_result=provider_result,
        )
        transactions = disposition_workspace.get("transactions") or []
        buyer_matches = disposition_workspace.get("buyerMatches") or []
        buyer_footprints = build_buyer_footprints(transactions, disposition_workspace["subject"])
        map_transactions = build_map_transactions(transactions, buyer_footprints)
        enhanced_workspace = {**disposition_workspace, "transactions": map_transactions}
        deal_summary = build_deal_intelligence_summary(buyer_footprints, buyer_matches, map_transactions)
        market_snapshot = build_market_snapshot(enhanced_workspace, buyer_footprints, deal_summary)

        return {
            **enhanced_workspace,
            "buyerFootprints": buyer_footprints,
            "dealIntelligenceSummary": deal_summary,
            "marketIntelligence": market_snapshot,
        }

    def refresh_transactions(
        self,
        lead_payload: dict[str, Any],
        filters: MarketIntelligenceFilters | None = None,
        provider_name: str = "",
    ) -> dict[str, Any]:
        filters = filters or MarketIntelligenceFilters()
        subject = build_subject_property(lead_payload)
        provider_result = get_provider(provider_name or None).refresh(subject, filters.to_provider_payload())
        return {
            "provider": provider_result.get("provider") or "mock",
            "sourceName": provider_result.get("sourceName") or "",
            "lastRefreshAt": provider_result.get("lastRefreshAt") or "",
            "errors": provider_result.get("errors") or [],
            "transactionCount": len(provider_result.get("transactions") or []),
        }

    def load_provider_result(
        self,
        subject: dict[str, Any],
        filters: MarketIntelligenceFilters,
        provider_name: str = "",
    ) -> dict[str, Any]:
        provider = get_provider(provider_name or None)
        provider_result = provider.search(subject, filters.to_provider_payload())
        if provider_result.get("transactions") or provider.name == "mock":
            return provider_result

        fallback_result = get_provider("mock").search(subject, filters.to_provider_payload())
        return {
            **fallback_result,
            "provider": provider.name,
            "sourceName": f"{provider_result.get('sourceName') or provider.name} / mock fallback",
            "lastRefreshAt": provider_result.get("lastRefreshAt") or fallback_result.get("lastRefreshAt") or "",
            "errors": [
                *(provider_result.get("errors") or []),
                "No saved transactions found for this provider yet, so ChatCRM is showing mock activity until a CSV is imported.",
            ],
        }


def build_market_snapshot(
    disposition_workspace: dict[str, Any],
    buyer_footprints: dict[str, dict[str, Any]],
    deal_summary: list[dict[str, Any]],
) -> dict[str, Any]:
    opportunity = build_opportunity_score(disposition_workspace, buyer_footprints)
    return {
        "engine": "Market Intelligence Engine",
        "version": "market-intelligence-map-v1",
        "modules": [
            "Transaction Engine",
            "Buyer Intelligence",
            "Buyer Footprints",
            "Corridor Detection",
            "Buyer Prediction",
            "Opportunity Scoring",
            "Market Intelligence Map",
        ],
        "opportunityScore": opportunity,
        "map": build_map_snapshot(disposition_workspace, buyer_footprints),
        "summary": build_plain_language_summary(disposition_workspace, buyer_footprints, opportunity),
        "dealSummary": deal_summary,
    }


def build_map_transactions(
    transactions: list[dict[str, Any]],
    buyer_footprints: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            **transaction,
            "normalizedBuyerName": normalize_entity_name(transaction.get("buyerName")),
            "marketMarkerType": classify_market_marker(transaction, buyer_footprints),
            "evidenceTags": build_transaction_evidence_tags(transaction, buyer_footprints),
        }
        for transaction in transactions
    ]


def build_map_snapshot(
    disposition_workspace: dict[str, Any],
    buyer_footprints: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    subject = disposition_workspace.get("subject") or {}
    transactions = disposition_workspace.get("transactions") or []
    filters = disposition_workspace.get("filters") or {}
    return {
        "center": subject.get("coordinates") or {},
        "subjectMarker": {
            "type": "subject_property",
            "label": "Subject Property",
            "address": subject.get("address") or "",
            "coordinates": subject.get("coordinates") or {},
            "color": "gold",
            "size": "large",
        },
        "markerLegend": [
            {"type": "recorded_sale", "label": "Nearby Recorded Sale", "color": "blue", "active": True},
            {"type": "cash_purchase", "label": "Cash Purchase", "color": "green", "active": True},
            {"type": "builder_purchase", "label": "Builder Purchase", "color": "gold", "active": True},
            {"type": "repeat_buyer", "label": "Repeat Buyer", "color": "purple", "active": True},
            {"type": "unknown_estimated", "label": "Unknown / Estimated", "color": "gray", "active": True},
        ],
        "futureLayers": [
            {"type": "active_permits", "label": "Active Permits", "available": False},
            {"type": "builder_holdings", "label": "Builder Holdings", "available": False},
            {"type": "utilities", "label": "Utilities", "available": False},
            {"type": "flood", "label": "Flood", "available": False},
            {"type": "zoning", "label": "Zoning", "available": False},
            {"type": "ownership", "label": "Ownership", "available": False},
        ],
        "timeline": {
            "options": [30, 90, 180, 365],
            "selectedDays": filters.get("soldWithinDays") or 365,
            "oldestSaleDate": min_sale_date(transactions),
            "newestSaleDate": max_sale_date(transactions),
            "visibleTransactionCount": len(transactions),
        },
        "buyerHighlights": build_buyer_highlights(buyer_footprints),
    }


def classify_market_marker(transaction: dict[str, Any], buyer_footprints: dict[str, dict[str, Any]]) -> str:
    buyer_key = normalize_entity_name(transaction.get("buyerName"))
    footprint = buyer_footprints.get(buyer_key) or {}
    quality = str(transaction.get("dataQuality") or "").lower()
    confidence = safe_float(transaction.get("confidence"), 100)
    buyer_type = str(transaction.get("buyerType") or "").lower()
    buyer_name = str(transaction.get("buyerName") or "").lower()

    if quality in {"estimated", "incomplete", "stale"} or confidence < 65 or not safe_float(transaction.get("salePrice"), 0):
        return "unknown_estimated"
    if safe_float(footprint.get("verifiedPurchaseCount"), 0) >= 2 or safe_float(footprint.get("transactionCount"), 0) >= 2:
        return "repeat_buyer"
    if buyer_type == "builder" or any(word in buyer_name for word in ["builder", "builders", "homes", "construction"]):
        return "builder_purchase"
    if transaction.get("cashSale"):
        return "cash_purchase"
    return "recorded_sale"


def build_transaction_evidence_tags(transaction: dict[str, Any], buyer_footprints: dict[str, dict[str, Any]]) -> list[str]:
    buyer_key = normalize_entity_name(transaction.get("buyerName"))
    footprint = buyer_footprints.get(buyer_key) or {}
    tags: list[str] = []
    if transaction.get("cashSale"):
        tags.append("Cash purchase")
    if str(transaction.get("buyerType") or "").lower() == "builder":
        tags.append("Builder activity")
    if safe_float(footprint.get("verifiedPurchaseCount"), 0) >= 2:
        tags.append("Verified repeat buyer")
    if safe_float(transaction.get("distanceMiles"), 999) <= 1:
        tags.append("Within 1 mile")
    if safe_float(transaction.get("confidence"), 100) < 80:
        tags.append("Needs source review")
    return tags


def build_buyer_highlights(buyer_footprints: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    highlights: dict[str, dict[str, Any]] = {}
    for key, footprint in buyer_footprints.items():
        highlights[key] = {
            "buyerName": footprint.get("entityName") or key.title(),
            "verifiedPurchases": footprint.get("verifiedPurchaseCount") or 0,
            "purchasesWithin": {
                "1": footprint.get("purchasesByRadius", {}).get("1", 0),
                "3": footprint.get("purchasesByRadius", {}).get("3", 0),
                "5": footprint.get("purchasesByRadius", {}).get("5", 0),
                "10": footprint.get("purchasesByRadius", {}).get("10", 0),
            },
            "averagePurchase": footprint.get("averagePurchasePrice") or 0,
            "averageAcreage": footprint.get("averageAcreage") or 0,
            "averagePricePerAcre": footprint.get("averagePricePerAcre") or 0,
            "latestPurchase": footprint.get("latestPurchaseDate") or "",
            "buyingTrend": footprint.get("activityTrend") or {},
            "intentSignals": footprint.get("intentSignals") or [],
        }
    return highlights


def min_sale_date(transactions: list[dict[str, Any]]) -> str:
    dates = [str(item.get("saleDate") or "") for item in transactions if item.get("saleDate")]
    return min(dates) if dates else ""


def max_sale_date(transactions: list[dict[str, Any]]) -> str:
    dates = [str(item.get("saleDate") or "") for item in transactions if item.get("saleDate")]
    return max(dates) if dates else ""


def build_opportunity_score(disposition_workspace: dict[str, Any], buyer_footprints: dict[str, dict[str, Any]]) -> dict[str, Any]:
    overview = disposition_workspace.get("overview") or {}
    transactions = disposition_workspace.get("transactions") or []
    buyer_matches = disposition_workspace.get("buyerMatches") or []
    subject = disposition_workspace.get("subject") or {}

    buyer_demand = min(25, safe_float(overview.get("verifiedNearbyBuyers"), 0) * 5 + safe_float(overview.get("highMatchBuyers"), 0) * 3)
    builder_activity = min(20, safe_float(overview.get("activeBuilders"), 0) * 7)
    corridor_strength = min(20, sum(len(item.get("corridorSignals") or []) for item in buyer_footprints.values()) * 5)
    pricing_signal = score_pricing_signal(disposition_workspace)
    parcel_fit = score_parcel_fit(subject, transactions)
    top_match_bonus = min(10, safe_float(buyer_matches[0].get("score"), 0) / 10) if buyer_matches else 0
    total = round(min(100, buyer_demand + builder_activity + corridor_strength + pricing_signal + parcel_fit + top_match_bonus))

    return {
        "score": total,
        "grade": score_grade(total),
        "reasons": [
            {"label": "Buyer Demand", "points": round(buyer_demand), "detail": f"{overview.get('verifiedNearbyBuyers', 0)} nearby buyer groups and {overview.get('highMatchBuyers', 0)} high matches."},
            {"label": "Builder Activity", "points": round(builder_activity), "detail": f"{overview.get('activeBuilders', 0)} active builders detected nearby."},
            {"label": "Corridor Strength", "points": round(corridor_strength), "detail": "Based on same-street, tight-radius, and recent acquisition signals."},
            {"label": "Pricing", "points": round(pricing_signal), "detail": "Compares projected spread and nearby price-per-acre evidence."},
            {"label": "Parcel Fit", "points": round(parcel_fit), "detail": "Compares acreage and land-use fit against nearby transactions."},
            {"label": "Strongest Buyer Match", "points": round(top_match_bonus), "detail": buyer_matches[0].get("buyerName") if buyer_matches else "No ranked buyer yet."},
        ],
    }


def score_pricing_signal(disposition_workspace: dict[str, Any]) -> float:
    overview = disposition_workspace.get("overview") or {}
    spread = safe_float(overview.get("estimatedAssignmentSpread"), 0)
    average_price_per_acre = safe_float(overview.get("averagePricePerAcre"), 0)
    if spread >= 25000:
        return 15
    if spread >= 10000 and average_price_per_acre:
        return 12
    if average_price_per_acre:
        return 8
    return 4


def score_parcel_fit(subject: dict[str, Any], transactions: list[dict[str, Any]]) -> float:
    subject_type = str(subject.get("propertyType") or "").lower()
    subject_acreage = safe_float(subject.get("acreage"), 0)
    if not transactions:
        return 3
    comparable_type_count = len(
        [item for item in transactions if subject_type and subject_type in str(item.get("propertyType") or "").lower()]
    )
    comparable_acreage_count = len(
        [
            item
            for item in transactions
            if subject_acreage and 0.5 <= safe_float(item.get("acreage"), 0) / max(subject_acreage, 0.01) <= 2
        ]
    )
    return min(10, comparable_type_count * 2 + comparable_acreage_count)


def build_plain_language_summary(
    disposition_workspace: dict[str, Any],
    buyer_footprints: dict[str, dict[str, Any]],
    opportunity: dict[str, Any],
) -> str:
    overview = disposition_workspace.get("overview") or {}
    strongest = (disposition_workspace.get("buyerMatches") or [{}])[0]
    corridor_count = sum(len(item.get("corridorSignals") or []) for item in buyer_footprints.values())
    return (
        f"Opportunity Score {opportunity['score']} ({opportunity['grade']}). "
        f"ChatCRM found {overview.get('verifiedNearbyBuyers', 0)} nearby buyer groups, "
        f"{overview.get('activeBuilders', 0)} active builders, and {corridor_count} corridor signals. "
        f"Strongest buyer match: {strongest.get('buyerName') or 'none yet'}."
    )


def score_grade(score: int) -> str:
    if score >= 90:
        return "Elite"
    if score >= 75:
        return "Strong"
    if score >= 55:
        return "Watch"
    return "Needs Data"