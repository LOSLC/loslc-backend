from datetime import datetime, timezone
from typing import Annotated

from fastapi import BackgroundTasks, Cookie, Depends, HTTPException, Response
from pydantic import EmailStr
from sqlmodel import Session, or_, select
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

from app.api.routes.v1.dto.message import MessageResponse
from app.core.config.env import get_env
from app.core.db.builders.permission import PermissionBuilder
from app.core.db.builders.role import RoleBuilder
from app.core.db.models import (
    AccountVerificationSession,
    AuthSession,
    LoginSession,
    User,
)
from app.core.db.setup import create_db_session
from app.core.security.checkers import (
    check_conditions,
    check_equality,
    check_existence,
    check_non_existence,
)
from app.core.security.permissions import (
    ACTION_CREATE,
    ACTION_READWRITE,
    ADMIN_ROLE_NAME,
    SUPER_ADMIN_ROLE_NAME,
    USER_RESOURCE,
    GlobalPermissionCheckModel,
    PermissionChecker,
)
from app.core.services.email import send_templated_email
from app.utils.crypto import hash_password, verify_password
from app.utils.date import utc

USER_SESSION_COOKIE_ID = "user_session_id"
AUTH_SESSION_COOKIE_ID = "_auths"


async def verify_account(
    db_session: Session,
    token: str,
    account_verification_session_id: str,  # search param
):
    account_verification_session = check_existence(
        db_session.get(
            AccountVerificationSession, account_verification_session_id
        ),
        detail="Session not found or expired.",
        status_code=HTTP_401_UNAUTHORIZED,
    )
    check_conditions(
        [
            not (account_verification_session.expired),
            not (
                utc(account_verification_session.expires_at)
                <= datetime.now(timezone.utc)
            ),
            not (
                account_verification_session.tries
                >= account_verification_session.max_tries
            ),
        ],
        detail="Session not found or expired.",
    )
    if not (account_verification_session.token == token):
        account_verification_session.tries += 1
        db_session.add(account_verification_session)
        db_session.commit()
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Invalid password."
        )
    account_verification_session.user.verified = True
    db_session.add(account_verification_session.user)
    db_session.delete(account_verification_session)
    db_session.commit()
    return MessageResponse(message="Account verified successfully.")


async def authenticate(
    db_session: Session,
    token: str,
    auth_session_id: str,  # cookie
    response: Response,
):
    auth_session = check_existence(
        db_session.get(AuthSession, auth_session_id),
        detail="Session expired.",
        status_code=HTTP_400_BAD_REQUEST,
    )
    check_conditions(
        [not (auth_session.tries >= auth_session.max_tries)],
        detail="Too much tries.",
        status_code=HTTP_400_BAD_REQUEST,
    )
    if not auth_session.token == token:
        auth_session.tries += 1
        db_session.add(auth_session)
        db_session.commit()
        raise HTTPException(
            detail="Token invalid.", status_code=HTTP_400_BAD_REQUEST
        )

    login_session = LoginSession(user_id=auth_session.user_id)
    auth_session.expired = True
    db_session.add(login_session)
    db_session.add(auth_session)
    db_session.commit()
    db_session.refresh(login_session)

    response.set_cookie(
        key=USER_SESSION_COOKIE_ID,
        value=login_session.id,
        expires=utc(login_session.expires_at),
        httponly=True,
        secure=True,
        samesite="lax",
    )
    response.delete_cookie(AUTH_SESSION_COOKIE_ID)


async def send_verification_email(db_session: Session, email: EmailStr):
    user = check_existence(
        db_session.exec(select(User).where(User.email == email)).first(),
        detail="User not found.",
    )
    account_verification_session = AccountVerificationSession(user_id=user.id)
    link = (
        get_env("FRONTEND_URL")
        + "/auth/verify?token="
        + account_verification_session.id
    )
    db_session.add(account_verification_session)
    db_session.commit()
    db_session.refresh(account_verification_session)
    send_templated_email(
        email=email,
        subject="Verify your account",
        template_name="account_verification",
        context={
            "username": user.name,
            "verification_link": link,
            "otp_code": account_verification_session.token,
        },
    )


