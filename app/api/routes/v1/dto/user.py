from pydantic import BaseModel


class UserDTO(BaseModel):
    id: str
    email: str
    username: str
    name: str


class PermissionDTO(BaseModel):
    id: str
    action_name: str
    resource_name: str
    resource_id: str | None


class RoleDTO(BaseModel):
    id: str
    name: str | None
    permissions_count: int


class CreateRoleDTO(BaseModel):
    name: str


class CreatePermissionDTO(BaseModel):
    role_id: str
    action_name: str
    resource_name: str
    resource_id: str | None = None


class AssignRoleDTO(BaseModel):
    user_id: str
    role_id: str
