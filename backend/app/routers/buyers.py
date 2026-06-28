import csv
import io
import json
import re
import time
import zipfile
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse
from urllib.request import Request, urlopen
from collections import Counter
from datetime import datetime, timedelta
from statistics import mean
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ..auth import CurrentUser
from . import leads as lead_store

router = APIRouter(prefix="/buyers", tags=["buyers"])


class BuyerProfile(BaseModel):
    id: str = ""
    name: str = ""
    normalizedCompanyName: str = ""
    company: str = ""
    buyerType: str = "unknown"
    phone: str = ""
    phones: list[str] = Field(default_factory=list)
    email: str = ""
    website: str = ""
    linkedinUrl: str = ""
    facebookUrl: str = ""
    contactFormUrl: str = ""
    socialLinks: list[str] = Field(default_factory=list)
    counties: list[str] = Field(default_factory=list)
    zipCodes: list[str] = Field(default_factory=list)
    priceMin: str = ""
    priceMax: str = ""
    propertyTypes: list[str] = Field(default_factory=list)
    fundingType: str = ""
    builderType: str = ""
    activityStatus: str = "warm"
    relationshipTier: str = "C"
    mailingAddress: str = ""
    registeredAgent: str = ""
    pastDealsBought: str = ""
    propertyCount: int = 0
    vacantLotCount: int = 0
    averageLandValue: str = ""
    averagePurchasePrice: str = ""
    lastPurchaseDate: str = ""
    estimatedBuyBox: str = ""
    confidenceScore: int = 0
    builderScore: int = 0
    assignmentFeeTolerance: str = ""
    notes: str = ""
    source: str = ""
    sourceUrls: list[str] = Field(default_factory=list)


class BuyerImportResult(BaseModel):
    buyers: list[BuyerProfile]
    warnings: list[str] = Field(default_factory=list)


class DallasCadImportResult(BaseModel):
    jobId: str = ""
    fileName: str = ""
    status: str = "preview"
    buyers: list[BuyerProfile]
    newBuyers: int = 0
    duplicatesSkipped: int = 0
    candidatesFound: int = 0
    propertyRowsRead: int = 0
    highScoreCount: int = 0
    columns: list[str] = Field(default_factory=list)
    mappedColumns: dict[str, str] = Field(default_factory=dict)
    rowPreview: list[dict[str, str]] = Field(default_factory=list)
    settings: dict[str, str | int | bool] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class DallasCadApplyRequest(BaseModel):
    jobId: str
    selectedBuyerIds: list[str] = Field(default_factory=list)


class DallasCadEnrichmentRequest(BaseModel):
    jobId: str
    selectedBuyerIds: list[str] = Field(default_factory=list)
    enrichmentEnabled: bool = True
    minBuilderScore: int = 50
    rateLimitMs: int = 750


class BuyerPublicEnrichmentRequest(BaseModel):
    selectedBuyerIds: list[str] = Field(default_factory=list)
    maxBuyers: int = 40
    minBuilderScore: int = 0
    rateLimitMs: int = 750


class BuyerPublicEnrichmentResult(BaseModel):
    buyers: list[BuyerProfile]
    checkedCount: int = 0
    updatedCount: int = 0
    phonesFound: int = 0


class DallasCadSettings(BaseModel):
    enrichmentEnabled: bool = True
    maxRecords: int = 500
    minBuilderScore: int = 20
    rateLimitMs: int = 750


class DealMatchRequest(BaseModel):
    id: str = ""
    address: str = ""
    county: str = ""
    zipCode: str = ""
    propertyType: str = "Land"
    price: str = ""
    rehabLevel: str = ""
    stage: str = ""


class BuyerMatch(BaseModel):
    buyer: BuyerProfile
    score: int
    reasons: list[str] = Field(default_factory=list)


def get_connection():
    return lead_store.get_postgres_connection() if lead_store.USE_POSTGRES else lead_store.get_sqlite_connection()


