from datetime import datetime
from enum import Enum
from typing import Dict, Any , Optional
# from pydantic import BaseModel, Field, validator, root_validator
from uuid import UUID


class EventType(Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


class MongoEvent:
    def __init__(self,event_type: EventType,collection: str,document_id: UUID, data: Dict[str, Any]):
        self.event_type = event_type
        self.collection = collection
        self.document_id = document_id
        self.data = data
        self.timestamp = datetime.utcnow()
        self.processed = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "collection": self.collection,
            "document_id": str(self.document_id),
            "data": self.data,
            "timestamp": self.timestamp,
            "processed": self.processed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MongoEvent":
        return cls(
            event_type=EventType(data["event_type"]),
            collection=data["collection"],
            document_id=UUID(data["document_id"]),
            data=data["data"]
        )