from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, field_validator
import re

class UserRegisterRequest(BaseModel):  
    email: EmailStr  
    password: str  
    phone: str  

    @field_validator('password')  
    def check_password_strength(cls, value):  
        if len(value) < 8:  
            raise ValueError('password must be at least 8')  
        return value  

    @field_validator('phone')  
    def validate_phone(cls, value):   
        if not re.match(r'^\+?1?\d{9,15}$', value):  
            raise ValueError('phone number format is invalid')  
        return value  

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    phone: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class BookCreateRequest(BaseModel):
    title: str
    isbn: str
    price: Decimal
    author_id: UUID
    genre_id: UUID
    description: Optional[str] = None
    total_units: int = 0

    @field_validator('isbn')  
    def validate_isbn(cls, value):  
        if not re.match(r'^\d{10}(\d{3})?$', value):  
            raise ValueError('Must be 13 digit')  
        return value  

class BookUpdateRequest(BaseModel):
    title: Optional[str] = None
    price: Optional[Decimal] = None
    description: Optional[str] = None
    genre_id: Optional[UUID] = None

class BookResponse(BaseModel):
    id: UUID
    title: str
    isbn: str
    price: Decimal
    author_id: UUID
    genre_id: UUID
    description: Optional[str]
    total_units: int
    available_units: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReservationCreateRequest(BaseModel):
    book_id: UUID
    start_time: datetime
    duration_days: int

class ReservationResponse(BaseModel):
    id: UUID
    customer_id: UUID
    book_id: UUID
    price: Decimal
    start_time: datetime
    end_time: datetime
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class CustomerUpdateRequest(BaseModel):
    subscription_type: Optional[str] = None

class WalletTransactionRequest(BaseModel):
    amount: Decimal

class CustomerResponse(BaseModel):
    id: UUID
    user_id: UUID
    subscription_type: str
    wallet_balance: Decimal
    active_reservations: int
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    size: int
    pages: int

class ErrorResponse(BaseModel):
    detail: str