import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..auth import CurrentUser

router = APIRouter(prefix="/leads", tags=["leads"])

def normalize_database_url(value: str) -> str:
    cleaned = (value or "").strip().strip("\"'")

    if cleaned.lower().startswith("database_url="):
        cleaned = cleaned.split("=", 1)[1].strip().strip("\"'")

    return cleaned


RAW_DATABASE_URL = os.getenv("DATABASE_URL", "")
DATABASE_URL = normalize_database_url(RAW_DATABASE_URL)
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", Path(__file__).resolve().parents[2] / "chatcrm.db"))
USE_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))


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


def get_sqlite_connection() -> sqlite3.Connection:
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


def postgres_connection_url() -> str:
    if not USE_POSTGRES:
        return DATABASE_URL

    parsed = urlsplit(DATABASE_URL)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))

    if parsed.hostname not in {"localhost", "127.0.0.1"} and "sslmode" not in query:
        query["sslmode"] = "require"

    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


def database_url_scheme() -> str:
    if not DATABASE_URL:
        return "missing"

    parsed = urlsplit(DATABASE_URL)
    return parsed.scheme or "unknown"


@contextmanager
def get_postgres_connection() -> Iterator[object]:
    import psycopg

    with psycopg.connect(postgres_connection_url()) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        yield connection


def list_saved_leads() -> list[Lead]:
    if USE_POSTGRES:
        with get_postgres_connection() as connection:
            rows = connection.execute("SELECT payload FROM leads ORDER BY created_at DESC, id DESC").fetchall()
        return [Lead.model_validate(json.loads(row[0])) for row in rows]

    with get_sqlite_connection() as connection:
        rows = connection.execute("SELECT payload FROM leads ORDER BY rowid DESC").fetchall()
    return [Lead.model_validate(json.loads(row["payload"])) for row in rows]


def replace_saved_leads(leads: list[Lead]) -> None:
    if USE_POSTGRES:
        with get_postgres_connection() as connection:
            connection.execute("DELETE FROM leads")
            with connection.cursor() as cursor:
                cursor.executemany(
                    "INSERT INTO leads (id, payload) VALUES (%s, %s)",
                    [(lead.id, lead.model_dump_json()) for lead in leads],
                )
        return

    with get_sqlite_connection() as connection:
        connection.execute("DELETE FROM leads")
        connection.executemany(
            "INSERT INTO leads (id, payload) VALUES (?, ?)",
            [(lead.id, lead.model_dump_json()) for lead in leads],
        )


def save_lead(lead: Lead) -> None:
    if USE_POSTGRES:
        with get_postgres_connection() as connection:
            connection.execute(
                """
                INSERT INTO leads (id, payload)
                VALUES (%s, %s)
                ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload
                """,
                (lead.id, lead.model_dump_json()),
            )
        return

    with get_sqlite_connection() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO leads (id, payload) VALUES (?, ?)",
            (lead.id, lead.model_dump_json()),
        )


def remove_lead(lead_id: str) -> None:
    if USE_POSTGRES:
        with get_postgres_connection() as connection:
            connection.execute("DELETE FROM leads WHERE id = %s", (lead_id,))
        return

    with get_sqlite_connection() as connection:
        connection.execute("DELETE FROM leads WHERE id = ?", (lead_id,))


@router.get("", response_model=list[Lead])
def list_leads(current_user: CurrentUser):
    return list_saved_leads()


@router.post("/sync", response_model=list[Lead])
def sync_leads(leads: list[Lead], current_user: CurrentUser):
    if not leads:
        raise HTTPException(status_code=400, detail="Refusing to sync an empty lead list")

    replace_saved_leads(leads)
    return leads


@router.post("", response_model=Lead)
def create_lead(lead: Lead, current_user: CurrentUser):
    save_lead(lead)
    return lead


@router.put("/{lead_id}", response_model=Lead)
def update_lead(lead_id: str, lead: Lead, current_user: CurrentUser):
    saved_lead = lead.model_copy(update={"id": lead_id})
    save_lead(saved_lead)
    return saved_lead


@router.delete("/{lead_id}")
def delete_lead(lead_id: str, current_user: CurrentUser):
    remove_lead(lead_id)
    return {"deleted": lead_id}
