from fastapi import APIRouter, HTTPException, status

from ..auth import CurrentUser, LoginRequest, LoginResponse, authenticate_user, create_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    return LoginResponse(access_token=create_token(user), user=user)


@router.get("/me")
def me(current_user: CurrentUser):
    return current_user
