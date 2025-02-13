from types import TracebackType
from typing import Optional, Type
from abc import ABC,abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession

from bookstore.infrastructure.persistence.repository.sql.book_repository import SQLBookRepository
from bookstore.infrastructure.persistence.repository.sql.user_repository import SQLUserRepository
from bookstore.infrastructure.persistence.repository.sql.customer_repository import SQLCustomerRepository
from bookstore.infrastructure.persistence.repository.sql.reservation_repository import SQLReservationRepository
from bookstore.infrastructure.persistence.repository.mongo.book_search_repository import MongoBookRepository
from bookstore.infrastructure.persistence.repository.redis.cache_repository import RedisCacheRepository


class UnitOfWork(ABC):

    books: SQLBookRepository
    users: SQLUserRepository
    customers: SQLCustomerRepository
    reservations: SQLReservationRepository
    book_search: MongoBookRepository
    cache: RedisCacheRepository

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError


class SqlAlchemyUnitOfWork(UnitOfWork):

    def __init__(self,session_factory: AsyncSession,mongo_client, redis_client):
        self.session_factory = session_factory
        self.mongo_client = mongo_client
        self.redis_client = redis_client

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self.session_factory()
        self.books = SQLBookRepository(self.session)
        self.users = SQLUserRepository(self.session)
        self.customers = SQLCustomerRepository(self.session)
        self.reservations = SQLReservationRepository(self.session)
        
        self.book_search = MongoBookRepository(self.mongo_client)
        
        self.cache = RedisCacheRepository(self.redis_client)
        
        return self

    async def __aexit__(self,exc_type: Optional[Type[BaseException]],exc_val: Optional[BaseException],exc_tb: Optional[TracebackType],) -> None:
        try:
            await super().__aexit__(exc_type, exc_val, exc_tb)
        finally:
            await self.session.close()

    async def commit(self) -> None:
        try:
            await self.session.commit()
            await self.book_search.flush()
   
            await self.cache.flush()
        except:
            await self.rollback()
            raise

    async def rollback(self) -> None:

        await self.session.rollback()
        await self.book_search.rollback()
        await self.cache.rollback()


class FakeUnitOfWork(UnitOfWork):
    def __init__(self):
        self.committed = False
        self.books = FakeBookRepository()
        self.users = FakeUserRepository()
        self.customers = FakeCustomerRepository()
        self.reservations = FakeReservationRepository()
        self.book_search = FakeBookSearchRepository()
        self.cache = FakeCacheRepository()

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass