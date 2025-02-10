from typing import Optional
from uuid import UUID
from bookstore.domain.base import Entity

class Genre(Entity):
    def __init__(self, id: Optional[UUID], name: str, description: str =""):

        super.__init__(id)
        self.set_name(name)
        self._description = description

    def set_name(self, name: str) -> None:
        if not name.strip():
            raise ValueError("Name cannot be empty")
        self._name = name.strip() 


    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description    