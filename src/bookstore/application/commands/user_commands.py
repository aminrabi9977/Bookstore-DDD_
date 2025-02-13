from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID
from bookstore.application.commands.base import Command
from bookstore.domain.aggregates.user import UserRole
from bookstore.domain.aggregates.customer import SubscriptionType


@dataclass
class RegisterUser(Command):
    email: str
    password: str
    phone: str
    role: UserRole = UserRole.CUSTOMER

@dataclass
class VerifyUser(Command):
    user_id: UUID
    otp: str
@dataclass
class CreateCustomer(Command):
    user_id: UUID
    subscription_type: SubscriptionType = SubscriptionType.FREE


@dataclass
class ChangeSubscription(Command):
    customer_id: UUID
    new_subscription: SubscriptionType




@dataclass
class AddWalletBalance(Command):
    customer_id: UUID
    amount: Decimal
@dataclass
class UpdateUserProfile(Command):
    user_id: UUID
    email: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class ChangeUserPassword(Command):
    """Command to change user password."""
    user_id: UUID
    old_password: str
    new_password: str


@dataclass
class RequestPasswordReset(Command):
    """Command to request password reset."""
    email: str


@dataclass
class ResetPassword(Command):
    """Command to reset password with token."""
    token: str
    new_password: str


@dataclass
class GenerateOTP(Command):
    """Command to generate and send OTP."""
    phone: str