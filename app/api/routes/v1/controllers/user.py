from typing import Annotated, List

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.routes.v1.dto.message import MessageResponse
from app.api.routes.v1.dto.user import (
    CreatePermissionDTO,
    CreateRoleDTO,
    PermissionDTO,
    RoleDTO,
    UserDTO,
)
from app.api.routes.v1.providers import user as user_provider
from app.api.routes.v1.providers.auth import get_current_user
from app.core.db.models import User
from app.core.db.setup import create_db_session

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserDTO])
async def get_users(
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Number of users to return"
    ),
):
    """Get all users with pagination (admin only or with proper permissions)."""
    return await user_provider.get_users(
        db_session=db_session,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Delete a user by ID (admin only or with proper permissions)."""
    return await user_provider.delete_user(
        db_session=db_session,
        current_user=current_user,
        target_user_id=user_id,
    )


@router.get("/{user_id}/roles", response_model=List[RoleDTO])
async def get_user_roles(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
    skip: int = Query(0, ge=0, description="Number of roles to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Number of roles to return"
    ),
):
    """Get roles for a specific user (admin only or with proper permissions)."""
    return await user_provider.get_user_roles(
        db_session=db_session,
        current_user=current_user,
        target_user_id=user_id,
        skip=skip,
        limit=limit,
    )


@router.get("/roles/{role_id}/permissions", response_model=List[PermissionDTO])
async def get_role_permissions(
    role_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
    skip: int = Query(0, ge=0, description="Number of permissions to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Number of permissions to return"
    ),
):
    """Get permissions for a specific role (admin only or with proper permissions)."""
    return await user_provider.get_role_permissions(
        db_session=db_session,
        current_user=current_user,
        role_id=role_id,
        skip=skip,
        limit=limit,
    )


@router.delete("/{user_id}/roles/{role_id}", response_model=MessageResponse)
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Remove a role from a user (admin only or with proper permissions)."""
    return await user_provider.remove_role_from_user(
        db_session=db_session,
        current_user=current_user,
        role_id=role_id,
        target_user_id=user_id,
    )


@router.get("/admin-check", response_model=bool)
async def is_admin_check(
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Check if the current user is an admin."""
    return await user_provider.is_admin(
        db_session=db_session,
        current_user=current_user,
    )


@router.get("/roles", response_model=List[RoleDTO])
async def get_all_roles(
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
    skip: int = Query(0, ge=0, description="Number of roles to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Number of roles to return"
    ),
):
    """Get all roles (admin only or with proper permissions)."""
    return await user_provider.get_all_roles(
        db_session=db_session,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )


@router.get("/permissions", response_model=List[PermissionDTO])
async def get_all_permissions(
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
    skip: int = Query(0, ge=0, description="Number of permissions to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Number of permissions to return"
    ),
):
    """Get all permissions (admin only or with proper permissions)."""
    return await user_provider.get_all_permissions(
        db_session=db_session,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )


@router.post("/roles", response_model=MessageResponse)
async def create_role(
    data: CreateRoleDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Create a new role (admin only or with proper permissions)."""
    return await user_provider.create_role(
        db_session=db_session,
        current_user=current_user,
        role_name=data.name,
    )


@router.delete("/roles/{role_id}", response_model=MessageResponse)
async def delete_role(
    role_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Delete a role (admin only or with proper permissions)."""
    return await user_provider.delete_role(
        db_session=db_session,
        current_user=current_user,
        role_id=role_id,
    )


@router.post("/{user_id}/roles/{role_id}", response_model=MessageResponse)
async def assign_role_to_user(
    user_id: str,
    role_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Assign a role to a user (admin only or with proper permissions)."""
    return await user_provider.assign_role_to_user(
        db_session=db_session,
        current_user=current_user,
        user_id=user_id,
        role_id=role_id,
    )


@router.post("/permissions", response_model=MessageResponse)
async def create_permission(
    data: CreatePermissionDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Create a new permission (admin only or with proper permissions)."""
    return await user_provider.create_permission(
        db_session=db_session,
        current_user=current_user,
        role_id=data.role_id,
        action_name=data.action_name,
        resource_name=data.resource_name,
        resource_id=data.resource_id,
    )


@router.delete("/permissions/{permission_id}", response_model=MessageResponse)
async def delete_permission(
    permission_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(create_db_session)],
):
    """Delete a permission (admin only or with proper permissions)."""
    return await user_provider.delete_permission(
        db_session=db_session,
        current_user=current_user,
        permission_id=permission_id,
    )
