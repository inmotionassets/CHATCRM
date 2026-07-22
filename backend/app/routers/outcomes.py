import json
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..auth import CurrentUser
from ..outcome_intelligence import build_learning_summary, build_outcome_record, parse_payload
from . import leads as lead_store

router = APIRouter(prefix="/outcomes", tags=["outcomes"])


class OutcomeCreate(BaseModel):
    propertyId: str = ""
    address: str = ""
    apn: str = ""
    county: str = ""
    originalOpportunityScore: int | str = 0
    recommendedAction: str = ""
    recommendedBuyer: str = ""
    confidence: int | str = 0
    recommendationTimestamp: str = ""
    finalBuyer: str = ""
    assignmentFee: float | str = 0
    daysToClose: int | str = 0
    purchasePrice: float | str = 0
    dispositionResult: str = "unknown"
    sellerOutcome: str = ""
    buyerResponseHours: float | str = -1
    outcomeDate: str = ""
    contractReassigned: bool = False
    priceChanged: bool = False
    notes: str = ""


def get_connection():
    return lead_store.get_postgres_connection() if lead_store.USE_POSTGRES else lead_store.get_sqlite_connection()


def ensure_outcome_table(connection) -> None:
    if lead_store.USE_POSTGRES:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS outcome_intelligence_records (
                id TEXT PRIMARY KEY,
                lead_id TEXT NOT NULL,
                property_id TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                apn TEXT NOT NULL DEFAULT '',
                county TEXT NOT NULL DEFAULT '',
                payload TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_lead_id ON outcome_intelligence_records (lead_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_county ON outcome_intelligence_records (county)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_created_at ON outcome_intelligence_records (created_at DESC)")
        return

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS outcome_intelligence_records (
            id TEXT PRIMARY KEY,
            lead_id TEXT NOT NULL,
            property_id TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL DEFAULT '',
            apn TEXT NOT NULL DEFAULT '',
            county TEXT NOT NULL DEFAULT '',
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_lead_id ON outcome_intelligence_records (lead_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_county ON outcome_intelligence_records (county)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_created_at ON outcome_intelligence_records (created_at DESC)")


def require_outcome_access(current_user: CurrentUser) -> None:
    if current_user.role not in {"Admin", "Disposition"}:
        raise HTTPException(status_code=403, detail="Outcome Intelligence is only available to Admin and Disposition users.")


def outcome_from_row(row) -> dict:
    payload = row[6] if lead_store.USE_POSTGRES else row["payload"]
    return parse_payload(payload)


def save_outcome_record(record: dict) -> dict:
    payload = json.dumps(record, separators=(",", ":"), sort_keys=True)
    property_payload = record.get("property") or {}

    with get_connection() as connection:
        ensure_outcome_table(connection)

        if lead_store.USE_POSTGRES:
            connection.execute(
                """
                INSERT INTO outcome_intelligence_records (
                    id, lead_id, property_id, address, apn, county, payload, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    lead_id = EXCLUDED.lead_id,
                    property_id = EXCLUDED.property_id,
                    address = EXCLUDED.address,
                    apn = EXCLUDED.apn,
                    county = EXCLUDED.county,
                    payload = EXCLUDED.payload,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    record["id"],
                    record["leadId"],
                    property_payload.get("propertyId") or "",
                    property_payload.get("address") or "",
                    property_payload.get("apn") or "",
                    property_payload.get("county") or "",
                    payload,
                    record.get("createdAt") or lead_store.iso_timestamp(),
                    record.get("updatedAt") or lead_store.iso_timestamp(),
                ),
            )
        else:
            connection.execute(
                """
                INSERT OR REPLACE INTO outcome_intelligence_records (
                    id, lead_id, property_id, address, apn, county, payload, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["id"],
                    record["leadId"],
                    property_payload.get("propertyId") or "",
                    property_payload.get("address") or "",
                    property_payload.get("apn") or "",
                    property_payload.get("county") or "",
                    payload,
                    record.get("createdAt") or lead_store.iso_timestamp(),
                    record.get("updatedAt") or lead_store.iso_timestamp(),
                ),
            )

    return record


def list_outcome_records(lead_id: str = "", limit: int = 200) -> list[dict]:
    clean_limit = min(max(limit, 1), 500)

    with get_connection() as connection:
        ensure_outcome_table(connection)

        if lead_store.USE_POSTGRES:
            if lead_id:
                rows = connection.execute(
                    """
                    SELECT id, lead_id, property_id, address, apn, county, payload, created_at, updated_at
                    FROM outcome_intelligence_records
                    WHERE lead_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (lead_id, clean_limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id, lead_id, property_id, address, apn, county, payload, created_at, updated_at
                    FROM outcome_intelligence_records
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (clean_limit,),
                ).fetchall()
        else:
            if lead_id:
                rows = connection.execute(
                    """
                    SELECT id, lead_id, property_id, address, apn, county, payload, created_at, updated_at
                    FROM outcome_intelligence_records
                    WHERE lead_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (lead_id, clean_limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id, lead_id, property_id, address, apn, county, payload, created_at, updated_at
                    FROM outcome_intelligence_records
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (clean_limit,),
                ).fetchall()

    return [outcome_from_row(row) for row in rows]


def build_learning_summary_for_lead(lead_id: str) -> dict:
    return build_learning_summary(list_outcome_records(lead_id=lead_id))


@router.post("/lead/{lead_id}")
def create_outcome_record(lead_id: str, outcome: OutcomeCreate, current_user: CurrentUser):
    require_outcome_access(current_user)
    lead = lead_store.get_saved_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    payload = outcome.model_dump()
    payload["leadId"] = lead_id
    record = build_outcome_record(
        record_id=f"outcome-{uuid4().hex}",
        lead_payload=lead.model_dump(),
        payload=payload,
    )
    return save_outcome_record(record)


@router.get("/lead/{lead_id}")
def get_lead_outcomes(lead_id: str, current_user: CurrentUser, limit: int = Query(50, ge=1, le=200)):
    require_outcome_access(current_user)
    return {
        "leadId": lead_id,
        "records": list_outcome_records(lead_id=lead_id, limit=limit),
        "learningSummary": build_learning_summary_for_lead(lead_id),
    }


@router.get("/summary")
def get_outcome_summary(current_user: CurrentUser, limit: int = Query(200, ge=1, le=500)):
    require_outcome_access(current_user)
    records = list_outcome_records(limit=limit)
    return build_learning_summary(records)
