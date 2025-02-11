from datetime import datetime, timedelta
from uuid import UUID
from enum import Enum
from typing import Optional
from bookstore.domain.base import AggregateRoot
from bookstore.domain.value_objects.money import Money
from bookstore.domain.events.customer_events import CustomerCreated, SubscriptionChanged, WalletCredited, WalletDebited

class SubscriptionType(Enum):
    FREE = "free"
    PLUS = "plus"
    PREMIUM = "premium"


class Customer(AggregateRoot):
    max_reservations = {
        SubscriptionType.FREE: 0,
        SubscriptionType.PLUS: 5,
        SubscriptionType.PREMIUM: 10
    }

    subscription_prices = {
        SubscriptionType.FREE: Money(0),
        SubscriptionType.PLUS: Money(10000),
        SubscriptionType.PREMIUM: Money(20000)
    }
    def __init__(self, user_id: UUID, subscription_type: SubscriptionType = SubscriptionType.FREE,
                    wallet_balance: Money = Money(0), id: Optional[UUID] = None):

            super().__init__(id)
            self._user_id = user_id
            self._subscription_type = subscription_type
            self._subscription_end = (
                datetime.utcnow() + timedelta(days = 30)
                if subscription_type != SubscriptionType.FREE
                else None

            )
            seld._wallet_balance = wallet_balance
            self._active_reservation = 0
            self.add_event(CustomerCreated(self.id, user_id, subscription_type, wallet_balance.amount))

    @property
    def user_id(self) -> UUID:
        return self._user_id
    @property
    def subscription_type(self) -> SubscriptionType:
        return self._subscription_type
    @property
    def subscription_end(self) -> Optional[datetime]:
        return self._subscription_end
    @property
    def wallet_balance(self) -> Money:
        return self._wallet_balance


    def change_subscription(self, new_type: SubscriptionType) -> None:

        if new_type == self._subscription_type:
            return

        cost = self.subscription_prices[new_type]
        if cost.amount >0 :
            self.debit_wallet(cost)

        old_type = self._subscription_type
        self._subscription_type = new_typeself._subscription_end(
            datetime.utcnow() + timedelta(days = 30)
            if new_type != SubscriptionType.FREE
            else None
        )        
        self.add_event(SubscriptionChanged(self.id, old_type, new_type))

    
    def credit_wallet(self, amount: Money) -> None:
        self._wallet_balance += amount
        self.add_event(WalletCredited(self.id, amount.amount))

    def debit_wallet(self, amount: Money) -> None:
        if amount > self._wallet_balance:
            raise ValueError("Insufficient funds")
            
        self._wallet_balance -= amount
        self.add_event(WalletDebited(self.id, amount.amount))

    def can_make_reservation(self) -> bool:
        if self._subscription_type == SubscriptionType.FREE:
            return False
            
        max_reservations = self.MAX_RESERVATIONS[self._subscription_type]
        return self._active_reservations < max_reservations

    def add_reservation(self) -> None:
        if not self.can_make_reservation():
            raise ValueError("Maximum reservations reached")
        self._active_reservations += 1

    def remove_reservation(self) -> None:
        if self._active_reservations <= 0:
            raise ValueError("No active reservations")
        self._active_reservations -= 1    