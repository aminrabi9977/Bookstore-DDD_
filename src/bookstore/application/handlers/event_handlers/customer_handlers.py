from bookstore.domain.events.customer_events import CustomerCreated,SubscriptionChanged,WalletCredited,WalletDebited, CustomerReachedSpendingThreshold
from bookstore.infrastructure.messaging.queue.events import DatabaseSyncRequired,CacheInvalidationRequired, PaymentProcessed
from bookstore.application.handlers.event_handlers.base import EventHandler
from typing import Union

class CustomerCreatedHandler(EventHandler[CustomerCreated]):
    async def handle(self, event: CustomerCreated) -> None:
        async with self.uow:
            user = await self.uow.users.get(event.user_id)
            if user:
                await self.uow.sms.send_sms(
                    user.phone,
                    "welcome to  bookstore! Your account has been creatd succesfully.")

            await self.uow.message_bus.publish(
                CacheInvalidationRequired(
                    cache_key="customers:list"
                )
            )

            await self.uow.commit()




class SubscriptionChangedHandler(EventHandler[SubscriptionChanged]):
    async def handle(self, event: SubscriptionChanged) -> None:
        async with self.uow:
            customer = await self.uow.customers.get(event.aggregate_id)
            if not customer:
                return

            if event.old_type.value < event.new_type.value:
                await self.uow.message_bus.publish(
                    PaymentProcessed(customer_id=event.aggregate_id,
                        amount=customer.SUBSCRIPTION_PRICES[event.new_type].amount,
                        payment_type="subscription",
                        reference_id=event.aggregate_id
                    )
                )

            await self.uow.message_bus.publish(
                CacheInvalidationRequired(
                    cache_key=f"customer:{event.aggregate_id}"
                )
            )
            user = await self.uow.users.get(customer.user_id)
            if user:
                await self.uow.sms.send_sms(
                    user.phone,
                    f"Your subscription has been changed to {event.new_type.value}."
                )

            await self.uow.commit()



class WalletTransactionHandler(EventHandler[Union[WalletCredited ,WalletDebited]]):
    async def handle(self, event: Union[WalletCredited , WalletDebited]) -> None:
        async with self.uow:
            await self.uow.message_bus.publish(
                CacheInvalidationRequired(
                    cache_key=f"customer:wallet:{event.aggregate_id}"
                )
            )

            transaction_type = (
                "credit" if isinstance(event, WalletCredited) else "debit"
            )
            await self.uow.message_bus.publish(
                DatabaseSyncRequired(entity_type="wallet_transaction",
                    entity_id=event.aggregate_id,
                    operation="create",
                    data={
                        "type": transaction_type,
                        "amount": str(event.amount),
                        "timestamp": event.occurred_on.isoformat()}
                )
            )

            await self.uow.commit()

class SpendingThresholdHandler(EventHandler[CustomerReachedSpendingThreshold]):
    async def handle(self, event: CustomerReachedSpendingThreshold) -> None:
        async with self.uow:
            customer = await self.uow.customers.get(event.aggregate_id)
            if not customer:
                return
            user = await self.uow.users.get(customer.user_id)
            if not user:
                return

            await self.uow.sms.send_sms(
                user.phone,
                f"congra! You've spent {event.total_spent} Toman "
                "and are eligible for a free subscription upgrade!"
            )
            await self.uow.commit()
