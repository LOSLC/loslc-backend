from typing import Literal

from sqlmodel import Session, select

from app.api.routes.v1.dto.message import MessageResponse
from app.core.db.builders.permission import PermissionBuilder
from app.core.db.builders.role import RoleBuilder
from app.core.db.models import Permission, Role, RoleUserLink, User
from app.core.security.checkers import check_existence
from app.core.security.permissions import (
    ACTION_READ,
    ACTION_READWRITE,
    ADMIN_RESOURCE,
    ADMIN_ROLE_NAME,
    ROLE_RESOURCE,
    USER_RESOURCE,
    GlobalPermissionCheckModel,
    PermissionChecker,
)


async def get_users(
    db_session: Session, current_user: User, skip: int, limit: int
):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_role=ADMIN_ROLE_NAME,
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=USER_RESOURCE, action_names=[ACTION_READ]
            ),
            GlobalPermissionCheckModel(
                resource_name=USER_RESOURCE, action_names=[ACTION_READWRITE]
            ),
        ],
    ).check(either=True)
    users = db_session.exec(select(User).offset(skip).limit(limit)).all()
    return [user.to_dto() for user in users]


async def delete_user(
    db_session: Session, current_user: User, target_user_id: str
):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_role=ADMIN_ROLE_NAME,
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=USER_RESOURCE, action_names=[ACTION_READWRITE]
            ),
        ],
    ).check(either=True)
    user = check_existence(
        db_session.get(User, target_user_id), detail="User not found."
    )
    db_session.delete(user)
    db_session.commit()
    return MessageResponse(
        message=f"User {target_user_id} deleted successfully."
    )


async def get_user_roles(
    db_session: Session,
    current_user: User,
    target_user_id: str,
    skip: int,
    limit: int,
):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_role=ADMIN_ROLE_NAME,
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=USER_RESOURCE, action_names=[ACTION_READ]
            ),
            GlobalPermissionCheckModel(
                resource_name=USER_RESOURCE, action_names=[ACTION_READWRITE]
            ),
        ],
    ).check(either=True)
    roles = db_session.exec(
        select(Role)
        .join(RoleUserLink)
        .join(User)
        .where(RoleUserLink.user_id == target_user_id)
        .offset(skip)
        .limit(limit)
    ).all()
    return [role.to_dto() for role in roles]


async def get_role_permissions(
    db_session: Session,
    current_user: User,
    role_id: str,
    skip: int,
    limit: int,
):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=ROLE_RESOURCE, action_names=[ACTION_READWRITE]
            ),
            GlobalPermissionCheckModel(
                resource_name=ROLE_RESOURCE, action_names=[ACTION_READ]
            ),
        ],
    ).check(either=True)
    check_existence(db_session.get(Role, role_id))
    permissions = db_session.exec(
        select(Permission)
        .where(Permission.role_id == role_id)
        .offset(skip)
        .limit(limit)
    ).all()
    return [permission.to_dto() for permission in permissions]


async def add_permission_to_user(
    db_session: Session,
    current_user: User,
    target_user_id: str,
    action_name: Literal["r", "rw"],
    resource_id: str,
    resource_name: Literal["resource", "link"],
    role_name: str | None = None,
):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=ADMIN_RESOURCE, action_names=[ACTION_READWRITE]
            )
        ],
    ).check()
    target_user = check_existence(
        db_session.get(User, target_user_id), detail="User not found."
    )
    role = RoleBuilder().addUser(target_user).withName(role_name).make()
    permission = (
        PermissionBuilder()
        .forRole(role)
        .withResourceName(resource_name)
        .withResourceId(resource_id)
        .withActionName(action_name)
        .make()
    )
    db_session.add_all([role, permission])
    db_session.commit()
    return MessageResponse(message="Permission added successfully.")


async def remove_role_from_user(
    db_session: Session, current_user: User, role_id: str, target_user_id: str
):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=USER_RESOURCE, action_names=[ACTION_READWRITE]
            )
        ],
    )
    user = check_existence(
        db_session.get(User, target_user_id), detail="User not found"
    )
    role_user_link = check_existence(
        db_session.exec(
            select(RoleUserLink).where(
                RoleUserLink.user_id == target_user_id,
                RoleUserLink.role_id == role_id,
            )
        ).first(),
        detail=f"Role not found for user: {user.name}",
    )
    db_session.delete(role_user_link)
    db_session.commit()
    return MessageResponse(message="Role remove from user successfully.")


