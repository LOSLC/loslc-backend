from typing import List, Optional

from app.core.db.models import Permission, Role, User


class RoleBuilder:
    def __init__(self) -> None:
        self.name: Optional[str] = None
        self.users: List[User] = []
        self.permissions: List[Permission] = []

    def withName(self, name: str):
        self.name = name
        return self

    def addUser(self, user: User):
        self.users.append(user)
        return self

    def addUsers(self, users: List[User]):
        for user in users:
            self.users.append(user)
        return self

    def addPermission(self, permission: Permission):
        self.permissions.append(permission)
        return self

    def addPermissions(self, permissions: List[Permission]):
        for permission in permissions:
            self.permissions.append(permission)
        return self

    def make(self):
        return Role(
            name=self.name,
            users=self.users,
            permissions=self.permissions,
        )
