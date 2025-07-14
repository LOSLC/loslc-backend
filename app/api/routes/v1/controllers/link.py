from typing import Annotated, List

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.routes.v1.dto.link import (
    LinkCreationDTO,
    LinkDTO,
    LinkUpdateDTO,
)
from app.api.routes.v1.dto.message import MessageResponse
from app.api.routes.v1.providers import link as link_provider
from app.api.routes.v1.providers.auth import get_current_user
from app.core.db.models import User
from app.core.db.setup import create_db_session

router = APIRouter(prefix="/links", tags=["Links"])


@router.get("/{link_id}", response_model=LinkDTO)
async def get_link_by_id(
    link_id: str,
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Get a specific link by its ID."""
    return await link_provider.get_link(db_session=db_session, link_id=link_id)


@router.get("/label/{label}", response_model=LinkDTO)
async def get_link_by_label(
    label: str,
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Get a specific link by its label (public endpoint)."""
    return await link_provider.get_link_by_label(
        db_session=db_session, label=label
    )


@router.get("", response_model=List[LinkDTO])
async def get_my_links(
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
    skip: int = Query(0, ge=0, description="Number of links to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Number of links to return"
    ),
):
    """Get current user's links with pagination."""
    return await link_provider.get_my_links(
        db_session=db_session,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=LinkDTO)
async def create_link(
    request: LinkCreationDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Create a new link."""
    return await link_provider.create_link(
        db_session=db_session,
        current_user=current_user,
        data=request,
    )


@router.put("", response_model=LinkDTO)
async def update_link(
    request: LinkUpdateDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Update an existing link."""
    return await link_provider.update_link(
        db_session=db_session,
        current_user=current_user,
        data=request,
    )


@router.delete("/{link_id}", response_model=MessageResponse)
async def delete_link(
    link_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Delete a link by its ID."""
    return await link_provider.delete_link(
        db_session=db_session,
        current_user=current_user,
        link_id=link_id,
    )


@router.get("/user/{user_id}", response_model=List[LinkDTO])
async def get_user_links(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
    skip: int = Query(0, ge=0, description="Number of links to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Number of links to return"
    ),
):
    """Get links for a specific user (admin only or with proper permissions)."""
    return link_provider.get_user_link(
        db_session=db_session,
        current_user=current_user,
        target_user_id=user_id,
        skip=skip,
        limit=limit,
    )
