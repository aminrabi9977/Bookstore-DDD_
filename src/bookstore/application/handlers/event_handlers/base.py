from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from bookstore.infrastructure.messaging.message_bus import Event
from bookstore.infrastructure.persistence.unit_of_work import UnitOfWork

E = TypeVar('E', bound=Event)
class EventHandler(ABC, Generic[E]):
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
    @abstractmethod
    async def handle(self, event: E) -> None:
        raise NotImplementedError

class EventHandlingError(Exception):
    pass