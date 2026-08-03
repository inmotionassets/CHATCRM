from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..auth import CurrentUser
from ..contact_intelligence import ContactIntelligenceService, ContactIntelligenceSnapshot
from . import leads as lead_store


router = APIRouter(prefix="/contact-intelligence", tags=["contact-intelligence"])


class ContactFeedbackRequest(BaseModel):
    leadId: str
    feedbackType: str
    notes: str = ""


class ContactBatchRequest(BaseModel):
    leadIds: list[str] = Field(default_factory=list)


def get_connection():
    return lead_store.get_postgres_connection() if lead_store.USE_POSTGRES else lead_store.get_sqlite_connection()


def ensure_contact_intelligence_table(connection) -> None:
    if lead_store.USE_POSTGRES:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_intelligence_records (
                lead_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute(
            """
            ALTER TABLE contact_intelligence_records
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            """
        )
        return

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS contact_intelligence_records (
            lead_id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def get_saved_snapshot(lead_id: str) -> ContactIntelligenceSnapshot | None:
    with get_connection() as connection:
        ensure_contact_intelligence_table(connection)
        if lead_store.USE_POSTGRES:
            row = connection.execute(
                "SELECT payload FROM contact_intelligence_records WHERE lead_id = %s",
                (lead_id,),
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT payload FROM contact_intelligence_records WHERE lead_id = ?",
                (lead_id,),
            ).fetchone()

    if not row:
        return None

    payload = row[0] if lead_store.USE_POSTGRES else row["payload"]
    return ContactIntelligenceSnapshot.model_validate(lead_store.parse_saved_payload(payload))


def save_snapshot(snapshot: ContactIntelligenceSnapshot) -> ContactIntelligenceSnapshot:
    with get_connection() as connection:
        ensure_contact_intelligence_table(connection)
        if lead_store.USE_POSTGRES:
            connection.execute(
                """
                INSERT INTO contact_intelligence_records (lead_id, payload, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (lead_id) DO UPDATE SET
                    payload = EXCLUDED.payload,
                    updated_at = now()
                """,
                (snapshot.leadId, snapshot.model_dump_json()),
            )
        else:
            connection.execute(
                """
                INSERT OR REPLACE INTO contact_intelligence_records (lead_id, payload, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (snapshot.leadId, snapshot.model_dump_json()),
            )

    return snapshot


def require_admin(current_user: CurrentUser) -> None:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")


def require_lead(lead_id: str):
    lead = lead_store.get_saved_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.get("/leads/{lead_id}", response_model=ContactIntelligenceSnapshot)
def get_lead_contact_intelligence(lead_id: str, current_user: CurrentUser):
    saved_snapshot = get_saved_snapshot(lead_id)
    if saved_snapshot:
        return saved_snapshot

    lead = require_lead(lead_id)
    snapshot = ContactIntelligenceService().build_snapshot(lead, enrich=False)
    return save_snapshot(snapshot)


@router.post("/leads/{lead_id}/enrich", response_model=ContactIntelligenceSnapshot)
def enrich_lead_contact_intelligence(lead_id: str, current_user: CurrentUser):
    lead = require_lead(lead_id)
    snapshot = ContactIntelligenceService().build_snapshot(lead, enrich=True)
    return save_snapshot(snapshot)


@router.post("/contacts/{contact_id}/feedback", response_model=ContactIntelligenceSnapshot)
def record_contact_feedback(contact_id: str, request: ContactFeedbackRequest, current_user: CurrentUser):
    lead = require_lead(request.leadId)
    saved_snapshot = get_saved_snapshot(request.leadId)
    if not saved_snapshot:
        saved_snapshot = ContactIntelligenceService().build_snapshot(lead, enrich=False)

    snapshot = ContactIntelligenceService().apply_feedback(
        saved_snapshot,
        contact_id,
        request.feedbackType,
        request.notes,
    )
    return save_snapshot(snapshot)


@router.post("/enrich-selected")
def enrich_selected_contacts(request: ContactBatchRequest, current_user: CurrentUser):
    require_admin(current_user)
    lead_ids = [lead_id for lead_id in dict.fromkeys(request.leadIds) if lead_id]
    if len(lead_ids) > 50:
        raise HTTPException(status_code=400, detail="Run at most 50 leads at a time")

    results: list[ContactIntelligenceSnapshot] = []
    for lead_id in lead_ids:
        lead = lead_store.get_saved_lead(lead_id)
        if not lead:
            continue
        results.append(save_snapshot(ContactIntelligenceService().build_snapshot(lead, enrich=True)))

    return {"updatedCount": len(results), "results": results}
