import base64
import hashlib
import hmac
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Iterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

SECRET_KEY = "chatcrm-local-dev-secret-change-before-production"
TOKEN_TTL_SECONDS = 60 * 60 * 12
AGREEMENT_VERSION = "chatcrm-partner-agreement-v2"
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", Path(__file__).resolve().parents[1] / "chatcrm.db"))
RAW_DATABASE_URL = os.getenv("DATABASE_URL", "")
CONTRACTS_PATH = Path(__file__).resolve().parents[1] / "contracts"
CONTRACTS_PATH.mkdir(exist_ok=True)
QUOTE_CACHE: dict[str, object] = {"date": "", "quote": None}


def normalize_database_url(value: str) -> str:
    cleaned = (value or "").strip().strip("\"'")
    if cleaned.lower().startswith("database_url="):
        cleaned = cleaned.split("=", 1)[1].strip().strip("\"'")
    return cleaned


DATABASE_URL = normalize_database_url(RAW_DATABASE_URL)
USE_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))


class User(BaseModel):
    username: str
    name: str
    role: str
    email: str = ""
    profile_complete: bool = False
    agreement_signed: bool = False


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class UserProfile(BaseModel):
    username: str
    name: str = ""
    email: str = ""
    signature: str = ""
    signed_at: str = ""
    agreement_version: str = AGREEMENT_VERSION


class ProfileUpdate(BaseModel):
    name: str
    email: str


class AgreementSignRequest(BaseModel):
    name: str
    email: str
    signature: str
    accepted: bool = False


class AgreementSignResponse(BaseModel):
    user: User
    download_url: str


class DailyQuote(BaseModel):
    quote: str
    author: str = ""
    source: str = "ZenQuotes"


USERS = {
    "virgo": {
        "password_hash": hashlib.sha256("Virgo2026!".encode()).hexdigest(),
        "name": "Virgo Davis",
        "role": "Admin",
    },
    "acq-caller-01": {
        "password_hash": "00745463c0c84317cf5f325166e4fbf688417c7e7811bafccc212332151f39fa",
        "name": "Acquisition Caller 01",
        "role": "Acquisition",
    },
    "acq-caller-02": {
        "password_hash": "99ef9954900de2a1d2a1d60969803dd244b18c2a783d758360ddbfc2a6819a1e",
        "name": "Acquisition Caller 02",
        "role": "Acquisition",
    },
    "acq-caller-03": {
        "password_hash": "f1cbfacdf2cc54ac5b25973836d60a29fabeebbf6d741a2edb11c2abc300b45e",
        "name": "Acquisition Caller 03",
        "role": "Acquisition",
    },
    "acq-caller-04": {
        "password_hash": "1e4c135e14161dcabb2f6f805af2e91a3ac6697bbc35d1f6c9894fc2e90d1a52",
        "name": "Acquisition Caller 04",
        "role": "Acquisition",
    },
    "acq-caller-05": {
        "password_hash": "6c2473e3f314e1fa0329935caf989992195d0e4b9f350c453561069530d1dea6",
        "name": "Acquisition Caller 05",
        "role": "Acquisition",
    },
    "acq-caller-06": {
        "password_hash": "b41e583f24af1979e0144abc57d6c56eb94994a1584152f392477442245f3a5f",
        "name": "Acquisition Caller 06",
        "role": "Acquisition",
    },
    "acq-caller-07": {
        "password_hash": "24d144b5e52eb20627e883743ffc73f14ebe4e97b71068b5a559559514c28499",
        "name": "Acquisition Caller 07",
        "role": "Acquisition",
    },
    "acq-caller-08": {
        "password_hash": "f8b84f7d7ca008c118a4c62bb9ab75df60c5a8a00b7a62aaab9e37d87e3927ac",
        "name": "Acquisition Caller 08",
        "role": "Acquisition",
    },
    "acq-caller-09": {
        "password_hash": "4bceec2584f566454344c000e7e309fa0e082f26b1fe1cfe71e214f92dbe8e4e",
        "name": "Acquisition Caller 09",
        "role": "Acquisition",
    },
    "acq-caller-10": {
        "password_hash": "3ed6a89102902d8c6d8ae39cadf47c36dce12a63104116a8697a4c80a5383a91",
        "name": "Acquisition Caller 10",
        "role": "Acquisition",
    },
    "acq-demo": {
        "password_hash": "709cb6cd3879d510d374ec1bce1a39288311a01a59f17497fba6ae92132f5881",
        "name": "Acquisition Demo",
        "role": "Acquisition",
        "email": "acq-demo@chatcrm.local",
        "profile_complete": True,
        "agreement_signed": True,
    },
}


