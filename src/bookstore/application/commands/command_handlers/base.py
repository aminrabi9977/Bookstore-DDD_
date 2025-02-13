from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from bookstore.application.commands.base import Command, CommandResult
from bookstore.infrastructure.persistence.unit_of_work import UnitOfWork

C = TypeVar('C', bound=Command)


class CommandHandler(ABC, Generic[C]):
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    @abstractmethod
    async def handle(self, command: C) -> CommandResult:
        raise NotImplementedError



class ValidationError(Exception):
    pass
class AuthorizationError(Exception):
    pass
class BusinessRuleViolation(Exception):
    pass