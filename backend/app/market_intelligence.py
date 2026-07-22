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
        market_intelligence = {
            **(market_workspace.get("marketIntelligence") or {}),
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


def build_market_narrative(workspace: dict[str, Any], subject: dict[str, Any]) -> list[dict[str, Any]]:
    overview = workspace.get("overview") or {}
    buyer_matches = workspace.get("buyerMatches") or []
    transactions = workspace.get("transactions") or []
    opportunity = (workspace.get("marketIntelligence") or {}).get("opportunityScore") or {}
    strongest_buyer = buyer_matches[0] if buyer_matches else {}
    same_street_matches = count_same_street_transactions(subject.get("address") or "", transactions)

    return [
        {
            "id": "corridor",
            "sentence": f"This property sits near {overview.get('activeBuilders', 0)} active builder groups and {overview.get('verifiedNearbyBuyers', 0)} nearby buyer groups.",
            "confidence": confidence_label(overview.get("activeBuilders", 0), overview.get("verifiedNearbyBuyers", 0)),
            "evidence": [
                {"label": "Active Builders", "value": overview.get("activeBuilders", 0)},
                {"label": "Nearby Buyer Groups", "value": overview.get("verifiedNearbyBuyers", 0)},
            ],
        },
        {
            "id": "buyer-demand",
            "sentence": f"{strongest_buyer.get('buyerName') or 'No buyer'} is currently the strongest ranked buyer for this property.",
            "confidence": confidence_label(strongest_buyer.get("score", 0)),
            "evidence": [
                {"label": "Match Score", "value": strongest_buyer.get("score", 0)},
                {"label": "Nearby Purchases", "value": strongest_buyer.get("nearbyPurchases", 0)},
            ],
        },
        {
            "id": "same-street",
            "sentence": f"LEGACY found {same_street_matches} same-street or close-street transaction signals around the subject address.",
            "confidence": confidence_label(same_street_matches),
            "evidence": [
                {"label": "Same Street Signals", "value": same_street_matches},
                {"label": "Visible Transactions", "value": len(transactions)},
            ],
        },
        {
            "id": "pricing",
            "sentence": f"Average nearby price per acre is ${overview.get('averagePricePerAcre', 0):,}, supporting an estimated spread of ${overview.get('estimatedAssignmentSpread', 0):,}.",
            "confidence": confidence_label(overview.get("averagePricePerAcre", 0)),
            "evidence": [
                {"label": "Average Price/Acre", "value": overview.get("averagePricePerAcre", 0)},
                {"label": "Estimated Assignment Spread", "value": overview.get("estimatedAssignmentSpread", 0)},
            ],
        },
        {
            "id": "opportunity",
            "sentence": f"Overall opportunity is {opportunity.get('grade') or 'Needs Data'} with a score of {opportunity.get('score', 0)}.",
            "confidence": confidence_label(opportunity.get("score", 0)),
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