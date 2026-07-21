from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .buyer_footprints import build_buyer_footprints, build_deal_intelligence_summary
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
        deal_summary = build_deal_intelligence_summary(buyer_footprints, buyer_matches, transactions)
        market_snapshot = build_market_snapshot(disposition_workspace, buyer_footprints, deal_summary)

        return {
            **disposition_workspace,
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
        "version": "market-intelligence-v1",
        "modules": [
            "Transaction Engine",
            "Buyer Intelligence",
            "Buyer Footprints",
            "Corridor Detection",
            "Buyer Prediction",
            "Opportunity Scoring",
        ],
        "opportunityScore": opportunity,
        "summary": build_plain_language_summary(disposition_workspace, buyer_footprints, opportunity),
        "dealSummary": deal_summary,
    }


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