def postgres_connection_url() -> str:
    if not USE_POSTGRES:
        return DATABASE_URL

    parsed = urlsplit(DATABASE_URL)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.pop("pgbouncer", None)

    if parsed.hostname not in {"localhost", "127.0.0.1"} and "sslmode" not in query:
        query["sslmode"] = "require"

    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


@contextmanager
def get_profile_connection() -> Iterator[object]:
    if USE_POSTGRES:
        import psycopg

        with psycopg.connect(postgres_connection_url(), prepare_threshold=None) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    username TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            yield connection
        return

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS user_profiles (
            username TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def load_profile(username: str) -> UserProfile:
    clean_username = username.lower().strip()
    with get_profile_connection() as connection:
        placeholder = "%s" if USE_POSTGRES else "?"
        row = connection.execute(f"SELECT payload FROM user_profiles WHERE username = {placeholder}", (clean_username,)).fetchone()

    if not row:
        return UserProfile(username=clean_username)

    payload = row[0] if USE_POSTGRES else row["payload"]
    return UserProfile.model_validate(parse_payload(payload) | {"username": clean_username})


def save_profile(profile: UserProfile) -> UserProfile:
    clean_profile = profile.model_copy(update={"username": profile.username.lower().strip()})
    payload = clean_profile.model_dump_json()

    with get_profile_connection() as connection:
        if USE_POSTGRES:
            connection.execute(
                """
                INSERT INTO user_profiles (username, payload)
                VALUES (%s, %s)
                ON CONFLICT (username) DO UPDATE SET payload = EXCLUDED.payload, updated_at = now()
                """,
                (clean_profile.username, payload),
            )
        else:
            connection.execute(
                """
                INSERT OR REPLACE INTO user_profiles (username, payload, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (clean_profile.username, payload),
            )

    return clean_profile


def parse_payload(payload: object) -> dict:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode("utf-8")
    if isinstance(payload, str):
        return json.loads(payload)
    return json.loads(str(payload))


def clean_email(value: str) -> str:
    email = str(value or "").strip()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valid email is required")
    return email


def build_user(username: str) -> User | None:
    clean_username = username.lower().strip()
    record = USERS.get(clean_username)
    if not record:
        return None

    profile = load_profile(clean_username)
    is_admin = record["role"] == "Admin"
    profile_complete = is_admin or bool(record.get("profile_complete")) or bool(profile.name.strip() and profile.email.strip())
    agreement_signed = is_admin or bool(record.get("agreement_signed")) or bool(profile.signature.strip() and profile.signed_at.strip())

    return User(
        username=clean_username,
        name=profile.name.strip() or record["name"],
        role=record["role"],
        email=profile.email.strip() or str(record.get("email", "")),
        profile_complete=profile_complete,
        agreement_signed=agreement_signed,
    )


def create_token(user: User) -> str:
    payload = {
        "agreement_signed": user.agreement_signed,
        "email": user.email,
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
        "name": user.name,
        "profile_complete": user.profile_complete,
        "role": user.role,
        "sub": user.username,
    }
    payload_text = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    payload_part = _b64encode(payload_text.encode())
    signature = hmac.new(SECRET_KEY.encode(), payload_part.encode(), hashlib.sha256).digest()
    return f"{payload_part}.{_b64encode(signature)}"


def authenticate_user(username: str, password: str) -> User | None:
    clean_username = username.lower().strip()
    record = USERS.get(clean_username)
    if not record:
        return None

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if not hmac.compare_digest(password_hash, record["password_hash"]):
        return None

    return build_user(clean_username)


def update_user_profile(username: str, update: ProfileUpdate) -> User:
    clean_username = username.lower().strip()
    existing = load_profile(clean_username)
    profile = existing.model_copy(update={"name": update.name.strip(), "email": clean_email(update.email)})
    save_profile(profile)
    user = build_user(clean_username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def sign_partner_agreement(username: str, request: AgreementSignRequest) -> AgreementSignResponse:
    if not request.accepted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agreement acceptance is required")

    signature = request.signature.strip()
    if len(signature) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Signature is required")

    clean_username = username.lower().strip()
    profile = load_profile(clean_username).model_copy(
        update={
            "name": request.name.strip(),
            "email": clean_email(request.email),
            "signature": signature,
            "signed_at": datetime.now(timezone.utc).isoformat(),
            "agreement_version": AGREEMENT_VERSION,
        }
    )
    save_profile(profile)
    build_signed_partner_pdf(profile)
    user = build_user(clean_username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return AgreementSignResponse(user=user, download_url="/auth/onboarding/agreement")


def signed_agreement_path(username: str) -> Path:
    safe_username = "".join(ch for ch in username.lower().strip() if ch.isalnum() or ch in {"-", "_"}) or "user"
    return CONTRACTS_PATH / f"chatcrm-signed-partner-agreement-{safe_username}.pdf"


def build_signed_partner_pdf(profile: UserProfile) -> Path:
    file_path = signed_agreement_path(profile.username)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="AgreementTitle",
            parent=styles["Heading1"],
            alignment=TA_CENTER,
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#18212f"),
        )
    )
    styles.add(ParagraphStyle(name="SmallNotice", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#64748b")))
    styles.add(ParagraphStyle(name="AgreementBody", parent=styles["BodyText"], fontSize=9.2, leading=12.5))

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )
    story = [
        Paragraph("CHATCRM", styles["AgreementTitle"]),
        Paragraph("One-Page Partner & Acquisition Agreement", styles["AgreementTitle"]),
        Spacer(1, 10),
        Paragraph("Mission: Find more sellers. Contract more deals. Build the largest buyer network in Texas. Scale nationwide.", styles["AgreementBody"]),
        Spacer(1, 10),
    ]

    clauses = [
        ("Confidentiality (NDA)", "All seller lists, buyer lists, lead data, training materials, scripts, processes, and ChatCRM information are confidential and remain property of ChatCRM."),
        ("Non-Circumvention", "Team members may not bypass ChatCRM to work directly with sellers, buyers, investors, builders, or business relationships introduced through the platform."),
        ("Compensation", "Commissions are paid after a successful closing and receipt of funds. ChatCRM will handle compensation and applicable tax reporting requirements."),
        ("Commission Structure", "15% ($0-$9,999) | 20% ($10k-$19,999) | 22.5% ($20k-$34,999) | 25% ($35k+)"),
        ("Caller Responsibilities", "Contact sellers, verify ownership, determine motivation, gather property details, update ChatCRM, and schedule follow-ups."),
    ]
    for title, detail in clauses:
        story.extend([Paragraph(f"<b>{title}</b>", styles["AgreementBody"]), Paragraph(detail, styles["AgreementBody"]), Spacer(1, 7)])

    signed_at = profile.signed_at or datetime.now(timezone.utc).isoformat()
    signature_data = [
        ["Team Member Name", profile.name],
        ["Email", profile.email],
        ["Electronic Signature", profile.signature],
        ["Signed Date", signed_at[:10]],
        ["Agreement Version", profile.agreement_version],
    ]
    table = Table(signature_data, colWidths=[1.75 * inch, 5.0 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef4ff")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1d4ed8")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd8d0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.extend([Spacer(1, 8), table, Spacer(1, 12)])
    story.append(Paragraph("CHATCRM - WE'RE GOING TO THE MOON", styles["SmallNotice"]))
    document.build(story)
    return file_path


def get_daily_quote() -> DailyQuote:
    today = datetime.now(timezone.utc).date().isoformat()
    cached_quote = QUOTE_CACHE.get("quote")
    if QUOTE_CACHE.get("date") == today and isinstance(cached_quote, DailyQuote):
        return cached_quote

    fallback = DailyQuote(quote="Discipline turns opportunity into income.", author="ChatCRM", source="Fallback")
    try:
        request = Request("https://zenquotes.io/api/today", headers={"User-Agent": "ChatCRM/1.0"})
        with urlopen(request, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))
        item = data[0] if isinstance(data, list) and data else data if isinstance(data, dict) else {}
        quote = str(item.get("q") or item.get("quote") or "").strip()
        author = str(item.get("a") or item.get("author") or "").strip()
        daily_quote = DailyQuote(quote=quote or fallback.quote, author=author or fallback.author, source="ZenQuotes")
    except Exception:
        daily_quote = fallback

    QUOTE_CACHE["date"] = today
    QUOTE_CACHE["quote"] = daily_quote
    return daily_quote


def get_current_user(authorization: Annotated[str | None, Header()] = None) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")

    token = authorization.split(" ", 1)[1]
    try:
        payload_part, signature_part = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    expected_signature = hmac.new(SECRET_KEY.encode(), payload_part.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(signature_part, _b64encode(expected_signature)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        payload = json.loads(_b64decode(payload_part))
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    username = str(payload.get("sub", "")).lower().strip()
    if username not in USERS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return User(
        username=username,
        name=str(payload.get("name", "")),
        role=str(payload.get("role", "")),
        email=str(payload.get("email", "")),
        profile_complete=bool(payload.get("profile_complete", False)),
        agreement_signed=bool(payload.get("agreement_signed", False)),
    )


CurrentUser = Annotated[User, Depends(get_current_user)]


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _b64decode(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding).decode()
