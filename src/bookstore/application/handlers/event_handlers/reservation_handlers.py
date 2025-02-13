from datetime import datetime
from bookstore.domain.events.book_events import BookCreated, BookPriceChanged,BookUnitAdded,BookUnitRemoved
from bookstore.infrastructure.messaging.queue.events import BookSearchIndexingRequired,DatabaseSyncRequired, CacheInvalidationRequired
from bookstore.application.handlers.event_handlers.base import EventHandler
from typing import Union
class BookCreatedHandler(EventHandler[BookCreated]):
    async def handle(self, event: BookCreated) -> None:
        async with self.uow:
            await self.uow.message_bus.publish(
                BookSearchIndexingRequired(
                    book_id=event.aggregate_id,
                    title=event.title,
                    description=event.description,
                    isbn=event.isbn
                )
            )
            await self.uow.message_bus.publish(
                CacheInvalidationRequired(
                    cache_key=f"books:list"
                )
            )

            await self.uow.commit()




class BookPriceChangedHandler(EventHandler[BookPriceChanged]):
    async def handle(self, event: BookPriceChanged) -> None:
        async with self.uow:
            await self.uow.message_bus.publish(
                DatabaseSyncRequired(
                    entity_type="book",
                    entity_id=event.aggregate_id,
                    operation="update",
                    data={"price": str(event.new_price)}
                )
            )
            await self.uow.message_bus.publish(
                CacheInvalidationRequired(
                    cache_key=f"book:price:{event.aggregate_id}"
                )
            )
            await self.uow.commit()


class BookInventoryChangedHandler(EventHandler[Union[BookUnitAdded , BookUnitRemoved]]):
    async def handle(self, event: Union[BookUnitAdded , BookUnitRemoved]) -> None:
        async with self.uow:
            book = await self.uow.books.get(event.aggregate_id)
            if not book:
                return
            await self.uow.message_bus.publish(
                DatabaseSyncRequired(
                    entity_type="book",
                    entity_id=event.aggregate_id,
                    operation="update",
                    data={
                        "total_units": book.total_units,
                        "available_units": book.available_units
                    }
                )
            )

            await self.uow.message_bus.publish(
                CacheInvalidationRequired(
                    cache_key=f"book:inventory:{event.aggregate_id}"
                )
            )
            await self.uow.commit()