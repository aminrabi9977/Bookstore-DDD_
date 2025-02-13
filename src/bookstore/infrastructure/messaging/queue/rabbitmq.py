import json
import logging
from typing import Any, Callable, Dict
import aio_pika
from aio_pika import Message, connect_robust
from aio_pika.abc import AbstractIncomingMessage

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.connection = None
        self.channel = None
        self._handlers: Dict[str, Callable] = {}


    async def connect(self) -> None:
        try:
            self.connection = await connect_robust(self.connection_url)
            self.channel = await self.connection.channel()
            logger.info("connected to RabbitMQ successfully")
        except Exception as e:
            logger.error(f"failed to connect to RabbitMQ: {str(e)}")
            raise
    async def close(self) -> None:
        if self.connection:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")



    async def declare_queue(self, queue_name: str) -> None:
        if not self.channel:
            raise RuntimeError("nt connected to RabbitMQ")
            
        await self.channel.declare_queue(
            queue_name,
            durable=True )
        logger.debug(f"Declared queue: {queue_name}")

    async def publish(self,queue_name: str, message: Dict[str, Any], priority: int = 0 ) -> None:
        if not self.channel:
            raise RuntimeError("not connected to RabbitMQ")
        try:
            await self.declare_queue(queue_name)
            message_bytes = json.dumps(message).encode()
            message_obj = Message(
                message_bytes,
                delivery_mode=2,  
                priority=priority,
                content_type="application/json"
            )
            await self.channel.default_exchange.publish(
                message_obj,
                routing_key=queue_name)
            
            logger.debug(f"published message to queue {queue_name}")
        except Exception as e:
            logger.error(f"failed to publish message: {str(e)}")
            raise

    async def subscribe(self,queue_name: str,callback: Callable[[Dict[str, Any]], None]) -> None:
        if not self.channel:
            raise RuntimeError("not connected to RabbitMQ")

        try:
            await self.declare_queue(queue_name)
            
            self._handlers[queue_name] = callback
            queue = await self.channel.declare_queue(queue_name, durable=True)
            await queue.consume(self._message_handler)
            
            logger.info(f"subscribed to queue: {queue_name}")
            
        except Exception as e:
            logger.error(f"failed to subscribe to queue: {str(e)}")
            raise

    async def _message_handler(self, message: AbstractIncomingMessage) -> None:
        async with message.process():
            try:
                payload = json.loads(message.body.decode())
                queue_name = message.routing_key
                handler = self._handlers.get(queue_name)
                if not handler:
                    logger.warning(f"no handler for queue: {queue_name}")
                    return
                await handler(payload)
                logger.debug(f"processed message from queue {queue_name}")
                
            except Exception as e:
                logger.error(f"error processing message: {str(e)}")
                await message.nack(requeue=True)
                return
            await message.ack()