from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlmodel import Session

import app.api.routes.v1.providers.file as file_provider
from app.api.routes.v1.providers.auth import (
    get_current_user,
    get_current_user_optional,
)
from app.core.db.models import User
from app.core.db.setup import create_db_session

router = APIRouter(prefix="/v1", tags=["File management"])


@router.get(
    "/file/{resource_id}", response_class=StreamingResponse
)
async def get_file_resource(
    db_session: Annotated[Session, Depends(create_db_session)],
    user: Annotated[User | None, Depends(get_current_user_optional)],
    resource_id: UUID,
):
    return await file_provider.get_file_resource(
        db_session=db_session, current_user=user, resource_id=resource_id
    )


@router.post("/file")
async def create_file_resource(
    db_session: Annotated[Session, Depends(create_db_session)],
    user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(),
    protected: bool = False,
):
    return await file_provider.create_file_resource(
        db_session=db_session,
        current_user=user,
        file=file,
        protected=protected,
    )


@router.post("/files")
async def create_file_resources(
    db_session: Annotated[Session, Depends(create_db_session)],
    user: Annotated[User, Depends(get_current_user)],
    files: list[UploadFile] = File(...),
    protected: bool = False,
):
    return await file_provider.create_file_resources(
        db_session=db_session,
        current_user=user,
        files=files,
        protected=protected,
    )
