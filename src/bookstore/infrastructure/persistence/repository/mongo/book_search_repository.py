from typing import List, Optional, Dict, Any
from uuid import UUID
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, TEXT, IndexModel

from bookstore.domain.aggregates.book import Book
from bookstore.domain.value_objects.money import Money
from bookstore.infrastructure.persistence.repository.base import SearchableRepository


class MongoBookRepository(SearchableRepository[Book]):
    def __init__(self, client: AsyncIOMotorClient):
        self._db = client.bookstore
        self._collection = self._db.books
        self._pending_operations: List[Dict] = []

    async def initialize(self) -> None:
        await self._collection.create_index([
            ("title", TEXT),
            ("description", TEXT)
        ])

        await self._collection.create_index([("isbn", ASCENDING)], unique=True)
        await self._collection.create_index([("genre_id", ASCENDING)])
        await self._collection.create_index([("author_id", ASCENDING)])

    async def add(self, book: Book) -> None:
        document = {
            "_id": str(book.id),
            "title": book.title,
            "isbn": book.isbn,
            "price": float(book.price.amount),
            "author_id": str(book.author_id),
            "genre_id": str(book.genre_id),
            "description": book.description,
            "total_units": book.total_units,
            "available_units": book.available_units
        }
        self._pending_operations.append(
            {"insert": document}
        )

    async def get(self, id: UUID) -> Optional[Book]:
        document = await self._collection.find_one({"_id": str(id)})
        if document is None:
            return None
            
        return self._document_to_book(document)

    async def update(self, book: Book) -> None:
        document = {
            "title": book.title,
            "isbn": book.isbn,
            "price": float(book.price.amount),
            "author_id": str(book.author_id),
            "genre_id": str(book.genre_id),
            "description": book.description,
            "total_units": book.total_units,
            "available_units": book.available_units
        }
        self._pending_operations.append(
            {"update": {"_id": str(book.id), "document": document}}
        )

    async def delete(self, id: UUID) -> None:
        self._pending_operations.append(
            {"delete": str(id)}
        )

    async def search(self,query: str,fields: List[str],skip: int = 0,limit: int = 50) -> List[Book]:
        search_query = {"$text": {"$search": query}}
        
        cursor = self._collection.find(search_query)
        cursor.skip(skip).limit(limit)
        
        documents = await cursor.to_list(length=limit)
        return [self._document_to_book(doc) for doc in documents]

    async def list(self,filters: Optional[Dict[str, Any]] = None,skip: int = 0,limit: int = 50) -> List[Book]:
        query = {}
        if filters:
            if 'genre_id' in filters:
                query['genre_id'] = str(filters['genre_id'])
            if 'author_id' in filters:
                query['author_id'] = str(filters['author_id'])
        
        cursor = self._collection.find(query)
        cursor.skip(skip).limit(limit)
        
        documents = await cursor.to_list(length=limit)
        return [self._document_to_book(doc) for doc in documents]

    def _document_to_book(self, document: Dict) -> Book:
        return Book(
            id=UUID(document['_id']),
            title=document['title'],
            isbn=document['isbn'],
            price=Money(document['price']),
            author_id=UUID(document['author_id']),
            genre_id=UUID(document['genre_id']),
            description=document['description'],
            total_units=document['total_units']
        )

    async def flush(self) -> None:
        if not self._pending_operations:
            return
            
        async with await self._db.client.start_session() as session:
            async with session.start_transaction():
                for operation in self._pending_operations:
                    if 'insert' in operation:
                        await self._collection.insert_one(
                            operation['insert'],
                            session=session
                        )
                    elif 'update' in operation:
                        await self._collection.update_one(
                            {'_id': operation['update']['_id']},
                            {'$set': operation['update']['document']},
                            session=session
                        )
                    elif 'delete' in operation:
                        await self._collection.delete_one(
                            {'_id': operation['delete']},
                            session=session
                        )
                self._pending_operations.clear()

    async def rollback(self) -> None:
        self._pending_operations.clear()