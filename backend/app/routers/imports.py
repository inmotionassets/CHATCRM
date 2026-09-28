import csv
import io
import re
from uuid import NAMESPACE_URL, uuid5

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from pypdf import PdfReader

from ..auth import CurrentUser
from . import leads as lead_store

router = APIRouter(prefix="/imports", tags=["imports"])


class ParsedLead(BaseModel):
    name: str
    address: str
    parcelNumber: str = ""
    county: str = ""
    bedrooms: str = ""
    bathrooms: str = ""
    sqft: str = ""
    yearBuilt: str = ""
    lotSize: str = ""
    phone: str = ""
    phones: list[str] = Field(default_factory=list)
    email: str = ""
    source: str
    confidence: int
    notes: str
    estimatedArv: str = ""
    assessedValue: str = ""


class ParseResult(BaseModel):
    file_name: str
    pages: int
    text_length: int
    leads: list[ParsedLead]
    warnings: list[str]


class CsvMergeResult(BaseModel):
    fileName: str
    parsedCount: int
    addedCount: int
    updatedCount: int
    duplicateCount: int
    finalCount: int
    warnings: list[str] = Field(default_factory=list)


@router.post("/parse-pdf", response_model=ParseResult)
async def parse_pdf(current_user: CurrentUser, file: UploadFile = File(...)):
    contents = await file.read()
    page_texts, warnings = extract_pdf_page_texts(contents)
    text = "\n".join(page_texts)
    pages = len(page_texts)
    leads = extract_wide_export_leads(page_texts, file.filename or "uploaded.pdf") or extract_leads(text, file.filename or "uploaded.pdf")

    if text.strip() and not leads:
        warnings.append("Text was found, but no clear lead rows were detected.")

    if not text.strip():
        warnings.append("No readable text found. This PDF may be scanned and need OCR.")

    return ParseResult(
        file_name=file.filename or "uploaded.pdf",
        pages=pages,
        text_length=len(text),
        leads=leads,
        warnings=warnings,
    )


@router.post("/parse-csv", response_model=ParseResult)
async def parse_csv(current_user: CurrentUser, file: UploadFile = File(...)):
    contents = await file.read()
    text = decode_csv(contents)
    leads, warnings = extract_csv_leads(text, file.filename or "uploaded.csv")

    if text.strip() and not leads:
        warnings.append("CSV text was found, but no clear property rows were detected.")

    return ParseResult(
        file_name=file.filename or "uploaded.csv",
        pages=1,
        text_length=len(text),
        leads=leads,
        warnings=warnings,
    )


@router.post("/merge-csv", response_model=CsvMergeResult)
async def merge_csv(current_user: CurrentUser, file: UploadFile = File(...)):
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    file_name = file.filename or "uploaded.csv"
    text = decode_csv(await file.read())
    parsed_leads, warnings = extract_csv_leads(text, file_name)
    if not parsed_leads:
        raise HTTPException(status_code=400, detail="No valid property leads were found in this CSV")

    existing_leads = lead_store.list_saved_leads()
    changed_leads, added_count, updated_count, duplicate_count = merge_csv_leads(
        existing_leads,
        parsed_leads,
        file_name,
    )
    lead_store.save_leads(changed_leads, allow_fallback=False)
    return CsvMergeResult(
        fileName=file_name,
        parsedCount=len(parsed_leads),
        addedCount=added_count,
        updatedCount=updated_count,
        duplicateCount=duplicate_count,
        finalCount=len(existing_leads) + added_count,
        warnings=warnings,
    )


def extract_pdf_text(contents: bytes) -> tuple[str, int, list[str]]:
    page_texts, warnings = extract_pdf_page_texts(contents)
    return "\n".join(page_texts), len(page_texts), warnings


def extract_pdf_page_texts(contents: bytes) -> tuple[list[str], list[str]]:
    warnings: list[str] = []

    try:
        reader = PdfReader(io.BytesIO(contents))
    except Exception:
        return [], ["The file could not be opened as a PDF."]

    page_text: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            page_text.append(page.extract_text() or "")
        except Exception:
            warnings.append(f"Page {index} could not be read.")

    return page_text, warnings


def extract_wide_export_leads(page_texts: list[str], source: str) -> list[ParsedLead]:
    owner_start = first_page_index(page_texts, "Owner 1 First Name")
    if owner_start <= 0:
        return []

    phone_start = first_page_index(page_texts[owner_start + 1 :], "Phone 1")
    phone_start = owner_start + 1 + phone_start if phone_start != -1 else -1
    group_size = phone_start - owner_start if phone_start > owner_start else owner_start

    if group_size <= 0:
        return []

    leads: list[ParsedLead] = []

    for page_offset in range(group_size):
        address_page_index = page_offset
        owner_page_index = owner_start + page_offset
        phone_page_index = phone_start + page_offset if phone_start != -1 else -1
        extra_phone_page_index = phone_start + group_size + page_offset if phone_start != -1 else -1

        if address_page_index >= len(page_texts) or owner_page_index >= len(page_texts):
            continue

        address_rows = extract_wide_address_rows(page_texts[address_page_index])
        owner_rows = extract_wide_text_rows(page_texts[owner_page_index])
        phone_rows = extract_wide_text_rows(page_texts[phone_page_index]) if phone_page_index < len(page_texts) else []
        extra_phone_rows = extract_wide_text_rows(page_texts[extra_phone_page_index]) if extra_phone_page_index < len(page_texts) else []
        owner_rows_aligned = len(owner_rows) == len(address_rows)
        phone_rows_aligned = not phone_rows or len(phone_rows) == len(address_rows)
        extra_phone_rows_aligned = not extra_phone_rows or len(extra_phone_rows) == len(address_rows)

        for row_index, row in enumerate(address_rows):
            owner_line = owner_rows[row_index] if owner_rows_aligned else ""
            phone_line = phone_rows[row_index] if phone_rows_aligned and row_index < len(phone_rows) else ""
            extra_phone_line = extra_phone_rows[row_index] if extra_phone_rows_aligned and row_index < len(extra_phone_rows) else ""
            name = build_wide_owner_name(owner_line, phone_line)
            phones = unique_phones(find_phones(phone_line) + find_phones(extra_phone_line))
            confidence = 75 if owner_rows_aligned else 55

            if name != "Unknown Owner":
                confidence += 10
            if phones:
                confidence += 10

            leads.append(
                ParsedLead(
                    name=name,
                    address=row["address"],
                    parcelNumber=row["parcelNumber"],
                    county=row["county"],
                    phone=phones[0] if phones else "",
                    phones=phones,
                    email="",
                    source=source,
                    confidence=min(confidence, 95),
                    notes="",
                )
            )

    return dedupe_leads(leads)


def first_page_index(page_texts: list[str], marker: str) -> int:
    marker_lower = marker.lower()
    for index, page_text in enumerate(page_texts):
        if marker_lower in page_text.lower():
            return index
    return -1


def extract_wide_address_rows(page_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    for line in extract_wide_text_rows(page_text):
        address = find_address(line)
        if not address:
            continue

        remaining = line.replace(address, "", 1)
        details = re.search(
            r"\b(?P<state>[A-Z]{2})\s+(?P<zip>\d{5})\s+(?P<county>[A-Za-z ]+?)\s+(?P<apn>[A-Za-z0-9-]{8,})\s+(?:Yes|No)\b",
            remaining,
        )

        rows.append(
            {
                "address": address,
                "county": clean_line(details.group("county")) if details else "",
                "parcelNumber": details.group("apn") if details else "",
            }
        )

    return rows


def extract_wide_text_rows(page_text: str) -> list[str]:
    header_markers = (
        "address unit",
        "owner 1 first name",
        "owner 2 last name",
        "phone 4",
        "email 1",
        "mailing city",
    )
    rows: list[str] = []

    for line in page_text.splitlines():
        row = clean_line(line)
        if not row:
            continue

        if any(marker in row.lower() for marker in header_markers):
            continue

        rows.append(row)

    return rows


def build_wide_owner_name(owner_line: str, phone_line: str = "") -> str:
    owner = clean_owner_line(owner_line)
    if not owner:
        return "Unknown Owner"

    leading_last_name = leading_phone_owner_name(phone_line)
    parts = owner.split()

    if leading_last_name and len(parts) >= 3:
        owner_one = " ".join(parts[:-1])
        owner_two = f"{parts[-1]} {leading_last_name}"
        return f"{owner_one} / {owner_two}"

    return owner


def clean_owner_line(value: str) -> str:
    owner = clean_line(value)
    owner = re.sub(r"\s+", " ", owner).strip(" ,")
    return owner if is_probable_owner_name(owner) else ""


def leading_phone_owner_name(phone_line: str) -> str:
    before_phone = PHONE_RE.split(phone_line, maxsplit=1)[0]
    before_phone = re.sub(r"\s*[-,]\s*$", "", before_phone).strip()

    if not before_phone:
        return ""

    if not re.fullmatch(r"[A-Za-z][A-Za-z.'-]*(?:\s+[A-Za-z][A-Za-z.'-]*)?", before_phone):
        return ""

    return before_phone if is_probable_owner_name(before_phone) else ""


def extract_leads(text: str, source: str) -> list[ParsedLead]:
    lines = [clean_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line]
    leads: list[ParsedLead] = []
    address_rows = [(index, find_address(line)) for index, line in enumerate(lines)]
    address_rows = [(index, address) for index, address in address_rows if address]

    for row_number, (index, address) in enumerate(address_rows):
        next_index = address_rows[row_number + 1][0] if row_number + 1 < len(address_rows) else len(lines)
        name_context = " ".join(lines[max(0, index - 6) : min(len(lines), index + 3)])
        record_context = " ".join(lines[index: min(len(lines), next_index)])
        name = find_name(name_context, address)
        phones = find_phones(record_context)
        phone = phones[0] if phones else ""
        email = find_first(EMAIL_RE, record_context)
        confidence = 70

        if phone:
            confidence += 10
        if email:
            confidence += 10
        if name != "Unknown Owner":
            confidence += 10

        leads.append(
            ParsedLead(
                name=name,
                address=address,
                phone=phone,
                phones=phones,
                email=email,
                source=source,
                confidence=min(confidence, 95),
                notes="",
            )
        )

    return dedupe_leads(leads)


def decode_csv(contents: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return contents.decode(encoding)
        except UnicodeDecodeError:
            continue
    return contents.decode("utf-8", errors="ignore")


def extract_csv_leads(text: str, source: str) -> tuple[list[ParsedLead], list[str]]:
    warnings: list[str] = []
    text = normalize_csv_text(text)
    lines = [line for line in text.splitlines() if line.strip()]
    header_index = find_csv_header_index(lines)

    if header_index == -1:
        return [], ["Could not find a CSV header row with Address columns."]

    reader = csv.DictReader(lines[header_index:])
    leads: list[ParsedLead] = []

    for row in reader:
        lead = parsed_lead_from_csv_row(row, source)
        if lead:
            leads.append(lead)

    return dedupe_leads(leads), warnings


def normalize_csv_text(text: str) -> str:
    replacements = {
        ",Garage, Detached,": ",Garage Detached,",
        ",Garage, Attached,": ",Garage Attached,",
        ",Garage, Built-in,": ",Garage Built-in,",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def find_csv_header_index(lines: list[str]) -> int:
    for index, line in enumerate(lines[:10]):
        header = [part.strip().lower() for part in next(csv.reader([line]))]
        if "address" in header and ("city" in header or "county" in header):
            return index
    return -1


def parsed_lead_from_csv_row(row: dict[str, str], source: str) -> ParsedLead | None:
    address = value_for(row, "Address")
    city = value_for(row, "City")
    state = value_for(row, "State")

    if not address:
        return None

    full_address = clean_address_parts(address, city, state)
    owner_name = first_present(
        value_for(row, "Owner 1 Full Name"),
        " ".join(part for part in [value_for(row, "Owner 1 First Name"), value_for(row, "Owner 1 Last Name")] if part).strip(),
        value_for(row, "Mailing Care of Name"),
        "Unknown Owner",
    )
    phones = phones_from_csv_row(row)
    emails = [value_for(row, f"Email {index}") for index in range(1, 5)]
    email = next((item for item in emails if item), "")
    confidence = 75

    if phones:
        confidence += 10
    if email:
        confidence += 5
    if owner_name != "Unknown Owner":
        confidence += 5

    return ParsedLead(
        name=owner_name,
        address=full_address,
        parcelNumber=first_present(value_for(row, "APN"), value_for(row, "Id")),
        county=value_for(row, "County"),
        bedrooms=first_present(value_for(row, "Bedrooms"), value_for(row, "Beds")),
        bathrooms=first_present(value_for(row, "Total Bathrooms"), value_for(row, "Bathrooms")),
        sqft=first_present(value_for(row, "Building Sqft"), value_for(row, "Living Square Feet")),
        yearBuilt=value_for(row, "Year Built"),
        lotSize=first_present(value_for(row, "Lot Size Sqft"), value_for(row, "Lot (Square Feet)")),
        phone=phones[0] if phones else "",
        phones=phones,
        email=email,
        source=source,
        confidence=min(confidence, 95),
        notes="",
        estimatedArv=first_present(value_for(row, "Est. Value"), value_for(row, "Total Assessed Value")),
        assessedValue=value_for(row, "Total Assessed Value"),
    )


def clean_address_parts(address: str, city: str, state: str) -> str:
    parts = [address.strip()]
    if city and city.lower() not in address.lower():
        parts.append(city.strip().title())
    if state and state.lower() not in address.lower():
        parts.append(state.strip().upper())
    return " ".join(parts)


def phones_from_csv_row(row: dict[str, str]) -> list[str]:
    phones: list[str] = []

    for key, value in row.items():
        if re.search(r"(phone|wireless|landline)", key or "", re.IGNORECASE):
            phones.extend(find_phones(value or ""))

    return unique_phones(phones)


def value_for(row: dict[str, str], field: str) -> str:
    value = row.get(field, "")
    return clean_csv_value(value)


def clean_csv_value(value: str | None) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    if re.fullmatch(r"\d+\.0", text):
        return text[:-2]
    return text


def first_present(*values: str) -> str:
    return next((value for value in values if value), "")


ADDRESS_RE = re.compile(
    r"\b\d{2,6}\s+[A-Za-z0-9 .'-]+?\s+"
    r"(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Blvd|Boulevard|Ct|Court|Cir|Circle|Way|Pkwy|Parkway|Pl|Place)\b"
    r"(?:\.|,\s*[A-Za-z .'-]+)?",
    re.IGNORECASE,
)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def find_address(text: str) -> str:
    match = ADDRESS_RE.search(text)
    return match.group(0).strip(" ,") if match else ""


def find_first(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(0) if match else ""


def find_phones(text: str) -> list[str]:
    phones: list[str] = []
    seen: set[str] = set()

    for match in PHONE_RE.finditer(text):
        phone = match.group(0)
        digits = re.sub(r"\D", "", phone)
        normalized = digits[1:] if len(digits) == 11 and digits.startswith("1") else digits

        if len(normalized) == 10 and normalized[0] in "23456789" and normalized[3] in "23456789":
            if normalized not in seen:
                seen.add(normalized)
                phones.append(phone)

    return phones


def unique_phones(values: list[str]) -> list[str]:
    phones: list[str] = []
    seen: set[str] = set()

    for phone in values:
        digits = re.sub(r"\D", "", phone)
        normalized = digits[1:] if len(digits) == 11 and digits.startswith("1") else digits
        if normalized and normalized not in seen:
            seen.add(normalized)
            phones.append(phone)

    return phones


def find_name(context: str, address: str) -> str:
    before_address = context.split(address)[0]
    candidates = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b", before_address)
    candidates = [candidate for candidate in candidates if is_probable_owner_name(candidate)]
    return candidates[-1] if candidates else "Unknown Owner"


def is_probable_owner_name(candidate: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", candidate.lower()).strip()
    blocked = {
        "address",
        "address unit",
        "apn owner",
        "balch springs",
        "cedar hill",
        "city state",
        "city state zip",
        "county record",
        "dallas",
        "duncanville",
        "garland",
        "grand prairie",
        "hutchins",
        "irving",
        "lancaster",
        "mesquite",
        "owner name",
        "owner oc",
        "owner occupied",
        "property address",
        "rowlett",
        "sachse",
        "seagoville",
        "tax list",
        "unit city",
        "zip county",
    }
    street_words = re.compile(
        r"\b(st|street|dr|drive|rd|road|ave|avenue|ln|lane|ct|court|cir|circle|blvd|boulevard|pkwy|parkway|pl|place|way)\b",
        re.IGNORECASE,
    )

    if normalized in blocked:
        return False

    if street_words.search(candidate):
        return False

    return bool(candidate.strip())


def dedupe_leads(leads: list[ParsedLead], limit: int | None = None) -> list[ParsedLead]:
    seen: set[str] = set()
    unique: list[ParsedLead] = []

    for lead in leads:
        key = lead.address.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(lead)

    return unique[:limit] if limit else unique


def normalize_import_apn(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean_csv_value(value).lower())


def normalize_import_address(value: str) -> str:
    normalized = clean_csv_value(value).lower()
    normalized = re.sub(r"\b(?:texas|tx)\b", " ", normalized)
    normalized = re.sub(r"\b\d{5}(?:-\d{4})?\b", " ", normalized)
    replacements = {
        "street": "st", "avenue": "ave", "road": "rd", "drive": "dr",
        "lane": "ln", "court": "ct", "circle": "cir", "boulevard": "blvd",
        "parkway": "pkwy", "place": "pl", "trail": "trl",
    }
    words = re.sub(r"[^a-z0-9]+", " ", normalized).split()
    return " ".join(replacements.get(word, word) for word in words)


def normalized_phone_key(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    return digits[1:] if len(digits) == 11 and digits.startswith("1") else digits


def merge_import_phones(existing: list[str], incoming: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for phone in [*existing, *incoming]:
        key = normalized_phone_key(phone)
        if len(key) != 10 or key in seen:
            continue
        seen.add(key)
        merged.append(phone.strip())
    return merged


def generic_owner_name(value: str) -> bool:
    return clean_csv_value(value).lower() in {"", "unknown owner", "owner needed", "import review", "review owner"}


def merge_parsed_lead(existing: lead_store.Lead, incoming: ParsedLead) -> lead_store.Lead:
    phones = merge_import_phones(existing.phones or ([existing.phone] if existing.phone else []), incoming.phones)
    updates = {
        "name": incoming.name if generic_owner_name(existing.name) and not generic_owner_name(incoming.name) else existing.name,
        "parcelNumber": existing.parcelNumber or incoming.parcelNumber,
        "county": existing.county or incoming.county,
        "bedrooms": existing.bedrooms or incoming.bedrooms,
        "bathrooms": existing.bathrooms or incoming.bathrooms,
        "sqft": existing.sqft or incoming.sqft,
        "yearBuilt": existing.yearBuilt or incoming.yearBuilt,
        "lotSize": existing.lotSize or incoming.lotSize,
        "phone": phones[0] if phones else existing.phone or incoming.phone,
        "phones": phones,
        "email": existing.email or incoming.email,
        "estimatedArv": existing.estimatedArv or incoming.estimatedArv,
        "assessedValue": existing.assessedValue or incoming.assessedValue,
        "score": max(existing.score, incoming.confidence),
    }
    return existing.model_copy(update=updates)


def lead_from_parsed_csv(incoming: ParsedLead, source: str) -> lead_store.Lead:
    apn_key = normalize_import_apn(incoming.parcelNumber)
    address_key = normalize_import_address(incoming.address)
    stable_key = f"apn:{apn_key}" if apn_key else f"address:{address_key}"
    return lead_store.Lead(
        id=f"import-{uuid5(NAMESPACE_URL, stable_key).hex}",
        name=incoming.name or "Unknown Owner",
        address=incoming.address,
        parcelNumber=incoming.parcelNumber,
        county=incoming.county,
        bedrooms=incoming.bedrooms,
        bathrooms=incoming.bathrooms,
        sqft=incoming.sqft,
        yearBuilt=incoming.yearBuilt,
        lotSize=incoming.lotSize,
        stage="New Lead",
        score=incoming.confidence,
        owner="Import Review",
        source=source,
        phone=incoming.phone,
        phones=incoming.phones,
        email=incoming.email,
        notes=incoming.notes,
        estimatedArv=incoming.estimatedArv,
        assessedValue=incoming.assessedValue,
        needsReview=True,
        contactStatus="needs-review",
    )


def merge_csv_leads(
    existing_leads: list[lead_store.Lead],
    incoming_leads: list[ParsedLead],
    source: str,
) -> tuple[list[lead_store.Lead], int, int, int]:
    by_apn: dict[str, lead_store.Lead] = {}
    by_address: dict[str, lead_store.Lead] = {}
    for lead in existing_leads:
        apn_key = normalize_import_apn(lead.parcelNumber)
        address_key = normalize_import_address(lead.address)
        if apn_key:
            by_apn[apn_key] = lead
        if address_key:
            by_address[address_key] = lead

    changed: dict[str, lead_store.Lead] = {}
    added_ids: set[str] = set()
    updated_ids: set[str] = set()
    duplicate_count = 0

    for incoming in incoming_leads:
        apn_key = normalize_import_apn(incoming.parcelNumber)
        address_key = normalize_import_address(incoming.address)
        current = (by_apn.get(apn_key) if apn_key else None) or (by_address.get(address_key) if address_key else None)
        if current:
            duplicate_count += 1
            merged = merge_parsed_lead(current, incoming)
            if merged.model_dump() != current.model_dump():
                changed[merged.id] = merged
                if merged.id not in added_ids:
                    updated_ids.add(merged.id)
            current = merged
        else:
            current = lead_from_parsed_csv(incoming, source)
            changed[current.id] = current
            added_ids.add(current.id)

        if apn_key:
            by_apn[apn_key] = current
        if address_key:
            by_address[address_key] = current

    return list(changed.values()), len(added_ids), len(updated_ids), duplicate_count
