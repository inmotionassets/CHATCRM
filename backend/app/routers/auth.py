from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from ..auth import (
    AgreementSignRequest,
    AgreementSignResponse,
    CurrentUser,
    DailyQuote,
    LoginRequest,
    LoginResponse,
    ProfileUpdate,
    User,
    authenticate_user,
    build_user,
    create_token,
    get_daily_quote,
    sign_partner_agreement,
    signed_agreement_path,
    update_user_profile,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    return LoginResponse(access_token=create_token(user), user=user)


@router.get("/me", response_model=User)
def me(current_user: CurrentUser):
    return build_user(current_user.username) or current_user


@router.put("/profile", response_model=User)
def update_profile(payload: ProfileUpdate, current_user: CurrentUser):
    return update_user_profile(current_user.username, payload)


@router.post("/onboarding/sign", response_model=AgreementSignResponse)
def sign_onboarding_agreement(payload: AgreementSignRequest, current_user: CurrentUser):
    return sign_partner_agreement(current_user.username, payload)


@router.get("/onboarding/agreement")
def download_signed_onboarding_agreement(current_user: CurrentUser):
    file_path = signed_agreement_path(current_user.username)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signed agreement not found")

    return FileResponse(file_path, media_type="application/pdf", filename=file_path.name)


@router.get("/quote/today", response_model=DailyQuote)
def today_quote(current_user: CurrentUser):
    return get_daily_quote()