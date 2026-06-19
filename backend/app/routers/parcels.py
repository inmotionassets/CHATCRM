from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..auth import CurrentUser
from . import leads as lead_store

router = APIRouter(prefix="/parcels", tags=["parcels"])


class ParcelIntelligence(BaseModel):
    leadId: str
    address: str = ""
    apn: str = ""
    county: str = ""
    acreage: str = ""
    lotDimensions: str = ""
    legalDescription: str = ""
    zoning: str = ""
    landUse: str = ""
    floodZone: str = ""
    utilityAvailability: str = ""
    opportunityZone: str = ""
    taxBalance: str = ""
    taxDelinquencyStatus: str = ""
    assessedValue: str = ""
    landValue: str = ""
    improvementValue: str = ""
    lastSaleDate: str = ""
    lastSalePrice: str = ""
    ownershipDuration: str = ""
    mortgageEstimate: str = ""
    estimatedEquity: str = ""
    ownershipHistory: str = ""
    mapLayers: list[str] = Field(default_factory=list)
    researchStatus: str = "Needs Research"
    dataSource: str = ""
    notes: str = ""
    updatedAt: str = ""


def get_connection():
    return lead_store.get_postgres_connection() if lead_store.USE_POSTGRES else lead_store.get_sqlite_connection()


def ensure_parcel_table(connection) -> None:
    if lead_store.USE_POSTGRES:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS parcel_intelligence (
                lead_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute(
            """
            ALTER TABLE parcel_intelligence
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            """
        )
        return

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS parcel_intelligence (
            lead_id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def empty_parcel_record(lead_id: str) -> ParcelIntelligence:
    return ParcelIntelligence(leadId=lead_id, updatedAt=current_timestamp())


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_parcel(parcel: ParcelIntelligence, lead_id: str) -> ParcelIntelligence:
    return parcel.model_copy(update={"leadId": lead_id, "updatedAt": current_timestamp()})


def get_saved_parcel(lead_id: str) -> ParcelIntelligence:
    with get_connection() as connection:
        ensure_parcel_table(connection)

        if lead_store.USE_POSTGRES:
            row = connection.execute(
                "SELECT payload FROM parcel_intelligence WHERE lead_id = %s",
                (lead_id,),
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT payload FROM parcel_intelligence WHERE lead_id = ?",
                (lead_id,),
            ).fetchone()

    if not row:
        return empty_parcel_record(lead_id)

    payload = row[0] if lead_store.USE_POSTGRES else row["payload"]
    return ParcelIntelligence.model_validate(lead_store.parse_saved_payload(payload))


def save_parcel(parcel: ParcelIntelligence, lead_id: str) -> ParcelIntelligence:
    clean_parcel = normalize_parcel(parcel, lead_id)

    with get_connection() as connection:
        ensure_parcel_table(connection)

        if lead_store.USE_POSTGRES:
            connection.execute(
                """
                INSERT INTO parcel_intelligence (lead_id, payload, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (lead_id) DO UPDATE SET
                    payload = EXCLUDED.payload,
                    updated_at = now()
                """,
                (lead_id, clean_parcel.model_dump_json()),
            )
        else:
            connection.execute(
                """
                INSERT OR REPLACE INTO parcel_intelligence (lead_id, payload, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (lead_id, clean_parcel.model_dump_json()),
            )

    return clean_parcel


@router.get("/{lead_id}", response_model=ParcelIntelligence)
def get_parcel_intelligence(lead_id: str, current_user: CurrentUser):
    return get_saved_parcel(lead_id)


@router.put("/{lead_id}", response_model=ParcelIntelligence)
def update_parcel_intelligence(lead_id: str, parcel: ParcelIntelligence, current_user: CurrentUser):
    return save_parcel(parcel, lead_id)
