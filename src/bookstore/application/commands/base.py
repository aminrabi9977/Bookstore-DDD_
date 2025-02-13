from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from bookstore.infrastructure.messaging.message_bus import Command


@dataclass
class CommandResult:
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None
@dataclass
class Command:
    pass