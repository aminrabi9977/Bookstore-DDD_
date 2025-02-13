from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional

from bookstore.interfaces.api.schemas import (UserRegisterRequest, UserLoginRequest, UserResponse,
    CustomerResponse,  CustomerUpdateRequest, WalletTransactionRequest)
from bookstore.interfaces.api.middleware.authentication import create_access_token, get_current_user_id
from bookstore.application.commands.user_commands import RegisterUser, CreateCustomer, ChangeSubscription, AddWalletBalance,GenerateOTP
from bookstore.domain.aggregates.user import UserRole
from bookstore.domain.aggregates.customer import SubscriptionType
from bookstore.infrastructure.persistence.database import get_session
from bookstore.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(request: UserRegisterRequest,session = Depends(get_session)):
    async with SqlAlchemyUnitOfWork(session) as uow:
        command = RegisterUser(
            email=request.email,
            password=request.password,
            phone=request.phone,
            role=UserRole.CUSTOMER
        )
        
        result = await uow.message_bus.execute(command)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error
            )

        customer_command = CreateCustomer(
            user_id=result.data["user_id"]
        )
        customer_result = await uow.message_bus.execute(customer_command)
        
        if not customer_result.success:
            raise HTTPException(
                status_code=400,
                detail=customer_result.error
            )

        user = await uow.users.get(result.data["user_id"])
        return UserResponse.model_validate(user)

@router.post("/login")
async def login_user(request: UserLoginRequest, session = Depends(get_session)):

    async with SqlAlchemyUnitOfWork(session) as uow:
        user = await uow.users.get_by_email(request.email)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
        if not user.verify_password(request.password):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )

        return {"access_token": access_token, "token_type": "bearer"}

@router.post("/verify-otp")
async def verify_otp(otp: str,phone: str,session = Depends(get_session)):
    async with SqlAlchemyUnitOfWork(session) as uow:
        is_valid = await uow.cache.verify_otp(phone, otp)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="invalid otp"
            )
        return {"message": "otp verified successfully"}

@router.post("/resend-otp")
async def resend_otp(phone: str, session = Depends(get_session)):
    async with SqlAlchemyUnitOfWork(session) as uow:
        command = GenerateOTP(phone=phone)
        result = await uow.message_bus.execute(command)
        if not result.success:
            raise HTTPException(status_code=400,
                detail=result.error
            )
        return {"message": "otp sent successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request,
    session = Depends(get_session)):
    user_id = get_current_user_id(request)
    async with SqlAlchemyUnitOfWork(session) as uow:
        user = await uow.users.get(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="user not found"
            )
        return UserResponse.model_validate(user)

@router.get("/me/customer", response_model=CustomerResponse)
async def get_customer_profile(request: Request,
    session = Depends(get_session)):
    user_id = get_current_user_id(request)
    async with SqlAlchemyUnitOfWork(session) as uow:
        customer = await uow.customers.get_by_user_id(user_id)
        if not customer:
            raise HTTPException(
                status_code=404,
                detail="customer profile not found")
        return CustomerResponse.model_validate(customer)

@router.put("/me/customer", response_model=CustomerResponse)
async def update_customer_profile(request: Request,profile_update: CustomerUpdateRequest,session = Depends(get_session)):
    user_id = get_current_user_id(request)
    async with SqlAlchemyUnitOfWork(session) as uow:
        customer = await uow.customers.get_by_user_id(user_id)
        if not customer:
            raise HTTPException(
                status_code=404,
                detail="customer profile not found")

        if profile_update.subscription_type:
            command = ChangeSubscription(
                customer_id=customer.id,
                new_subscription=SubscriptionType[profile_update.subscription_type])
            result = await uow.message_bus.execute(command)
            
            if not result.success:
                raise HTTPException(
                    status_code=400,
                    detail=result.error)

        customer = await uow.customers.get_by_user_id(user_id)
        return CustomerResponse.model_validate(customer)

@router.post("/me/wallet/credit", response_model=CustomerResponse)
async def credit_wallet(request: Request,
    transaction: WalletTransactionRequest,
    session = Depends(get_session)):
    user_id = get_current_user_id(request)
    async with SqlAlchemyUnitOfWork(session) as uow:
        customer = await uow.customers.get_by_user_id(user_id)
        if not customer:
            raise HTTPException(
                status_code=404,
                detail="customer profile not found")

        command = AddWalletBalance(
            customer_id=customer.id,
            amount=transaction.amount)
        result = await uow.message_bus.execute(command)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error)

        customer = await uow.customers.get_by_user_id(user_id)
        return CustomerResponse.model_validate(customer)