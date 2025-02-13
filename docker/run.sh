echo "building and starting containers..."
docker-compose up --build -d

echo "waiting for databases to be ready..."
sleep 10


echo "initializing databases..."
docker-compose exec app python -m src.bookstore.infrastructure.persistence.database init_db

echo "deployment complete! The application is running at http://localhost:8000"
echo "API documentation is available at http://localhost:8000/docs"
echo "rabbitMQ management interface is available at http://localhost:15672"