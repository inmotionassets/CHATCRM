from __future__ import annotations

import csv
import hashlib
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from io import StringIO
from typing import Any, Protocol

from .disposition_engine import (
    build_mock_transactions,
    haversine_miles,
    infer_property_type,
    marker_type_for_transaction,
    normalize_buyer_name,
    offset_coordinate,
    parse_date,
    safe_float,
)
from .routers import leads as lead_store


DATA_QUALITY_VALUES = {"verified", "estimated", "incomplete", "stale", "duplicate", "excluded"}
DEFAULT_SOURCE_NAME = "Dallas County CSV Import"


class DispositionProvider(Protocol):
    name: str

    def search(self, subject: dict[str, Any], filters: dict[str, Any]) -> dict[str, Any]:
        ...

    def refresh(self, subject: dict[str, Any], filters: dict[str, Any]) -> dict[str, Any]:
        ...


class MockDispositionProvider:
    name = "mock"

    def search(self, subject: dict[str, Any], filters: dict[str, Any]) -> dict[str, Any]:
        return {
            "provider": self.name,
            "sourceName": "Mock buyer activity",
            "lastRefreshAt": current_timestamp(),
            "errors": [],
            "transactions": [with_source_metadata(item, self.name, "Mock buyer activity") for item in build_mock_transactions(subject)],
        }

    def refresh(self, subject: dict[str, Any], filters: dict[str, Any]) -> dict[str, Any]:
        return self.search(subject, filters)


