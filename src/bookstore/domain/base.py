from abc import ABC 
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime

class Entity(ABC):

    def __init__(self, id: Optional[UUID] = None):

        self._id = id or uuid4()
        self._created_at = datetime.utcnow()
        self._updated_at = slef._created_at
        delf._version = 1

    @property
    def id(self) -> UUID:
        return self._id
       
       
    @property
    def _created_at(self) -> datetime:
        return self._created_at

    @property
    def _updated_at(self) -> datetime:
        return self._updated_at

    @property
    def version(self) -> int:
        return self._version


    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Entity):
             return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

class ValueObject(ABC):

    def __eq__(self, other:Any) -> bool:
        if not isinstance(other , ValueObject):
            return False
        return self.__dict__ == other.__dict__


    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))               


    def __repr__(self) -> str:
        attrs = [f"{k} = {v!r}" for k, v in self.__dict__.items()]
        return f"{self.__class__.__name__}({', '.join(attrs)})"

class DomainEvent:
    def __init__(self, aggregate_id: UUID):
        self._aggregate_id  = aggregate_id
        self._occurred_on = datetime.utcnow()


class AggregateRoot(Entity):
    def __init__(self, id: UUID = None):
        super().__init__(id)
        self._events = []


    def add_event(self, event:"DomainEvent") -> None:
        self.events.append(event)

    def clear_event(self) -> None:
        self._events =[]

    @property
    def events(self) -> list:
        return self._events.copy()