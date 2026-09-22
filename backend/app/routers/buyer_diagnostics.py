import sqlite3
from pathlib import Path
from typing import Any

import psycopg
from fastapi import APIRouter, HTTPException, status
from psycopg import sql

from ..auth import CurrentUser
from . import leads as lead_store

router = APIRouter(prefix="/buyers", tags=["buyer diagnostics"])

BUYER_TABLES = [
    "buyers",
    "buyer_profiles",
    "buyer_contacts",
    "buyer_locations",
    "buyer_activity",
    "buyer_contact_sources",
    "buyer_enrichment_results",
    "deal_buyer_matches",
    "disposition_transactions",
    "buyer_entities",
    "buyer_transaction_links",
]


def require_admin(current_user: CurrentUser) -> None:
    if current_user.role != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


def empty_table_status() -> dict[str, Any]:
    return {
        "exists": False,
        "count": None,
        "error": "",
    }


def count_postgres_tables() -> dict[str, dict[str, Any]]:
    table_status: dict[str, dict[str, Any]] = {table: empty_table_status() for table in BUYER_TABLES}

    with psycopg.connect(lead_store.postgres_connection_url(), prepare_threshold=None) as connection:
        with connection.cursor() as cursor:
            for table in BUYER_TABLES:
                cursor.execute("SELECT to_regclass(%s)", (f"public.{table}",))
                exists = cursor.fetchone()[0] is not None
                table_status[table]["exists"] = exists
                if not exists:
                    continue

                cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
                table_status[table]["count"] = int(cursor.fetchone()[0] or 0)

    return table_status


def count_sqlite_tables(path: Path) -> dict[str, dict[str, Any]]:
    table_status: dict[str, dict[str, Any]] = {table: empty_table_status() for table in BUYER_TABLES}
    if not path.exists():
        return table_status

    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        for table in BUYER_TABLES:
            exists = (
                connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                    (table,),
                ).fetchone()
                is not None
            )
            table_status[table]["exists"] = exists
            if not exists:
                continue

            quoted_table = '"' + table.replace('"', '""') + '"'
            table_status[table]["count"] = int(connection.execute(f"SELECT COUNT(*) FROM {quoted_table}").fetchone()[0] or 0)
    finally:
        connection.close()

    return table_status


@router.get("/status")
def buyer_data_status(current_user: CurrentUser):
    require_admin(current_user)

    result: dict[str, Any] = {
        "database": "postgres" if lead_store.USE_POSTGRES else "sqlite",
        "databaseUrlConfigured": bool(lead_store.DATABASE_URL),
        "databaseUrlSummary": lead_store.database_url_summary(),
        "sqliteFallbackPath": str(lead_store.DATABASE_PATH),
        "sqliteFallbackExists": lead_store.DATABASE_PATH.exists(),
        "postgres": {
            "connectionOk": False,
            "errorType": "",
            "errorMessage": "",
            "tables": {table: empty_table_status() for table in BUYER_TABLES},
        },
        "sqliteFallback": {
            "tables": count_sqlite_tables(lead_store.DATABASE_PATH),
        },
    }

    if lead_store.USE_POSTGRES:
        try:
            result["postgres"]["tables"] = count_postgres_tables()
            result["postgres"]["connectionOk"] = True
        except Exception as exc:
            result["postgres"]["errorType"] = type(exc).__name__
            result["postgres"]["errorMessage"] = str(exc)[:500]

    return result
