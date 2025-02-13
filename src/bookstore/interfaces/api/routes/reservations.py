from fastapi import APIRouter, Depends, HTTPException, Request, Query
from typing import List
from uuid import UUID

from bookstore.interfaces.api.schemas import ReservationCreateRequest,ReservationResponse,PaginatedResponse
from bookstore.interfaces.api.middleware.authentication import get_current_user_id
from bookstore.application.commands.reservation_commands import CreateReservation,CancelReservation,CompleteReservation,ExtendReservation
from bookstore.infrastructure.persistence.database import get_session
from bookstore.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter()

@router.post("", response_model=ReservationResponse)
async def create_reservation(
    request: Request,
    reservation_data: ReservationCreateRequest,
    session = Depends(get_session)):
    user_id = get_current_user_id(request)
    async with SqlAlchemyUnitOfWork(session) as uow:
        customer = await uow.customers.get_by_user_id(user_id)
        if not customer:
            raise HTTPException(
                status_code=404,
                detail="customer profile not found")

        command = CreateReservation(
            customer_id=customer.id,
            book_id=reservation_data.book_id,
            start_time=reservation_data.start_time,
            duration_days=reservation_data.duration_days)
        
        result = await uow.message_bus.execute(command)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error)

        reservation = await uow.reservations.get(result.data["reservation_id"])
        return ReservationResponse.model_validate(reservation)




@router.get("", response_model=PaginatedResponse)
async def list_reservations(request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    session = Depends(get_session)):
    user_id = get_current_user_id(request)
    async with SqlAlchemyUnitOfWork(session) as uow:
        customer = await uow.customers.get_by_user_id(user_id)
        if not customer:
            raise HTTPException(
                status_code=404,
                detail="customer profile not found")

        skip = (page - 1) * size
        reservations = await uow.reservations.list(
            filters={"customer_id": customer.id},
            skip=skip,
            limit=size)
        
        total = len(await uow.reservations.list(
            filters={"customer_id": customer.id}))
        
        return PaginatedResponse(
            items=[ReservationResponse.model_validate(r) for r in reservations],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size)





@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
    request: Request,
    reservation_id: UUID,
    session = Depends(get_session)):
    user_id = get_current_user_id(request)
    async with SqlAlchemyUnitOfWork(session) as uow:
        customer = await uow.customers.get_by_user_id(user_id)
        if not customer:
            raise HTTPException(
                status_code=404,
                detail="Customer profile not found")

        reservation = await uow.reservations.get(reservation_id)
        if not reservation or reservation.customer_id != customer.id:
            raise HTTPException(
                status_code=404,
                detail="reservation not found")

        return ReservationResponse.model_validate(reservation)



@router.post("/{reservation_id}/cancel")
async def cancel_reservation(
    request: Request,
    reservation_id: UUID,
    session = Depends(get_session)):
    user_id = get_current_user_id(request)
    async with SqlAlchemyUnitOfWork(session) as uow:
        customer = await uow.customers.get_by_user_id(user_id)
        if not customer:
            raise HTTPException(
                status_code=404,
                detail="customer profile not found")

        command = CancelReservation(
            id=reservation_id,
            customer_id=customer.id)
        
        result = await uow.message_bus.execute(command)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error)

        return {"message": "Reservation cancelled successfully"}

@router.post("/{reservation_id}/complete")
async def complete_reservation(
    request: Request,
    reservation_id: UUID,
    session = Depends(get_session)):
    user_id = get_current_user_id(request)
    async with SqlAlchemyUnitOfWork(session) as uow:
        customer = await uow.customers.get_by_user_id(user_id)
        if not customer:
            raise HTTPException(
                status_code=404,
                detail="customer profile not found")

        command = CompleteReservation(
            id=reservation_id,
            customer_id=customer.id)
        
        result = await uow.message_bus.execute(command)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error)

        return {"message": "Reservation completed successfully"}


@router.post("/{reservation_id}/extend")
async def extend_reservation(
    request: Request,
    reservation_id: UUID,
    additional_days: int = Query(..., gt=0),
    session = Depends(get_session)):
    user_id = get_current_user_id(request)
    async with SqlAlchemyUnitOfWork(session) as uow:
        customer = await uow.customers.get_by_user_id(user_id)
        if not customer:
            raise HTTPException(status_code=404,
                detail="customer profile not found")

        command = ExtendReservation(
            id=reservation_id,
            customer_id=customer.id,
            additional_days=additional_days)
        
        result = await uow.message_bus.execute(command)
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error)

        return {"message": f"Reservation extended by {additional_days} days"}