class CsvDispositionProvider:
    name = "csv"

    def search(self, subject: dict[str, Any], filters: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as connection:
            ensure_disposition_tables(connection)
            rows = fetch_persisted_transactions(connection)
            source_status = fetch_latest_source_status(connection, self.name)

        transactions = [
            prepare_persisted_transaction_for_subject(lead_store.parse_saved_payload(row_payload), subject)
            for row_payload in rows
        ]
        return {
            "provider": self.name,
            "sourceName": source_status.get("sourceName") or DEFAULT_SOURCE_NAME,
            "lastRefreshAt": source_status.get("lastRefreshAt") or "",
            "errors": source_status.get("errors") or [],
            "transactions": transactions,
        }

    def refresh(self, subject: dict[str, Any], filters: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as connection:
            ensure_disposition_tables(connection)
            save_transaction_source(
                connection,
                provider=self.name,
                source_name=DEFAULT_SOURCE_NAME,
                status="ready",
                error="",
                refreshed_at=current_timestamp(),
            )
        return self.search(subject, filters)


class CountyDispositionProvider:
    name = "county"

    def search(self, subject: dict[str, Any], filters: dict[str, Any]) -> dict[str, Any]:
        return {
            "provider": self.name,
            "sourceName": "County provider placeholder",
            "lastRefreshAt": current_timestamp(),
            "errors": ["County provider is ready as a contract, but no county automation is connected yet."],
            "transactions": [],
        }

    def refresh(self, subject: dict[str, Any], filters: dict[str, Any]) -> dict[str, Any]:
        return self.search(subject, filters)


def get_provider(name: str | None = None) -> DispositionProvider:
    provider_name = (name or os.getenv("DISPOSITION_PROVIDER") or "mock").strip().lower()
    if provider_name == "csv":
        return CsvDispositionProvider()
    if provider_name == "county":
        return CountyDispositionProvider()
    return MockDispositionProvider()


@contextmanager
def get_connection():
    if lead_store.USE_POSTGRES:
        with lead_store.get_postgres_connection() as connection:
            yield connection
        return

    connection = lead_store.get_sqlite_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def ensure_disposition_tables(connection) -> None:
    if lead_store.USE_POSTGRES:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS transaction_sources (
                id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                source_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ready',
                error TEXT NOT NULL DEFAULT '',
                payload TEXT NOT NULL DEFAULT '{}',
                last_refreshed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS disposition_transactions (
                id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                source_record_id TEXT NOT NULL,
                parcel_id TEXT NOT NULL DEFAULT '',
                apn TEXT NOT NULL DEFAULT '',
                sale_date TEXT NOT NULL DEFAULT '',
                sale_price NUMERIC NOT NULL DEFAULT 0,
                buyer_name TEXT NOT NULL DEFAULT '',
                latitude NUMERIC NOT NULL DEFAULT 0,
                longitude NUMERIC NOT NULL DEFAULT 0,
                data_quality TEXT NOT NULL DEFAULT 'incomplete',
                payload TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_disposition_transactions_provider_source ON disposition_transactions (provider, source_record_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_disposition_transactions_apn_date_price ON disposition_transactions (apn, sale_date, sale_price)")
        connection.execute("CREATE TABLE IF NOT EXISTS buyer_entities (id TEXT PRIMARY KEY, normalized_name TEXT NOT NULL UNIQUE, display_name TEXT NOT NULL, payload TEXT NOT NULL DEFAULT '{}', updated_at TIMESTAMPTZ NOT NULL DEFAULT now())")
        connection.execute("CREATE TABLE IF NOT EXISTS buyer_aliases (id TEXT PRIMARY KEY, buyer_entity_id TEXT NOT NULL, alias TEXT NOT NULL, normalized_alias TEXT NOT NULL, payload TEXT NOT NULL DEFAULT '{}', updated_at TIMESTAMPTZ NOT NULL DEFAULT now())")
        connection.execute("CREATE TABLE IF NOT EXISTS buyer_transaction_links (id TEXT PRIMARY KEY, buyer_entity_id TEXT NOT NULL, transaction_id TEXT NOT NULL, confidence NUMERIC NOT NULL DEFAULT 0, payload TEXT NOT NULL DEFAULT '{}', updated_at TIMESTAMPTZ NOT NULL DEFAULT now())")
        connection.execute("CREATE TABLE IF NOT EXISTS deal_buyer_matches (id TEXT PRIMARY KEY, deal_id TEXT NOT NULL, buyer_id TEXT NOT NULL, score INTEGER NOT NULL, reasons TEXT NOT NULL, payload TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now())")
        return

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS transaction_sources (
            id TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            source_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ready',
            error TEXT NOT NULL DEFAULT '',
            payload TEXT NOT NULL DEFAULT '{}',
            last_refreshed_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS disposition_transactions (
            id TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            source_record_id TEXT NOT NULL,
            parcel_id TEXT NOT NULL DEFAULT '',
            apn TEXT NOT NULL DEFAULT '',
            sale_date TEXT NOT NULL DEFAULT '',
            sale_price REAL NOT NULL DEFAULT 0,
            buyer_name TEXT NOT NULL DEFAULT '',
            latitude REAL NOT NULL DEFAULT 0,
            longitude REAL NOT NULL DEFAULT 0,
            data_quality TEXT NOT NULL DEFAULT 'incomplete',
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_disposition_transactions_provider_source ON disposition_transactions (provider, source_record_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_disposition_transactions_apn_date_price ON disposition_transactions (apn, sale_date, sale_price)")
    connection.execute("CREATE TABLE IF NOT EXISTS buyer_entities (id TEXT PRIMARY KEY, normalized_name TEXT NOT NULL UNIQUE, display_name TEXT NOT NULL, payload TEXT NOT NULL DEFAULT '{}', updated_at TEXT NOT NULL)")
    connection.execute("CREATE TABLE IF NOT EXISTS buyer_aliases (id TEXT PRIMARY KEY, buyer_entity_id TEXT NOT NULL, alias TEXT NOT NULL, normalized_alias TEXT NOT NULL, payload TEXT NOT NULL DEFAULT '{}', updated_at TEXT NOT NULL)")
    connection.execute("CREATE TABLE IF NOT EXISTS buyer_transaction_links (id TEXT PRIMARY KEY, buyer_entity_id TEXT NOT NULL, transaction_id TEXT NOT NULL, confidence REAL NOT NULL DEFAULT 0, payload TEXT NOT NULL DEFAULT '{}', updated_at TEXT NOT NULL)")
    connection.execute("CREATE TABLE IF NOT EXISTS deal_buyer_matches (id TEXT PRIMARY KEY, deal_id TEXT NOT NULL, buyer_id TEXT NOT NULL, score INTEGER NOT NULL, reasons TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")


def import_csv_transactions(csv_text: str, source_name: str = DEFAULT_SOURCE_NAME, provider: str = "csv") -> dict[str, Any]:
    imported_at = current_timestamp()
    reader = csv.DictReader(StringIO(csv_text))
    if not reader.fieldnames:
        return {"importedCount": 0, "updatedCount": 0, "duplicateCount": 0, "warnings": ["CSV file has no header row."]}

    warnings: list[str] = []
    imported_count = 0
    updated_count = 0
    duplicate_count = 0
    normalized_rows: list[dict[str, Any]] = []

    for row_number, row in enumerate(reader, start=2):
        transaction = normalize_provider_transaction(row, provider=provider, source_name=source_name, imported_at=imported_at)
        if transaction["dataQuality"] == "incomplete":
            warnings.append(f"Row {row_number}: saved as incomplete because buyer, sale date, price, or coordinates are missing.")
        normalized_rows.append(transaction)

    with get_connection() as connection:
        ensure_disposition_tables(connection)
        save_transaction_source(
            connection,
            provider=provider,
            source_name=source_name,
            status="ready",
            error="",
            refreshed_at=imported_at,
            metadata={"columns": reader.fieldnames, "rowCount": len(normalized_rows)},
        )
        for transaction in normalized_rows:
            result = upsert_transaction(connection, transaction)
            imported_count += 1 if result == "inserted" else 0
            updated_count += 1 if result == "updated" else 0
            duplicate_count += 1 if result == "duplicate" else 0
            upsert_buyer_entity(connection, transaction)

    return {
        "importedCount": imported_count,
        "updatedCount": updated_count,
        "duplicateCount": duplicate_count,
        "totalRows": len(normalized_rows),
        "warnings": warnings,
        "sourceName": source_name,
        "lastRefreshAt": imported_at,
    }


def normalize_provider_transaction(
    row: dict[str, Any],
    provider: str,
    source_name: str,
    imported_at: str | None = None,
) -> dict[str, Any]:
    imported_at = imported_at or current_timestamp()
    source_record_id = pick_value(row, "source_record_id", "source record id", "record_id", "transaction_id", "id")
    apn = pick_value(row, "parcel_id", "parcel id", "apn", "account_number", "account number")
    address = pick_value(row, "address", "property_address", "site_address", "situs_address")
    sale_date = normalize_date_text(pick_value(row, "sale_date", "sale date", "deed_date", "transaction_date", "date"))
    sale_price = int(safe_float(pick_value(row, "sale_price", "sale price", "sales_price", "price", "amount"), 0))
    acreage = safe_float(pick_value(row, "acreage", "acres", "lot_acres", "land_acres"), 0)
    latitude = safe_float(pick_value(row, "latitude", "lat", "y"), 0)
    longitude = safe_float(pick_value(row, "longitude", "lng", "lon", "x"), 0)
    buyer_name = pick_value(row, "buyer_name", "buyer", "grantee", "owner_name", "owner")
    seller_name = pick_value(row, "seller_name", "seller", "grantor")
    buyer_mailing_address = pick_value(row, "buyer_mailing_address", "mailing_address", "mailing address", "owner_address")
    property_type = pick_value(row, "property_type", "property type", "land_use", "land use", "use") or infer_property_type(row)
    financing_type = pick_value(row, "financing_type", "financing", "loan_type", "deed_type")
    deed_type = pick_value(row, "deed_type", "deed", "document_type")
    zoning = pick_value(row, "zoning", "zone")
    confidence = clamp_confidence(safe_float(pick_value(row, "confidence", "match_confidence"), 0))
    if not confidence:
        confidence = infer_confidence(sale_price, buyer_name, sale_date, latitude, longitude)
    source_record_id = source_record_id or fallback_source_record_id(provider, apn, address, sale_date, sale_price, buyer_name)
    price_per_acre = round(sale_price / acreage) if sale_price and acreage else 0
    cash_sale = is_cash_sale(financing_type, deed_type, pick_value(row, "cash_sale", "cash sale", "cash"))
    data_quality = infer_data_quality(sale_price, buyer_name, sale_date, latitude, longitude, confidence)

    transaction = {
        "id": transaction_id(provider, source_record_id),
        "source": provider,
        "sourceName": source_name,
        "sourceRecordId": source_record_id,
        "parcelId": apn,
        "apn": apn,
        "address": address or "Address missing",
        "coordinates": {"lat": latitude, "lng": longitude},
        "saleDate": sale_date,
        "salePrice": sale_price,
        "acreage": acreage,
        "pricePerAcre": price_per_acre,
        "deedType": deed_type,
        "financingType": financing_type,
        "cashSale": cash_sale,
        "buyerName": buyer_name or "Unidentified Buyer",
        "sellerName": seller_name,
        "buyerMailingAddress": buyer_mailing_address,
        "propertyType": property_type,
        "zoning": zoning,
        "confidence": confidence,
        "dataQuality": data_quality,
        "verified": data_quality == "verified",
        "estimated": data_quality == "estimated",
        "sourceLastRefreshed": imported_at,
        "rawSourceMetadata": clean_row(row),
        "markerType": marker_type_for_transaction({"buyerType": infer_buyer_type(buyer_name, property_type), "cashSale": cash_sale}),
        "buyerType": infer_buyer_type(buyer_name, property_type),
        "relationshipTier": "C",
    }
    return transaction


def prepare_persisted_transaction_for_subject(transaction: dict[str, Any], subject: dict[str, Any]) -> dict[str, Any]:
    lat = safe_float(transaction.get("coordinates", {}).get("lat"), 0)
    lng = safe_float(transaction.get("coordinates", {}).get("lng"), 0)
    if not lat or not lng:
        lat, lng = estimate_coordinates(subject, transaction.get("address") or transaction.get("apn") or transaction.get("sourceRecordId"))
        transaction["coordinates"] = {"lat": round(lat, 6), "lng": round(lng, 6)}
        if transaction.get("dataQuality") == "verified":
            transaction["dataQuality"] = "estimated"
            transaction["estimated"] = True
            transaction["verified"] = False

    subject_lat = safe_float(subject.get("coordinates", {}).get("lat"), 0)
    subject_lng = safe_float(subject.get("coordinates", {}).get("lng"), 0)
    transaction["distanceMiles"] = round(haversine_miles(subject_lat, subject_lng, lat, lng), 2)
    if not transaction.get("pricePerAcre"):
        sale_price = safe_float(transaction.get("salePrice"), 0)
        acreage = safe_float(transaction.get("acreage"), 0)
        transaction["pricePerAcre"] = round(sale_price / acreage) if sale_price and acreage else 0
    return transaction


def with_source_metadata(transaction: dict[str, Any], provider: str, source_name: str) -> dict[str, Any]:
    now = current_timestamp()
    return {
        **transaction,
        "source": provider,
        "sourceName": source_name,
        "sourceRecordId": transaction.get("id") or "",
        "parcelId": transaction.get("apn") or "",
        "deedType": transaction.get("deedType") or "Recorded deed",
        "financingType": transaction.get("financingType") or ("Cash" if transaction.get("cashSale") else "Unknown"),
        "sellerName": transaction.get("sellerName") or "",
        "zoning": transaction.get("zoning") or "",
        "confidence": transaction.get("confidence") or 92,
        "dataQuality": transaction.get("dataQuality") or "verified",
        "verified": True,
        "estimated": False,
        "sourceLastRefreshed": now,
        "rawSourceMetadata": transaction.get("rawSourceMetadata") or {},
    }


def fetch_persisted_transactions(connection) -> list[Any]:
    rows = connection.execute("SELECT payload FROM disposition_transactions ORDER BY sale_date DESC, updated_at DESC").fetchall()
    if lead_store.USE_POSTGRES:
        return [row[0] for row in rows]
    return [row["payload"] for row in rows]


def fetch_latest_source_status(connection, provider: str) -> dict[str, Any]:
    placeholder = "%s" if lead_store.USE_POSTGRES else "?"
    row = connection.execute(
        f"SELECT source_name, status, error, last_refreshed_at FROM transaction_sources WHERE provider = {placeholder} ORDER BY updated_at DESC LIMIT 1",
        (provider,),
    ).fetchone()
    if not row:
        return {}
    if lead_store.USE_POSTGRES:
        source_name, status, error, refreshed_at = row
    else:
        source_name, status, error, refreshed_at = row["source_name"], row["status"], row["error"], row["last_refreshed_at"]
    return {
        "sourceName": source_name,
        "status": status,
        "errors": [error] if error else [],
        "lastRefreshAt": str(refreshed_at or ""),
    }


def save_transaction_source(
    connection,
    provider: str,
    source_name: str,
    status: str,
    error: str,
    refreshed_at: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    source_id = transaction_id(provider, source_name)
    payload = json.dumps(metadata or {})
    if lead_store.USE_POSTGRES:
        connection.execute(
            """
            INSERT INTO transaction_sources (id, provider, source_name, status, error, payload, last_refreshed_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (id) DO UPDATE SET
                source_name = EXCLUDED.source_name,
                status = EXCLUDED.status,
                error = EXCLUDED.error,
                payload = EXCLUDED.payload,
                last_refreshed_at = EXCLUDED.last_refreshed_at,
                updated_at = now()
            """,
            (source_id, provider, source_name, status, error, payload, refreshed_at),
        )
        return

    connection.execute(
        """
        INSERT INTO transaction_sources (id, provider, source_name, status, error, payload, last_refreshed_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            source_name = excluded.source_name,
            status = excluded.status,
            error = excluded.error,
            payload = excluded.payload,
            last_refreshed_at = excluded.last_refreshed_at,
            updated_at = excluded.updated_at
        """,
        (source_id, provider, source_name, status, error, payload, refreshed_at, current_timestamp()),
    )


def upsert_transaction(connection, transaction: dict[str, Any]) -> str:
    transaction_payload = json.dumps(transaction)
    existing = find_existing_transaction(connection, transaction)
    result = "updated" if existing else "inserted"
    if existing and existing != transaction["id"]:
        transaction = {**transaction, "id": existing, "dataQuality": "duplicate"}
        result = "duplicate"

    if lead_store.USE_POSTGRES:
        connection.execute(
            """
            INSERT INTO disposition_transactions (
                id, provider, source_record_id, parcel_id, apn, sale_date, sale_price,
                buyer_name, latitude, longitude, data_quality, payload, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (id) DO UPDATE SET
                source_record_id = EXCLUDED.source_record_id,
                parcel_id = EXCLUDED.parcel_id,
                apn = EXCLUDED.apn,
                sale_date = EXCLUDED.sale_date,
                sale_price = EXCLUDED.sale_price,
                buyer_name = EXCLUDED.buyer_name,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                data_quality = EXCLUDED.data_quality,
                payload = EXCLUDED.payload,
                updated_at = now()
            """,
            transaction_row_values(transaction),
        )
        return result

    connection.execute(
        """
        INSERT INTO disposition_transactions (
            id, provider, source_record_id, parcel_id, apn, sale_date, sale_price,
            buyer_name, latitude, longitude, data_quality, payload, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            source_record_id = excluded.source_record_id,
            parcel_id = excluded.parcel_id,
            apn = excluded.apn,
            sale_date = excluded.sale_date,
            sale_price = excluded.sale_price,
            buyer_name = excluded.buyer_name,
            latitude = excluded.latitude,
            longitude = excluded.longitude,
            data_quality = excluded.data_quality,
            payload = excluded.payload,
            updated_at = excluded.updated_at
        """,
        (*transaction_row_values(transaction), current_timestamp()),
    )
    return result


def transaction_row_values(transaction: dict[str, Any]) -> tuple[Any, ...]:
    coordinates = transaction.get("coordinates") or {}
    return (
        transaction.get("id") or "",
        transaction.get("source") or "csv",
        transaction.get("sourceRecordId") or "",
        transaction.get("parcelId") or transaction.get("apn") or "",
        transaction.get("apn") or "",
        transaction.get("saleDate") or "",
        safe_float(transaction.get("salePrice"), 0),
        transaction.get("buyerName") or "",
        safe_float(coordinates.get("lat"), 0),
        safe_float(coordinates.get("lng"), 0),
        transaction.get("dataQuality") or "incomplete",
        json.dumps(transaction),
    )


def find_existing_transaction(connection, transaction: dict[str, Any]) -> str:
    provider = transaction.get("source") or "csv"
    source_record_id = transaction.get("sourceRecordId") or ""
    placeholder = "%s" if lead_store.USE_POSTGRES else "?"
    row = connection.execute(
        f"SELECT id FROM disposition_transactions WHERE provider = {placeholder} AND source_record_id = {placeholder}",
        (provider, source_record_id),
    ).fetchone()
    if row:
        return row[0] if lead_store.USE_POSTGRES else row["id"]

    apn = transaction.get("apn") or ""
    sale_date = transaction.get("saleDate") or ""
    sale_price = safe_float(transaction.get("salePrice"), 0)
    if apn and sale_date and sale_price:
        row = connection.execute(
            f"SELECT id FROM disposition_transactions WHERE apn = {placeholder} AND sale_date = {placeholder} AND sale_price = {placeholder}",
            (apn, sale_date, sale_price),
        ).fetchone()
        if row:
            return row[0] if lead_store.USE_POSTGRES else row["id"]
    return ""


def upsert_buyer_entity(connection, transaction: dict[str, Any]) -> None:
    buyer_name = str(transaction.get("buyerName") or "").strip()
    normalized = normalize_buyer_name(buyer_name)
    if not normalized or buyer_name == "Unidentified Buyer":
        return
    buyer_id = transaction_id("buyer", normalized)
    payload = json.dumps(
        {
            "displayName": buyer_name,
            "buyerType": transaction.get("buyerType") or "unknown",
            "mailingAddress": transaction.get("buyerMailingAddress") or "",
            "source": transaction.get("source") or "",
        }
    )
    now = current_timestamp()
    if lead_store.USE_POSTGRES:
        connection.execute(
            """
            INSERT INTO buyer_entities (id, normalized_name, display_name, payload, updated_at)
            VALUES (%s, %s, %s, %s, now())
            ON CONFLICT (normalized_name) DO UPDATE SET display_name = EXCLUDED.display_name, payload = EXCLUDED.payload, updated_at = now()
            """,
            (buyer_id, normalized, buyer_name, payload),
        )
        connection.execute(
            """
            INSERT INTO buyer_transaction_links (id, buyer_entity_id, transaction_id, confidence, payload, updated_at)
            VALUES (%s, %s, %s, %s, %s, now())
            ON CONFLICT (id) DO NOTHING
            """,
            (transaction_id(buyer_id, transaction.get("id")), buyer_id, transaction.get("id"), transaction.get("confidence") or 0, "{}"),
        )
        return

    connection.execute(
        """
        INSERT INTO buyer_entities (id, normalized_name, display_name, payload, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(normalized_name) DO UPDATE SET display_name = excluded.display_name, payload = excluded.payload, updated_at = excluded.updated_at
        """,
        (buyer_id, normalized, buyer_name, payload, now),
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO buyer_transaction_links (id, buyer_entity_id, transaction_id, confidence, payload, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (transaction_id(buyer_id, transaction.get("id")), buyer_id, transaction.get("id"), transaction.get("confidence") or 0, "{}", now),
    )


def pick_value(row: dict[str, Any], *names: str) -> str:
    normalized = {normalize_header(key): value for key, value in row.items()}
    for name in names:
        value = normalized.get(normalize_header(name))
        if value not in (None, ""):
            return str(value).strip()
    return ""


def normalize_header(value: Any) -> str:
    return "".join(char for char in str(value or "").lower() if char.isalnum())


def normalize_date_text(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    parsed = parse_date(text)
    return parsed.isoformat() if parsed else text


def infer_confidence(sale_price: int, buyer_name: str, sale_date: str, latitude: float, longitude: float) -> int:
    score = 40
    if sale_price:
        score += 15
    if buyer_name:
        score += 15
    if sale_date:
        score += 15
    if latitude and longitude:
        score += 15
    return clamp_confidence(score)


def infer_data_quality(sale_price: int, buyer_name: str, sale_date: str, latitude: float, longitude: float, confidence: int) -> str:
    if not sale_price or not buyer_name or not sale_date:
        return "incomplete"
    if not latitude or not longitude:
        return "estimated"
    if confidence >= 80:
        return "verified"
    return "estimated"


def infer_buyer_type(buyer_name: str, property_type: str) -> str:
    text = f"{buyer_name} {property_type}".lower()
    if any(word in text for word in ["builder", "builders", "homes", "construction", "custom homes"]):
        return "builder"
    if any(word in text for word in ["development", "developer", "communities"]):
        return "developer"
    if any(word in text for word in ["invest", "capital", "holdings", "properties", "land", "llc"]):
        return "investor"
    return "unknown"


def is_cash_sale(financing_type: str, deed_type: str, cash_value: str) -> bool:
    text = f"{financing_type} {deed_type} {cash_value}".lower()
    if text.strip() in {"true", "yes", "1"}:
        return True
    return "cash" in text or "warranty deed" in text and "deed of trust" not in text


def estimate_coordinates(subject: dict[str, Any], seed_value: Any) -> tuple[float, float]:
    subject_lat = safe_float(subject.get("coordinates", {}).get("lat"), 32.7767)
    subject_lng = safe_float(subject.get("coordinates", {}).get("lng"), -96.7970)
    seed = sum(ord(char) for char in str(seed_value or "transaction"))
    north_miles = ((seed % 100) / 100) * 8 - 4
    east_miles = (((seed // 5) % 100) / 100) * 8 - 4
    return offset_coordinate(subject_lat, subject_lng, north_miles, east_miles)


def fallback_source_record_id(provider: str, apn: str, address: str, sale_date: str, sale_price: int, buyer_name: str) -> str:
    return transaction_id(provider, "|".join([apn, address, sale_date, str(sale_price), buyer_name]))


def transaction_id(*parts: Any) -> str:
    text = "|".join(str(part or "") for part in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def clamp_confidence(value: float) -> int:
    return max(0, min(100, round(value)))


def clean_row(row: dict[str, Any]) -> dict[str, str]:
    return {str(key): str(value or "") for key, value in row.items()}


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
