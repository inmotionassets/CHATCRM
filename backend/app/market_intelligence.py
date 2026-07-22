from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
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

    def build_property_snapshot(
        self,
        lead_payload: dict[str, Any],
        parcel_payload: dict[str, Any] | None = None,
        filters: MarketIntelligenceFilters | None = None,
        provider_name: str = "",
    ) -> dict[str, Any]:
        filters = filters or MarketIntelligenceFilters(radius_miles=10, sold_within_days=365)
        parcel_payload = parcel_payload or {}
        merged_payload = merge_property_payload(lead_payload, parcel_payload)
        market_workspace = self.build_snapshot(merged_payload, filters=filters, provider_name=provider_name)
        subject = build_property_subject(
            market_workspace.get("subject") or {},
            lead_payload,
            parcel_payload,
            market_workspace.get("marketIntelligence", {}).get("opportunityScore") or {},
            market_workspace.get("readiness") or [],
        )
        narrative = build_market_narrative(market_workspace, subject)
        most_probable_buyers = build_most_probable_buyers(market_workspace.get("buyerMatches") or [])
        source_badges = build_source_badges(lead_payload, parcel_payload, market_workspace)
        confidence = build_overall_confidence(market_workspace, subject, source_badges)
        assessment = build_legacy_assessment(market_workspace, subject, most_probable_buyers, confidence)
        evidence_breakdown = build_evidence_breakdown(market_workspace, subject, confidence)
        workspace_header = build_workspace_header(confidence, source_badges)
        market_intelligence = {
            **(market_workspace.get("marketIntelligence") or {}),
            "workspaceHeader": workspace_header,
            "assessment": assessment,
            "evidenceBreakdown": evidence_breakdown,
            "confidence": confidence,
            "sourceBadges": source_badges,
            "narrative": narrative,
            "mostProbableBuyers": most_probable_buyers,
        }
        map_snapshot = {
            **(market_intelligence.get("map") or {}),
            "center": subject.get("coordinates") or {},
            "subjectMarker": {
                **((market_intelligence.get("map") or {}).get("subjectMarker") or {}),
                "type": "subject_property",
                "label": "Subject Property",
                "address": subject.get("address") or "",
                "coordinates": subject.get("coordinates") or {},
                "color": "gold",
                "size": "large",
            },
            "subjectParcel": subject.get("parcel") or {},
        }
        market_intelligence["map"] = map_snapshot

        return {
            "engine": "LEGACY Property Intelligence",
            "version": "property-intelligence-workspace-v1",
            "addressTrigger": subject.get("address") or "",
            "workspaceType": "Property Intelligence Workspace",
            "subjectProperty": subject,
            "workspaceHeader": workspace_header,
            "assessment": assessment,
            "marketIntelligence": market_intelligence,
            "transactions": market_workspace.get("transactions") or [],
            "buyerMatches": market_workspace.get("buyerMatches") or [],
            "buyerFootprints": market_workspace.get("buyerFootprints") or {},
            "dealIntelligenceSummary": market_workspace.get("dealIntelligenceSummary") or [],
            "source": market_workspace.get("source") or {},
            "overview": market_workspace.get("overview") or {},
            "contactIntelligence": build_contact_intelligence(lead_payload, parcel_payload),
            "workspacePanels": [
                "Subject Property",
                "Market Intelligence Map",
                "Market Narrative",
                "Buyer Matches",
                "Buyer Footprint",
                "Contact Intelligence",
            ],
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
        "subjectParcel": {
            "boundary": build_estimated_parcel_boundary(subject),
            "boundaryType": "estimated",
            "boundarySource": "Address-based estimate until county GIS parcel geometry is connected.",
            "glow": "gold",
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

def merge_property_payload(lead_payload: dict[str, Any], parcel_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **lead_payload,
        "address": parcel_payload.get("address") or lead_payload.get("address") or "",
        "parcelNumber": parcel_payload.get("apn") or lead_payload.get("parcelNumber") or "",
        "county": parcel_payload.get("county") or lead_payload.get("county") or "Dallas",
        "lotSize": parcel_payload.get("acreage") or parcel_payload.get("lotDimensions") or lead_payload.get("lotSize") or "",
        "zoning": parcel_payload.get("zoning") or lead_payload.get("zoning") or "",
        "floodZone": parcel_payload.get("floodZone") or lead_payload.get("floodZone") or "",
        "utilities": parcel_payload.get("utilityAvailability") or lead_payload.get("utilities") or "",
    }


def build_property_subject(
    subject: dict[str, Any],
    lead_payload: dict[str, Any],
    parcel_payload: dict[str, Any],
    opportunity: dict[str, Any],
    readiness: list[dict[str, Any]],
) -> dict[str, Any]:
    coordinates = subject.get("coordinates") or {}
    parcel_boundary = build_estimated_parcel_boundary(subject)
    deal_timeline = [
        {"label": item.get("label") or "", "complete": bool(item.get("complete"))}
        for item in readiness
        if item.get("label")
    ]

    return {
        "leadId": subject.get("leadId") or lead_payload.get("id") or "",
        "address": subject.get("address") or lead_payload.get("address") or "",
        "coordinates": coordinates,
        "latitude": coordinates.get("lat"),
        "longitude": coordinates.get("lng"),
        "parcel": {
            "apn": subject.get("apn") or parcel_payload.get("apn") or "",
            "boundary": parcel_boundary,
            "boundaryType": "estimated",
            "boundarySource": "Address-based estimate until county GIS geometry is connected.",
            "confidence": 58 if parcel_boundary else 0,
        },
        "apn": subject.get("apn") or parcel_payload.get("apn") or "",
        "county": subject.get("county") or parcel_payload.get("county") or "Dallas",
        "subdivision": parcel_payload.get("legalDescription") or "",
        "lotSize": parcel_payload.get("acreage") or subject.get("acreage") or "",
        "acreage": subject.get("acreage") or 0,
        "propertyType": subject.get("propertyType") or parcel_payload.get("landUse") or "Vacant Land",
        "zoning": subject.get("zoning") or parcel_payload.get("zoning") or "Unknown",
        "utilities": subject.get("utilities") or parcel_payload.get("utilityAvailability") or "Unknown",
        "floodZone": subject.get("floodZone") or parcel_payload.get("floodZone") or "Unknown",
        "roadAccess": parcel_payload.get("roadAccess") or "Needs Review",
        "taxStatus": parcel_payload.get("taxDelinquencyStatus") or "Unknown",
        "owner": lead_payload.get("name") or lead_payload.get("owner") or "Owner needed",
        "seller": lead_payload.get("name") or "Seller needed",
        "contractPrice": subject.get("contractPrice") or 0,
        "targetAssignment": subject.get("targetAssignmentPrice") or 0,
        "opportunityScore": opportunity.get("score") or 0,
        "opportunityGrade": opportunity.get("grade") or "Needs Data",
        "dealStatus": lead_payload.get("stage") or "New Lead",
        "dealTimeline": deal_timeline,
    }


def build_estimated_parcel_boundary(subject: dict[str, Any]) -> list[dict[str, float]]:
    coordinates = subject.get("coordinates") or {}
    lat = safe_float(coordinates.get("lat"), 0)
    lng = safe_float(coordinates.get("lng"), 0)
    if not lat or not lng:
        return []

    acreage = max(safe_float(subject.get("acreage"), 1.2), 0.1)
    offset = min(max((acreage ** 0.5) * 0.00055, 0.00035), 0.0022)
    return [
        {"lat": round(lat - offset, 6), "lng": round(lng - offset, 6)},
        {"lat": round(lat - offset, 6), "lng": round(lng + offset, 6)},
        {"lat": round(lat + offset, 6), "lng": round(lng + offset, 6)},
        {"lat": round(lat + offset, 6), "lng": round(lng - offset, 6)},
    ]


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_workspace_header(confidence: dict[str, Any], source_badges: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "title": "LEGACY Workspace",
        "subtitle": "Property Intelligence Workspace",
        "analyzedAt": current_timestamp(),
        "confidence": confidence.get("score") or 0,
        "confidenceLabel": confidence.get("label") or "Needs Data",
        "sources": source_badges,
    }


def build_source_badges(
    lead_payload: dict[str, Any],
    parcel_payload: dict[str, Any],
    workspace: dict[str, Any],
) -> list[dict[str, Any]]:
    source = workspace.get("source") or {}
    transactions = workspace.get("transactions") or []
    buyer_matches = workspace.get("buyerMatches") or []
    apn = parcel_payload.get("apn") or lead_payload.get("parcelNumber") or ""
    address = parcel_payload.get("address") or lead_payload.get("address") or ""
    avg_transaction_confidence = average_number([item.get("confidence") for item in transactions])

    return [
        {
            "label": "County Records",
            "status": "Verified" if apn else "Needs APN",
            "confidence": 82 if apn else 48,
            "verified": bool(apn),
            "source": parcel_payload.get("dataSource") or "Lead / parcel record",
            "detail": "APN and county fields are present." if apn else "Add APN to strengthen county record confidence.",
        },
        {
            "label": "Recorded Sales",
            "status": "Active" if transactions else "Needs Import",
            "confidence": round(avg_transaction_confidence) if avg_transaction_confidence else 45,
            "verified": bool(transactions),
            "source": source.get("sourceName") or "Market transaction provider",
            "detail": f"{len(transactions)} nearby transaction signals loaded.",
        },
        {
            "label": "Buyer Activity",
            "status": "Active" if buyer_matches else "Needs Buyer Data",
            "confidence": min(96, 58 + len(buyer_matches) * 6) if buyer_matches else 40,
            "verified": bool(buyer_matches),
            "source": "Buyer matching and footprint engine",
            "detail": f"{len(buyer_matches)} ranked buyer groups found.",
        },
        {
            "label": "Internal Intelligence",
            "status": "Active" if address else "Needs Address",
            "confidence": 86 if address else 35,
            "verified": bool(address),
            "source": "ChatCRM lead record",
            "detail": "Lead address and workflow history are available." if address else "Address is needed before LEGACY can build the workspace.",
        },
    ]


def build_overall_confidence(
    workspace: dict[str, Any],
    subject: dict[str, Any],
    source_badges: list[dict[str, Any]],
) -> dict[str, Any]:
    source_score = average_number([item.get("confidence") for item in source_badges]) or 0
    transaction_score = average_number([item.get("confidence") for item in workspace.get("transactions") or []]) or 0
    buyer_count = len(workspace.get("buyerMatches") or [])
    buyer_score = min(96, 52 + buyer_count * 7) if buyer_count else 36
    parcel_score = 88 if subject.get("apn") and subject.get("address") else 58 if subject.get("address") else 35
    overall = round(average_number([source_score, transaction_score or source_score, buyer_score, parcel_score]) or 0)
    return {
        "score": max(0, min(100, overall)),
        "label": percent_confidence_label(overall),
        "drivers": [
            {"label": "Source Coverage", "score": round(source_score)},
            {"label": "Transaction Quality", "score": round(transaction_score or source_score)},
            {"label": "Buyer Evidence", "score": round(buyer_score)},
            {"label": "Parcel Completeness", "score": round(parcel_score)},
        ],
    }


def build_legacy_assessment(
    workspace: dict[str, Any],
    subject: dict[str, Any],
    most_probable_buyers: list[dict[str, Any]],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    market_intelligence = workspace.get("marketIntelligence") or {}
    opportunity = market_intelligence.get("opportunityScore") or {}
    overview = workspace.get("overview") or {}
    top_buyer = most_probable_buyers[0] if most_probable_buyers else {}
    score = safe_float(opportunity.get("score"), 0)
    confidence_score = safe_float(confidence.get("score"), 0)
    spread = safe_float(overview.get("estimatedAssignmentSpread"), 0)
    assignment_potential = build_assignment_potential(spread, subject)
    action = recommended_action(score, confidence_score)
    next_action = next_best_action(top_buyer, subject, overview, score)

    summary = build_assessment_summary(action, overview, top_buyer, opportunity, assignment_potential)
    return {
        "recommendedAction": action,
        "actionTone": action_tone(action),
        "nextBestAction": next_action,
        "assignmentPotential": assignment_potential,
        "confidence": confidence,
        "summary": summary,
        "evidence": [
            {"label": "Opportunity Score", "value": opportunity.get("score") or 0, "source": "Opportunity Engine"},
            {"label": "Top Buyer", "value": top_buyer.get("buyerName") or "No ranked buyer yet", "source": "Buyer Intelligence"},
            {"label": "Nearby Buyer Groups", "value": overview.get("verifiedNearbyBuyers", 0), "source": "Buyer Activity"},
            {"label": "Active Builders", "value": overview.get("activeBuilders", 0), "source": "Buyer Activity"},
            {"label": "Estimated Assignment Potential", "value": assignment_potential.get("label"), "source": "Pricing Intelligence"},
        ],
    }


def build_assignment_potential(spread: float, subject: dict[str, Any]) -> dict[str, Any]:
    if spread <= 0:
        target_assignment = safe_float(subject.get("targetAssignment"), 0)
        contract_price = safe_float(subject.get("contractPrice"), 0)
        spread = max(0, target_assignment - contract_price)
    if spread <= 0:
        return {"low": 0, "high": 0, "label": "Needs pricing data", "source": "Pricing Intelligence"}
    low = round(spread * 0.7)
    high = round(spread * 1.15)
    return {"low": low, "high": high, "label": f"${low:,.0f} - ${high:,.0f}", "source": "Pricing Intelligence"}


def recommended_action(score: float, confidence_score: float) -> str:
    if score >= 85 and confidence_score >= 80:
        return "Pursue Immediately"
    if score >= 72:
        return "Pursue"
    if score >= 55:
        return "Review"
    if score >= 42:
        return "Reprice"
    return "Pass"


def action_tone(action: str) -> str:
    return {
        "Pursue Immediately": "strong",
        "Pursue": "positive",
        "Review": "watch",
        "Reprice": "caution",
        "Pass": "muted",
    }.get(action, "watch")


def next_best_action(
    top_buyer: dict[str, Any],
    subject: dict[str, Any],
    overview: dict[str, Any],
    score: float,
) -> dict[str, Any]:
    if top_buyer.get("buyerName") and safe_float(top_buyer.get("score"), 0) >= 70:
        return {
            "label": f"Call {top_buyer.get('buyerName')} first",
            "reason": "This buyer has the strongest match score and nearby activity.",
            "source": "Recommendation Engine",
        }
    if str(subject.get("utilities") or "").lower() in {"", "unknown", "needs review"}:
        return {
            "label": "Verify utility availability",
            "reason": "Utility confidence is still low, and that can affect buyer demand.",
            "source": "Recommendation Engine",
        }
    if safe_float(overview.get("recentSimilarSales"), 0) < 3:
        return {
            "label": "Expand search radius",
            "reason": "LEGACY needs more comparable sales before making a stronger recommendation.",
            "source": "Recommendation Engine",
        }
    if score < 55:
        return {
            "label": "Review price before outreach",
            "reason": "The opportunity score is not strong enough yet for aggressive buyer outreach.",
            "source": "Recommendation Engine",
        }
    return {
        "label": "Prepare buyer outreach package",
        "reason": "Market and buyer signals are strong enough to move toward disposition.",
        "source": "Recommendation Engine",
    }


def build_assessment_summary(
    action: str,
    overview: dict[str, Any],
    top_buyer: dict[str, Any],
    opportunity: dict[str, Any],
    assignment_potential: dict[str, Any],
) -> str:
    buyer_count = overview.get("verifiedNearbyBuyers", 0)
    builder_count = overview.get("activeBuilders", 0)
    top_buyer_name = top_buyer.get("buyerName") or "the top ranked buyer"
    if action in {"Pursue Immediately", "Pursue"}:
        return (
            f"This parcel sits inside an active buyer pocket with {buyer_count} buyer groups and "
            f"{builder_count} builder groups detected nearby. {top_buyer_name} should be contacted first, "
            f"with estimated assignment potential of {assignment_potential.get('label')}.")
    if action == "Review":
        return (
            f"LEGACY sees a workable opportunity, but the evidence is not complete yet. "
            f"Review buyer demand, utilities, and price support before pushing this deal hard.")
    if action == "Reprice":
        return "LEGACY needs stronger pricing support before this should move forward. Recheck contract price, acreage, and nearby transaction quality."
    return "LEGACY does not see enough evidence yet to recommend pursuit. Add better parcel, pricing, or transaction data before investing more time."


def build_evidence_breakdown(
    workspace: dict[str, Any],
    subject: dict[str, Any],
    confidence: dict[str, Any],
) -> list[dict[str, Any]]:
    overview = workspace.get("overview") or {}
    transactions = workspace.get("transactions") or []
    buyer_matches = workspace.get("buyerMatches") or []
    buyer_footprints = workspace.get("buyerFootprints") or {}
    opportunity = (workspace.get("marketIntelligence") or {}).get("opportunityScore") or {}
    recent_90 = count_recent_transactions(transactions, 90)
    cash_count = len([item for item in transactions if item.get("cashSale")])
    same_street = count_same_street_transactions(subject.get("address") or "", transactions)
    top_buyer = buyer_matches[0] if buyer_matches else {}

    return [
        {
            "id": "buyer-demand",
            "label": "Buyer Demand",
            "score": min(100, safe_float(overview.get("verifiedNearbyBuyers"), 0) * 18 + safe_float(overview.get("highMatchBuyers"), 0) * 10),
            "confidence": confidence.get("label"),
            "source": "Buyer Activity",
            "summary": "Measures how many real buyer groups are active around this property.",
            "evidence": [
                {"label": "Nearby buyer groups", "value": overview.get("verifiedNearbyBuyers", 0)},
                {"label": "High-match buyers", "value": overview.get("highMatchBuyers", 0)},
                {"label": "Top buyer", "value": top_buyer.get("buyerName") or "No ranked buyer yet"},
                {"label": "Cash purchase signals", "value": cash_count},
            ],
        },
        {
            "id": "builder-activity",
            "label": "Builder Activity",
            "score": min(100, safe_float(overview.get("activeBuilders"), 0) * 30 + same_street * 12),
            "confidence": confidence.get("label"),
            "source": "Buyer Footprints",
            "summary": "Looks for builder and repeat-buyer activity close to the subject parcel.",
            "evidence": [
                {"label": "Active builders", "value": overview.get("activeBuilders", 0)},
                {"label": "Same-street signals", "value": same_street},
                {"label": "Buyer footprints", "value": len(buyer_footprints)},
            ],
        },
        {
            "id": "market-velocity",
            "label": "Market Velocity",
            "score": min(100, recent_90 * 18 + len(transactions) * 4),
            "confidence": confidence.get("label"),
            "source": "Recorded Sales",
            "summary": "Shows whether nearby land has been moving recently.",
            "evidence": [
                {"label": "Sales in last 90 days", "value": recent_90},
                {"label": "Visible transactions", "value": len(transactions)},
                {"label": "Latest sale", "value": max_sale_date(transactions) or "No sale date"},
            ],
        },
        {
            "id": "price-support",
            "label": "Price Support",
            "score": min(100, safe_float(overview.get("estimatedAssignmentSpread"), 0) / 350 + (25 if overview.get("averagePricePerAcre") else 0)),
            "confidence": confidence.get("label"),
            "source": "Pricing Intelligence",
            "summary": "Compares nearby price-per-acre evidence against the current acquisition target.",
            "evidence": [
                {"label": "Average price per acre", "value": overview.get("averagePricePerAcre", 0)},
                {"label": "Estimated assignment spread", "value": overview.get("estimatedAssignmentSpread", 0)},
                {"label": "Opportunity score", "value": opportunity.get("score") or 0},
            ],
        },
        {
            "id": "parcel-quality",
            "label": "Parcel Quality",
            "score": parcel_quality_score(subject),
            "confidence": confidence.get("label"),
            "source": "County Records",
            "summary": "Checks whether core parcel facts are present and usable.",
            "evidence": [
                {"label": "APN", "value": subject.get("apn") or "Missing"},
                {"label": "Acreage", "value": subject.get("acreage") or "Missing"},
                {"label": "Zoning", "value": subject.get("zoning") or "Unknown"},
                {"label": "Utilities", "value": subject.get("utilities") or "Unknown"},
                {"label": "Flood zone", "value": subject.get("floodZone") or "Unknown"},
            ],
        },
        {
            "id": "confidence",
            "label": "Confidence",
            "score": confidence.get("score") or 0,
            "confidence": confidence.get("label"),
            "source": "Evidence Engine",
            "summary": "Shows how reliable LEGACY believes this recommendation is right now.",
            "evidence": confidence.get("drivers") or [],
        },
    ]


def average_number(values: list[Any]) -> float:
    clean = [safe_float(value, 0) for value in values if safe_float(value, 0) > 0]
    return sum(clean) / len(clean) if clean else 0


def percent_confidence_label(value: Any) -> str:
    score = safe_float(value, 0)
    if score >= 82:
        return "High"
    if score >= 62:
        return "Medium"
    if score > 0:
        return "Low"
    return "Needs Data"


def count_recent_transactions(transactions: list[dict[str, Any]], days: int) -> int:
    today = datetime.now(timezone.utc).date()
    count = 0
    for transaction in transactions:
        sale_date = str(transaction.get("saleDate") or "")
        if not sale_date:
            continue
        try:
            parsed = datetime.fromisoformat(sale_date[:10]).date()
        except ValueError:
            continue
        if (today - parsed).days <= days:
            count += 1
    return count


def parcel_quality_score(subject: dict[str, Any]) -> int:
    score = 0
    if subject.get("apn"):
        score += 22
    if safe_float(subject.get("acreage"), 0):
        score += 20
    if str(subject.get("zoning") or "").lower() not in {"", "unknown"}:
        score += 16
    if str(subject.get("utilities") or "").lower() not in {"", "unknown", "needs review"}:
        score += 18
    if str(subject.get("floodZone") or "").lower() not in {"", "unknown"}:
        score += 14
    if subject.get("coordinates"):
        score += 10
    return min(100, score)

def build_market_narrative(workspace: dict[str, Any], subject: dict[str, Any]) -> list[dict[str, Any]]:
    overview = workspace.get("overview") or {}
    buyer_matches = workspace.get("buyerMatches") or []
    transactions = workspace.get("transactions") or []
    opportunity = (workspace.get("marketIntelligence") or {}).get("opportunityScore") or {}
    strongest_buyer = buyer_matches[0] if buyer_matches else {}
    same_street_matches = count_same_street_transactions(subject.get("address") or "", transactions)
    recent_90 = count_recent_transactions(transactions, 90)
    cash_count = len([item for item in transactions if item.get("cashSale")])
    active_builders = overview.get("activeBuilders", 0)
    nearby_buyers = overview.get("verifiedNearbyBuyers", 0)

    corridor_sentence = "This property sits inside an active residential builder pocket."
    if not active_builders and not nearby_buyers:
        corridor_sentence = "LEGACY needs more buyer and builder evidence before calling this a proven market pocket."

    buyer_sentence = f"{strongest_buyer.get('buyerName') or 'No ranked buyer yet'} is the first buyer to review because the match score is {strongest_buyer.get('score', 0)}."
    if not strongest_buyer:
        buyer_sentence = "No ranked buyer has enough evidence yet, so the next step is importing or refreshing nearby activity."

    velocity_sentence = f"Recent activity shows {recent_90} nearby purchases in the last ninety days and {len(transactions)} visible transaction signals overall."
    if recent_90 == 0:
        velocity_sentence = "Recent purchase velocity is still unproven because LEGACY has not found a sale in the last ninety days."

    pricing_sentence = f"Nearby price-per-acre evidence is ${overview.get('averagePricePerAcre', 0):,}, with estimated assignment potential of ${overview.get('estimatedAssignmentSpread', 0):,}."
    if not overview.get("averagePricePerAcre"):
        pricing_sentence = "Pricing support is still low because LEGACY has not found usable price-per-acre evidence."

    return [
        {
            "id": "corridor",
            "sentence": corridor_sentence,
            "confidence": confidence_label(active_builders, nearby_buyers),
            "source": "Buyer Activity",
            "evidence": [
                {"label": "Active Builders", "value": active_builders},
                {"label": "Nearby Buyer Groups", "value": nearby_buyers},
            ],
        },
        {
            "id": "buyer-demand",
            "sentence": buyer_sentence,
            "confidence": confidence_label(strongest_buyer.get("score", 0)),
            "source": "Buyer Intelligence",
            "evidence": [
                {"label": "Match Score", "value": strongest_buyer.get("score", 0)},
                {"label": "Nearby Purchases", "value": strongest_buyer.get("nearbyPurchases", 0)},
                {"label": "Cash Purchase Signals", "value": cash_count},
            ],
        },
        {
            "id": "same-street",
            "sentence": f"LEGACY found {same_street_matches} same-street or close-street signals, which helps reveal whether this block is already attracting buyers.",
            "confidence": confidence_label(same_street_matches),
            "source": "Recorded Sales",
            "evidence": [
                {"label": "Same Street Signals", "value": same_street_matches},
                {"label": "Visible Transactions", "value": len(transactions)},
            ],
        },
        {
            "id": "velocity",
            "sentence": velocity_sentence,
            "confidence": confidence_label(recent_90, len(transactions)),
            "source": "Recorded Sales",
            "evidence": [
                {"label": "Purchases Last 90 Days", "value": recent_90},
                {"label": "Visible Transactions", "value": len(transactions)},
                {"label": "Latest Sale", "value": max_sale_date(transactions) or "No sale date"},
            ],
        },
        {
            "id": "pricing",
            "sentence": pricing_sentence,
            "confidence": confidence_label(overview.get("averagePricePerAcre", 0)),
            "source": "Pricing Intelligence",
            "evidence": [
                {"label": "Average Price/Acre", "value": overview.get("averagePricePerAcre", 0)},
                {"label": "Estimated Assignment Spread", "value": overview.get("estimatedAssignmentSpread", 0)},
            ],
        },
        {
            "id": "opportunity",
            "sentence": f"LEGACY rates this opportunity {opportunity.get('grade') or 'Needs Data'} at {opportunity.get('score', 0)} because the score is built from buyer demand, builder activity, pricing, parcel fit, and confidence.",
            "confidence": confidence_label(opportunity.get("score", 0)),
            "source": "Opportunity Engine",
            "evidence": opportunity.get("reasons") or [],
        },
    ]

def build_most_probable_buyers(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rank": index + 1,
            "buyerName": match.get("buyerName") or "Unknown Buyer",
            "normalizedBuyerName": match.get("normalizedBuyerName") or "",
            "score": match.get("score") or 0,
            "buyerType": match.get("buyerType") or "unknown",
            "reasons": [
                {"label": reason, "evidence": reason}
                for reason in (match.get("reasons") or [])
            ],
            "nearbyPurchases": match.get("nearbyPurchases") or 0,
            "latestPurchaseDate": match.get("latestPurchaseDate") or "",
            "averagePurchasePrice": match.get("averagePurchasePrice") or 0,
            "averageAcreage": match.get("averageAcreage") or 0,
            "averagePricePerAcre": match.get("averagePricePerAcre") or 0,
        }
        for index, match in enumerate(matches[:6])
    ]


def build_contact_intelligence(lead_payload: dict[str, Any], parcel_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "public-data-ready",
        "confidence": "Needs Public Source",
        "businessPhone": "",
        "officePhone": "",
        "email": lead_payload.get("email") or "",
        "website": "",
        "mailingAddress": "",
        "registeredAgent": "",
        "knownContacts": [],
        "verifiedToday": [
            item
            for item in [
                {"label": "Seller Email", "value": lead_payload.get("email") or "", "source": "Lead record"},
                {"label": "Parcel APN", "value": parcel_payload.get("apn") or lead_payload.get("parcelNumber") or "", "source": "Lead / parcel record"},
            ]
            if item.get("value")
        ],
        "futureProviders": ["Public business registry", "County records", "OpenCorporates", "Licensed skip trace", "Premium data"],
        "note": "Contact Intelligence replaces one-off skip tracing. Private phone enrichment is intentionally provider-ready, not hardcoded.",
    }


def count_same_street_transactions(address: str, transactions: list[dict[str, Any]]) -> int:
    street_tokens = [token for token in str(address).lower().split() if token and not token.isdigit()]
    street_key = " ".join(street_tokens[:2])
    if not street_key:
        return 0
    return len([item for item in transactions if street_key in str(item.get("address") or "").lower()])


def confidence_label(*values: Any) -> str:
    strongest = max([safe_float(value, 0) for value in values] or [0])
    if strongest >= 80:
        return "High"
    if strongest >= 3:
        return "Medium"
    if strongest > 0:
        return "Early Signal"
    return "Needs Data"