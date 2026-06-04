import base64
import hashlib
import hmac
import json
import time
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

SECRET_KEY = "chatcrm-local-dev-secret-change-before-production"
TOKEN_TTL_SECONDS = 60 * 60 * 12


class User(BaseModel):
    username: str
    name: str
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


USERS = {
    "virgo": {
        "password_hash": hashlib.sha256("Virgo2026!".encode()).hexdigest(),
        "name": "Virgo Davis",
        "role": "Admin",
    },
    "test-acq": {
        "password_hash": hashlib.sha256("TestAcq2026!".encode()).hexdigest(),
        "name": "Test Acquisition",
        "role": "Acquisition",
    },
    "test-dispo": {
        "password_hash": hashlib.sha256("TestDispo2026!".encode()).hexdigest(),
        "name": "Test Disposition",
        "role": "Disposition",
    },
    "test-va": {
        "password_hash": hashlib.sha256("TestVa2026!".encode()).hexdigest(),
        "name": "Test VA",
        "role": "VA",
    },
}


def create_token(user: User) -> str:
    payload = {
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
        "name": user.name,
        "role": user.role,
        "sub": user.username,
    }
    payload_text = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    payload_part = _b64encode(payload_text.encode())
    signature = hmac.new(SECRET_KEY.encode(), payload_part.encode(), hashlib.sha256).digest()
    return f"{payload_part}.{_b64encode(signature)}"


def authenticate_user(username: str, password: str) -> User | None:
    record = USERS.get(username.lower().strip())
    if not record:
        return None

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if not hmac.compare_digest(password_hash, record["password_hash"]):
        return None

    return User(username=username.lower().strip(), name=record["name"], role=record["role"])


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

    return User(
        username=str(payload.get("sub", "")),
        name=str(payload.get("name", "")),
        role=str(payload.get("role", "")),
    )


CurrentUser = Annotated[User, Depends(get_current_user)]


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _b64decode(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding).decode()
