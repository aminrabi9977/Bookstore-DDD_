# BookStore API

Bookstore with DDD pattern

## Features
- User authentication with JWT and OTP verification
- Book management with search functionality
- Subscription system with different tiers
- Reservation system with queue management
- Wallet system for payments
- Rate limiting
- Event-driven architecture
- Multi-database synchronization

## Technologies
- FastAPI for REST API
- PostgreSQL for main database
- MongoDB for search functionality
- Redis for caching and rate limiting
- RabbitMQ for message queuing
- Docker for containerization

## Prerequisites
- Docker
- Docker Compose
- Python 3.9.19+

## Installation
1. Clone the repository:

!git clone <repository-url>
cd bookstore

2. Create .env file:
cp .env.example .env

3. Run the application:
chmod +x run.sh
./run.sh


The application will be available at:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- RabbitMQ Management: http://localhost:15672

## Project Structure


booksrore-ddd/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│   └── init.sql
├   └── run.sh
├── docs/
│   └── api/
│       └── postman/
│           └── collection.json
├── src/
│   ├── bookstore/
│   │   ├── domain/          
│   │   ├── application/     
│   │   ├── infrastructure/  
│   │   └── interfaces/      
│   
├
└── README.md
└── .env.example
└── requirement.txt


## API Documentation

### Authentication

- POST /api/users/register - Register new user
- POST /api/users/login - Login user
- POST /api/users/verify-otp - Verify OTP

### Books

- GET /api/books - List books
- GET /api/books/search - Search books
- POST /api/books - Create book
- PUT /api/books/{id} - Update book
- DELETE /api/books/{id} - Delete book

### Reservations

- POST /api/reservations - Create reservation
- GET /api/reservations - List user's reservations
- POST /api/reservations/{id}/cancel - Cancel reservation
- POST /api/reservations/{id}/extend - Extend reservation

Full API documentation is available in the Postman collection and at /docs endpoint.

## Monitoring

- RabbitMQ Management Interface: http://localhost:15672
  - Username: guest
  - Password: guest

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error
