from uuid import UUID
from typing import Optional
from enum import Enum
from datetime import datetime
from bookstore.domain.base import AggregateRoot
from bookstore.domain.events.user_events import (UserCreated, UserRoleChanged, UserVerified)


class UserRole(Enum):
    CUSTOMER = "customer"
    Author = "author"
    ADMIN = "admin"

class User(AggregateRoot):
    def __init__(self, email:str, password_hash: str, phone:str,role: UserRole = UserRole.CUSTOMER, is_verified: bool = False, id: Optional[UUID] = None):
        super.__init__(id)
        self._email = email
        self._password_hash = password_hash
        self._phone = phone
        self._role = role
        self._is_verified = is_verified
        self._last_login = None
        self._failed_login_attemps = 0
        self.add_event(UserCreated(self.id, email,phone, role))

    @property
    def email(self) -> str:
        return self._email
    @property
    def phone(self) -> str:
        return self._phone
    @property
    def role(self) -> UserRole:
        return self._role
    @property
    def is_verified(self) -> bool:
        return self._is_verified
    @property
    def last_login(self) -> Optional[datetime]:
        return self._last_login


    def verify(self) -> None:
        if self._is_verified:
            raise   ValueError("User is already verified")
        self.is_verified = True
        self.add_event(UserVerified(self.id))        

    def change_role(self, new_rol:UserRole) -> None:
        if self._role == new.role:
            return

        old_role = self._role
        self._role = new_role
        self.add_event(UserRoleChanged(self.id, old_role, new_role))


    def record_login_attempt(self, successful: bool) -> None:
        if successful:
            self._last_login = datetime.now()
            self._failed_login_attemps = 0
        else:
            self._failed_login_attemps += 1

    def is_locked(self) -> bool:
        return self._failed_login_attemps >= 5




