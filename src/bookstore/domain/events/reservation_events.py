from datetime import datetime
from decimal import Decimal
from uuid import UUID
from bookstore.domain.base import DomainEvent
from bookstore.domain.entities.reservation import ReservationStatus
from typing import Optional
class ReservationCreated(DomainEvent):
    def __init__(self,aggregate_id: UUID,customer_id: UUID, book_id: UUID,price: Decimal,start_time: datetime, end_time: datetime):
        super().__init__(aggregate_id)
        self.customer_id = customer_id
        self.book_id = book_id
        self.price = price
        self.start_time = start_time
        self.end_time = end_time

class ReservationStatusChanged(DomainEvent):
    def __init__(self, aggregate_id: UUID, old_status: ReservationStatus,new_status: ReservationStatus):
        super().__init__(aggregate_id)
        self.old_status = old_status
        self.new_status = new_status

class ReservationQueuePositionChanged(DomainEvent):
    def __init__(self,aggregate_id: UUID,old_position: Optional[int],new_position: int):
        super().__init__(aggregate_id)
        self.old_position = old_position
        self.new_position = new_position

class ReservationOverdue(DomainEvent):
    def __init__(self, aggregate_id: UUID, customer_id: UUID):
        super().__init__(aggregate_id)
        self.customer_id = customer_id