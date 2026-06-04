import json
import sqlite3
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..auth import CurrentUser

router = APIRouter(prefix="/leads", tags=["leads"])

DATABASE_PATH = Path(__file__).resolve().parents[2] / "chatcrm.db"


class Lead(BaseModel):
    id: str
    name: str = ""
    address: str = ""
    parcelNumber: str = ""
    county: str = ""
    bedrooms: str = ""
    bathrooms: str = ""
    sqft: str = ""
    yearBuilt: str = ""
    lotSize: str = ""
    stage: str = "New Lead"
    score: int = 0
    owner: str = ""
    source: str = ""
    phone: str = ""
    phones: list[str] = Field(default_factory=list)
    email: str = ""
    notes: str = ""
    estimatedArv: str = ""
    assessedValue: str = ""
    repairBudget: str = ""
    maxOfferPercent: str = "70"
    assignmentFee: str = ""
    followUpDate: str = ""
    needsReview: bool = False
    contactStatus: str = "needs-review"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL
        )
        """
    )
    return connection


@router.get("", response_model=list[Lead])
def list_leads(current_user: CurrentUser):
    with get_connection() as connection:
        rows = connection.execute("SELECT payload FROM leads ORDER BY rowid DESC").fetchall()
    return [Lead.model_validate(json.loads(row["payload"])) for row in rows]


@router.post("/sync", response_model=list[Lead])
def sync_leads(leads: list[Lead], current_user: CurrentUser):
    with get_connection() as connection:
        connection.execute("DELETE FROM leads")
        connection.executemany(
            "INSERT INTO leads (id, payload) VALUES (?, ?)",
            [(lead.id, lead.model_dump_json()) for lead in leads],
        )
    return leads


@router.post("", response_model=Lead)
def create_lead(lead: Lead, current_user: CurrentUser):
    with get_connection() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO leads (id, payload) VALUES (?, ?)",
            (lead.id, lead.model_dump_json()),
        )
    return lead


@router.put("/{lead_id}", response_model=Lead)
def update_lead(lead_id: str, lead: Lead, current_user: CurrentUser):
    saved_lead = lead.model_copy(update={"id": lead_id})
    with get_connection() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO leads (id, payload) VALUES (?, ?)",
            (saved_lead.id, saved_lead.model_dump_json()),
        )
    return saved_lead


@router.delete("/{lead_id}")
def delete_lead(lead_id: str, current_user: CurrentUser):
    with get_connection() as connection:
        connection.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    return {"deleted": lead_id}
