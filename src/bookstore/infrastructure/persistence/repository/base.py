from abc import ABC
from uuid import UUID
from typin import Generic, TypeVar, List, Dict, Any, Optional

from bookstore.domain.base import Entity


T = TypeVar('T', bound = Entity)
class BaseRepository(ABC, Generic[T]):

    @abstractmethod
    async def add(self, entity: T) -> None:
        raise NotImplementedError


    @abstractmethod
    async def get(self, id: UUID) -> Optional[T]:
        raise NotImplementedError


    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list(self, filters: Optional[Dict[str, Any]] = None, skip: int =0, limit: int = 50) -> List[T]:
        raise NotImplementedError

class SearchableRepository(BaseRepository[T]):

    @abstractmethod
    async def search(self, query: str, fields: List[str], skip: int: 0, limit: int = 50) -> List[T]:
        raise NotImplementedError

class CacheableRepository(BaseRepository[T]):
    @abstractmethod
    async def get_cache(self, id: UUID) -> Optional[T]:
        raise NotImplementedError

    @abstractmethod
    async def invalidate_cache(self, id: UUID) -> None:
        raise NotImplementedError

