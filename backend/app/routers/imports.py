import csv
import io
import re

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel, Field
from pypdf import PdfReader

from ..auth import CurrentUser

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


@router.post("/parse-pdf", response_model=ParseResult)
async def parse_pdf(current_user: CurrentUser, file: UploadFile = File(...)):
    contents = await file.read()
    text, pages, warnings = extract_pdf_text(contents)
    leads = extract_leads(text, file.filename or "uploaded.pdf")

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


def extract_pdf_text(contents: bytes) -> tuple[str, int, list[str]]:
    warnings: list[str] = []

    try:
        reader = PdfReader(io.BytesIO(contents))
    except Exception:
        return "", 0, ["The file could not be opened as a PDF."]

    page_text: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            page_text.append(page.extract_text() or "")
        except Exception:
            warnings.append(f"Page {index} could not be read.")

    return "\n".join(page_text), len(reader.pages), warnings


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

    return dedupe_leads(leads, limit=100)


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
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
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
    blocked = {"Tax List", "County Record", "Property Address", "Owner Name"}
    candidates = [candidate for candidate in candidates if candidate not in blocked]
    return candidates[-1] if candidates else "Unknown Owner"


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
