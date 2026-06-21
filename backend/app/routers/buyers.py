import csv
import io
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timedelta
from statistics import mean
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
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
    buyers: list[BuyerProfile]
    newBuyers: int = 0
    duplicatesSkipped: int = 0
    candidatesFound: int = 0
    propertyRowsRead: int = 0
    highScoreCount: int = 0
    warnings: list[str] = Field(default_factory=list)


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
        else:
            connection.execute(
                "INSERT OR REPLACE INTO buyers (id, payload) VALUES (?, ?)",
                (clean_buyer.id, clean_buyer.model_dump_json()),
            )
            upsert_buyer_side_tables(connection, clean_buyer, "?")

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
            else:
                connection.execute(
                    "INSERT INTO buyers (id, payload) VALUES (?, ?)",
                    (buyer.id, buyer.model_dump_json()),
                )
                upsert_buyer_side_tables(connection, buyer, "?")

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


def remove_buyer(buyer_id: str) -> None:
    with get_connection() as connection:
        ensure_buyer_tables(connection)
        placeholder = "%s" if lead_store.USE_POSTGRES else "?"
        for table in ["deal_buyer_matches", "buyer_activity", "buyer_contacts", "buyer_criteria", "buyer_locations"]:
            column = "buyer_id"
            connection.execute(f"DELETE FROM {table} WHERE {column} = {placeholder}", (buyer_id,))
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


def import_buyers_from_dcad_zip(file_obj, source: str) -> DallasCadImportResult:
    warnings: list[str] = []
    groups: dict[str, dict] = {}
    account_to_group: dict[str, str] = {}
    property_rows_read = 0

    with zipfile.ZipFile(file_obj) as archive:
        account_entry = find_zip_entry(archive, "ACCOUNT_INFO.CSV")
        appraisal_entry = find_zip_entry(archive, "ACCOUNT_APPRL_YEAR.CSV")
        land_entry = find_zip_entry(archive, "LAND.CSV")

        if not account_entry:
            return DallasCadImportResult(
                buyers=[],
                warnings=["ACCOUNT_INFO.CSV was not found in the Dallas CAD ZIP."],
            )

        for row in iter_zip_csv(archive, account_entry):
            property_rows_read += 1
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
    cad_buyers = [buyer for buyer in cad_buyers if buyer.builderScore >= 20]
    cad_buyers.sort(key=lambda buyer: buyer.builderScore, reverse=True)

    existing_buyers = list_saved_buyers()
    merged_buyers, new_count, duplicates_skipped = merge_dcad_buyers(existing_buyers, cad_buyers)
    if new_count:
        replace_saved_buyers(merged_buyers)

    return DallasCadImportResult(
        buyers=merged_buyers,
        newBuyers=new_count,
        duplicatesSkipped=duplicates_skipped,
        candidatesFound=len(cad_buyers),
        propertyRowsRead=property_rows_read,
        highScoreCount=sum(1 for buyer in cad_buyers if buyer.builderScore >= 70),
        warnings=warnings,
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


@router.get("", response_model=list[BuyerProfile])
def list_buyers(current_user: CurrentUser):
    return list_saved_buyers()


@router.post("", response_model=BuyerProfile)
def create_buyer(buyer: BuyerProfile, current_user: CurrentUser):
    return save_buyer(buyer)


@router.put("/{buyer_id}", response_model=BuyerProfile)
def update_buyer(buyer_id: str, buyer: BuyerProfile, current_user: CurrentUser):
    return save_buyer(buyer.model_copy(update={"id": buyer_id}))


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

    saved_buyers = list_saved_buyers()
    merged_buyers = merge_buyers(saved_buyers, result.buyers)
    replace_saved_buyers(merged_buyers)

    return BuyerImportResult(buyers=merged_buyers, warnings=result.warnings)


@router.post("/import-dcad", response_model=DallasCadImportResult)
async def import_dallas_cad(current_user: CurrentUser, file: UploadFile = File(...)):
    await file.seek(0)
    try:
        return import_buyers_from_dcad_zip(file.file, file.filename or "Dallas CAD ZIP")
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="Upload a valid Dallas CAD ZIP file.") from exc


@router.post("/match", response_model=list[BuyerMatch])
def match_buyers(deal: DealMatchRequest, current_user: CurrentUser):
    buyers = list_saved_buyers()
    matches = [score_buyer_for_deal(buyer, deal) for buyer in buyers]
    matches = [match for match in matches if match.score > 0]
    matches.sort(key=lambda match: match.score, reverse=True)
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
                    "socialLinks": clean_list([*current.socialLinks, *buyer.socialLinks]),
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
                    "notes": current.notes or buyer.notes,
                    "source": current.source or buyer.source,
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
