from uuid import UUID
from  bookstore.domain.base import DomainEvent
# from bookstore.domain.aggregates.user import UserRole
from enum import Enum


class UserRole(Enum):
    CUSTOMER = "customer"
    Author = "author"
    ADMIN = "admin"


class UserCreated(DomainEvent):
    def __init__(self, aggregate_id: UUID, email: str, phone: str, role: UserRole):
        super().__init__(aggregate_id)
        self.email = email
        self.phone = phone
        self.role = role



class UserVerified(DomainEvent):
    def __init__(self, aggregate_id: UUID):
        super().__init__(aggregate_id)


class UserRoleChanged(DomainEvent):
    def __init__(self, aggregate_id:UUID, old_role : UserRole, new_role: UserRole):
        super.__init__(aggregate_id) 
        self.old_role = old_role
        self.new_role = new_role               