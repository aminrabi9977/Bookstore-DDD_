from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID
from bookstore.application.commands.base import Command


@dataclass
class CreateBook(Command):
    title: str
    isbn: str
    price: Decimal
    author_id: UUID
    genre_id: UUID
    description: str = ""
    total_units: int = 0


@dataclass
class UpdateBook(Command):
    id: UUID
    title: Optional[str] = None
    price: Optional[Decimal] = None
    description: Optional[str] = None
    genre_id: Optional[UUID] = None


@dataclass
class DeleteBook(Command):
    id: UUID



@dataclass
class AddBookUnits(Command):
    id: UUID
    count: int
@dataclass
class RemoveBookUnits(Command):
    id: UUID
    count: int




@dataclass
class UpdateBookPrice(Command):
    id: UUID
    new_price: Decimal