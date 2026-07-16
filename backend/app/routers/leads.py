import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

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
    lastContactedUserId: str = ""
    lastContactedBy: str = ""
    lastContactedAt: str = ""
    lastActivityAction: str = ""
    lockedByUserId: str = ""
    lockedByUserName: str = ""
    lockedUntil: str = ""


class LeadActivity(BaseModel):
    id: str
    leadId: str
    userId: str
    userNameSnapshot: str
    actionType: str
    callOutcome: str = ""
    notes: str = ""
    createdAt: str
    followUpDate: str = ""
    leadAddress: str = ""


class LeadActivityCreate(BaseModel):
    actionType: str
    callOutcome: str = ""
    notes: str = ""
    followUpDate: str = ""
    phoneNumber: str = ""


class LeadLock(BaseModel):
    leadId: str
    lockedByUserId: str = ""
    lockedByUserName: str = ""
    lockedUntil: str = ""
    isActive: bool = False


class DailyCallCount(BaseModel):
    userId: str
    userName: str
    count: int


class LeadResetResult(BaseModel):
    updatedLeads: int
    activitiesDeleted: int
    locksCleared: int


CONTACT_ACTIVITY_TYPES = {
    "called",
    "call_started",
    "status_changed",
    "follow_up_set",
    "hot_lead_marked",
    "not_interested",
    "voicemail",
    "wrong_number",
}

CALL_COUNT_ACTIVITY_TYPES = {"called", "call_started", "voicemail", "not_interested", "wrong_number"}


def get_sqlite_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    ensure_lead_tables(connection)
    return connection


