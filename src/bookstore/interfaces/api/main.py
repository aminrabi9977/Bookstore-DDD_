from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bookstore.interfaces.api.routes import books, users, reservations
from bookstore.interfaces.api.middleware.authentication import AuthenticationMiddleware
from bookstore.interfaces.api.middleware.rate_limiter import RateLimitMiddleware
from bookstore.infrastructure.persistence.database import init_db

app = FastAPI(
    title="BookStore API" )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthenticationMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(books.router, prefix="/api/books", tags=["books"])
app.include_router(reservations.router, prefix="/api/reservations", tags=["reservations"])




@app.get("/health")
async def health_check():
    return {"status": "healthy"}