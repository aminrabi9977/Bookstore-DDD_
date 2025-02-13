import logging
from typing import Dict, Any
from bookstore.infrastructure.messaging.queue.rabbitmq import RabbitMQClient
from bookstore.infrastructure.persistence.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)

class QueueManager:
    def __init__(self, rabbitmq: RabbitMQClient, uow: UnitOfWork):
        self.rabbitmq = rabbitmq
        self.uow = uow

    async def initialize(self) -> None:
        await self.rabbitmq.subscribe(
            "database_sync",
            self.handle_database_sync)
        await self.rabbitmq.subscribe(
            "search_indexing",
            self.handle_search_indexing)
        await self.rabbitmq.subscribe(
            "reservation_reminders",
            self.handle_reservation_reminder)

    async def handle_database_sync(self, message: Dict[str, Any]) -> None:
        try:
            entity_type = message.get("entity_type")
            entity_id = message.get("entity_id")
            operation = message.get("operation")
            data = message.get("data", {})

            async with self.uow:
                if entity_type == "book":
                    if operation == "create":
                        await self.uow.book_search.add(data)
                    elif operation == "update":
                        await self.uow.book_search.update(data)
                    elif operation == "delete":
                        await self.uow.book_search.delete(entity_id)
                await self.uow.commit()
                logger.info(
                    f"Synchronized {entity_type} {entity_id} - {operation}"
                )
        except Exception as e:
            logger.error(f"Error in database sync: {str(e)}")
            raise

    async def handle_search_indexing(self, message: Dict[str, Any]) -> None:
        try:
            book_id = message.get("book_id")
            title = message.get("title")
            description = message.get("description")

            async with self.uow:
                await self.uow.book_search.index_book(
                    book_id,
                    title,
                    description)
                await self.uow.commit()
                logger.info(f"Indexed book {book_id} in search database")

        except Exception as e:
            logger.error(f"Error in search indexing: {str(e)}")
            raise

    async def handle_reservation_reminder(self, message: Dict[str, Any]) -> None:
        try:
            customer_id = message.get("customer_id")
            book_title = message.get("book_title")
            end_date = message.get("end_date")
            customer_phone = message.get("customer_phone")

            async with self.uow:
                reminder_text = (
                    f"reminder: Your reservation for '{book_title}' "
                    f"ends on {end_date}. Please return the book or extend "
                    "your reservation."
                )
                await self.uow.sms.send_sms(customer_phone, reminder_text)
                logger.info(f"Sent reminder to customer {customer_id}")

        except Exception as e:
            logger.error(f"Error sending reminder: {str(e)}")
            raise

    async def publish_database_sync(self,entity_type: str, entity_id: str,operation: str, data: Dict[str, Any]) -> None:
        message = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "operation": operation,
            "data": data
        }
        await self.rabbitmq.publish("database_sync", message)

    async def publish_search_indexing(self,book_id: str, title: str, description: str) -> None:
        message = {
            "book_id": book_id,
            "title": title,
            "description": description
        }
        await self.rabbitmq.publish("search_indexing", message)

    async def publish_reservation_reminder(self,customer_id: str,book_title: str, end_date: str,customer_phone: str) -> None:
        message = {
            "customer_id": customer_id,
            "book_title": book_title,
            "end_date": end_date,
            "customer_phone": customer_phone
        }
        await self.rabbitmq.publish(
            "reservation_reminders",
            message,
            priority=1)