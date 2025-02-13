from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bookstore.domain.aggregates.user import User, UserRole
from bookstore.infrastructure.persistence.repository.base import BaseRepository
from bookstore.infrastructure.persistence.repository.sql.models import users_table


class SQLUserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, user: User) -> None:
        query = users_table.insert().values(
            id=user.id,
            email=user.email,
            password_hash=user._password_hash,
            phone=user.phone,
            role=user.role,
            is_verified=user.is_verified,
            last_login=user.last_login,
            failed_login_attempts=user._failed_login_attempts,
            version=user.version,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        await self._session.execute(query)

    async def get(self, id: UUID) -> Optional[User]:
        query = select(users_table).where(users_table.c.id == id)
        result = await self._session.execute(query)
        row = result.first()
        
        if row is None:
            return None    
        return User(
            email=row.email,
            password_hash=row.password_hash,
            phone=row.phone,
            role=UserRole(row.role),
            is_verified=row.is_verified,
            id=row.id
        )

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(users_table).where(users_table.c.email == email)
        result = await self._session.execute(query)
        row = result.first()
        if row is None:
            return None
            
        return User(
            email=row.email,
            password_hash=row.password_hash,
            phone=row.phone,
            role=UserRole(row.role),
            is_verified=row.is_verified,
            id=row.id
        )

    async def get_by_phone(self, phone: str) -> Optional[User]:
        query = select(users_table).where(users_table.c.phone == phone)
        result = await self._session.execute(query)
        row = result.first()
        if row is None:
            return None
            
        return User(
            email=row.email,
            password_hash=row.password_hash,
            phone=row.phone,
            role=UserRole(row.role),
            is_verified=row.is_verified,
            id=row.id
        )

    async def update(self, user: User) -> None:
        query = (
            users_table.update()
            .where(
                users_table.c.id == user.id,
                users_table.c.version == user.version
            )
            .values(
                email=user.email,
                password_hash=user._password_hash,
                phone=user.phone,
                role=user.role,
                is_verified=user.is_verified,
                last_login=user.last_login,
                failed_login_attempts=user._failed_login_attempts,
                version=user.version + 1,
                updated_at=user.updated_at
            )
        )
        result = await self._session.execute(query)
        if result.rowcount == 0:
            raise OptimisticLockError(f"User {user.id} was modified concurrently")

    async def delete(self, id: UUID) -> None:
        query = users_table.delete().where(users_table.c.id == id)
        await self._session.execute(query)

    async def list(self,filters: Optional[Dict[str, Any]] = None,skip: int = 0,limit: int = 50) -> List[User]:

        query = select(users_table)
        
        if filters:
            conditions = []
            if 'role' in filters:
                conditions.append(users_table.c.role == filters['role'])
            if 'is_verified' in filters:
                conditions.append(users_table.c.is_verified == filters['is_verified'])
            if conditions:
                query = query.where(*conditions)
        
        query = query.offset(skip).limit(limit)
        result = await self._session.execute(query)
        
        return [
            User(
                email=row.email,
                password_hash=row.password_hash,
                phone=row.phone,
                role=UserRole(row.role),
                is_verified=row.is_verified,
                id=row.id
            )
            for row in result
        ]


class OptimisticLockError(Exception):
    pass