from datetime import datetime, timedelta
from typing import Optional
from bookstore.application.commands.reservation_commands import CreateReservation,CancelReservation, CompleteReservation, ExtendReservation, ProcessQueuedReservation,AddToReservationQueue
from bookstore.application.commands.base import CommandResult
from bookstore.domain.entities.reservation import Reservation, ReservationStatus
from bookstore.domain.value_objects.money import Money
from bookstore.application.commands.command_handlers.base import CommandHandler, ValidationError, BusinessRuleViolation


class CreateReservationHandler(CommandHandler[CreateReservation]):
    async def handle(self, command: CreateReservation) -> CommandResult:
        try:
            async with self.uow:
                customer = await self.uow.customers.get(command.customer_id)
                if not customer:
                    raise ValidationError("customer not found")
                if not customer.can_make_reservation():
                    raise BusinessRuleViolation(
                        "maximum reservations reached or invalid subscription"
                    )
                book = await self.uow.books.get(command.book_id)
                if not book:
                    raise ValidationError("book not found")

                daily_rate = Money(1000) 
                total_price = daily_rate * command.duration_days

                if customer.wallet_balance < total_price:
                    raise BusinessRuleViolation("insufficient wallet balance")
                if book.available_units > 0:
                    reservation = Reservation(customer_id=command.customer_id,
                        book_id=command.book_id,
                        price=total_price,
                        start_time=command.start_time,
                        duration_days=command.duration_days)
                    book.reserve_unit()
                    customer.add_reservation()
                    customer.debit_wallet(total_price)

                    await self.uow.reservations.add(reservation)
                    await self.uow.books.update(book)
                    await self.uow.customers.update(customer)
                    await self.uow.commit()
                    return CommandResult(success=True,
                        message="reservation created successfully",
                        data={"reservation_id": str(reservation.id)}
                    )
                else:
                    return await self._add_to_queue(command)

        except (ValidationError, BusinessRuleViolation) as e:
            return CommandResult(success=False,
                message=str(e),
                error=str(e)
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message="failed to crete reservation",
                error=str(e)
            )


    async def _add_to_queue(self, command: CreateReservation) -> CommandResult:
        queue_handler = AddToReservationQueueHandler(self.uow)
        queue_command = AddToReservationQueue(customer_id=command.customer_id,
            book_id=command.book_id,
            requested_days=command.duration_days
        )
        return await queue_handler.handle(queue_command)

class CancelReservationHandler(CommandHandler[CancelReservation]):
    async def handle(self, command: CancelReservation) -> CommandResult:
        try:
            async with self.uow:
                reservation = await self.uow.reservations.get(command.id)
                if not reservation:
                    raise ValidationError("reservation not found")
                if reservation.customer_id != command.customer_id:
                    raise ValidationError("unauthorized to cancel this reservation")

                if reservation.status != ReservationStatus.ACTIVE:
                    raise BusinessRuleViolation(
                        "only active reservations can be cancelled")
                reservation.cancel()

                book = await self.uow.books.get(reservation.book_id)
                customer = await self.uow.customers.get(reservation.customer_id)
                book.release_unit()
                customer.remove_reservation()

                if datetime.utcnow() < reservation.start_time:
                    customer.credit_wallet(reservation.price)

                await self.uow.reservations.update(reservation)
                await self.uow.books.update(book)
                await self.uow.customers.update(customer)


                await self._process_queue(reservation.book_id)
                await self.uow.commit()
                return CommandResult(success=True,
                    message="reservation cancelled successfully")


        except (ValidationError, BusinessRuleViolation) as e:
            return CommandResult(success=False,
                message=str(e),
                error=str(e))

        except Exception as e:
            return CommandResult(success=False,
                message="failed to cancel reservation",
                error=str(e))

    async def _process_queue(self, book_id) -> None:
        queue_handler = ProcessQueuedReservationHandler(self.uow)
        await queue_handler.handle(ProcessQueuedReservation(book_id=book_id))



