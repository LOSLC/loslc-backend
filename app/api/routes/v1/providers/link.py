from pydantic import Field
from sqlmodel import Session, select

from app.api.routes.v1.dto.link import LinkCreationDTO, LinkUpdateDTO
from app.api.routes.v1.dto.message import MessageResponse
from app.core.db.builders.permission import PermissionBuilder
from app.core.db.builders.role import RoleBuilder
from app.core.db.models import Link, User
from app.core.security.checkers import check_existence, check_non_existence
from app.core.security.permissions import (
    ACTION_READ,
    ACTION_READWRITE,
    ADMIN_ROLE_NAME,
    LINK_RESOURCE,
    GlobalPermissionCheckModel,
    PermissionChecker,
    PermissionCheckModel,
)


async def get_link_by_label(
    db_session: Session, label: str = Field(pattern=r"^[a-zA-Z0-9-]+$")
):
    link = check_existence(
        db_session.exec(select(Link).where(Link.label == label)).first()
    )
    return link.to_dto()


async def get_link(db_session: Session, link_id: str):
    link = check_existence(
        db_session.get(Link, link_id), detail="Link not found."
    )
    return link.to_dto()


async def get_my_links(
    db_session: Session, current_user: User, skip: int, limit: int
):
    links = db_session.exec(
        select(Link)
        .where(Link.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    ).all()
    return [link.to_dto() for link in links]


async def create_link(
    db_session: Session, current_user: User, data: LinkCreationDTO
):
    check_non_existence(
        db_session.exec(select(Link).where(Link.label == data.label)).first()
    )
    link = Link(
        label=data.label,
        url=str(data.url),
        description=data.description,
        user_id=current_user.id,
    )
    rw_role = RoleBuilder().addUser(current_user).make()
    rw_perm = (
        PermissionBuilder()
        .forRole(rw_role)
        .withActionName(ACTION_READWRITE)
        .withResourceName(LINK_RESOURCE)
        .withResourceId(link.id)
        .make()
    )
    db_session.add(link)
    db_session.add(rw_role)
    db_session.add(rw_perm)
    db_session.commit()
    db_session.refresh(link)
    return link.to_dto()


async def update_link(
    db_session: Session, current_user: User, data: LinkUpdateDTO
):
    link = check_existence(db_session.get(Link, data.id))
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        pcheck_models=[
            PermissionCheckModel(
                resource_name=LINK_RESOURCE,
                resource_id=link.id,
                action_names=[ACTION_READWRITE],
            )
        ],
    ).check()
    link.label = data.label
    link.url = str(data.url)
    link.description = data.description
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)
    return link.to_dto()


async def delete_link(db_session: Session, current_user: User, link_id: str):
    link = check_existence(db_session.get(Link, link_id))
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_role=ADMIN_ROLE_NAME,
        pcheck_models=[
            PermissionCheckModel(
                resource_name=LINK_RESOURCE,
                resource_id=link.id,
                action_names=[ACTION_READWRITE],
            )
        ],
    ).check()
    db_session.delete(link)
    db_session.commit()
    return MessageResponse(message="Link deleted successfully.")


def get_user_link(
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
                resource_name=LINK_RESOURCE, action_names=[ACTION_READ]
            ),
            GlobalPermissionCheckModel(
                resource_name=LINK_RESOURCE, action_names=[ACTION_READWRITE]
            ),
        ],
    ).check(either=True)
    check_existence(
        db_session.get(User, target_user_id), detail="User not found."
    )
    links = db_session.exec(
        select(Link)
        .where(Link.user_id == target_user_id)
        .offset(skip)
        .limit(limit)
    ).all()
    return [link.to_dto() for link in links]