def ensure_lead_tables(connection) -> None:
    if USE_POSTGRES:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute(
            """
            ALTER TABLE leads
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS lead_activities (
                id TEXT PRIMARY KEY,
                lead_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                user_name_snapshot TEXT NOT NULL,
                action_type TEXT NOT NULL,
                call_outcome TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                follow_up_date TEXT NOT NULL DEFAULT '',
                lead_address TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_lead_activities_lead_id ON lead_activities (lead_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_lead_activities_created_at ON lead_activities (created_at DESC)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS lead_locks (
                lead_id TEXT PRIMARY KEY,
                locked_by_user_id TEXT NOT NULL,
                locked_by_user_name TEXT NOT NULL,
                locked_until TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        return

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS lead_activities (
            id TEXT PRIMARY KEY,
            lead_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            user_name_snapshot TEXT NOT NULL,
            action_type TEXT NOT NULL,
            call_outcome TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            follow_up_date TEXT NOT NULL DEFAULT '',
            lead_address TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_lead_activities_lead_id ON lead_activities (lead_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_lead_activities_created_at ON lead_activities (created_at DESC)")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS lead_locks (
            lead_id TEXT PRIMARY KEY,
            locked_by_user_id TEXT NOT NULL,
            locked_by_user_name TEXT NOT NULL,
            locked_until TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )


def postgres_connection_url() -> str:
    if not USE_POSTGRES:
        return DATABASE_URL

    parsed = urlsplit(DATABASE_URL)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.pop("pgbouncer", None)

    if parsed.hostname not in {"localhost", "127.0.0.1"} and "sslmode" not in query:
        query["sslmode"] = "require"

    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


def database_url_scheme() -> str:
    if not DATABASE_URL:
        return "missing"

    parsed = urlsplit(DATABASE_URL)
    return parsed.scheme or "unknown"


def database_url_summary() -> dict[str, object]:
    if not DATABASE_URL:
        return {
            "scheme": "missing",
            "host": "",
            "port": None,
            "username": "",
            "path": "",
            "query_keys": [],
        }

    parsed = urlsplit(DATABASE_URL)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))

    return {
        "scheme": parsed.scheme or "unknown",
        "host": parsed.hostname or "",
        "port": parsed.port,
        "username": parsed.username or "",
        "path": parsed.path,
        "query_keys": sorted(query.keys()),
    }


@contextmanager
def get_postgres_connection() -> Iterator[object]:
    import psycopg

    with psycopg.connect(postgres_connection_url(), prepare_threshold=None) as connection:
        ensure_lead_tables(connection)
        yield connection


def list_saved_leads() -> list[Lead]:
    if USE_POSTGRES:
        with get_postgres_connection() as connection:
            rows = connection.execute("SELECT payload FROM leads ORDER BY id DESC").fetchall()
        return [Lead.model_validate(parse_saved_payload(row[0])) for row in rows]

    with get_sqlite_connection() as connection:
        rows = connection.execute("SELECT payload FROM leads ORDER BY rowid DESC").fetchall()
    return [Lead.model_validate(parse_saved_payload(row["payload"])) for row in rows]


def parse_saved_payload(payload: object) -> dict:
    if isinstance(payload, dict):
        return payload

    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode("utf-8")

    if isinstance(payload, str):
        return json.loads(payload)

    return json.loads(str(payload))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_timestamp(value: object | None = None) -> str:
    if value is None:
        return utc_now().isoformat()

    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat() if value.tzinfo else value.replace(tzinfo=timezone.utc).isoformat()

    return str(value)


def parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def user_display_name(current_user: CurrentUser) -> str:
    return (current_user.name or current_user.username).strip()


def get_saved_lead(lead_id: str) -> Lead | None:
    if USE_POSTGRES:
        with get_postgres_connection() as connection:
            row = connection.execute("SELECT payload FROM leads WHERE id = %s", (lead_id,)).fetchone()
        return Lead.model_validate(parse_saved_payload(row[0])) if row else None

    with get_sqlite_connection() as connection:
        row = connection.execute("SELECT payload FROM leads WHERE id = ?", (lead_id,)).fetchone()
    return Lead.model_validate(parse_saved_payload(row["payload"])) if row else None


def update_lead_payload(lead_id: str, updates: dict[str, object]) -> Lead | None:
    lead = get_saved_lead(lead_id)
    if not lead:
        return None

    updated_lead = lead.model_copy(update=updates)
    save_lead(updated_lead)
    return updated_lead


def activity_from_row(row) -> LeadActivity:
    return LeadActivity(
        id=str(row[0]),
        leadId=str(row[1]),
        userId=str(row[2]),
        userNameSnapshot=str(row[3]),
        actionType=str(row[4]),
        callOutcome=str(row[5] or ""),
        notes=str(row[6] or ""),
        followUpDate=str(row[7] or ""),
        leadAddress=str(row[8] or ""),
        createdAt=iso_timestamp(row[9]),
    )


def lock_from_row(row) -> LeadLock:
    if not row:
        return LeadLock(leadId="")

    locked_until = iso_timestamp(row[3])
    expires_at = parse_timestamp(locked_until)
    is_active = bool(expires_at and expires_at > utc_now())
    return LeadLock(
        leadId=str(row[0]),
        lockedByUserId=str(row[1]),
        lockedByUserName=str(row[2]),
        lockedUntil=locked_until,
        isActive=is_active,
    )


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
            connection.execute("DELETE FROM lead_activities WHERE lead_id = %s", (lead_id,))
            connection.execute("DELETE FROM lead_locks WHERE lead_id = %s", (lead_id,))
            connection.execute("DELETE FROM leads WHERE id = %s", (lead_id,))
        return

    with get_sqlite_connection() as connection:
        connection.execute("DELETE FROM lead_activities WHERE lead_id = ?", (lead_id,))
        connection.execute("DELETE FROM lead_locks WHERE lead_id = ?", (lead_id,))
        connection.execute("DELETE FROM leads WHERE id = ?", (lead_id,))


def reset_notes_and_followups() -> LeadResetResult:
    leads = list_saved_leads()
    reset_leads: list[Lead] = []

    for lead in leads:
        updates: dict[str, object] = {
            "notes": "",
            "followUpDate": "",
            "lastContactedUserId": "",
            "lastContactedBy": "",
            "lastContactedAt": "",
            "lastActivityAction": "",
            "lockedByUserId": "",
            "lockedByUserName": "",
            "lockedUntil": "",
        }

        if lead.stage == "Follow Up":
            updates["stage"] = "New Lead"
        if lead.contactStatus in {"follow-up", "left-voicemail", "no-answer"}:
            updates["contactStatus"] = "needs-review"
            updates["needsReview"] = True

        reset_leads.append(lead.model_copy(update=updates))

    activities_deleted = 0
    locks_cleared = 0

    if USE_POSTGRES:
        with get_postgres_connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    "UPDATE leads SET payload = %s WHERE id = %s",
                    [(lead.model_dump_json(), lead.id) for lead in reset_leads],
                )
            activities_cursor = connection.execute("DELETE FROM lead_activities")
            locks_cursor = connection.execute("DELETE FROM lead_locks")
            activities_deleted = max(activities_cursor.rowcount or 0, 0)
            locks_cleared = max(locks_cursor.rowcount or 0, 0)
    else:
        with get_sqlite_connection() as connection:
            connection.executemany(
                "UPDATE leads SET payload = ? WHERE id = ?",
                [(lead.model_dump_json(), lead.id) for lead in reset_leads],
            )
            activities_cursor = connection.execute("DELETE FROM lead_activities")
            locks_cursor = connection.execute("DELETE FROM lead_locks")
            activities_deleted = max(activities_cursor.rowcount or 0, 0)
            locks_cleared = max(locks_cursor.rowcount or 0, 0)

    return LeadResetResult(
        updatedLeads=len(reset_leads),
        activitiesDeleted=activities_deleted,
        locksCleared=locks_cleared,
    )


def create_lead_activity(lead_id: str, activity: LeadActivityCreate, current_user: CurrentUser) -> LeadActivity:
    lead = get_saved_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    created_at = iso_timestamp()
    clean_action = activity.actionType.strip() or "note_added"
    clean_notes = activity.notes.strip()
    if activity.phoneNumber.strip() and activity.phoneNumber.strip() not in clean_notes:
        clean_notes = f"{clean_notes} Phone: {activity.phoneNumber.strip()}".strip()

    saved_activity = LeadActivity(
        id=f"activity-{uuid4().hex}",
        leadId=lead_id,
        userId=current_user.username,
        userNameSnapshot=user_display_name(current_user),
        actionType=clean_action,
        callOutcome=activity.callOutcome.strip(),
        notes=clean_notes,
        followUpDate=activity.followUpDate.strip(),
        leadAddress=lead.address,
        createdAt=created_at,
    )

    if USE_POSTGRES:
        with get_postgres_connection() as connection:
            connection.execute(
                """
                INSERT INTO lead_activities (
                    id, lead_id, user_id, user_name_snapshot, action_type, call_outcome,
                    notes, follow_up_date, lead_address, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    saved_activity.id,
                    saved_activity.leadId,
                    saved_activity.userId,
                    saved_activity.userNameSnapshot,
                    saved_activity.actionType,
                    saved_activity.callOutcome,
                    saved_activity.notes,
                    saved_activity.followUpDate,
                    saved_activity.leadAddress,
                    saved_activity.createdAt,
                ),
            )
    else:
        with get_sqlite_connection() as connection:
            connection.execute(
                """
                INSERT INTO lead_activities (
                    id, lead_id, user_id, user_name_snapshot, action_type, call_outcome,
                    notes, follow_up_date, lead_address, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    saved_activity.id,
                    saved_activity.leadId,
                    saved_activity.userId,
                    saved_activity.userNameSnapshot,
                    saved_activity.actionType,
                    saved_activity.callOutcome,
                    saved_activity.notes,
                    saved_activity.followUpDate,
                    saved_activity.leadAddress,
                    saved_activity.createdAt,
                ),
            )

    lead_updates: dict[str, object] = {"lastActivityAction": saved_activity.actionType}
    if saved_activity.actionType in CONTACT_ACTIVITY_TYPES:
        lead_updates.update(
            {
                "lastContactedUserId": saved_activity.userId,
                "lastContactedBy": saved_activity.userNameSnapshot,
                "lastContactedAt": saved_activity.createdAt,
            }
        )
    if saved_activity.followUpDate:
        lead_updates["followUpDate"] = saved_activity.followUpDate

    update_lead_payload(lead_id, lead_updates)
    return saved_activity


def list_lead_activities(lead_id: str, limit: int = 80) -> list[LeadActivity]:
    clean_limit = min(max(limit, 1), 200)
    columns = """
        id, lead_id, user_id, user_name_snapshot, action_type, call_outcome,
        notes, follow_up_date, lead_address, created_at
    """

    if USE_POSTGRES:
        with get_postgres_connection() as connection:
            rows = connection.execute(
                f"SELECT {columns} FROM lead_activities WHERE lead_id = %s ORDER BY created_at DESC LIMIT %s",
                (lead_id, clean_limit),
            ).fetchall()
    else:
        with get_sqlite_connection() as connection:
            rows = connection.execute(
                f"SELECT {columns} FROM lead_activities WHERE lead_id = ? ORDER BY created_at DESC LIMIT ?",
                (lead_id, clean_limit),
            ).fetchall()

    return [activity_from_row(row) for row in rows]


def list_recent_activities(limit: int, current_user: CurrentUser) -> list[LeadActivity]:
    clean_limit = min(max(limit, 1), 200)
    columns = """
        id, lead_id, user_id, user_name_snapshot, action_type, call_outcome,
        notes, follow_up_date, lead_address, created_at
    """

    if USE_POSTGRES:
        with get_postgres_connection() as connection:
            if current_user.role == "Admin":
                rows = connection.execute(
                    f"SELECT {columns} FROM lead_activities ORDER BY created_at DESC LIMIT %s",
                    (clean_limit,),
                ).fetchall()
            else:
                rows = connection.execute(
                    f"SELECT {columns} FROM lead_activities WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
                    (current_user.username, clean_limit),
                ).fetchall()
    else:
        with get_sqlite_connection() as connection:
            if current_user.role == "Admin":
                rows = connection.execute(
                    f"SELECT {columns} FROM lead_activities ORDER BY created_at DESC LIMIT ?",
                    (clean_limit,),
                ).fetchall()
            else:
                rows = connection.execute(
                    f"SELECT {columns} FROM lead_activities WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                    (current_user.username, clean_limit),
                ).fetchall()

    return [activity_from_row(row) for row in rows]


def list_daily_call_counts(current_user: CurrentUser) -> list[DailyCallCount]:
    action_types = tuple(sorted(CALL_COUNT_ACTIVITY_TYPES))
    placeholders = ", ".join(["%s" if USE_POSTGRES else "?"] * len(action_types))

    if USE_POSTGRES:
        params: tuple[object, ...] = action_types
        user_filter = ""
        if current_user.role != "Admin":
            user_filter = "AND user_id = %s"
            params = (*params, current_user.username)

        with get_postgres_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT user_id, user_name_snapshot, COUNT(*)
                FROM lead_activities
                WHERE action_type IN ({placeholders})
                  AND created_at >= CURRENT_DATE
                  {user_filter}
                GROUP BY user_id, user_name_snapshot
                ORDER BY COUNT(*) DESC
                """,
                params,
            ).fetchall()
    else:
        params = action_types
        user_filter = ""
        if current_user.role != "Admin":
            user_filter = "AND user_id = ?"
            params = (*params, current_user.username)

        with get_sqlite_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT user_id, user_name_snapshot, COUNT(*)
                FROM lead_activities
                WHERE action_type IN ({placeholders})
                  AND date(created_at) = date('now')
                  {user_filter}
                GROUP BY user_id, user_name_snapshot
                ORDER BY COUNT(*) DESC
                """,
                params,
            ).fetchall()

    return [DailyCallCount(userId=str(row[0]), userName=str(row[1]), count=int(row[2])) for row in rows]


def get_active_lead_lock(lead_id: str) -> LeadLock:
    columns = "lead_id, locked_by_user_id, locked_by_user_name, locked_until"
    if USE_POSTGRES:
        with get_postgres_connection() as connection:
            row = connection.execute(f"SELECT {columns} FROM lead_locks WHERE lead_id = %s", (lead_id,)).fetchone()
    else:
        with get_sqlite_connection() as connection:
            row = connection.execute(f"SELECT {columns} FROM lead_locks WHERE lead_id = ?", (lead_id,)).fetchone()

    if not row:
        return LeadLock(leadId=lead_id)

    lock = lock_from_row(row)
    return lock.model_copy(update={"leadId": lead_id}) if lock.leadId == "" else lock


def lock_lead_for_user(lead_id: str, current_user: CurrentUser) -> LeadLock:
    if not get_saved_lead(lead_id):
        raise HTTPException(status_code=404, detail="Lead not found")

    existing_lock = get_active_lead_lock(lead_id)
    if (
        existing_lock.isActive
        and existing_lock.lockedByUserId
        and existing_lock.lockedByUserId != current_user.username
        and current_user.role != "Admin"
    ):
        return existing_lock

    lock_until = iso_timestamp(utc_now() + timedelta(minutes=10))
    user_name = user_display_name(current_user)

    if USE_POSTGRES:
        with get_postgres_connection() as connection:
            connection.execute(
                """
                INSERT INTO lead_locks (lead_id, locked_by_user_id, locked_by_user_name, locked_until, updated_at)
                VALUES (%s, %s, %s, %s, now())
                ON CONFLICT (lead_id) DO UPDATE SET
                    locked_by_user_id = EXCLUDED.locked_by_user_id,
                    locked_by_user_name = EXCLUDED.locked_by_user_name,
                    locked_until = EXCLUDED.locked_until,
                    updated_at = now()
                """,
                (lead_id, current_user.username, user_name, lock_until),
            )
    else:
        with get_sqlite_connection() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO lead_locks (
                    lead_id, locked_by_user_id, locked_by_user_name, locked_until, updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (lead_id, current_user.username, user_name, lock_until, iso_timestamp()),
            )

    update_lead_payload(
        lead_id,
        {
            "lockedByUserId": current_user.username,
            "lockedByUserName": user_name,
            "lockedUntil": lock_until,
        },
    )
    return LeadLock(
        leadId=lead_id,
        lockedByUserId=current_user.username,
        lockedByUserName=user_name,
        lockedUntil=lock_until,
        isActive=True,
    )


@router.get("", response_model=list[Lead])
def list_leads(current_user: CurrentUser):
    return list_saved_leads()


@router.post("/reset/notes-followups", response_model=LeadResetResult)
def reset_lead_notes_followups(current_user: CurrentUser):
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return reset_notes_and_followups()


@router.get("/activity/recent", response_model=list[LeadActivity])
def recent_team_activity(current_user: CurrentUser, limit: int = 50):
    return list_recent_activities(limit, current_user)


@router.get("/activity/daily-counts", response_model=list[DailyCallCount])
def daily_call_counts(current_user: CurrentUser):
    return list_daily_call_counts(current_user)


@router.get("/{lead_id}/activity", response_model=list[LeadActivity])
def lead_activity(lead_id: str, current_user: CurrentUser):
    return list_lead_activities(lead_id)


@router.post("/{lead_id}/activity", response_model=LeadActivity)
def record_lead_activity(lead_id: str, activity: LeadActivityCreate, current_user: CurrentUser):
    return create_lead_activity(lead_id, activity, current_user)


@router.get("/{lead_id}/lock", response_model=LeadLock)
def get_lead_lock(lead_id: str, current_user: CurrentUser):
    lock = get_active_lead_lock(lead_id)
    return lock.model_copy(update={"leadId": lead_id}) if not lock.leadId else lock


@router.post("/{lead_id}/lock", response_model=LeadLock)
def create_lead_lock(lead_id: str, current_user: CurrentUser):
    return lock_lead_for_user(lead_id, current_user)


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
