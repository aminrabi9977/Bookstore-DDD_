from uuid import UUID
from datetime import datetime
from decimal import Decimal
from bookstore.domain.base import DomainEvent

class BookCreated(DomainEvent):
    def __init__(self, aggregate_id: UUID, title: str, price: Decimal,
    author_id: UUID,isbn:str,genre_id: UUID, description:str,total_units: int,  created_at: datetime):

        super().__init__(aggregate_id)
        self.title = title
        self.isbn = isbn
        self.price = price
        self.author_id = author_id
        self.genre_id = gebre_id
        self.description = description
        self.total_units = total_units

    @property
    def created_at(self) -> datetime:
        return self._occurred_on

class BookPriceChanged(DomainEvent):
    def __init__(seld, aggregate_id: UUID, old_price: Decimal, new_price: Decimal):

        super().__init__(aggregate_id)
        self.old_price = old_price
        self.new_price = new_price


class BookUnitAdded(DomainEvent):
    def __init__(self, aggregate_id: UUID, count: int):
        super().__init__(aggregate_id)
        self.count = count

class BookUnitRemoved(DomainEvent):
    def __init__(self, aggregate_id: UUID, count: int):
        super().__init__(aggregate_id)
        self.count = count

class BookReserved(DomainEvent):
    def __init__(self, aggregate_id: UUID, customer_id: UUID):
        super().__init__(aggregate_id)
        self.customer_id = customer_id

class BookReservationReleased(DomainEvent):
    def __init__(self, aggregate_id: UUID, customer_id: UUID):
        super().__init__(aggregate_id)
        self.customer_id = customer_id