def ensure_buyer_tables(connection) -> None:
    if lead_store.USE_POSTGRES:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS buyers (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS buyer_locations (
                buyer_id TEXT PRIMARY KEY,
                counties TEXT NOT NULL DEFAULT '',
                zip_codes TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS buyer_criteria (
                buyer_id TEXT PRIMARY KEY,
                price_min TEXT NOT NULL DEFAULT '',
                price_max TEXT NOT NULL DEFAULT '',
                property_types TEXT NOT NULL DEFAULT '',
                funding_type TEXT NOT NULL DEFAULT '',
                builder_type TEXT NOT NULL DEFAULT '',
                assignment_fee_tolerance TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS buyer_contacts (
                buyer_id TEXT PRIMARY KEY,
                phone TEXT NOT NULL DEFAULT '',
                phones TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                website TEXT NOT NULL DEFAULT '',
                socials TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS buyer_activity (
                buyer_id TEXT PRIMARY KEY,
                activity_status TEXT NOT NULL DEFAULT '',
                relationship_tier TEXT NOT NULL DEFAULT '',
                past_deals_bought TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS deal_buyer_matches (
                id TEXT PRIMARY KEY,
                deal_id TEXT NOT NULL,
                buyer_id TEXT NOT NULL,
                score INTEGER NOT NULL,
                reasons TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cad_import_jobs (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                settings TEXT NOT NULL DEFAULT '{}',
                columns TEXT NOT NULL DEFAULT '[]',
                mapped_columns TEXT NOT NULL DEFAULT '{}',
                row_count INTEGER NOT NULL DEFAULT 0,
                candidate_count INTEGER NOT NULL DEFAULT 0,
                imported_count INTEGER NOT NULL DEFAULT 0,
                payload TEXT NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cad_import_rows (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                row_index INTEGER NOT NULL DEFAULT 0,
                account_num TEXT NOT NULL DEFAULT '',
                owner_name TEXT NOT NULL DEFAULT '',
                company_name TEXT NOT NULL DEFAULT '',
                mailing_address TEXT NOT NULL DEFAULT '',
                property_address TEXT NOT NULL DEFAULT '',
                payload TEXT NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS buyer_builder_candidates (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                buyer_id TEXT NOT NULL,
                score INTEGER NOT NULL DEFAULT 0,
                selected BOOLEAN NOT NULL DEFAULT false,
                imported BOOLEAN NOT NULL DEFAULT false,
                payload TEXT NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS buyer_profiles (
                buyer_id TEXT PRIMARY KEY,
                normalized_company TEXT NOT NULL DEFAULT '',
                buyer_type TEXT NOT NULL DEFAULT '',
                builder_score INTEGER NOT NULL DEFAULT 0,
                confidence_score INTEGER NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT '',
                payload TEXT NOT NULL DEFAULT '{}',
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS buyer_contact_sources (
                id TEXT PRIMARY KEY,
                buyer_id TEXT NOT NULL,
                source_name TEXT NOT NULL DEFAULT '',
                source_url TEXT NOT NULL DEFAULT '',
                value_type TEXT NOT NULL DEFAULT '',
                value TEXT NOT NULL DEFAULT '',
                confidence INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS buyer_enrichment_results (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                buyer_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT '',
                payload TEXT NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS parcel_gis_matches (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                account_num TEXT NOT NULL DEFAULT '',
                parcel_id TEXT NOT NULL DEFAULT '',
                property_address TEXT NOT NULL DEFAULT '',
                match_confidence INTEGER NOT NULL DEFAULT 0,
                payload TEXT NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        return

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS buyers (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS cad_import_jobs (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            settings TEXT NOT NULL DEFAULT '{}',
            columns TEXT NOT NULL DEFAULT '[]',
            mapped_columns TEXT NOT NULL DEFAULT '{}',
            row_count INTEGER NOT NULL DEFAULT 0,
            candidate_count INTEGER NOT NULL DEFAULT 0,
            imported_count INTEGER NOT NULL DEFAULT 0,
            payload TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS cad_import_rows (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            row_index INTEGER NOT NULL DEFAULT 0,
            account_num TEXT NOT NULL DEFAULT '',
            owner_name TEXT NOT NULL DEFAULT '',
            company_name TEXT NOT NULL DEFAULT '',
            mailing_address TEXT NOT NULL DEFAULT '',
            property_address TEXT NOT NULL DEFAULT '',
            payload TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS buyer_builder_candidates (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            buyer_id TEXT NOT NULL,
            score INTEGER NOT NULL DEFAULT 0,
            selected INTEGER NOT NULL DEFAULT 0,
            imported INTEGER NOT NULL DEFAULT 0,
            payload TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS buyer_profiles (
            buyer_id TEXT PRIMARY KEY,
            normalized_company TEXT NOT NULL DEFAULT '',
            buyer_type TEXT NOT NULL DEFAULT '',
            builder_score INTEGER NOT NULL DEFAULT 0,
            confidence_score INTEGER NOT NULL DEFAULT 0,
            source TEXT NOT NULL DEFAULT '',
            payload TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS buyer_contact_sources (
            id TEXT PRIMARY KEY,
            buyer_id TEXT NOT NULL,
            source_name TEXT NOT NULL DEFAULT '',
            source_url TEXT NOT NULL DEFAULT '',
            value_type TEXT NOT NULL DEFAULT '',
            value TEXT NOT NULL DEFAULT '',
            confidence INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS buyer_enrichment_results (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            buyer_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '',
            payload TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS parcel_gis_matches (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            account_num TEXT NOT NULL DEFAULT '',
            parcel_id TEXT NOT NULL DEFAULT '',
            property_address TEXT NOT NULL DEFAULT '',
            match_confidence INTEGER NOT NULL DEFAULT 0,
            payload TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS buyer_locations (
            buyer_id TEXT PRIMARY KEY,
            counties TEXT NOT NULL DEFAULT '',
            zip_codes TEXT NOT NULL DEFAULT ''
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS buyer_criteria (
            buyer_id TEXT PRIMARY KEY,
            price_min TEXT NOT NULL DEFAULT '',
            price_max TEXT NOT NULL DEFAULT '',
            property_types TEXT NOT NULL DEFAULT '',
            funding_type TEXT NOT NULL DEFAULT '',
            builder_type TEXT NOT NULL DEFAULT '',
            assignment_fee_tolerance TEXT NOT NULL DEFAULT ''
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS buyer_contacts (
            buyer_id TEXT PRIMARY KEY,
            phone TEXT NOT NULL DEFAULT '',
            phones TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL DEFAULT '',
            website TEXT NOT NULL DEFAULT '',
            socials TEXT NOT NULL DEFAULT ''
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS buyer_activity (
            buyer_id TEXT PRIMARY KEY,
            activity_status TEXT NOT NULL DEFAULT '',
            relationship_tier TEXT NOT NULL DEFAULT '',
            past_deals_bought TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT ''
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS deal_buyer_matches (
            id TEXT PRIMARY KEY,
            deal_id TEXT NOT NULL,
            buyer_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            reasons TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def list_saved_buyers() -> list[BuyerProfile]:
    with get_connection() as connection:
        ensure_buyer_tables(connection)
        rows = connection.execute("SELECT payload FROM buyers ORDER BY id DESC").fetchall()

    return [BuyerProfile.model_validate(lead_store.parse_saved_payload(row[0])) for row in rows]


def save_buyer(buyer: BuyerProfile) -> BuyerProfile:
    clean_buyer = sanitize_buyer(buyer)

    with get_connection() as connection:
        ensure_buyer_tables(connection)

        if lead_store.USE_POSTGRES:
            connection.execute(
                """
                INSERT INTO buyers (id, payload)
                VALUES (%s, %s)
                ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload
                """,
                (clean_buyer.id, clean_buyer.model_dump_json()),
            )
            upsert_buyer_side_tables(connection, clean_buyer, "%s")
            upsert_buyer_profile_tables(connection, clean_buyer, "%s")
        else:
            connection.execute(
                "INSERT OR REPLACE INTO buyers (id, payload) VALUES (?, ?)",
                (clean_buyer.id, clean_buyer.model_dump_json()),
            )
            upsert_buyer_side_tables(connection, clean_buyer, "?")
            upsert_buyer_profile_tables(connection, clean_buyer, "?")

    return clean_buyer


def replace_saved_buyers(buyers: list[BuyerProfile]) -> list[BuyerProfile]:
    clean_buyers = [sanitize_buyer(buyer) for buyer in buyers]

    with get_connection() as connection:
        ensure_buyer_tables(connection)
        for table in [
            "deal_buyer_matches",
            "buyer_activity",
            "buyer_contacts",
            "buyer_criteria",
            "buyer_locations",
            "buyer_profiles",
            "buyers",
        ]:
            connection.execute(f"DELETE FROM {table}")

        for buyer in clean_buyers:
            if lead_store.USE_POSTGRES:
                connection.execute(
                    "INSERT INTO buyers (id, payload) VALUES (%s, %s)",
                    (buyer.id, buyer.model_dump_json()),
                )
                upsert_buyer_side_tables(connection, buyer, "%s")
                upsert_buyer_profile_tables(connection, buyer, "%s")
            else:
                connection.execute(
                    "INSERT INTO buyers (id, payload) VALUES (?, ?)",
                    (buyer.id, buyer.model_dump_json()),
                )
                upsert_buyer_side_tables(connection, buyer, "?")
                upsert_buyer_profile_tables(connection, buyer, "?")

    return clean_buyers


def upsert_buyer_side_tables(connection, buyer: BuyerProfile, placeholder: str) -> None:
    if placeholder == "%s":
        conflict = "ON CONFLICT (buyer_id) DO UPDATE SET"
        connection.execute(
            f"""
            INSERT INTO buyer_locations (buyer_id, counties, zip_codes)
            VALUES (%s, %s, %s)
            {conflict} counties = EXCLUDED.counties, zip_codes = EXCLUDED.zip_codes
            """,
            (buyer.id, json.dumps(buyer.counties), json.dumps(buyer.zipCodes)),
        )
        connection.execute(
            f"""
            INSERT INTO buyer_criteria (
                buyer_id, price_min, price_max, property_types, funding_type, builder_type, assignment_fee_tolerance
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            {conflict}
                price_min = EXCLUDED.price_min,
                price_max = EXCLUDED.price_max,
                property_types = EXCLUDED.property_types,
                funding_type = EXCLUDED.funding_type,
                builder_type = EXCLUDED.builder_type,
                assignment_fee_tolerance = EXCLUDED.assignment_fee_tolerance
            """,
            (
                buyer.id,
                buyer.priceMin,
                buyer.priceMax,
                json.dumps(buyer.propertyTypes),
                buyer.fundingType,
                buyer.builderType,
                buyer.assignmentFeeTolerance,
            ),
        )
        connection.execute(
            f"""
            INSERT INTO buyer_contacts (buyer_id, phone, phones, email, website, socials)
            VALUES (%s, %s, %s, %s, %s, %s)
            {conflict}
                phone = EXCLUDED.phone,
                phones = EXCLUDED.phones,
                email = EXCLUDED.email,
                website = EXCLUDED.website,
                socials = EXCLUDED.socials
            """,
            (buyer.id, buyer.phone, json.dumps(buyer.phones), buyer.email, buyer.website, json.dumps(buyer.socialLinks)),
        )
        connection.execute(
            f"""
            INSERT INTO buyer_activity (buyer_id, activity_status, relationship_tier, past_deals_bought, notes)
            VALUES (%s, %s, %s, %s, %s)
            {conflict}
                activity_status = EXCLUDED.activity_status,
                relationship_tier = EXCLUDED.relationship_tier,
                past_deals_bought = EXCLUDED.past_deals_bought,
                notes = EXCLUDED.notes
            """,
            (buyer.id, buyer.activityStatus, buyer.relationshipTier, buyer.pastDealsBought, buyer.notes),
        )
        return

    connection.execute(
        """
        INSERT OR REPLACE INTO buyer_locations (buyer_id, counties, zip_codes)
        VALUES (?, ?, ?)
        """,
        (buyer.id, json.dumps(buyer.counties), json.dumps(buyer.zipCodes)),
    )
    connection.execute(
        """
        INSERT OR REPLACE INTO buyer_criteria (
            buyer_id, price_min, price_max, property_types, funding_type, builder_type, assignment_fee_tolerance
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            buyer.id,
            buyer.priceMin,
            buyer.priceMax,
            json.dumps(buyer.propertyTypes),
            buyer.fundingType,
            buyer.builderType,
            buyer.assignmentFeeTolerance,
        ),
    )
    connection.execute(
        """
        INSERT OR REPLACE INTO buyer_contacts (buyer_id, phone, phones, email, website, socials)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (buyer.id, buyer.phone, json.dumps(buyer.phones), buyer.email, buyer.website, json.dumps(buyer.socialLinks)),
    )
    connection.execute(
        """
        INSERT OR REPLACE INTO buyer_activity (buyer_id, activity_status, relationship_tier, past_deals_bought, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (buyer.id, buyer.activityStatus, buyer.relationshipTier, buyer.pastDealsBought, buyer.notes),
    )


def upsert_buyer_profile_tables(connection, buyer: BuyerProfile, placeholder: str) -> None:
    if placeholder == "%s":
        connection.execute(
            """
            INSERT INTO buyer_profiles (
                buyer_id, normalized_company, buyer_type, builder_score, confidence_score, source, payload, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (buyer_id) DO UPDATE SET
                normalized_company = EXCLUDED.normalized_company,
                buyer_type = EXCLUDED.buyer_type,
                builder_score = EXCLUDED.builder_score,
                confidence_score = EXCLUDED.confidence_score,
                source = EXCLUDED.source,
                payload = EXCLUDED.payload,
                updated_at = now()
            """,
            (
                buyer.id,
                buyer.normalizedCompanyName,
                buyer.buyerType,
                buyer.builderScore,
                buyer.confidenceScore,
                buyer.source,
                buyer.model_dump_json(),
            ),
        )
        return

    connection.execute(
        """
        INSERT OR REPLACE INTO buyer_profiles (
            buyer_id, normalized_company, buyer_type, builder_score, confidence_score, source, payload, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            buyer.id,
            buyer.normalizedCompanyName,
            buyer.buyerType,
            buyer.builderScore,
            buyer.confidenceScore,
            buyer.source,
            buyer.model_dump_json(),
        ),
    )


def remove_buyer(buyer_id: str) -> None:
    with get_connection() as connection:
        ensure_buyer_tables(connection)
        placeholder = "%s" if lead_store.USE_POSTGRES else "?"
        for table in ["deal_buyer_matches", "buyer_activity", "buyer_contacts", "buyer_criteria", "buyer_locations", "buyer_profiles"]:
            column = "buyer_id"
            connection.execute(f"DELETE FROM {table} WHERE {column} = {placeholder}", (buyer_id,))
        connection.execute(f"DELETE FROM buyer_contact_sources WHERE buyer_id = {placeholder}", (buyer_id,))
        connection.execute(f"DELETE FROM buyers WHERE id = {placeholder}", (buyer_id,))


def sanitize_buyer(buyer: BuyerProfile) -> BuyerProfile:
    phones = unique_phones([*buyer.phones, buyer.phone])
    name = clean_text(buyer.name)
    company = clean_text(buyer.company)
    normalized_company = clean_text(buyer.normalizedCompanyName) or normalize_company_name(company or name)

    return buyer.model_copy(
        update={
            "id": clean_text(buyer.id) or f"buyer-{uuid4().hex[:12]}",
            "name": name or company or "Unknown Buyer",
            "normalizedCompanyName": normalized_company,
            "company": company,
            "buyerType": clean_text(buyer.buyerType) or "unknown",
            "phone": phones[0] if phones else clean_text(buyer.phone),
            "phones": phones,
            "email": clean_text(buyer.email),
            "website": clean_text(buyer.website),
            "linkedinUrl": clean_text(buyer.linkedinUrl),
            "facebookUrl": clean_text(buyer.facebookUrl),
            "contactFormUrl": clean_text(buyer.contactFormUrl),
            "socialLinks": clean_list(buyer.socialLinks),
            "counties": clean_list(buyer.counties),
            "zipCodes": unique_zips(buyer.zipCodes),
            "priceMin": clean_text(buyer.priceMin),
            "priceMax": clean_text(buyer.priceMax),
            "propertyTypes": clean_list(buyer.propertyTypes),
            "fundingType": clean_text(buyer.fundingType),
            "builderType": clean_text(buyer.builderType),
            "activityStatus": clean_text(buyer.activityStatus).lower() or "warm",
            "relationshipTier": (clean_text(buyer.relationshipTier).upper() or "C")[:1],
            "mailingAddress": clean_text(buyer.mailingAddress),
            "registeredAgent": clean_text(buyer.registeredAgent),
            "pastDealsBought": clean_text(buyer.pastDealsBought),
            "propertyCount": int_number(str(buyer.propertyCount)),
            "vacantLotCount": int_number(str(buyer.vacantLotCount)),
            "averageLandValue": clean_text(buyer.averageLandValue),
            "averagePurchasePrice": clean_text(buyer.averagePurchasePrice),
            "lastPurchaseDate": clean_text(buyer.lastPurchaseDate),
            "estimatedBuyBox": clean_text(buyer.estimatedBuyBox),
            "confidenceScore": min(100, max(0, int_number(str(buyer.confidenceScore)))),
            "builderScore": min(100, max(0, int_number(str(buyer.builderScore)))),
            "assignmentFeeTolerance": clean_text(buyer.assignmentFeeTolerance),
            "notes": clean_text(buyer.notes),
            "source": clean_text(buyer.source),
            "sourceUrls": clean_list(buyer.sourceUrls),
        }
    )


def import_buyers_from_csv(contents: bytes, source: str) -> BuyerImportResult:
    text = decode_csv(contents)
    lines = [line for line in text.splitlines() if line.strip()]

    if not lines:
        return BuyerImportResult(buyers=[], warnings=["The CSV was empty."])

    reader = csv.DictReader(lines)
    buyers: list[BuyerProfile] = []

    for row in reader:
        buyer = buyer_from_csv_row(row, source)
        if buyer:
            buyers.append(buyer)

    if not buyers:
        return BuyerImportResult(buyers=[], warnings=["No buyer rows were found. Check the CSV headers."])

    return BuyerImportResult(buyers=dedupe_buyers(buyers))


BUILDER_KEYWORDS = {
    "builder",
    "builders",
    "building",
    "capital",
    "communities",
    "construction",
    "custom homes",
    "development",
    "developers",
    "group",
    "holdings",
    "home",
    "homes",
    "investments",
    "land",
    "llc",
    "partners",
    "properties",
    "realty",
    "ventures",
}

ENTITY_KEYWORDS = {
    "co",
    "company",
    "corp",
    "corporation",
    "inc",
    "investments",
    "llc",
    "lp",
    "ltd",
    "partners",
    "properties",
    "trust",
}

VACANT_TERMS = {"vacant", "unimproved", "land", "lot", "acreage"}


def import_buyers_from_dcad_zip(
    file_obj,
    source: str,
    settings: DallasCadSettings | None = None,
) -> DallasCadImportResult:
    settings = normalize_dcad_settings(settings)
    warnings: list[str] = []
    groups: dict[str, dict] = {}
    account_to_group: dict[str, str] = {}
    property_rows_read = 0
    row_preview: list[dict[str, str]] = []
    columns: list[str] = []
    mapped_columns: dict[str, str] = {}

    with zipfile.ZipFile(file_obj) as archive:
        account_entry = find_zip_entry(archive, "ACCOUNT_INFO.CSV")
        appraisal_entry = find_zip_entry(archive, "ACCOUNT_APPRL_YEAR.CSV")
        land_entry = find_zip_entry(archive, "LAND.CSV")

        if not account_entry:
            return DallasCadImportResult(
                buyers=[],
                warnings=["ACCOUNT_INFO.CSV was not found in the Dallas CAD ZIP."],
            )

        columns = read_zip_csv_headers(archive, account_entry)
        mapped_columns = infer_dcad_column_map(columns)

        for row in iter_zip_csv(archive, account_entry):
            if property_rows_read >= settings.maxRecords:
                warnings.append(f"Stopped at the admin max of {settings.maxRecords} account rows.")
                break

            property_rows_read += 1
            if len(row_preview) < 8:
                row_preview.append(compact_dcad_preview_row(row))

            account = clean_text(row.get("ACCOUNT_NUM"))
            owner_name = first_present(row.get("BIZ_NAME", ""), row.get("OWNER_NAME1", ""), row.get("OWNER_NAME2", ""))
            company_name = first_present(row.get("BIZ_NAME", ""), owner_name)
            normalized = normalize_company_name(company_name)
            mailing_address = build_mailing_address(row)

            if not account or not normalized:
                continue

            keyword_match = keyword_matches(company_name)
            is_business = bool(keyword_match) or looks_like_business_owner(company_name)
            if not is_business:
                continue

            group = groups.setdefault(
                normalized,
                {
                    "name": owner_name,
                    "company": company_name,
                    "normalized": normalized,
                    "mailing": mailing_address,
                    "accounts": set(),
                    "phones": set(),
                    "property_zips": Counter(),
                    "counties": Counter(),
                    "property_types": Counter(),
                    "builder_keywords": Counter(),
                    "mailing_addresses": Counter(),
                    "land_values": [],
                    "market_values": [],
                    "purchase_dates": [],
                    "vacant_accounts": set(),
                    "improved_accounts": set(),
                    "zoning": Counter(),
                    "sample_addresses": [],
                },
            )

            group["accounts"].add(account)
            account_to_group[account] = normalized
            if row.get("PHONE_NUM"):
                group["phones"].update(unique_phones([row.get("PHONE_NUM", "")]))
            if row.get("PROPERTY_ZIPCODE"):
                group["property_zips"].update(unique_zips([row.get("PROPERTY_ZIPCODE", "")]))
            group["counties"].update(["Dallas"])
            if row.get("DIVISION_CD"):
                group["property_types"].update([clean_text(row.get("DIVISION_CD"))])
            for keyword in keyword_match:
                group["builder_keywords"].update([keyword])
            if mailing_address:
                group["mailing_addresses"].update([mailing_address])
            purchase_date = parse_date(row.get("DEED_TXFR_DATE", ""))
            if purchase_date:
                group["purchase_dates"].append(purchase_date)
            property_address = build_property_address(row)
            if property_address and len(group["sample_addresses"]) < 5:
                group["sample_addresses"].append(property_address)

        if land_entry:
            for row in iter_zip_csv(archive, land_entry):
                account = clean_text(row.get("ACCOUNT_NUM"))
                group_key = account_to_group.get(account)
                if not group_key:
                    continue

                group = groups[group_key]
                land_desc = first_present(row.get("SPTD_DESC", ""), row.get("ZONING", ""))
                if land_desc:
                    group["property_types"].update([land_desc])
                if row.get("ZONING"):
                    group["zoning"].update([clean_text(row.get("ZONING"))])
                land_value = money_number(row.get("VAL_AMT", ""))
                if land_value:
                    group["land_values"].append(land_value)
                if any(term in normalize_key(land_desc) for term in VACANT_TERMS):
                    group["vacant_accounts"].add(account)

        if appraisal_entry:
            for row in iter_zip_csv(archive, appraisal_entry):
                account = clean_text(row.get("ACCOUNT_NUM"))
                group_key = account_to_group.get(account)
                if not group_key:
                    continue

                group = groups[group_key]
                land_value = money_number(row.get("LAND_VAL", ""))
                market_value = money_number(row.get("TOT_VAL", ""))
                improvement_value = money_number(row.get("IMPR_VAL", ""))
                property_type = first_present(
                    row.get("PROPERTY_CLASS_DESC", ""),
                    row.get("STATE_CD_DESC", ""),
                    row.get("SPTD_DESC", ""),
                    row.get("DIVISION_CD", ""),
                )

                if land_value:
                    group["land_values"].append(land_value)
                if market_value:
                    group["market_values"].append(market_value)
                if property_type:
                    group["property_types"].update([property_type])
                if improvement_value:
                    group["improved_accounts"].add(account)
                if land_value and improvement_value == 0:
                    group["vacant_accounts"].add(account)

    cad_buyers = [buyer_from_dcad_group(group, source) for group in groups.values()]
    cad_buyers = [buyer for buyer in cad_buyers if buyer.builderScore >= settings.minBuilderScore]
    if settings.enrichmentEnabled:
        cad_buyers = apply_public_enrichment_to_candidates(cad_buyers, settings, max_public_lookups=20)
    cad_buyers.sort(key=lambda buyer: buyer.builderScore, reverse=True)

    return DallasCadImportResult(
        jobId=f"cad-{uuid4().hex[:12]}",
        fileName=source,
        status="preview",
        buyers=cad_buyers,
        candidatesFound=len(cad_buyers),
        propertyRowsRead=property_rows_read,
        highScoreCount=sum(1 for buyer in cad_buyers if buyer.builderScore >= 70),
        columns=columns,
        mappedColumns=mapped_columns,
        rowPreview=row_preview,
        settings=settings.model_dump(),
        warnings=warnings,
    )


def import_buyers_from_dcad_csv(
    contents: bytes,
    source: str,
    settings: DallasCadSettings | None = None,
) -> DallasCadImportResult:
    settings = normalize_dcad_settings(settings)
    text = decode_csv(contents)
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return DallasCadImportResult(fileName=source, buyers=[], warnings=["The Dallas CAD CSV was empty."])

    reader = csv.DictReader(lines)
    columns = list(reader.fieldnames or [])
    mapped_columns = infer_dcad_column_map(columns)
    groups: dict[str, dict] = {}
    account_to_group: dict[str, str] = {}
    row_preview: list[dict[str, str]] = []
    property_rows_read = 0
    warnings: list[str] = []

    for row in reader:
        if property_rows_read >= settings.maxRecords:
            warnings.append(f"Stopped at the admin max of {settings.maxRecords} account rows.")
            break

        property_rows_read += 1
        if len(row_preview) < 8:
            row_preview.append(compact_dcad_preview_row(row))

        account = clean_text(row.get("ACCOUNT_NUM") or row.get("account_num") or row.get("Account Number"))
        owner_name = first_present(
            row.get("BIZ_NAME", ""),
            row.get("OWNER_NAME1", ""),
            row.get("OWNER_NAME2", ""),
            row.get("Owner Name", ""),
            row.get("owner", ""),
        )
        company_name = first_present(row.get("BIZ_NAME", ""), row.get("Company", ""), row.get("company", ""), owner_name)
        normalized = normalize_company_name(company_name)
        mailing_address = build_mailing_address(row)

        if not account:
            account = f"row-{property_rows_read}"
        if not normalized:
            continue

        keyword_match = keyword_matches(company_name)
        is_business = bool(keyword_match) or looks_like_business_owner(company_name)
        if not is_business:
            continue

        group = groups.setdefault(
            normalized,
            {
                "name": owner_name,
                "company": company_name,
                "normalized": normalized,
                "mailing": mailing_address,
                "accounts": set(),
                "phones": set(),
                "property_zips": Counter(),
                "counties": Counter(),
                "property_types": Counter(),
                "builder_keywords": Counter(),
                "mailing_addresses": Counter(),
                "land_values": [],
                "market_values": [],
                "purchase_dates": [],
                "vacant_accounts": set(),
                "improved_accounts": set(),
                "zoning": Counter(),
                "sample_addresses": [],
            },
        )

        group["accounts"].add(account)
        account_to_group[account] = normalized
        if row.get("PHONE_NUM") or row.get("Phone"):
            group["phones"].update(unique_phones([row.get("PHONE_NUM", ""), row.get("Phone", "")]))
        if row.get("PROPERTY_ZIPCODE") or row.get("ZIP"):
            group["property_zips"].update(unique_zips([row.get("PROPERTY_ZIPCODE", ""), row.get("ZIP", "")]))
        group["counties"].update([clean_text(row.get("COUNTY") or row.get("County") or "Dallas")])
        property_type = first_present(
            row.get("DIVISION_CD", ""),
            row.get("PROPERTY_CLASS_DESC", ""),
            row.get("STATE_CD_DESC", ""),
            row.get("Land Use", ""),
            row.get("Property Type", ""),
        )
        if property_type:
            group["property_types"].update([property_type])
        for keyword in keyword_match:
            group["builder_keywords"].update([keyword])
        if mailing_address:
            group["mailing_addresses"].update([mailing_address])
        purchase_date = parse_date(row.get("DEED_TXFR_DATE", "") or row.get("Last Sale Date", ""))
        if purchase_date:
            group["purchase_dates"].append(purchase_date)
        property_address = build_property_address(row)
        if property_address and len(group["sample_addresses"]) < 5:
            group["sample_addresses"].append(property_address)

        land_value = money_number(row.get("LAND_VAL", "") or row.get("VAL_AMT", "") or row.get("Land Value", ""))
        market_value = money_number(row.get("TOT_VAL", "") or row.get("Market Value", ""))
        improvement_value = money_number(row.get("IMPR_VAL", "") or row.get("Improvement Value", ""))
        if land_value:
            group["land_values"].append(land_value)
        if market_value:
            group["market_values"].append(market_value)
        if improvement_value:
            group["improved_accounts"].add(account)
        if any(term in normalize_key(property_type) for term in VACANT_TERMS) or (land_value and improvement_value == 0):
            group["vacant_accounts"].add(account)

    cad_buyers = [buyer_from_dcad_group(group, source) for group in groups.values()]
    cad_buyers = [buyer for buyer in cad_buyers if buyer.builderScore >= settings.minBuilderScore]
    if settings.enrichmentEnabled:
        cad_buyers = apply_public_enrichment_to_candidates(cad_buyers, settings, max_public_lookups=20)
    cad_buyers.sort(key=lambda buyer: buyer.builderScore, reverse=True)

    return DallasCadImportResult(
        jobId=f"cad-{uuid4().hex[:12]}",
        fileName=source,
        status="preview",
        buyers=cad_buyers,
        candidatesFound=len(cad_buyers),
        propertyRowsRead=property_rows_read,
        highScoreCount=sum(1 for buyer in cad_buyers if buyer.builderScore >= 70),
        columns=columns,
        mappedColumns=mapped_columns,
        rowPreview=row_preview,
        settings=settings.model_dump(),
        warnings=warnings,
    )


def preview_buyers_from_dcad_upload(contents: bytes, source: str, settings: DallasCadSettings) -> DallasCadImportResult:
    file_obj = io.BytesIO(contents)
    if zipfile.is_zipfile(file_obj):
        file_obj.seek(0)
        return import_buyers_from_dcad_zip(file_obj, source, settings)
    return import_buyers_from_dcad_csv(contents, source, settings)


def normalize_dcad_settings(settings: DallasCadSettings | None = None) -> DallasCadSettings:
    settings = settings or DallasCadSettings()
    return DallasCadSettings(
        enrichmentEnabled=bool(settings.enrichmentEnabled),
        maxRecords=min(25000, max(25, int_number(str(settings.maxRecords)) or 500)),
        minBuilderScore=min(100, max(0, int_number(str(settings.minBuilderScore)))),
        rateLimitMs=min(10000, max(0, int_number(str(settings.rateLimitMs)))),
    )


def read_zip_csv_headers(archive: zipfile.ZipFile, entry) -> list[str]:
    with archive.open(entry) as raw_file:
        text_file = io.TextIOWrapper(raw_file, encoding="utf-8-sig", errors="ignore", newline="")
        reader = csv.DictReader(text_file)
        return list(reader.fieldnames or [])


def infer_dcad_column_map(columns: list[str]) -> dict[str, str]:
    wanted = {
        "owner name": ["OWNER_NAME1", "OWNER_NAME2", "Owner Name", "owner"],
        "company name": ["BIZ_NAME", "Company", "company"],
        "mailing address": ["OWNER_ADDRESS_LINE1", "Mailing Address", "mailing"],
        "property address": ["FULL_STREET_NAME", "Property Address", "Situs Address"],
        "account number": ["ACCOUNT_NUM", "Account Number"],
        "parcel id": ["GIS_PARCEL_ID", "APN", "Parcel ID"],
        "city": ["PROPERTY_CITY", "City"],
        "zip code": ["PROPERTY_ZIPCODE", "ZIP", "Zip"],
        "legal description": ["LEGAL1", "Legal Description"],
        "land value": ["LAND_VAL", "VAL_AMT", "Land Value"],
        "market value": ["TOT_VAL", "Market Value"],
        "property type": ["DIVISION_CD", "PROPERTY_CLASS_DESC", "Property Type"],
        "last sale date": ["DEED_TXFR_DATE", "Last Sale Date"],
        "phone": ["PHONE_NUM", "Phone"],
    }
    lower_lookup = {normalize_key(column): column for column in columns}
    mapped: dict[str, str] = {}
    for label, options in wanted.items():
        for option in options:
            direct = next((column for column in columns if column == option), "")
            if direct:
                mapped[label] = direct
                break
            normalized = normalize_key(option)
            if normalized in lower_lookup:
                mapped[label] = lower_lookup[normalized]
                break
        mapped.setdefault(label, "")
    return mapped


def compact_dcad_preview_row(row: dict[str, str]) -> dict[str, str]:
    keys = [
        "ACCOUNT_NUM",
        "BIZ_NAME",
        "OWNER_NAME1",
        "OWNER_ADDRESS_LINE1",
        "PROPERTY_CITY",
        "PROPERTY_ZIPCODE",
        "FULL_STREET_NAME",
        "LAND_VAL",
        "TOT_VAL",
        "PHONE_NUM",
    ]
    return {key: clean_text(row.get(key, "")) for key in keys if clean_text(row.get(key, ""))}


PUBLIC_LOOKUP_TIMEOUT_SECONDS = 4
PUBLIC_LOOKUP_MAX_BYTES = 250_000
PUBLIC_LOOKUP_PREVIEW_LIMIT = 20
PUBLIC_LOOKUP_REFRESH_LIMIT = 40
PUBLIC_LOOKUP_USER_AGENT = "Mozilla/5.0 (compatible; ChatCRM Public Business Contact Enrichment)"
SEARCH_RESULT_BLOCKLIST = {
    "bing.com",
    "dallasact.com",
    "dallascad.org",
    "duckduckgo.com",
    "google.com",
    "search.yahoo.com",
    "yahoo.com",
}
PRIVATE_HOST_TERMS = {"localhost", "127.0.0.1", "0.0.0.0"}
CONTACT_PATH_WORDS = ("contact", "about", "team", "locations")


def apply_public_enrichment_to_candidates(
    buyers: list[BuyerProfile],
    settings: DallasCadSettings,
    selected_ids: set[str] | None = None,
    max_public_lookups: int = PUBLIC_LOOKUP_PREVIEW_LIMIT,
) -> list[BuyerProfile]:
    enriched: list[BuyerProfile] = []
    lookup_count = 0

    for buyer in buyers:
        selected = selected_ids is None or buyer.id in selected_ids
        allow_web_lookup = selected and lookup_count < max_public_lookups and not buyer.phones and is_public_business_candidate(buyer)
        if allow_web_lookup:
            lookup_count += 1
        enriched.append(apply_public_candidate_enrichment(buyer, settings, allow_web_lookup=allow_web_lookup))

    return enriched


def apply_public_candidate_enrichment(
    buyer: BuyerProfile,
    settings: DallasCadSettings,
    allow_web_lookup: bool = True,
) -> BuyerProfile:
    source_urls = clean_list(
        [
            *buyer.sourceUrls,
            "https://www.dallascad.org/SearchOwner.aspx",
            "https://www.dallasact.com/act_webdev/dallas/index.jsp",
        ]
    )
    confidence = buyer.confidenceScore
    phones = list(buyer.phones)
    email = buyer.email
    website = buyer.website
    contact_form_url = buyer.contactFormUrl
    linkedin_url = buyer.linkedinUrl
    facebook_url = buyer.facebookUrl
    notes = buyer.notes
    enrichment_note = "Public enrichment: checked CAD/source links only. No paid skip tracing or private personal lookup."

    if allow_web_lookup and settings.enrichmentEnabled:
        result = lookup_public_business_contact(buyer)
        phones = unique_phones([*phones, *result["phones"]])
        email = email or first_present(*result["emails"])
        website = website or result["website"]
        contact_form_url = contact_form_url or result["contactFormUrl"]
        linkedin_url = linkedin_url or result["linkedinUrl"]
        facebook_url = facebook_url or result["facebookUrl"]
        source_urls = clean_list([*source_urls, *result["sourceUrls"]])
        if result["phones"]:
            enrichment_note = f"Public enrichment: found {len(result['phones'])} public business phone(s) from {', '.join(result['domains'][:3])}."
        elif result["sourceUrls"]:
            enrichment_note = "Public enrichment: checked public business pages, but no phone was found."

        if settings.rateLimitMs:
            time.sleep(min(settings.rateLimitMs, 2000) / 1000)

    if phones:
        confidence = max(confidence, 82 if allow_web_lookup else 70)
    if website or contact_form_url or email:
        confidence = max(confidence, 76)

    if "Public enrichment:" not in notes:
        notes = f"{notes}\n{enrichment_note}".strip()
    elif enrichment_note not in notes and "found" in enrichment_note:
        notes = f"{notes}\n{enrichment_note}".strip()

    return sanitize_buyer(
        buyer.model_copy(
            update={
                "phone": phones[0] if phones else buyer.phone,
                "phones": phones,
                "email": email,
                "website": website,
                "contactFormUrl": contact_form_url,
                "linkedinUrl": linkedin_url,
                "facebookUrl": facebook_url,
                "socialLinks": clean_list([*buyer.socialLinks, linkedin_url, facebook_url]),
                "confidenceScore": confidence,
                "notes": notes,
                "sourceUrls": source_urls,
            }
        )
    )


def lookup_public_business_contact(buyer: BuyerProfile) -> dict:
    company = clean_text(buyer.company or buyer.name)
    if not company:
        return empty_public_contact_result()

    query_parts = [company, "Dallas TX", "phone", "contact"]
    search_url = f"https://duckduckgo.com/html/?q={quote_plus(' '.join(query_parts))}"
    urls: list[str] = []
    source_urls = [search_url]

    if buyer.website and is_safe_public_url(buyer.website):
        urls.append(buyer.website)

    search_html = fetch_public_page(search_url)
    urls.extend(extract_search_result_urls(search_html))
    urls = [url for url in clean_list(urls) if is_safe_public_url(url)]

    phones: list[str] = []
    emails: list[str] = []
    domains: list[str] = []
    website = buyer.website
    contact_form_url = buyer.contactFormUrl
    linkedin_url = buyer.linkedinUrl
    facebook_url = buyer.facebookUrl

    for url in urls[:5]:
        page_html = fetch_public_page(url)
        if not page_html:
            continue

        page_text = html_to_searchable_text(page_html)
        if not is_relevant_business_page(buyer, page_text, url):
            continue

        source_urls.append(url)
        domain = website_domain(url)
        if domain:
            domains.append(domain)
        if not website and is_likely_company_website(url):
            website = public_site_root(url)
        if "linkedin.com" in domain and not linkedin_url:
            linkedin_url = url
        if "facebook.com" in domain and not facebook_url:
            facebook_url = url

        found_phones = unique_phones([page_text])
        if found_phones:
            phones = unique_phones([*phones, *found_phones])
        emails = clean_list([*emails, *extract_public_emails(page_text)])

        for contact_url in extract_contact_links(url, page_html)[:2]:
            if contact_form_url:
                break
            contact_html = fetch_public_page(contact_url)
            contact_text = html_to_searchable_text(contact_html)
            if not contact_text or not is_relevant_business_page(buyer, contact_text, contact_url):
                continue
            source_urls.append(contact_url)
            contact_form_url = contact_url
            phones = unique_phones([*phones, *unique_phones([contact_text])])
            emails = clean_list([*emails, *extract_public_emails(contact_text)])

        if phones and (website or contact_form_url):
            break

    return {
        "phones": phones[:4],
        "emails": emails[:2],
        "website": website,
        "contactFormUrl": contact_form_url,
        "linkedinUrl": linkedin_url,
        "facebookUrl": facebook_url,
        "sourceUrls": source_urls[:10],
        "domains": clean_list(domains),
    }


def empty_public_contact_result() -> dict:
    return {
        "phones": [],
        "emails": [],
        "website": "",
        "contactFormUrl": "",
        "linkedinUrl": "",
        "facebookUrl": "",
        "sourceUrls": [],
        "domains": [],
    }


def fetch_public_page(url: str) -> str:
    if not is_safe_public_url(url):
        return ""
    try:
        request = Request(url, headers={"User-Agent": PUBLIC_LOOKUP_USER_AGENT, "Accept": "text/html,text/plain;q=0.9,*/*;q=0.1"})
        with urlopen(request, timeout=PUBLIC_LOOKUP_TIMEOUT_SECONDS) as response:
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                return ""
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read(PUBLIC_LOOKUP_MAX_BYTES).decode(charset, errors="ignore")
    except (HTTPError, URLError, TimeoutError, ValueError):
        return ""


def extract_search_result_urls(page_html: str) -> list[str]:
    urls: list[str] = []
    for href in re.findall(r"href=[\"']([^\"']+)[\"']", page_html or "", flags=re.IGNORECASE):
        href = unescape(href)
        if "uddg=" in href:
            parsed = urlparse(urljoin("https://duckduckgo.com", href))
            target = first_present(*parse_qs(parsed.query).get("uddg", []))
            href = unquote(target)
        elif href.startswith("//"):
            href = f"https:{href}"
        elif href.startswith("/"):
            continue

        if not href.startswith(("http://", "https://")):
            continue
        domain = website_domain(href)
        if any(domain == blocked or domain.endswith(f".{blocked}") for blocked in SEARCH_RESULT_BLOCKLIST):
            continue
        urls.append(href)

    return clean_list(urls)[:8]


def html_to_searchable_text(page_html: str) -> str:
    text = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", page_html or "")
    text = re.sub(r"(?is)<br\s*/?>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_contact_links(base_url: str, page_html: str) -> list[str]:
    links: list[str] = []
    for href in re.findall(r"href=[\"']([^\"']+)[\"']", page_html or "", flags=re.IGNORECASE):
        href = unescape(href).strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        absolute = urljoin(base_url, href)
        path = urlparse(absolute).path.lower()
        if any(word in path for word in CONTACT_PATH_WORDS) and is_safe_public_url(absolute):
            links.append(absolute)
    return clean_list(links)


def extract_public_emails(text: str) -> list[str]:
    emails = re.findall(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text or "", flags=re.IGNORECASE)
    return clean_list([email for email in emails if not re.search(r"\.(png|jpg|jpeg|gif|webp|svg)$", email, re.IGNORECASE)])


def is_public_business_candidate(buyer: BuyerProfile) -> bool:
    text = normalize_key(" ".join([buyer.company, buyer.name, buyer.normalizedCompanyName, buyer.builderType, buyer.buyerType]))
    return looks_like_business_owner(text) or any(keyword in text for keyword in BUILDER_KEYWORDS)


def is_relevant_business_page(buyer: BuyerProfile, page_text: str, url: str) -> bool:
    company = buyer.company or buyer.name or buyer.normalizedCompanyName
    tokens = significant_company_tokens(company)
    if not tokens:
        return False
    normalized_page = normalize_key(page_text)[:12000]
    domain = normalize_key(website_domain(url))
    hits = sum(1 for token in tokens if token in normalized_page or token in domain)
    return hits >= min(2, len(tokens)) or normalize_company_name(company)[:12] in normalized_page


def significant_company_tokens(value: str) -> list[str]:
    blocked = BUILDER_KEYWORDS | ENTITY_KEYWORDS | {"the", "and", "of", "tx", "texas", "dallas"}
    tokens = re.findall(r"[a-z0-9]+", clean_text(value).lower())
    return [token for token in tokens if len(token) >= 3 and token not in blocked][:5]


def is_safe_public_url(url: str) -> bool:
    parsed = urlparse(clean_text(url))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    host = parsed.hostname or ""
    if host in PRIVATE_HOST_TERMS or host.endswith(".local"):
        return False
    if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", host):
        return not (host.startswith("10.") or host.startswith("127.") or host.startswith("192.168.") or host.startswith("172.16."))
    return True


def is_likely_company_website(url: str) -> bool:
    domain = website_domain(url)
    blocked = {"facebook.com", "linkedin.com", "instagram.com", "youtube.com", "x.com", "twitter.com"}
    directory_terms = ("bbb.org", "manta.com", "chamberofcommerce.com", "buildzoom.com", "bizapedia.com", "opencorporates.com")
    return bool(domain) and not any(domain == blocked_domain or domain.endswith(f".{blocked_domain}") for blocked_domain in blocked) and not any(term in domain for term in directory_terms)


def public_site_root(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""


def save_cad_import_preview(result: DallasCadImportResult) -> DallasCadImportResult:
    with get_connection() as connection:
        ensure_buyer_tables(connection)
        placeholder = "%s" if lead_store.USE_POSTGRES else "?"

        if lead_store.USE_POSTGRES:
            connection.execute(
                """
                INSERT INTO cad_import_jobs (
                    id, source, status, settings, columns, mapped_columns, row_count, candidate_count, payload, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    settings = EXCLUDED.settings,
                    columns = EXCLUDED.columns,
                    mapped_columns = EXCLUDED.mapped_columns,
                    row_count = EXCLUDED.row_count,
                    candidate_count = EXCLUDED.candidate_count,
                    payload = EXCLUDED.payload,
                    updated_at = now()
                """,
                (
                    result.jobId,
                    result.fileName,
                    result.status,
                    json.dumps(result.settings),
                    json.dumps(result.columns),
                    json.dumps(result.mappedColumns),
                    result.propertyRowsRead,
                    result.candidatesFound,
                    result.model_dump_json(),
                ),
            )
        else:
            connection.execute(
                """
                INSERT OR REPLACE INTO cad_import_jobs (
                    id, source, status, settings, columns, mapped_columns, row_count, candidate_count, payload, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    result.jobId,
                    result.fileName,
                    result.status,
                    json.dumps(result.settings),
                    json.dumps(result.columns),
                    json.dumps(result.mappedColumns),
                    result.propertyRowsRead,
                    result.candidatesFound,
                    result.model_dump_json(),
                ),
            )

        connection.execute(f"DELETE FROM cad_import_rows WHERE job_id = {placeholder}", (result.jobId,))
        connection.execute(f"DELETE FROM buyer_builder_candidates WHERE job_id = {placeholder}", (result.jobId,))
        connection.execute(f"DELETE FROM buyer_enrichment_results WHERE job_id = {placeholder}", (result.jobId,))
        connection.execute(f"DELETE FROM parcel_gis_matches WHERE job_id = {placeholder}", (result.jobId,))

        for index, row in enumerate(result.rowPreview):
            row_id = f"cadrow-{uuid4().hex[:12]}"
            values = (
                row_id,
                result.jobId,
                index,
                row.get("ACCOUNT_NUM", ""),
                first_present(row.get("OWNER_NAME1", ""), row.get("BIZ_NAME", "")),
                row.get("BIZ_NAME", ""),
                row.get("OWNER_ADDRESS_LINE1", ""),
                " ".join(part for part in [row.get("FULL_STREET_NAME", ""), row.get("PROPERTY_CITY", ""), row.get("PROPERTY_ZIPCODE", "")] if part),
                json.dumps(row),
            )
            if lead_store.USE_POSTGRES:
                connection.execute(
                    """
                    INSERT INTO cad_import_rows (
                        id, job_id, row_index, account_num, owner_name, company_name, mailing_address, property_address, payload
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    values,
                )
            else:
                connection.execute(
                    """
                    INSERT INTO cad_import_rows (
                        id, job_id, row_index, account_num, owner_name, company_name, mailing_address, property_address, payload
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    values,
                )

        for buyer in result.buyers:
            save_cad_candidate(connection, result.jobId, buyer, imported=False)
            save_candidate_contact_sources(connection, result.jobId, buyer)

    return result


def save_cad_candidate(connection, job_id: str, buyer: BuyerProfile, imported: bool = False) -> None:
    candidate_id = f"cand-{job_id}-{buyer.id}"
    values = (
        candidate_id,
        job_id,
        buyer.id,
        buyer.builderScore,
        False,
        imported,
        buyer.model_dump_json(),
    )
    if lead_store.USE_POSTGRES:
        connection.execute(
            """
            INSERT INTO buyer_builder_candidates (id, job_id, buyer_id, score, selected, imported, payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                score = EXCLUDED.score,
                selected = EXCLUDED.selected,
                imported = EXCLUDED.imported,
                payload = EXCLUDED.payload
            """,
            values,
        )
        return

    connection.execute(
        """
        INSERT OR REPLACE INTO buyer_builder_candidates (id, job_id, buyer_id, score, selected, imported, payload)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        values,
    )


def save_candidate_contact_sources(connection, job_id: str, buyer: BuyerProfile) -> None:
    placeholder = "%s" if lead_store.USE_POSTGRES else "?"
    connection.execute(f"DELETE FROM buyer_contact_sources WHERE buyer_id = {placeholder}", (buyer.id,))

    sources: list[tuple[str, str, str, str, int]] = []
    for url in buyer.sourceUrls:
        sources.append(("Public Source", url, "url", url, buyer.confidenceScore))
    public_contact_url = first_public_contact_source_url(buyer.sourceUrls)
    phone_source_name = "Public Business Contact" if public_contact_url else "Dallas CAD"
    phone_source_url = public_contact_url or "https://www.dallascad.org/SearchOwner.aspx"
    for phone in buyer.phones:
        sources.append((phone_source_name, phone_source_url, "phone", phone, buyer.confidenceScore))

    for source_name, source_url, value_type, value, confidence in sources[:12]:
        source_id = f"source-{uuid4().hex[:12]}"
        values = (source_id, buyer.id, source_name, source_url, value_type, value, confidence)
        if lead_store.USE_POSTGRES:
            connection.execute(
                """
                INSERT INTO buyer_contact_sources (
                    id, buyer_id, source_name, source_url, value_type, value, confidence
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                values,
            )
        else:
            connection.execute(
                """
                INSERT INTO buyer_contact_sources (
                    id, buyer_id, source_name, source_url, value_type, value, confidence
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )

    enrichment_id = f"enrich-{uuid4().hex[:12]}"
    payload = json.dumps({"sourceCount": len(sources), "confidenceScore": buyer.confidenceScore})
    values = (enrichment_id, job_id, buyer.id, "public-source-links", payload)
    if lead_store.USE_POSTGRES:
        connection.execute(
            """
            INSERT INTO buyer_enrichment_results (id, job_id, buyer_id, status, payload)
            VALUES (%s, %s, %s, %s, %s)
            """,
            values,
        )
        return

    connection.execute(
        """
        INSERT INTO buyer_enrichment_results (id, job_id, buyer_id, status, payload)
        VALUES (?, ?, ?, ?, ?)
        """,
        values,
    )


def first_public_contact_source_url(source_urls: list[str]) -> str:
    for url in source_urls:
        domain = website_domain(url)
        if domain and not any(term in domain for term in ["dallascad.org", "dallasact.com", "google.com", "duckduckgo.com"]):
            return url
    return ""

def list_cad_job_candidates(job_id: str) -> list[BuyerProfile]:
    with get_connection() as connection:
        ensure_buyer_tables(connection)
        placeholder = "%s" if lead_store.USE_POSTGRES else "?"
        rows = connection.execute(
            f"SELECT payload FROM buyer_builder_candidates WHERE job_id = {placeholder} ORDER BY score DESC",
            (job_id,),
        ).fetchall()

    return [BuyerProfile.model_validate(lead_store.parse_saved_payload(row[0])) for row in rows]


def import_selected_cad_buyers(job_id: str, selected_buyer_ids: list[str]) -> DallasCadImportResult:
    candidates = list_cad_job_candidates(job_id)
    if not candidates:
        raise HTTPException(status_code=404, detail="CAD import job was not found or has no candidates.")

    selected_ids = set(clean_list(selected_buyer_ids))
    selected = [buyer for buyer in candidates if not selected_ids or buyer.id in selected_ids]
    selected = enrich_imported_buyers(selected, max_public_lookups=PUBLIC_LOOKUP_REFRESH_LIMIT)
    existing_buyers = list_saved_buyers()
    existing_keys = set()
    for buyer in existing_buyers:
        existing_keys.update(duplicate_keys_for_buyer(buyer))
    imported_buyer_ids: set[str] = set()
    for buyer in selected:
        buyer_keys = duplicate_keys_for_buyer(buyer)
        if not buyer_keys & existing_keys:
            imported_buyer_ids.add(buyer.id)
            existing_keys.update(buyer_keys)

    merged_buyers, new_count, duplicates_skipped = merge_dcad_buyers(existing_buyers, selected)
    if new_count:
        replace_saved_buyers(merged_buyers)

    with get_connection() as connection:
        ensure_buyer_tables(connection)
        placeholder = "%s" if lead_store.USE_POSTGRES else "?"
        for buyer in selected:
            imported = buyer.id in imported_buyer_ids
            if lead_store.USE_POSTGRES:
                connection.execute(
                    f"UPDATE buyer_builder_candidates SET selected = true, imported = %s WHERE job_id = {placeholder} AND buyer_id = %s",
                    (imported, job_id, buyer.id),
                )
            else:
                connection.execute(
                    f"UPDATE buyer_builder_candidates SET selected = 1, imported = ? WHERE job_id = {placeholder} AND buyer_id = ?",
                    (1 if imported else 0, job_id, buyer.id),
                )
        if lead_store.USE_POSTGRES:
            connection.execute(
                "UPDATE cad_import_jobs SET status = %s, imported_count = %s, updated_at = now() WHERE id = %s",
                ("imported", new_count, job_id),
            )
        else:
            connection.execute(
                "UPDATE cad_import_jobs SET status = ?, imported_count = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                ("imported", new_count, job_id),
            )

    return DallasCadImportResult(
        jobId=job_id,
        status="imported",
        buyers=merged_buyers,
        newBuyers=new_count,
        duplicatesSkipped=duplicates_skipped,
        candidatesFound=len(candidates),
        highScoreCount=sum(1 for buyer in candidates if buyer.builderScore >= 70),
    )


def buyer_from_dcad_group(group: dict, source: str) -> BuyerProfile:
    property_count = len(group["accounts"])
    vacant_count = len(group["vacant_accounts"])
    land_values = group["land_values"]
    market_values = group["market_values"]
    last_purchase = max(group["purchase_dates"]) if group["purchase_dates"] else None
    top_zips = [zip_code for zip_code, _count in group["property_zips"].most_common(12)]
    top_counties = [county for county, _count in group["counties"].most_common(5)]
    top_types = [item for item, _count in group["property_types"].most_common(8)]
    top_keywords = [item for item, _count in group["builder_keywords"].most_common(5)]
    phones = sorted(group["phones"])
    score, score_notes = score_dcad_group(group)
    buyer_type = classify_dcad_buyer(group, score)
    avg_land_value = int(mean(land_values)) if land_values else 0
    avg_market_value = int(mean(market_values)) if market_values else 0
    company = clean_text(group["company"] or group["name"])
    google_query = "+".join(part for part in [company, "Dallas", "builder", "contact"] if part)

    notes = [
        f"Dallas CAD import. {property_count} property record(s), {vacant_count} likely vacant/land record(s).",
        f"Score reasons: {', '.join(score_notes) or 'Needs review'}.",
    ]
    if group["sample_addresses"]:
        notes.append(f"Sample properties: {'; '.join(group['sample_addresses'][:3])}.")

    return sanitize_buyer(
        BuyerProfile(
            name=clean_text(group["name"]) or company,
            normalizedCompanyName=group["normalized"],
            company=company,
            buyerType=buyer_type,
            phone=phones[0] if phones else "",
            phones=phones,
            counties=top_counties,
            zipCodes=top_zips,
            propertyTypes=top_types,
            fundingType="Unknown",
            builderType=", ".join(top_keywords) if top_keywords else buyer_type.title(),
            activityStatus="hot" if score >= 70 else "warm",
            relationshipTier="A" if score >= 80 else "B" if score >= 60 else "C",
            mailingAddress=group["mailing"],
            propertyCount=property_count,
            vacantLotCount=vacant_count,
            averageLandValue=str(avg_land_value) if avg_land_value else "",
            averagePurchasePrice=str(avg_market_value) if avg_market_value else "",
            lastPurchaseDate=last_purchase.isoformat() if last_purchase else "",
            estimatedBuyBox=build_estimated_buy_box(market_values, top_types),
            confidenceScore=70 if phones else 55,
            builderScore=score,
            notes="\n".join(notes),
            source="Dallas CAD Import",
            sourceUrls=[
                "https://www.dallascad.org/SearchOwner.aspx",
                "https://www.dallasact.com/act_webdev/dallas/index.jsp",
                f"https://www.google.com/search?q={google_query}",
            ],
        )
    )


def score_dcad_group(group: dict) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    property_count = len(group["accounts"])
    vacant_count = len(group["vacant_accounts"])
    normalized_name = normalize_key(group["company"] or group["name"])
    repeated_zip = any(count >= 2 for count in group["property_zips"].values())
    repeated_county = any(count >= 2 for count in group["counties"].values())
    recent_cutoff = datetime.now() - timedelta(days=730)
    recent_purchase = any(date >= recent_cutoff for date in group["purchase_dates"])

    if property_count >= 10:
        score += 30
        reasons.append("10+ properties")
    elif property_count >= 5:
        score += 20
        reasons.append("5+ properties")
    elif property_count >= 2:
        score += 10
        reasons.append("Multiple properties")

    if looks_like_business_owner(normalized_name):
        score += 15
        reasons.append("LLC/business owner")

    if group["builder_keywords"]:
        score += 20
        reasons.append("builder/investor keyword")

    if vacant_count:
        score += 15
        reasons.append("vacant/land ownership")

    if recent_purchase:
        score += 20
        reasons.append("recent purchase")

    if group["improved_accounts"]:
        score += 20
        reasons.append("improvement/new construction signal")

    if repeated_zip or repeated_county:
        score += 15
        reasons.append("repeated ZIP/county activity")

    if len(group["mailing_addresses"]) == 1 and property_count >= 3:
        score += 10
        reasons.append("same mailing address portfolio")

    return min(score, 100), reasons


def classify_dcad_buyer(group: dict, score: int) -> str:
    text = normalize_key(" ".join([group["company"], group["name"], " ".join(group["builder_keywords"])]))

    if any(word in text for word in ["builder", "construction", "custom homes", "communities", "home", "homes"]):
        return "builder"
    if any(word in text for word in ["development", "developer", "land"]):
        return "developer"
    if any(word in text for word in ["realty", "properties", "investments", "holdings", "capital"]):
        return "investor"
    if score >= 60:
        return "investor"
    return "unknown"


def build_estimated_buy_box(values: list[float], property_types: list[str]) -> str:
    if not values:
        return ", ".join(property_types[:3])

    low = int(min(values))
    high = int(max(values))
    type_text = ", ".join(property_types[:3])
    range_text = f"${low:,} - ${high:,}"
    return f"{range_text} / {type_text}" if type_text else range_text


def merge_dcad_buyers(existing_buyers: list[BuyerProfile], imported_buyers: list[BuyerProfile]) -> tuple[list[BuyerProfile], int, int]:
    existing_keys: set[str] = set()
    for buyer in existing_buyers:
        existing_keys.update(duplicate_keys_for_buyer(buyer))

    new_buyers: list[BuyerProfile] = []
    duplicates = 0
    for buyer in imported_buyers:
        buyer_keys = duplicate_keys_for_buyer(buyer)
        if buyer_keys & existing_keys:
            duplicates += 1
            continue
        new_buyers.append(buyer)
        existing_keys.update(buyer_keys)

    return [*existing_buyers, *new_buyers], len(new_buyers), duplicates


def duplicate_keys_for_buyer(buyer: BuyerProfile) -> set[str]:
    keys = {
        f"name:{normalize_company_name(buyer.normalizedCompanyName or buyer.company or buyer.name)}",
        f"mail:{normalize_key(buyer.mailingAddress)}",
        f"domain:{website_domain(buyer.website)}",
    }
    keys.update(f"phone:{phone_key}" for phone_key in [re.sub(r"\D", "", phone) for phone in buyer.phones] if phone_key)
    return {key for key in keys if not key.endswith(":")}


def find_zip_entry(archive: zipfile.ZipFile, file_name: str):
    expected = file_name.lower()
    return next((entry for entry in archive.infolist() if entry.filename.lower().endswith(expected)), None)


def iter_zip_csv(archive: zipfile.ZipFile, entry):
    with archive.open(entry) as raw_file:
        text_file = io.TextIOWrapper(raw_file, encoding="utf-8-sig", errors="ignore", newline="")
        reader = csv.DictReader(text_file)
        for row in reader:
            yield row


def build_mailing_address(row: dict[str, str]) -> str:
    parts = [
        row.get("OWNER_ADDRESS_LINE1", ""),
        row.get("OWNER_ADDRESS_LINE2", ""),
        row.get("OWNER_ADDRESS_LINE3", ""),
        row.get("OWNER_ADDRESS_LINE4", ""),
        row.get("OWNER_CITY", ""),
        row.get("OWNER_STATE", ""),
        row.get("OWNER_ZIPCODE", ""),
    ]
    return " ".join(clean_text(part) for part in parts if clean_text(part))


def build_property_address(row: dict[str, str]) -> str:
    street = " ".join(
        clean_text(part)
        for part in [row.get("STREET_NUM", ""), row.get("STREET_HALF_NUM", ""), row.get("FULL_STREET_NAME", "")]
        if clean_text(part)
    )
    parts = [street, row.get("PROPERTY_CITY", ""), row.get("PROPERTY_ZIPCODE", "")]
    return " ".join(clean_text(part) for part in parts if clean_text(part))


def keyword_matches(value: str) -> list[str]:
    text = normalize_key(value)
    return [keyword for keyword in BUILDER_KEYWORDS if keyword in text]


def looks_like_business_owner(value: str) -> bool:
    text = normalize_key(value)
    return any(re.search(rf"\b{re.escape(keyword)}\b", text) for keyword in ENTITY_KEYWORDS)


def normalize_company_name(value: str = "") -> str:
    text = normalize_key(value)
    suffixes = [
        "limited liability company",
        "corporation",
        "company",
        "incorporated",
        "holdings",
        "properties",
        "property",
        "partners",
        "ventures",
        "llc",
        "inc",
        "corp",
        "co",
        "lp",
        "ltd",
    ]
    for suffix in suffixes:
        text = re.sub(rf"\b{re.escape(suffix)}\b", "", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_date(value: str = "") -> datetime | None:
    text = clean_text(value)
    if not text:
        return None

    formats = ["%Y%m%d", "%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"]
    for date_format in formats:
        try:
            return datetime.strptime(text[:10], date_format)
        except ValueError:
            continue
    return None


def website_domain(value: str = "") -> str:
    text = clean_text(value).lower()
    text = re.sub(r"^https?://", "", text)
    text = text.split("/", 1)[0]
    return text.removeprefix("www.")


def buyer_from_csv_row(row: dict[str, str], source: str) -> BuyerProfile | None:
    name = value_for(row, "name", "buyer name", "contact name", "full name", "first name")
    company = value_for(row, "company", "business", "builder", "buyer company", "llc", "entity")
    email = value_for(row, "email", "email address", "contact email")
    website = value_for(row, "website", "url", "site")
    phone_values = [
        value
        for key, value in row.items()
        if re.search(r"(phone|mobile|cell|wireless|contact)", key or "", re.IGNORECASE)
    ]
    phones = unique_phones(phone_values)

    if not any([name, company, email, website, phones]):
        return None

    social_values = [
        value
        for key, value in row.items()
        if re.search(r"(social|linkedin|facebook|instagram|twitter|x profile|profile)", key or "", re.IGNORECASE)
    ]

    return sanitize_buyer(
        BuyerProfile(
            name=name,
            company=company,
            phone=phones[0] if phones else "",
            phones=phones,
            email=email,
            website=website,
            socialLinks=split_values(first_present(*social_values)),
            counties=split_values(value_for(row, "counties", "county", "markets", "market", "areas")),
            zipCodes=extract_zips(value_for(row, "zip codes", "zips", "zip", "zipcodes", "postal codes", "buy box zips")),
            priceMin=value_for(row, "price min", "min price", "minimum price", "low price", "min"),
            priceMax=value_for(row, "price max", "max price", "maximum price", "high price", "max"),
            propertyTypes=split_values(value_for(row, "property types", "property type", "asset type", "strategy", "buy box")),
            fundingType=value_for(row, "funding", "funding type", "cash", "financing"),
            builderType=value_for(row, "builder type", "investor type", "buyer type", "strategy type"),
            activityStatus=value_for(row, "activity", "activity status", "status") or "warm",
            relationshipTier=value_for(row, "tier", "relationship tier", "buyer tier") or "C",
            pastDealsBought=value_for(row, "past deals", "deals bought", "bought", "purchase count"),
            assignmentFeeTolerance=value_for(row, "assignment fee", "fee tolerance", "assignment fee tolerance"),
            notes=value_for(row, "notes", "comments", "description"),
            source=source,
        )
    )


def score_buyer_for_deal(buyer: BuyerProfile, deal: DealMatchRequest) -> BuyerMatch:
    score = 0
    reasons: list[str] = []
    deal_zip = clean_text(deal.zipCode) or first_present(*extract_zips(deal.address))
    deal_county = normalize_key(deal.county)
    deal_price = money_number(deal.price)
    deal_type = normalize_key(deal.propertyType)

    buyer_zips = {zip_code[:5] for zip_code in buyer.zipCodes}
    buyer_counties = {normalize_key(county).replace("county", "").strip() for county in buyer.counties}

    if deal_zip and deal_zip in buyer_zips:
        score += 35
        reasons.append(f"ZIP match: {deal_zip}")
    elif deal_county and deal_county.replace("county", "").strip() in buyer_counties:
        score += 25
        reasons.append(f"County match: {deal.county}")
    elif not buyer_zips and not buyer_counties:
        score += 6
        reasons.append("Open geography")

    min_price = money_number(buyer.priceMin)
    max_price = money_number(buyer.priceMax)
    if deal_price and (min_price or max_price):
        if (not min_price or deal_price >= min_price) and (not max_price or deal_price <= max_price):
            score += 20
            reasons.append("Price in buy box")
        elif max_price and deal_price <= max_price * 1.15:
            score += 10
            reasons.append("Near max price")
    elif not min_price and not max_price:
        score += 8
        reasons.append("No price cap")

    buyer_types = {normalize_key(item) for item in buyer.propertyTypes}
    if deal_type and any(deal_type in item or item in deal_type for item in buyer_types):
        score += 15
        reasons.append(f"Property type match: {deal.propertyType}")
    elif not buyer_types:
        score += 7
        reasons.append("Flexible property type")

    funding = normalize_key(buyer.fundingType)
    if any(word in funding for word in ["cash", "pof", "proof"]):
        score += 10
        reasons.append("Strong funding")
    elif "hard money" in funding or "private" in funding:
        score += 8
        reasons.append("Funded buyer")
    elif funding:
        score += 4

    activity = normalize_key(buyer.activityStatus)
    if activity in {"hot", "active"}:
        score += 10
        reasons.append("Hot buyer")
    elif activity == "warm":
        score += 6
        reasons.append("Warm buyer")

    tier = clean_text(buyer.relationshipTier).upper()
    tier_points = {"A": 10, "B": 7, "C": 4}.get(tier, 0)
    if tier_points:
        score += tier_points
        reasons.append(f"Tier {tier}")

    past_deals = int_number(buyer.pastDealsBought)
    if past_deals:
        score += min(10, past_deals * 2)
        reasons.append(f"{past_deals} past deal{'' if past_deals == 1 else 's'}")

    builder_type = normalize_key(buyer.builderType)
    rehab_level = normalize_key(deal.rehabLevel)
    if rehab_level and any(word in builder_type for word in ["flip", "infill", "builder"]):
        score += 5
        reasons.append("Rehab/build fit")

    return BuyerMatch(buyer=buyer, score=min(score, 100), reasons=reasons[:6])


def save_deal_matches(deal: DealMatchRequest, matches: list[BuyerMatch]) -> None:
    deal_id = clean_text(deal.id) or f"deal-{uuid4().hex[:10]}"

    with get_connection() as connection:
        ensure_buyer_tables(connection)
        placeholder = "%s" if lead_store.USE_POSTGRES else "?"
        connection.execute(f"DELETE FROM deal_buyer_matches WHERE deal_id = {placeholder}", (deal_id,))

        for match in matches[:20]:
            match_id = f"{deal_id}-{match.buyer.id}"
            if lead_store.USE_POSTGRES:
                connection.execute(
                    """
                    INSERT INTO deal_buyer_matches (id, deal_id, buyer_id, score, reasons, payload)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        score = EXCLUDED.score,
                        reasons = EXCLUDED.reasons,
                        payload = EXCLUDED.payload
                    """,
                    (match_id, deal_id, match.buyer.id, match.score, json.dumps(match.reasons), match.model_dump_json()),
                )
            else:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO deal_buyer_matches (id, deal_id, buyer_id, score, reasons, payload)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (match_id, deal_id, match.buyer.id, match.score, json.dumps(match.reasons), match.model_dump_json()),
                )


def enrich_single_buyer_on_save(buyer: BuyerProfile) -> BuyerProfile:
    clean_buyer = sanitize_buyer(buyer)
    if clean_buyer.phones or not is_public_business_candidate(clean_buyer):
        return clean_buyer
    settings = normalize_dcad_settings(DallasCadSettings(enrichmentEnabled=True, maxRecords=1, minBuilderScore=0, rateLimitMs=250))
    return apply_public_candidate_enrichment(clean_buyer, settings, allow_web_lookup=True)


def enrich_imported_buyers(buyers: list[BuyerProfile], max_public_lookups: int = 15) -> list[BuyerProfile]:
    settings = normalize_dcad_settings(
        DallasCadSettings(enrichmentEnabled=True, maxRecords=max_public_lookups, minBuilderScore=0, rateLimitMs=350)
    )
    return apply_public_enrichment_to_candidates(
        [sanitize_buyer(buyer) for buyer in buyers],
        settings,
        max_public_lookups=max_public_lookups,
    )

def enrich_top_buyer_matches(
    matches: list[BuyerMatch],
    saved_buyers: list[BuyerProfile],
    max_public_lookups: int = 6,
) -> tuple[list[BuyerMatch], list[BuyerProfile]]:
    settings = normalize_dcad_settings(
        DallasCadSettings(enrichmentEnabled=True, maxRecords=max_public_lookups, minBuilderScore=0, rateLimitMs=250)
    )
    updated_by_id: dict[str, BuyerProfile] = {}
    lookup_count = 0

    for match in matches[:12]:
        if lookup_count >= max_public_lookups:
            break

        buyer = sanitize_buyer(match.buyer)
        if buyer.phones or not is_public_business_candidate(buyer):
            continue

        lookup_count += 1
        enriched = apply_public_candidate_enrichment(buyer, settings, allow_web_lookup=True)
        if enriched.model_dump() != buyer.model_dump():
            updated_by_id[buyer.id] = enriched

    if not updated_by_id:
        return matches, saved_buyers

    updated_buyers = [updated_by_id.get(buyer.id, buyer) for buyer in saved_buyers]
    updated_matches = [
        match.model_copy(update={"buyer": updated_by_id.get(match.buyer.id, match.buyer)}) for match in matches
    ]
    replace_saved_buyers(updated_buyers)
    return updated_matches, updated_buyers

@router.get("", response_model=list[BuyerProfile])
def list_buyers(current_user: CurrentUser):
    return list_saved_buyers()


@router.post("", response_model=BuyerProfile)
def create_buyer(buyer: BuyerProfile, current_user: CurrentUser):
    return save_buyer(enrich_single_buyer_on_save(buyer))


@router.put("/{buyer_id}", response_model=BuyerProfile)
def update_buyer(buyer_id: str, buyer: BuyerProfile, current_user: CurrentUser):
    return save_buyer(enrich_single_buyer_on_save(buyer.model_copy(update={"id": buyer_id})))


@router.delete("/{buyer_id}")
def delete_buyer(buyer_id: str, current_user: CurrentUser):
    remove_buyer(buyer_id)
    return {"deleted": buyer_id}


@router.post("/sync", response_model=list[BuyerProfile])
def sync_buyers(buyers: list[BuyerProfile], current_user: CurrentUser):
    if not buyers:
        raise HTTPException(status_code=400, detail="Refusing to sync an empty buyer list")
    return replace_saved_buyers(buyers)


@router.post("/import-csv", response_model=BuyerImportResult)
async def import_buyer_csv(current_user: CurrentUser, file: UploadFile = File(...)):
    contents = await file.read()
    result = import_buyers_from_csv(contents, file.filename or "Buyer CSV")
    enriched_imports = enrich_imported_buyers(result.buyers, max_public_lookups=15)

    saved_buyers = list_saved_buyers()
    merged_buyers = merge_buyers(saved_buyers, enriched_imports)
    replace_saved_buyers(merged_buyers)

    return BuyerImportResult(buyers=merged_buyers, warnings=result.warnings)


@router.post("/import-dcad/preview", response_model=DallasCadImportResult)
async def preview_dallas_cad(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    enrichmentEnabled: bool = Form(True),
    maxRecords: int = Form(500),
    minBuilderScore: int = Form(20),
    rateLimitMs: int = Form(750),
):
    settings = normalize_dcad_settings(
        DallasCadSettings(
            enrichmentEnabled=enrichmentEnabled,
            maxRecords=maxRecords,
            minBuilderScore=minBuilderScore,
            rateLimitMs=rateLimitMs,
        )
    )
    contents = await file.read()
    try:
        result = preview_buyers_from_dcad_upload(contents, file.filename or "Dallas CAD Import", settings)
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="Upload a valid Dallas CAD ZIP or CSV file.") from exc

    return save_cad_import_preview(result)


@router.post("/import-dcad/enrich", response_model=DallasCadImportResult)
def refresh_dallas_cad_enrichment(request: DallasCadEnrichmentRequest, current_user: CurrentUser):
    candidates = list_cad_job_candidates(request.jobId)
    if not candidates:
        raise HTTPException(status_code=404, detail="CAD import job was not found or has no candidates.")

    settings = normalize_dcad_settings(
        DallasCadSettings(
            enrichmentEnabled=request.enrichmentEnabled,
            minBuilderScore=request.minBuilderScore,
            rateLimitMs=request.rateLimitMs,
        )
    )
    selected_ids = set(clean_list(request.selectedBuyerIds))
    updated = apply_public_enrichment_to_candidates(
        candidates,
        settings,
        selected_ids=selected_ids if selected_ids else None,
        max_public_lookups=PUBLIC_LOOKUP_REFRESH_LIMIT,
    )
    with get_connection() as connection:
        ensure_buyer_tables(connection)
        for buyer in updated:
            save_cad_candidate(connection, request.jobId, buyer, imported=False)
            save_candidate_contact_sources(connection, request.jobId, buyer)
        if lead_store.USE_POSTGRES:
            connection.execute(
                "UPDATE cad_import_jobs SET status = %s, updated_at = now() WHERE id = %s",
                ("enriched", request.jobId),
            )
        else:
            connection.execute(
                "UPDATE cad_import_jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                ("enriched", request.jobId),
            )

    result = DallasCadImportResult(
        jobId=request.jobId,
        status="enriched",
        buyers=updated,
        candidatesFound=len(updated),
        highScoreCount=sum(1 for buyer in updated if buyer.builderScore >= 70),
        settings=settings.model_dump(),
    )
    return result


@router.post("/import-dcad/import", response_model=DallasCadImportResult)
def import_selected_dallas_cad(request: DallasCadApplyRequest, current_user: CurrentUser):
    return import_selected_cad_buyers(request.jobId, request.selectedBuyerIds)


@router.post("/import-dcad", response_model=DallasCadImportResult)
async def import_dallas_cad(current_user: CurrentUser, file: UploadFile = File(...)):
    contents = await file.read()
    try:
        preview = preview_buyers_from_dcad_upload(
            contents,
            file.filename or "Dallas CAD Import",
            normalize_dcad_settings(DallasCadSettings()),
        )
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="Upload a valid Dallas CAD ZIP or CSV file.") from exc

    existing_buyers = list_saved_buyers()
    merged_buyers, new_count, duplicates_skipped = merge_dcad_buyers(existing_buyers, preview.buyers)
    if new_count:
        replace_saved_buyers(merged_buyers)

    return preview.model_copy(
        update={
            "status": "imported",
            "buyers": merged_buyers,
            "newBuyers": new_count,
            "duplicatesSkipped": duplicates_skipped,
        }
    )


@router.post("/enrich-public", response_model=BuyerPublicEnrichmentResult)
def enrich_saved_buyer_contacts(request: BuyerPublicEnrichmentRequest, current_user: CurrentUser):
    buyers = list_saved_buyers()
    selected_ids = set(clean_list(request.selectedBuyerIds))
    max_buyers = min(100, max(1, int_number(str(request.maxBuyers)) or 40))
    min_score = min(100, max(0, int_number(str(request.minBuilderScore))))
    settings = normalize_dcad_settings(
        DallasCadSettings(
            enrichmentEnabled=True,
            maxRecords=max_buyers,
            minBuilderScore=min_score,
            rateLimitMs=request.rateLimitMs,
        )
    )

    checked_count = 0
    updated_count = 0
    phones_found = 0
    enriched_buyers: list[BuyerProfile] = []

    for buyer in buyers:
        should_check = (
            checked_count < max_buyers
            and not buyer.phones
            and (not selected_ids or buyer.id in selected_ids)
            and buyer.builderScore >= min_score
            and is_public_business_candidate(buyer)
        )
        if not should_check:
            enriched_buyers.append(buyer)
            continue

        checked_count += 1
        before_phones = set(buyer.phones)
        enriched = apply_public_candidate_enrichment(buyer, settings, allow_web_lookup=True)
        new_phones = set(enriched.phones) - before_phones
        if enriched.model_dump() != buyer.model_dump():
            updated_count += 1
        phones_found += len(new_phones)
        enriched_buyers.append(enriched)

    if checked_count:
        replace_saved_buyers(enriched_buyers)

    return BuyerPublicEnrichmentResult(
        buyers=enriched_buyers,
        checkedCount=checked_count,
        updatedCount=updated_count,
        phonesFound=phones_found,
    )


@router.post("/match", response_model=list[BuyerMatch])
def match_buyers(deal: DealMatchRequest, current_user: CurrentUser):
    buyers = list_saved_buyers()
    matches = [score_buyer_for_deal(buyer, deal) for buyer in buyers]
    matches = [match for match in matches if match.score > 0]
    matches.sort(key=lambda match: match.score, reverse=True)
    matches, buyers = enrich_top_buyer_matches(matches, buyers)
    save_deal_matches(deal, matches)
    return matches[:25]


def merge_buyers(existing_buyers: list[BuyerProfile], imported_buyers: list[BuyerProfile]) -> list[BuyerProfile]:
    merged = {buyer_key(buyer): buyer for buyer in existing_buyers}

    for buyer in imported_buyers:
        key = buyer_key(buyer)
        current = merged.get(key)
        if not current:
            merged[key] = buyer
            continue

        merged[key] = sanitize_buyer(
            current.model_copy(
                update={
                    "name": current.name or buyer.name,
                    "company": current.company or buyer.company,
                    "phones": unique_phones([*current.phones, *buyer.phones]),
                    "email": current.email or buyer.email,
                    "website": current.website or buyer.website,
                    "linkedinUrl": current.linkedinUrl or buyer.linkedinUrl,
                    "facebookUrl": current.facebookUrl or buyer.facebookUrl,
                    "contactFormUrl": current.contactFormUrl or buyer.contactFormUrl,
                    "socialLinks": clean_list([*current.socialLinks, *buyer.socialLinks, buyer.linkedinUrl, buyer.facebookUrl]),
                    "counties": clean_list([*current.counties, *buyer.counties]),
                    "zipCodes": unique_zips([*current.zipCodes, *buyer.zipCodes]),
                    "propertyTypes": clean_list([*current.propertyTypes, *buyer.propertyTypes]),
                    "priceMin": current.priceMin or buyer.priceMin,
                    "priceMax": current.priceMax or buyer.priceMax,
                    "fundingType": current.fundingType or buyer.fundingType,
                    "builderType": current.builderType or buyer.builderType,
                    "activityStatus": current.activityStatus or buyer.activityStatus,
                    "relationshipTier": current.relationshipTier or buyer.relationshipTier,
                    "pastDealsBought": current.pastDealsBought or buyer.pastDealsBought,
                    "assignmentFeeTolerance": current.assignmentFeeTolerance or buyer.assignmentFeeTolerance,
                    "mailingAddress": current.mailingAddress or buyer.mailingAddress,
                    "registeredAgent": current.registeredAgent or buyer.registeredAgent,
                    "confidenceScore": max(current.confidenceScore, buyer.confidenceScore),
                    "notes": current.notes or buyer.notes,
                    "source": current.source or buyer.source,
                    "sourceUrls": clean_list([*current.sourceUrls, *buyer.sourceUrls]),
                }
            )
        )

    return list(merged.values())


def buyer_key(buyer: BuyerProfile) -> str:
    return normalize_key(first_present(buyer.email, buyer.phone, buyer.company, buyer.name, buyer.id))


def decode_csv(contents: bytes) -> str:
    for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            return contents.decode(encoding)
        except UnicodeDecodeError:
            continue
    return contents.decode("utf-8", errors="ignore")


def value_for(row: dict[str, str], *fields: str) -> str:
    lookup = {normalize_key(key): clean_text(value) for key, value in row.items()}

    for field in fields:
        value = lookup.get(normalize_key(field))
        if value:
            return value

    return ""


def first_present(*values: str) -> str:
    return next((clean_text(value) for value in values if clean_text(value)), "")


def clean_text(value: object = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    if re.fullmatch(r"\d+\.0", text):
        return text[:-2]
    return re.sub(r"\s+", " ", text)


def clean_list(values: list[str]) -> list[str]:
    seen: set[str] = set()
    cleaned: list[str] = []

    for value in values:
        for item in split_values(value):
            key = normalize_key(item)
            if not key or key in seen:
                continue
            seen.add(key)
            cleaned.append(item)

    return cleaned


def split_values(value: str) -> list[str]:
    return [clean_text(item) for item in re.split(r"[,;|\n]+", clean_text(value)) if clean_text(item)]


def extract_zips(value: str) -> list[str]:
    return unique_zips(re.findall(r"\b\d{5}(?:-\d{4})?\b", clean_text(value)))


def unique_zips(values: list[str]) -> list[str]:
    seen: set[str] = set()
    zips: list[str] = []

    for value in values:
        for zip_code in re.findall(r"\b\d{5}(?:-\d{4})?\b", clean_text(value)):
            key = zip_code[:5]
            if key in seen:
                continue
            seen.add(key)
            zips.append(key)

    return zips


def unique_phones(values: list[str]) -> list[str]:
    phones: list[str] = []
    seen: set[str] = set()

    for value in values:
        for match in re.findall(r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)", clean_text(value)):
            digits = re.sub(r"\D", "", match)
            digits = digits[1:] if len(digits) == 11 and digits.startswith("1") else digits
            if len(digits) != 10 or digits in seen:
                continue
            seen.add(digits)
            phones.append(digits)

    return phones


def dedupe_buyers(buyers: list[BuyerProfile]) -> list[BuyerProfile]:
    deduped: dict[str, BuyerProfile] = {}

    for buyer in buyers:
        deduped[buyer_key(buyer)] = buyer

    return list(deduped.values())


def normalize_key(value: str = "") -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean_text(value).lower()).strip()


def money_number(value: str = "") -> float:
    cleaned = re.sub(r"[^0-9.]", "", clean_text(value))
    if not cleaned:
        return 0

    try:
        return float(cleaned)
    except ValueError:
        return 0


def int_number(value: str = "") -> int:
    cleaned = re.sub(r"[^0-9]", "", clean_text(value))
    return int(cleaned) if cleaned else 0
