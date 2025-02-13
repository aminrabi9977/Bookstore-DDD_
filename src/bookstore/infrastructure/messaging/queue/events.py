from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from bookstore.infrastructure.messaging.message_bus import Event


@dataclass
class BookSearchIndexingRequired(Event):
    book_id: UUID
    title: str
    description: str
    isbn: str
@dataclass
class DatabaseSyncRequired(Event):
    entity_type: str
    entity_id: UUID
    operation: str  # 'create', 'update', or 'delete'
    data: dict
@dataclass
class ReservationReminder(Event):
    reservation_id: UUID
    customer_id: UUID
    book_title: str
    end_date: datetime
    customer_phone: str
@dataclass
class PaymentProcessed(Event):
    customer_id: UUID
    amount: Decimal
    payment_type: str  
    reference_id: UUID
@dataclass
class CacheInvalidationRequired(Event):
    cache_key: str