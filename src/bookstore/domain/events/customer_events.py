
from decimal import Decimal
from uuid import UUID

from bookstore.domain.base import DomainEvent
from enum import Enum

class SubscriptionType(Enum):
    FREE = "free"
    PLUS = "plus"
    PREMIUM = "premium"

class CustomerCreated(DomainEvent):
    
    def __init__(self, aggregate_id: UUID, user_id: UUID, subscription_type: SubscriptionType, initial_balance: Decimal):
        super().__init__(aggregate_id)
        self.user_id = user_id
        self.subscription_type = subscription_type
        self.initial_balance = initial_balance


class SubscriptionChanged(DomainEvent):
    def __init__(self, aggregate_id: UUID, old_type: SubscriptionType, new_type: SubscriptionType):
        super().__init__(aggregate_id)
        self.old_type = old_type
        self.new_type = new_type


class WalletCredited(DomainEvent):   
    def __init__(self, aggregate_id: UUID, amount: Decimal):
        super().__init__(aggregate_id)
        self.amount = amount


class WalletDebited(DomainEvent):   
    def __init__(self, aggregate_id: UUID, amount: Decimal):
        super().__init__(aggregate_id)
        self.amount = amount


class CustomerReachedSpendingThreshold(DomainEvent):   
    def __init__(self, aggregate_id: UUID, total_spent: Decimal):
        super().__init__(aggregate_id)
        self.total_spent = total_spent


class CustomerReachedReadingThreshold(DomainEvent):   
    def __init__(self, aggregate_id: UUID, books_read: int):
        super().__init__(aggregate_id)
        self.books_read = books_read