async def is_admin(db_session: Session, current_user: User):
    return PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_role=ADMIN_ROLE_NAME,
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=ADMIN_RESOURCE, action_names=[ACTION_READWRITE]
            )
        ],
    ).check()


async def get_all_roles(
    db_session: Session, current_user: User, skip: int, limit: int
):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_role=ADMIN_ROLE_NAME,
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=ROLE_RESOURCE, action_names=[ACTION_READ]
            ),
            GlobalPermissionCheckModel(
                resource_name=ROLE_RESOURCE, action_names=[ACTION_READWRITE]
            ),
        ],
    ).check(either=True)
    roles = db_session.exec(select(Role).offset(skip).limit(limit)).all()
    return [role.to_dto() for role in roles]


async def get_all_permissions(
    db_session: Session, current_user: User, skip: int, limit: int
):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_role=ADMIN_ROLE_NAME,
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=ROLE_RESOURCE, action_names=[ACTION_READ]
            ),
            GlobalPermissionCheckModel(
                resource_name=ROLE_RESOURCE, action_names=[ACTION_READWRITE]
            ),
        ],
    ).check(either=True)
    permissions = db_session.exec(
        select(Permission).offset(skip).limit(limit)
    ).all()
    return [permission.to_dto() for permission in permissions]


async def create_role(db_session: Session, current_user: User, role_name: str):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_role=ADMIN_ROLE_NAME,
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=ROLE_RESOURCE, action_names=[ACTION_READWRITE]
            )
        ],
    ).check()
    role = RoleBuilder().withName(role_name).make()
    db_session.add(role)
    db_session.commit()
    return MessageResponse(message=f"Role '{role_name}' created successfully.")


async def delete_role(db_session: Session, current_user: User, role_id: str):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_role=ADMIN_ROLE_NAME,
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=ROLE_RESOURCE, action_names=[ACTION_READWRITE]
            )
        ],
    ).check()
    role = check_existence(
        db_session.get(Role, role_id), detail="Role not found."
    )
    db_session.delete(role)
    db_session.commit()
    return MessageResponse(message="Role deleted successfully.")


async def assign_role_to_user(
    db_session: Session, current_user: User, user_id: str, role_id: str
):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_role=ADMIN_ROLE_NAME,
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=USER_RESOURCE, action_names=[ACTION_READWRITE]
            )
        ],
    ).check()
    user = check_existence(
        db_session.get(User, user_id), detail="User not found."
    )
    role = check_existence(
        db_session.get(Role, role_id), detail="Role not found."
    )

    # Check if user already has this role
    existing_link = db_session.exec(
        select(RoleUserLink).where(
            RoleUserLink.user_id == user_id, RoleUserLink.role_id == role_id
        )
    ).first()

    if existing_link:
        return MessageResponse(message="User already has this role.")

    role_user_link = RoleUserLink(user_id=user_id, role_id=role_id)
    db_session.add(role_user_link)
    db_session.commit()
    return MessageResponse(message="Role assigned to user successfully.")


async def create_permission(
    db_session: Session,
    current_user: User,
    role_id: str,
    action_name: str,
    resource_name: str,
    resource_id: str | None = None,
):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_role=ADMIN_ROLE_NAME,
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=ROLE_RESOURCE, action_names=[ACTION_READWRITE]
            )
        ],
    ).check()
    role = check_existence(
        db_session.get(Role, role_id), detail="Role not found."
    )
    permission = (
        PermissionBuilder()
        .forRole(role)
        .withActionName(action_name)
        .withResourceName(resource_name)
        .withResourceId(resource_id)
        .make()
    )
    db_session.add(permission)
    db_session.commit()
    return MessageResponse(message="Permission created successfully.")


async def delete_permission(
    db_session: Session, current_user: User, permission_id: str
):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_role=ADMIN_ROLE_NAME,
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=ROLE_RESOURCE, action_names=[ACTION_READWRITE]
            )
        ],
    ).check()
    permission = check_existence(
        db_session.get(Permission, permission_id),
        detail="Permission not found.",
    )
    db_session.delete(permission)
    db_session.commit()
    return MessageResponse(message="Permission deleted successfully.")