async def register(
    db_session: Session,
    username: str,
    email: EmailStr,
    password: str,
    password_confirm: str,
    name: str,
    bt: BackgroundTasks,
):
    check_non_existence(
        (
            db_session.exec(
                select(User).where(
                    or_(User.email == email, User.username == username)
                )
            )
        ).first()
    )
    check_equality(password, password_confirm)
    hashed_password = hash_password(password=password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        name=name,
    )
    role = RoleBuilder().addUser(user).make()
    admin_role = (
        RoleBuilder().addUser(user).withName(ADMIN_ROLE_NAME).make()
        if email.lower() in get_env("ADMIN_EMAILS").split(",")
        else None
    )
    super_admin_role = (
        RoleBuilder().addUser(user).withName(SUPER_ADMIN_ROLE_NAME).make()
        if email.lower() in get_env("SUPER_ADMIN_EMAILS").split(",")
        else None
    )
    perm = (
        PermissionBuilder()
        .withActionName(ACTION_READWRITE)
        .withResourceName(USER_RESOURCE)
        .withResourceId(user.id)
        .forRole(role)
        .make()
    )

    db_session.add_all([user, perm, role])
    if admin_role is not None:
        db_session.add(admin_role)

    if super_admin_role is not None:
        db_session.add(super_admin_role)

    bt.add_task(send_verification_email, db_session=db_session, email=email)

    db_session.commit()
    return MessageResponse(
        message="Registered !"
        + " An email verification mail was sent to your inbox."
    )


async def login(
    db_session: Session,
    email: EmailStr,
    password: str,
    response: Response,
    bt: BackgroundTasks,
):
    user = check_existence(
        (db_session.exec(select(User).where(User.email == email))).first()
    )
    check_conditions([verify_password(password, user.hashed_password)])

    if get_env("ALLOW_ADMINS_ONLY") == "True":
        PermissionChecker(
            db_session=db_session,
            roles=user.roles,
            bypass_roles=[ADMIN_ROLE_NAME, SUPER_ADMIN_ROLE_NAME],
            pcheck_models=[
                GlobalPermissionCheckModel(
                    resource_name=USER_RESOURCE, action_names=[ACTION_CREATE]
                )
            ],
        ).check(message="Email not authorized.")

    auth_session = AuthSession(user_id=user.id)
    db_session.add(auth_session)
    db_session.commit()
    db_session.refresh(auth_session)

    response.set_cookie(key=AUTH_SESSION_COOKIE_ID, value=auth_session.id)

    bt.add_task(
        send_templated_email,
        email=email,
        subject="Login Verification",
        template_name="otp",
        context={
            "username": user.name,
            "otp_code": auth_session.token,
        },
    )

    return MessageResponse(message="OTP sent to your email.")


async def get_current_user(
    db_session: Annotated[Session, Depends(create_db_session)],
    session_id: Annotated[str | None, Cookie(alias="user_session_id")] = None,
):
    login_session = check_existence(
        db_session.get(
            LoginSession,
            check_existence(session_id, detail="Not authenticated"),
        ),
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated.",
    )
    check_conditions(
        [
            utc(login_session.expires_at) > datetime.now(timezone.utc),
            not login_session.expired,
            login_session.user.verified,
        ],
        detail="Not authenticated.",
    )
    return login_session.user


async def ws_get_current_user(
    db_session: Annotated[Session, Depends(create_db_session)],
    session_id: Annotated[str | None, Cookie(alias="user_session_id")] = None,
):
    login_session = check_existence(
        db_session.get(LoginSession, session_id),
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated.",
    )
    check_conditions(
        [
            utc(login_session.expires_at) > datetime.now(timezone.utc),
            not login_session.expired,
            login_session.user.verified,
        ],
        detail="Not authenticated.",
        is_ws=True,
    )
    return login_session.user


async def get_current_user_optional(
    db_session: Annotated[Session, Depends(create_db_session)],
    session_id: Annotated[str | None, Cookie(alias="user_session_id")] = None,
) -> User | None:
    """Get current user without throwing errors if not authenticated"""
    if session_id is None:
        return None

    try:
        return await get_current_user(
            db_session=db_session, session_id=session_id
        )
    except Exception:
        return None
