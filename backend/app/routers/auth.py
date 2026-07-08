from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from ..auth import (
    AgreementSignRequest,
    AgreementSignResponse,
    CurrentUser,
    DailyQuote,
    LoginRequest,
    LoginResponse,
    OnboardingStatus,
    ProfileUpdate,
    User,
    authenticate_user,
    build_user,
    create_token,
    get_daily_quote,
    get_or_build_signed_agreement,
    list_onboarding_statuses,
    sign_partner_agreement,
    update_user_profile,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def require_admin(current_user: User) -> None:
    refreshed_user = build_user(current_user.username) or current_user
    if refreshed_user.role != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


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
    file_path = get_or_build_signed_agreement(current_user.username)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signed agreement not found")

    return FileResponse(file_path, media_type="application/pdf", filename=file_path.name)


@router.get("/admin/onboarding", response_model=list[OnboardingStatus])
def admin_onboarding_tracker(current_user: CurrentUser):
    require_admin(current_user)
    return list_onboarding_statuses()


@router.get("/admin/onboarding/{username}/agreement")
def download_admin_signed_onboarding_agreement(username: str, current_user: CurrentUser):
    require_admin(current_user)
    if not build_user(username):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    file_path = get_or_build_signed_agreement(username)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signed agreement not found")

    return FileResponse(file_path, media_type="application/pdf", filename=file_path.name)


@router.get("/quote/today", response_model=DailyQuote)
def today_quote(current_user: CurrentUser):
    return get_daily_quote()
