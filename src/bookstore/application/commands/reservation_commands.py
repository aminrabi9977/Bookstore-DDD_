from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from bookstore.application.commands.base import Command


@dataclass
class CreateReservation(Command):
    customer_id: UUID
    book_id: UUID
    start_time: datetime
    duration_days: int
@dataclass
class CancelReservation(Command):
    id: UUID
    customer_id: UUID  
@dataclass
class CompleteReservation(Command):
    id: UUID
    customer_id: UUID  
@dataclass
class ExtendReservation(Command):
    id: UUID
    customer_id: UUID
    additional_days: int
@dataclass
class ProcessQueuedReservation(Command):
    book_id: UUID


@dataclass
class AddToReservationQueue(Command):
    customer_id: UUID
    book_id: UUID
    requested_days: int