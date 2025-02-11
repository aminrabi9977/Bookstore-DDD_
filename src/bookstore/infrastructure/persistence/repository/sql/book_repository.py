from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bookstore.domain.aggregates.book import Book
from bookstore.domain.value_objects.money import Money
from bookstore.domain.base import BaseRepository
from bookstore.infrastructure.persistence.repository.sql.models import books_table


class SQLBookRepository(BaseRepository[Book]):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, book: Book) -> None:
        query = books_table.insert().values(
            id=book.id,
            title=book.title,
            isbn=book.isbn,
            price=book.price.amount,
            author_id=book.author_id,
            genre_id=book.genre_id,
            description=book.description,
            total_units=book.total_units,
            available_units=book.available_units,
            version=book.version,
            created_at=book.created_at,
            updated_at=book.updated_at
        )
        await self._session.execute(query)

    async def get(self, id: UUID) -> Optional[Book]:
        query = select(books_table).where(books_table.c.id == id)
        result = await self._session.execute(query)
        row = result.first()
        
        if row is None:
            return None        
        return Book(
            id=row.id,
            title=row.title,
            isbn=row.isbn,
            price=Money(row.price),
            author_id=row.author_id,
            genre_id=row.genre_id,
            description=row.description,
            total_units=row.total_units
        )

    async def update(self, book: Book) -> None:
        query = (
            books_table.update()
            .where(
                books_table.c.id == book.id,
                books_table.c.version == book.version
            )
            .values(
                title=book.title,
                isbn=book.isbn,
                price=book.price.amount,
                author_id=book.author_id,
                genre_id=book.genre_id,
                description=book.description,
                total_units=book.total_units,
                available_units=book.available_units,
                version=book.version + 1,
                updated_at=book.updated_at
            )
        )
        result = await self._session.execute(query)
        if result.rowcount == 0:
            raise OptimisticLockError(f"Book {book.id} was modified concurrently")

    async def delete(self, id: UUID) -> None:
        query = books_table.delete().where(books_table.c.id == id)
        await self._session.execute(query)

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Book]:
        query = select(books_table)
        
        if filters:
            conditions = []
            if 'genre_id' in filters:
                conditions.append(books_table.c.genre_id == filters['genre_id'])
            if 'author_id' in filters:
                conditions.append(books_table.c.author_id == filters['author_id'])
            if conditions:
                query = query.where(*conditions)
        
        query = query.offset(skip).limit(limit)
        result = await self._session.execute(query)
        
        return [
            Book(
                id=row.id,
                title=row.title,
                isbn=row.isbn,
                price=Money(row.price),
                author_id=row.author_id,
                genre_id=row.genre_id,
                descriptioss=row.total_units
            )
            for row in result
        ]


class OptimisticLockError(Exception):
    pass