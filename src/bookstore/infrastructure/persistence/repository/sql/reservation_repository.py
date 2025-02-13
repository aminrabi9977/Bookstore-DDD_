from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bookstore.domain.entities.reservation import Reservation, ReservationStatus
from bookstore.domain.value_objects.money import Money
from bookstore.infrastructure.persistence.repository.base import BaseRepository
from bookstore.infrastructure.persistence.repository.sql.models import reservations_table


class SQLReservationRepository(BaseRepository[Reservation]):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, reservation: Reservation) -> None:
        query = reservations_table.insert().values(
            id=reservation.id,
            customer_id=reservation.customer_id,
            book_id=reservation.book_id,
            price=reservation.price.amount,
            start_time=reservation.start_time,
            end_time=reservation.end_time,
            status=reservation.status,
            queue_position=reservation.queue_position,
            version=reservation.version,
            created_at=reservation.created_at,
            updated_at=reservation.updated_at
        )
        await self._session.execute(query)

    async def get(self, id: UUID) -> Optional[Reservation]:
        query = select(reservations_table).where(reservations_table.c.id == id)
        result = await self._session.execute(query)
        row = result.first()
        
        if row is None:
            return None
            
        return Reservation(
            customer_id=row.customer_id,
            book_id=row.book_id,
            price=Money(row.price),
            start_time=row.start_time,
            duration_days=(row.end_time - row.start_time).days,
            id=row.id
        )

    async def update(self, reservation: Reservation) -> None:
        query = (
            reservations_table.update()
            .where(
                reservations_table.c.id == reservation.id,
                reservations_table.c.version == reservation.version
            )
            .values(
                status=reservation.status,
                queue_position=reservation.queue_position,
                version=reservation.version + 1,
                updated_at=reservation.updated_at
            )
        )
        result = await self._session.execute(query)
        if result.rowcount == 0:
            raise OptimisticLockError(f"Reservation {reservation.id} was modified concurrently")

    async def delete(self, id: UUID) -> None:
        query = reservations_table.delete().where(reservations_table.c.id == id)
        await self._session.execute(query)

    async def list(self,filters: Optional[Dict[str, Any]] = None,skip: int = 0,limit: int = 50) -> List[Reservation]:
        query = select(reservations_table)
        
        if filters:
            conditions = []
            if 'customer_id' in filters:
                conditions.append(reservations_table.c.customer_id == filters['customer_id'])
            if 'book_id' in filters:
                conditions.append(reservations_table.c.book_id == filters['book_id'])
            if 'status' in filters:
                conditions.append(reservations_table.c.status == filters['status'])
            if conditions:
                query = query.where(*conditions)
        
        query = query.offset(skip).limit(limit)
        result = await self._session.execute(query)
        
        return [
            Reservation(
                customer_id=row.customer_id,
                book_id=row.book_id,
                price=Money(row.price),
                start_time=row.start_time,
                duration_days=(row.end_time - row.start_time).days,
                id=row.id
            )
            for row in result
        ]

    async def get_active_reservations_for_book(
        self,
        book_id: UUID,
        current_time: Optional[datetime] = None
    ) -> List[Reservation]:
        if current_time is None:
            current_time = datetime.utcnow()
            
        query = select(reservations_table).where(
            and_(
                reservations_table.c.book_id == book_id,
                reservations_table.c.status == ReservationStatus.ACTIVE,
                reservations_table.c.start_time <= current_time,
                reservations_table.c.end_time >= current_time
            )
        )
        result = await self._session.execute(query)
        
        return [
            Reservation(
                customer_id=row.customer_id,
                book_id=row.book_id,
                price=Money(row.price),
                start_time=row.start_time,
                duration_days=(row.end_time - row.start_time).days,
                id=row.id
            )
            for row in result
        ]

    async def get_customer_active_reservations(self,customer_id: UUID) -> List[Reservation]:
        query = select(reservations_table).where(
            and_(
                reservations_table.c.customer_id == customer_id,
                reservations_table.c.status == ReservationStatus.ACTIVE
            )
        )
        result = await self._session.execute(query)
        
        return [
            Reservation(
                customer_id=row.customer_id,
                book_id=row.book_id,
                price=Money(row.price),
                start_time=row.start_time,
                duration_days=(row.end_time - row.start_time).days,
                id=row.id
            )
            for row in result
        ]

    async def get_overdue_reservations(self,current_time: Optional[datetime] = None) -> List[Reservation]:
        if current_time is None:
            current_time = datetime.utcnow()
            
        query = select(reservations_table).where(
            and_(
                reservations_table.c.status == ReservationStatus.ACTIVE,
                reservations_table.c.end_time < current_time
            )
        )
        result = await self._session.execute(query)
        
        return [
            Reservation(
                customer_id=row.customer_id,
                book_id=row.book_id,
                price=Money(row.price),
                start_time=row.start_time,
                duration_days=(row.end_time - row.start_time).days,
                id=row.id
            )
            for row in result
        ]


class OptimisticLockError(Exception):
    pass