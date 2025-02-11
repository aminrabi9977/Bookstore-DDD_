
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Table, Column, ForeignKey,
    String, Integer, Numeric, Text, DateTime, Enum,
    MetaData
            )
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from bookstore.domain.aggregates.user import UserRole
from bookstore.domain.aggregates.customer import SubscriptionType
from bookstore.domain.entities.reservation import ReservationStatus

metadata = MetaData()

books_table = Table(
    'books',
    metadata,
    Column('id', PostgresUUID, primary_key=True),
    Column('title', String(255), nullable=False),
    Column('isbn', String(13), unique=True, nullable=False, index=True),
    Column('price', Numeric(10, 2), nullable=False),
    Column('author_id', PostgresUUID, ForeignKey('users.id'), nullable=False),
    Column('genre_id', PostgresUUID, ForeignKey('genres.id'), nullable=False),
    Column('description', Text),
    Column('total_units', Integer, nullable=False, default=0),
    Column('available_units', Integer, nullable=False, default=0),
    Column('version', Integer, nullable=False, default=1),  
    Column('created_at', DateTime(timezone=True), default=datetime.utcnow),
    Column('updated_at', DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
)


users_table = Table(
    'users',
    metadata,
    Column('id', PostgresUUID, primary_key=True),
    Column('email', String(255), unique=True, nullable=False),
    Column('password_hash', String(255), nullable=False),
    Column('phone', String(20), unique=True, nullable=False),
    Column('role', Enum(UserRole), nullable=False, default=UserRole.CUSTOMER),
    Column('is_verified', Boolean, nullable=False, default=False),
    Column('last_login', DateTime(timezone=True)),
    Column('failed_login_attempts', Integer, default=0),
    Column('version', Integer, nullable=False, default=1),
    Column('created_at', DateTime(timezone=True), default=datetime.utcnow),
    Column('updated_at', DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
)

customers_table = Table(
    'customers',
    metadata,
    Column('id', PostgresUUID, primary_key=True),
    Column('user_id', PostgresUUID, ForeignKey('users.id'), unique=True, nullable=False),
    Column('subscription_type', Enum(SubscriptionType), nullable=False, default=SubscriptionType.FREE),
    Column('subscription_end', DateTime(timezone=True)),
    Column('wallet_balance', Numeric(10, 2), nullable=False, default=0),
    Column('active_reservations', Integer, nullable=False, default=0),
    Column('version', Integer, nullable=False, default=1),
    Column('created_at', DateTime(timezone=True), default=datetime.utcnow),
    Column('updated_at', DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
)

genres_table = Table(
    'genres',
    metadata,
    Column('id', PostgresUUID, primary_key=True),
    Column('name', String(100), unique=True, nullable=False),
    Column('description', Text),
    Column('version', Integer, nullable=False, default=1),
    Column('created_at', DateTime(timezone=True), default=datetime.utcnow),
    Column('updated_at', DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
)

reservations_table = Table(
    'reservations',
    metadata,
    Column('id', PostgresUUID, primary_key=True),
    Column('customer_id', PostgresUUID, ForeignKey('customers.id'), nullable=False),
    Column('book_id', PostgresUUID, ForeignKey('books.id'), nullable=False),
    Column('price', Numeric(10, 2), nullable=False),
    Column('start_time', DateTime(timezone=True), nullable=False),
    Column('end_time', DateTime(timezone=True), nullable=False),
    Column('status', Enum(ReservationStatus), nullable=False),
    Column('queue_position', Integer),
    Column('version', Integer, nullable=False, default=1),
    Column('created_at', DateTime(timezone=True), default=datetime.utcnow),
    Column('updated_at', DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
)