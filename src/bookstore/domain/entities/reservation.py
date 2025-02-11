from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID
from bookstore.domain.base import Entity
from bookstore.domain.value_objects.money import Money

class ReservationStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Reservation(Entity):
    def __init__(self, customer_id: UUID, book_id: UUID,price: Money,start_time: datetime, duration_days: int, id: Optional[UUID] = None
    ):
        super().__init__(id)
        self._customer_id = customer_id
        self._book_id = book_id
        self._price = price
        self._start_time = start_time
        self._end_time = start_time + timedelta(days=duration_days)
        self._status = ReservationStatus.PENDING
        self._queue_position = None

    @property
    def customer_id(self) -> UUID:
        return self._customer_id

    @property
    def book_id(self) -> UUID:
        return self._book_id

    @property
    def price(self) -> Money:
        return self._price

    @property
    def start_time(self) -> datetime:
        return self._start_time

    @property
    def end_time(self) -> datetime:
        return self._end_time

    @property
    def status(self) -> ReservationStatus:
        return self._status

    @property
    def queue_position(self) -> Optional[int]:
        return self._queue_position

    def activate(self) -> None:
        if self._status != ReservationStatus.PENDING:
            raise ValueError("Only pending reservations can be activated")
        self._status = ReservationStatus.ACTIVE

    def complete(self) -> None:
        if self._status != ReservationStatus.ACTIVE:
            raise ValueError("Only active reservations can be completed")
        self._status = ReservationStatus.COMPLETED

    def cancel(self) -> None:
        if self._status in [ReservationStatus.COMPLETED, ReservationStatus.CANCELLED]:
            raise ValueError("Cannot cancel completed or already cancelled reservations")
        self._status = ReservationStatus.CANCELLED

    def set_queue_position(self, position: int) -> None:
        if position < 0:
            raise ValueError("Queue position cannot be negative")
        self._queue_position = position

    def is_overdue(self) -> bool:
        return datetime.utcnow() > self._end_time