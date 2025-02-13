from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bookstore.domain.aggregates.customer import Customer, SubscriptionType
from bookstore.domain.value_objects.money import Money
from bookstore.infrastructure.persistence.repository.base import BaseRepository
from bookstore.infrastructure.persistence.repository.sql.models import customers_table


class SQLCustomerRepository(BaseRepository[Customer]):


    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, customer: Customer) -> None:
        query = customers_table.insert().values(
            id=customer.id,
            user_id=customer.user_id,
            subscription_type=customer.subscription_type,
            subscription_end=customer.subscription_end,
            wallet_balance=customer.wallet_balance.amount,
            active_reservations=customer._active_reservations,
            version=customer.version,
            created_at=customer.created_at,
            updated_at=customer.updated_at
        )
        await self._session.execute(query)

    async def get(self, id: UUID) -> Optional[Customer]:
        query = select(customers_table).where(customers_table.c.id == id)
        result = await self._session.execute(query)
        row = result.first()
        
        if row is None:
            return None
            
        return Customer(
            user_id=row.user_id,
            subscription_type=SubscriptionType(row.subscription_type),
            wallet_balance=Money(row.wallet_balance),
            id=row.id
        )

    async def get_by_user_id(self, user_id: UUID) -> Optional[Customer]:
        query = select(customers_table).where(customers_table.c.user_id == user_id)
        result = await self._session.execute(query)
        row = result.first()
        
        if row is None:
            return None
            
        return Customer(
            user_id=row.user_id,
            subscription_type=SubscriptionType(row.subscription_type),
            wallet_balance=Money(row.wallet_balance),
            id=row.id
        )

    async def update(self, customer: Customer) -> None:
        query = (
            customers_table.update()
            .where(
                customers_table.c.id == customer.id,
                customers_table.c.version == customer.version
            )
            .values(
                subscription_type=customer.subscription_type,
                subscription_end=customer.subscription_end,
                wallet_balance=customer.wallet_balance.amount,
                active_reservations=customer._active_reservations,
                version=customer.version + 1,
                updated_at=customer.updated_at
            )
        )
        result = await self._session.execute(query)
        if result.rowcount == 0:
            raise OptimisticLockError(f"Customer {customer.id} was modified concurrently")

    async def delete(self, id: UUID) -> None:
        """Delete a customer by ID."""
        query = customers_table.delete().where(customers_table.c.id == id)
        await self._session.execute(query)

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Customer]:
        """List customers with optional filtering and pagination."""
        query = select(customers_table)
        
        if filters:
            conditions = []
            if 'subscription_type' in filters:
                conditions.append(customers_table.c.subscription_type == filters['subscription_type'])
            if conditions:
                query = query.where(*conditions)
        
        query = query.offset(skip).limit(limit)
        result = await self._session.execute(query)
        
        return [
            Customer(
                user_id=row.user_id,
                subscription_type=SubscriptionType(row.subscription_type),
                wallet_balance=Money(row.wallet_balance),
                id=row.id
            )
            for row in result
        ]


class OptimisticLockError(Exception):
    """Raised when optimistic locking detects a concurrent modification."""
    pass