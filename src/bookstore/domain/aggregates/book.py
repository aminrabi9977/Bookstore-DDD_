from typing import  Optional
from datetime import datetime
from uuid import UUID

from bookstore.domain.base import AggregateRoot
from bookstore.domain.value_objects.money import Money
from bookstore.domain.events.book_events import (BookCreated, BookPriceChanged, BookUnitAdded, BookUnitRemoved)


class Book(AggregateRoot):
    def __init__(self, id: Optional[UUID], title: str, price: Money, 
    isbn: str, author_id: UUID,
    genre_id: UUID,
    description: str ="",
    total_units: int = 0):

        super().__init__(id)
        self._validation_isbn(isbn)
        self._title = title
        self._price = price
        self._isbn = isbn
        self._author_id = author_id
        self._genre_id = genre_id
        self._description = description
        self._total_units = total_units
        self._available_units = total_units
        self.add_events(BookCreated(self.id, title, isbn, price.amount,author_id, genre_id, description, total_units ))

    @staticmethod
    def _validation_isbn(isbn: str) -> None:
        if not isbn.replace("-", "").isdigit():
            raise ValueError("ISBN must be a number")
        clear_isbn = isbn.replace("-", "")
        if len(clear_isbn) not in [10,13]:
            raise ValueError("ISBN must be 10 or 13 digits")

    @property
    def title(self) -> str:
        return self._title

    @property
    def isbn(self) -> str:
        return self._isbn

    @property
    def price(self) -> Money:
        return self._price

    @property
    def author_id(self) -> UUID:
        return self._author_id

    @property
    def genre_id(self) -> UUID:
        return self._genre_id

    @property
    def description(self) -> str:
        return self._description

    @property
    def total_units(self) -> int:
        return self._total_units

    @property
    def available_units(self) -> int:
        return self._available_units

    def change_price(self, new_price: Money) -> None:
        if new_price < Money(0):
            raise ValueError("Price cannot be negative")
        
        old_price = self._price
        self._price = new_price
        self.add_event(BookPriceChanged(self.id, old_price.amount, new_price.amount))

    def add_units(self, count: int) -> None:
        if count <= 0:
            raise ValueError("Count must be positive")
            
        self._total_units += count
        self._available_units += count
        self.add_event(BookUnitAdded(self.id, count))

    def remove_units(self, count: int) -> None:
        if count <= 0:
            raise ValueError("Count must be positive")
        if count > self._available_units:
            raise ValueError("Not enough units available")
            
        self._total_units -= count
        self._available_units -= count
        self.add_event(BookUnitRemoved(self.id, count))

    def reserve_unit(self) -> None:
        if self._available_units <= 0:
            raise ValueError("No units available for reservation")
        self._available_units -= 1

    def release_unit(self) -> None:
        if self._available_units >= self._total_units:
            raise ValueError("All units are already available")
        self._available_units += 1


            