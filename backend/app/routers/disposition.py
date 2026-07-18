from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from ..auth import CurrentUser
from ..disposition_engine import build_disposition_workspace, build_subject_property
from ..disposition_providers import (
    DEFAULT_SOURCE_NAME,
    get_provider,
    import_csv_transactions as import_disposition_csv_transactions,
)
from . import leads as lead_store

router = APIRouter(prefix="/disposition", tags=["disposition"])


class Coordinates(BaseModel):
    lat: float
    lng: float


class SubjectProperty(BaseModel):
    leadId: str
    address: str
    coordinates: Coordinates
    apn: str = ""
    acreage: float = 0
    propertyType: str = ""
    county: str = ""
    zoning: str = ""
    floodZone: str = ""
    utilities: str = ""
    sellerAskingPrice: int = 0
    contractPrice: int = 0
    targetAssignmentPrice: int = 0
    projectedSpread: int = 0


class DealReadinessItem(BaseModel):
    label: str
    complete: bool = False


class BuyerSaleTransaction(BaseModel):
    id: str
    source: str = "mock"
    sourceName: str = "Mock buyer activity"
    sourceRecordId: str = ""
    parcelId: str = ""
    address: str
    apn: str = ""
    saleDate: str = ""
    salePrice: int = 0
    acreage: float = 0
    propertyType: str = ""
    cashSale: bool = False
    buyerName: str = ""
    sellerName: str = ""
    buyerMailingAddress: str = ""
    buyerType: str = "unknown"
    deedType: str = ""
    financingType: str = ""
    zoning: str = ""
    coordinates: Coordinates
    distanceMiles: float = 0
    pricePerAcre: int = 0
    markerType: str = "standard"
    relationshipTier: str = "C"
    confidence: int = 0
    dataQuality: str = "estimated"
    verified: bool = False
    estimated: bool = False
    sourceLastRefreshed: str = ""
    rawSourceMetadata: dict[str, Any] = Field(default_factory=dict)


class BuyerMatch(BaseModel):
    buyerName: str
    normalizedBuyerName: str
    buyerType: str = "unknown"
    buyerMailingAddress: str = ""
    score: int
    scoreBreakdown: dict[str, int] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    totalVerifiedPurchases: int = 0
    nearbyPurchases: int = 0
    latestPurchaseDate: str = ""
    averagePurchasePrice: int = 0
    averageAcreage: float = 0
    averagePricePerAcre: int = 0
    transactions: list[BuyerSaleTransaction] = Field(default_factory=list)


class DispositionFilters(BaseModel):
    radiusMiles: float = 5
    soldWithinDays: int = 365
    vacantLandOnly: bool = False
    cashOnly: bool = False
    buyerTypes: list[str] = Field(default_factory=list)


class DispositionSource(BaseModel):
    provider: str = "mock"
    sourceName: str = "Mock buyer activity"
    lastRefreshAt: str = ""
    errors: list[str] = Field(default_factory=list)


class DispositionOverview(BaseModel):
    verifiedNearbyBuyers: int = 0
    highMatchBuyers: int = 0
    activeBuilders: int = 0
    recentSimilarSales: int = 0
    averagePricePerAcre: int = 0
    suggestedBuyerAskingPrice: int = 0
    estimatedAssignmentSpread: int = 0


class DispositionWorkspace(BaseModel):
    subject: SubjectProperty
    filters: DispositionFilters
    readiness: list[DealReadinessItem]
    transactions: list[BuyerSaleTransaction]
    buyerMatches: list[BuyerMatch]
    buyerFootprints: dict[str, Any] = Field(default_factory=dict)
    dealIntelligenceSummary: list[dict[str, Any]] = Field(default_factory=list)
    source: DispositionSource
    overview: DispositionOverview


class TransactionImportResult(BaseModel):
    importedCount: int = 0
    updatedCount: int = 0
    duplicateCount: int = 0
    totalRows: int = 0
    warnings: list[str] = Field(default_factory=list)
    sourceName: str = DEFAULT_SOURCE_NAME
    lastRefreshAt: str = ""


class DispositionRefreshResult(BaseModel):
    provider: str = "mock"
    sourceName: str = ""
    lastRefreshAt: str = ""
    errors: list[str] = Field(default_factory=list)
    transactionCount: int = 0


