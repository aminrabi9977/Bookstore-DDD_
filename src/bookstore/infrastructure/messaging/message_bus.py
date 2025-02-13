from typing import Dict, List, Type, Callable, Any, Awaitable
import logging

from dataclasses import dataclass

logger = logging.getLogger(__name__)


CommandHandler = Callable[..., Awaitable[Any]]
EventHandler = Callable[..., Awaitable[None]]


@dataclass
class Command:
    pass


@dataclass
class Event:
    pass


class MessageBus:
    def __init__(self):
        self._command_handlers: Dict[Type[Command], CommandHandler] = {}
        self._event_handlers: Dict[Type[Event], List[EventHandler]] = {}


    def register_command_handler(self, command_type: Type[Command],handler: CommandHandler) -> None:
        if command_type in self._command_handlers:
            raise ValueError(f"Handler already registered for command: {command_type}")   
        self._command_handlers[command_type] = handler
        logger.debug(f"Registered handler for command {command_type.__name__}")






    def register_event_handler(self,event_type: Type[Event],
        handler: EventHandler) -> None:
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.debug(
            f"Registered handler for event {event_type.__name__} "
            f"(total handlers:{len(self._event_handlers[event_type])})")

    async def execute(self, command: Command) -> Any:
        command_type = type(command)
        handler = self._command_handlers.get(command_type)
        if not handler:
            raise ValueError(f"No handler registered for: {command_type}")
            

        logger.debug(command_type.__name__)
        return await handler(command)




    async def publish(self, event: Event) -> None:
        event_type = type(event)
        handlers = self._event_handlers.get(event_type, [])       
        logger.debug(
            f"Publishing event:{event_type.__name__}"
            f"{len(handlers)} handlers")
        
        for handler in handlers:
            try:
                await handler(event)

            except Exception as e:
                logger.error(
                    f"Error {event_type.__name__}: {str(e)}",
                    exc_info=True )





    def clear_handlers(self) -> None:
        self._command_handlers.clear()
        self._event_handlers.clear()
        logger.debug("Cleared all message handlers.")