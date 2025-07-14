from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Cookie,
    Depends,
    HTTPException,
    Response,
)
from pydantic import EmailStr
from sqlmodel import Session

import app.api.routes.v1.providers.auth as auth_provider
from app.api.routes.v1.dto.auth import (
    AccountVerificationDTO,
    LoginRequestDTO,
    LoginVerificationDTO,
    RegisterRequestDTO,
    UserResponseDTO,
)
from app.api.routes.v1.dto.message import MessageResponse
from app.core.db.models import User
from app.core.db.setup import create_db_session

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=MessageResponse)
async def register_user(
    request: RegisterRequestDTO,
    bt: BackgroundTasks,
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Register a new user account."""
    return await auth_provider.register(
        db_session=db_session,
        username=request.username,
        email=request.email,
        password=request.password,
        password_confirm=request.password_confirm,
        name=request.name,
        bt=bt,
    )


@router.post("/login", response_model=MessageResponse)
async def login_user(
    request: LoginRequestDTO,
    bt: BackgroundTasks,
    db_session: Annotated[Session, Depends(create_db_session)],
    response: Response,
):
    """Login user and send OTP for verification."""
    return await auth_provider.login(
        db_session=db_session,
        email=request.email,
        password=request.password,
        response=response,
        bt=bt,
    )


@router.get("/me", response_model=UserResponseDTO)
async def get_me(
    current_user: Annotated[User, Depends(auth_provider.get_current_user)],
):
    """Get current authenticated user information."""
    return current_user


@router.post("/logout", response_model=MessageResponse)
async def logout_user(
    response: Response,
):
    """Logout user by clearing session cookie."""
    response.delete_cookie(key="user_session_id", httponly=True)
    return MessageResponse(message="Logged out successfully.")


@router.post("/verify-account", response_model=MessageResponse)
async def verify_user_account(
    request: AccountVerificationDTO,
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Verify user account using OTP token."""
    return await auth_provider.verify_account(
        db_session=db_session,
        token=request.token,
        account_verification_session_id=request.session_id,
    )


@router.post("/verify-login", response_model=MessageResponse)
async def verify_login_otp(
    request: LoginVerificationDTO,
    response: Response,
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Verify login OTP and create user session."""
    await auth_provider.authenticate(
        db_session=db_session,
        token=request.token,
        auth_session_id=request.session_id,
        response=response,
    )
    return MessageResponse(message="Login verified successfully.")


@router.post("/send-verification", response_model=MessageResponse)
async def send_verification_email(
    email: EmailStr,
    bt: BackgroundTasks,
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Send verification email to user."""

    bt.add_task(
        auth_provider.send_verification_email,
        db_session=db_session,
        email=email,
    )
    return MessageResponse(message="Verification email sent successfully.")


@router.post("/verify-login-otp", response_model=MessageResponse)
async def verify_login_otp_cookie(
    token: str,
    response: Response,
    db_session: Annotated[Session, Depends(create_db_session)],
    auth_session_id: Annotated[str | None, Cookie(alias="_auths")] = None,
):
    """Verify login OTP using cookie-based auth session."""
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")

    if not auth_session_id:
        raise HTTPException(status_code=400, detail="No auth session found")

    await auth_provider.authenticate(
        db_session=db_session,
        token=token,
        auth_session_id=auth_session_id,
        response=response,
    )
    return MessageResponse(message="Login verified successfully.")