def require_disposition_access(current_user: CurrentUser) -> None:
    if current_user.role not in {"Admin", "Disposition"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Disposition Intelligence is only available to Admin and Disposition users.",
        )


@router.get("/workspace/{lead_id}", response_model=DispositionWorkspace)
def get_disposition_workspace(
    lead_id: str,
    current_user: CurrentUser,
    radius_miles: float = Query(5, ge=1, le=25, alias="radiusMiles"),
    sold_within_days: int = Query(365, ge=30, le=365, alias="soldWithinDays"),
    vacant_land_only: bool = Query(False, alias="vacantLandOnly"),
    cash_only: bool = Query(False, alias="cashOnly"),
    buyer_type: list[str] = Query(default_factory=list, alias="buyerType"),
    provider_name: str = Query("", alias="provider"),
) -> dict[str, Any]:
    require_disposition_access(current_user)

    lead = lead_store.get_saved_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    lead_payload = lead.model_dump()
    filter_payload = build_filter_payload(radius_miles, sold_within_days, vacant_land_only, cash_only, buyer_type)
    provider_result = load_provider_result(lead_payload, filter_payload, provider_name=provider_name)

    return build_disposition_workspace(
        lead_payload,
        radius_miles=radius_miles,
        sold_within_days=sold_within_days,
        vacant_land_only=vacant_land_only,
        cash_only=cash_only,
        buyer_types=buyer_type,
        transactions=provider_result.get("transactions") or [],
        provider_result=provider_result,
    )


@router.post("/workspace/{lead_id}/refresh", response_model=DispositionRefreshResult)
def refresh_disposition_workspace(
    lead_id: str,
    current_user: CurrentUser,
    radius_miles: float = Query(5, ge=1, le=25, alias="radiusMiles"),
    sold_within_days: int = Query(365, ge=30, le=365, alias="soldWithinDays"),
    vacant_land_only: bool = Query(False, alias="vacantLandOnly"),
    cash_only: bool = Query(False, alias="cashOnly"),
    buyer_type: list[str] = Query(default_factory=list, alias="buyerType"),
    provider_name: str = Query("", alias="provider"),
) -> dict[str, Any]:
    require_disposition_access(current_user)

    lead = lead_store.get_saved_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    subject = build_subject_property(lead.model_dump())
    filter_payload = build_filter_payload(radius_miles, sold_within_days, vacant_land_only, cash_only, buyer_type)
    provider_result = get_provider(provider_name or None).refresh(subject, filter_payload)
    return {
        "provider": provider_result.get("provider") or "mock",
        "sourceName": provider_result.get("sourceName") or "",
        "lastRefreshAt": provider_result.get("lastRefreshAt") or "",
        "errors": provider_result.get("errors") or [],
        "transactionCount": len(provider_result.get("transactions") or []),
    }


@router.post("/transactions/import-csv", response_model=TransactionImportResult)
async def import_disposition_transactions(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    source_name: str = Form(DEFAULT_SOURCE_NAME),
) -> dict[str, Any]:
    require_disposition_access(current_user)

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload a CSV transaction file.")

    raw_content = await file.read()
    try:
        csv_text = raw_content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV must be saved as UTF-8.") from exc

    return import_disposition_csv_transactions(csv_text, source_name=source_name or DEFAULT_SOURCE_NAME)


def build_filter_payload(
    radius_miles: float,
    sold_within_days: int,
    vacant_land_only: bool,
    cash_only: bool,
    buyer_type: list[str],
) -> dict[str, Any]:
    return {
        "radiusMiles": radius_miles,
        "soldWithinDays": sold_within_days,
        "vacantLandOnly": vacant_land_only,
        "cashOnly": cash_only,
        "buyerTypes": buyer_type,
    }


def load_provider_result(lead_payload: dict[str, Any], filters: dict[str, Any], provider_name: str = "") -> dict[str, Any]:
    subject = build_subject_property(lead_payload)
    provider = get_provider(provider_name or None)
    provider_result = provider.search(subject, filters)
    if provider_result.get("transactions") or provider.name == "mock":
        return provider_result

    fallback_result = get_provider("mock").search(subject, filters)
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