class CompleteReservationHandler(CommandHandler[CompleteReservation]):
    async def handle(self, command: CompleteReservation) -> CommandResult:
        try:
            async with self.uow:
                reservation = await self.uow.reservations.get(command.id)
                if not reservation:
                    raise ValidationError("reservation not found")
                if reservation.customer_id != command.customer_id:
                    raise ValidationError("unauthorized to complete this reservation")


                reservation.complete()
                book = await self.uow.books.get(reservation.book_id)
                customer = await self.uow.customers.get(reservation.customer_id)
                book.release_unit()
                customer.remove_reservation()

                

                await self.uow.reservations.update(reservation)
                await self.uow.books.update(book)
                await self.uow.customers.update(customer)
                await self._process_queue(reservation.book_id)
                await self.uow.commit()
                return CommandResult(success=True,message="reservation completed successfully")

        except (ValidationError, BusinessRuleViolation) as e:
            return CommandResult(success=False,
                message=str(e),
                error=str(e))

        except Exception as e:
            return CommandResult(success=False,
                message="failed to complete reservation",
                error=str(e)
            )

    async def _process_queue(self, book_id) -> None:
        queue_handler = ProcessQueuedReservationHandler(self.uow)
        await queue_handler.handle(ProcessQueuedReservation(book_id=book_id))


class ExtendReservationHandler(CommandHandler[ExtendReservation]):
    async def handle(self, command: ExtendReservation) -> CommandResult:
        try:
            async with self.uow:
                reservation = await self.uow.reservations.get(command.id)
                if not reservation:
                    raise ValidationError("reservation not found")

                if reservation.customer_id != command.customer_id:
                    raise ValidationError("unauthorized to extend this reservation")
                daily_rate = Money(1000)  
                additional_cost = daily_rate * command.additional_days

                customer = await self.uow.customers.get(command.customer_id)
                if customer.wallet_balance < additional_cost:
                    raise BusinessRuleViolation("insufficient wallet balance")
                new_end_time = reservation._end_time + timedelta(
                    days=command.additional_days
                )
                reservation._end_time = new_end_time
                customer.debit_wallet(additional_cost)

                await self.uow.reservations.update(reservation)
                await self.uow.customers.update(customer)
                await self.uow.commit()

                return CommandResult(
                    success=True,
                    message="reservation extended successfully")

        except (ValidationError, BusinessRuleViolation) as e:
            return CommandResult(success=False,
                message=str(e),
                error=str(e))

        except Exception as e:
            return CommandResult(
                success=False,
                message="failed to extend reservation",
                error=str(e)
            )


class ProcessQueuedReservationHandler(CommandHandler[ProcessQueuedReservation]):
    async def handle(self, command: ProcessQueuedReservation) -> CommandResult:
        try:
            async with self.uow:
                book = await self.uow.books.get(command.book_id)
                if not book or book.available_units <= 0:
                    return CommandResult(success=True,
                        message="no units available for queue procesing"
                    )
                queued = await self.uow.reservations.list(
                    filters={
                        "book_id": command.book_id,
                        "status": ReservationStatus.PENDING },
                    limit=1)


                if not queued:
                    return CommandResult(success=True,
                        message="no queued reservtions to process")

                next_reservation = queued[0]
                customer = await self.uow.customers.get(next_reservation.customer_id)

                next_reservation.activate()
                book.reserve_unit()
                customer.add_reservation()

                await self.uow.reservations.update(next_reservation)
                await self.uow.books.update(book)
                await self.uow.customers.update(customer)
                await self.uow.commit()

                return CommandResult(success=True,
                    message="queue reservation processed successfully")


        except Exception as e:
            return CommandResult(success=False,
                message="failed to process queued reservation",
                error=str(e))


class AddToReservationQueueHandler(CommandHandler[AddToReservationQueue]):
    async def handle(self, command: AddToReservationQueue) -> CommandResult:
        try:
            async with self.uow:
                customer = await self.uow.customers.get(command.customer_id)
                book = await self.uow.books.get(command.book_id)

                if not customer or not book:
                    raise ValidationError("customer or book not found")

                reservation = Reservation(
                    customer_id=command.customer_id,
                    book_id=command.book_id,
                    price=Money(0),  
                    start_time=datetime.utcnow(),
                    duration_days=command.requested_days)

                await self.uow.reservations.add(reservation)
                await self.uow.commit()

                return CommandResult(success=True,
                    message="added to reservation queue successfully",
                    data={"queue_position": reservation.queue_position})


        except ValidationError as e:
            return CommandResult(
                success=False,
                message=str(e),
                error=str(e))


        except Exception as e:
            return CommandResult(success=False,
                message="failed to add to reservation queue",
                error=str(e))