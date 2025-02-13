from typing import Optional
from uuid import UUID
from bookstore.application.commands.book_commands import CreateBook,UpdateBook, DeleteBook,AddBookUnits,RemoveBookUnits,  UpdateBookPrice
from bookstore.application.commands.base import CommandResult
from bookstore.domain.aggregates.book import Book
from bookstore.domain.value_objects.money import Money
from bookstore.infrastructure.persistence.unit_of_work import UnitOfWork
from bookstore.application.commands.command_handlers.base import CommandHandler, ValidationError, BusinessRuleViolation


class CreateBookHandler(CommandHandler[CreateBook]):
    async def handle(self, command: CreateBook) -> CommandResult:
        try:
            async with self.uow:
                existing_books = await self.uow.books.list(
                    filters={"isbn": command.isbn}
                )
                if existing_books:
                    raise ValidationError("ISBN already exists")
                book = Book(
                    title=command.title,
                    isbn=command.isbn,
                    price=Money(command.price),
                    author_id=command.author_id,
                    genre_id=command.genre_id,
                    description=command.description,
                    total_units=command.total_units
                )

                await self.uow.books.add(book)
                await self.uow.book_search.add(book)
                await self.uow.commit()

                return CommandResult(
                    success=True,
                    message="Book created sucessfully",
                    data={"book_id": str(book.id)}
                )

        except ValidationError as e:
            return CommandResult(
                success=False,
                message="Validation error",
                error=str(e))


        except Exception as e:
            return CommandResult(
                success=False,
                message="failed to create book",
                error=str(e)
            )


class UpdateBookHandler(CommandHandler[UpdateBook]):
    async def handle(self, command: UpdateBook) -> CommandResult:
        try:
            async with self.uow:
                book = await self.uow.books.get(command.id)
                if not book:
                    raise ValidationError("book not found")
                if command.title is not None:
                    book._title = command.title
                if command.price is not None:
                    book.change_price(Money(command.price))
                if command.description is not None:
                    book._description = command.description
                if command.genre_id is not None:
                    book._genre_id = command.genre_id

                await self.uow.books.update(book)
                await self.uow.book_search.update(book)
                await self.uow.commit()

                return CommandResult(success=True,
                    message="Book updated successfully")


        except ValidationError as e:
            return CommandResult(
                success=False,
                message="validation error",
                error=str(e))


        except Exception as e:
            return CommandResult(
                success=False,
                message="failed to update book",
                error=str(e))




class DeleteBookHandler(CommandHandler[DeleteBook]):
    async def handle(self, command: DeleteBook) -> CommandResult:
        try:
            async with self.uow:
                book = await self.uow.books.get(command.id)
                if not book:
                    raise ValidationError("book not found")
                reservations = await self.uow.reservations.get_active_reservations_for_book(command.id)
                if reservations:
                    raise BusinessRuleViolation("cannot delete book with active reservations")

                await self.uow.books.delete(command.id)
                await self.uow.book_search.delete(command.id)
                await self.uow.commit()

                return CommandResult(
                    success=True,
                    message="Book deleted successfully")

        except (ValidationError, BusinessRuleViolation) as e:
            return CommandResult(success=False,
                message=str(e),
                error=str(e))
        except Exception as e:
            return CommandResult(
                success=False,
                message="Failed to delete book",
                error=str(e))




class AddBookUnitsHandler(CommandHandler[AddBookUnits]):
    async def handle(self, command: AddBookUnits) -> CommandResult:
        try:
            async with self.uow:
                book = await self.uow.books.get(command.id)
                if not book:
                    raise ValidationError("Book not found")

                book.add_units(command.count)

                await self.uow.books.update(book)
                await self.uow.commit()
                return CommandResult(success=True,
                    message=f"added {command.count} units successfully")


        except ValidationError as e:
            return CommandResult(
                success=False,
                message="Validation error",
                error=str(e))


        except Exception as e:
            return CommandResult(
                success=False,
                message="Failed to add units",
                error=str(e))



class RemoveBookUnitsHandler(CommandHandler[RemoveBookUnits]):
    async def handle(self, command: RemoveBookUnits) -> CommandResult:
        try:
            async with self.uow:
                book = await self.uow.books.get(command.id)
                if not book:
                    raise ValidationError("Book not found")

                book.remove_units(command.count)
                await self.uow.books.update(book)
                await self.uow.commit()

                return CommandResult(
                    success=True,
                    message=f"removed {command.count} units successfull"
                )


        except ValidationError as e:
            return CommandResult(
                success=False,
                message="validation error",
                error=str(e)
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message="failed to remove units",
                error=str(e))




class UpdateBookPriceHandler(CommandHandler[UpdateBookPrice]):
    async def handle(self, command: UpdateBookPrice) -> CommandResult:
        try:
            async with self.uow:
                book = await self.uow.books.get(command.id)
                if not book:
                    raise ValidationError("book not found")
                book.change_price(Money(command.new_price))

                await self.uow.books.update(book)
                await self.uow.book_search.update(book)
                await self.uow.commit()

                return CommandResult(success=True,
                    message="price updated successfully"
                )



        except ValidationError as e:
            return CommandResult(success=False,
                message="validation error",
                error=str(e))
        except Exception as e:
            return CommandResult(success=False,
                message="failed to update price",
                error=str(e))