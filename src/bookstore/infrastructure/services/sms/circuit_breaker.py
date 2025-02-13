from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any, Dict, Optional
import asyncio

import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      
    OPEN = "open"         
    HALF_OPEN = "half_open"  




class CircuitBreaker:
    def __init__(self,failure_threshold: int = 5, recovery_timeout: int = 60,half_open_timeout: int = 30):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = timedelta(seconds=recovery_timeout)
        self._half_open_timeout = timedelta(seconds=half_open_timeout)
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._last_failure_time: Optional[datetime] = None
        self._last_test_time: Optional[datetime] = None

    @property
    def state(self) -> CircuitState:
        return self._state


    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    async def call(self,func: Callable,*args: Any,**kwargs: Any) -> Any:
        if self._state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self._state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerError("Circuit is open")


        try:
            result = await func(*args, **kwargs)
            
            if self._state == CircuitState.HALF_OPEN:
                self._close_circuit()
                
            return result
            
        except Exception as e:
            self._handle_failure(e)
            raise



    def _handle_failure(self, exception: Exception) -> None:

        self._failures += 1
        self._last_failure_time = datetime.utcnow()
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
        elif self._failures >= self._failure_threshold:
            self._state = CircuitState.OPEN    
        logger.warning(
            f"Circuit breaker failure:{str(exception)}."
            f"State:{self._state.value} , Failures: {self._failures}"
        )



    def _should_attempt_recovery(self) -> bool:
        if not self._last_failure_time:
            return True
            
        return datetime.utcnow() - self._last_failure_time >= self._recovery_timeout



    def _close_circuit(self) -> None:
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._last_failure_time = None
        self._last_test_time = None
        logger.info("circuit breaker closed , retrning to normal operation")




class CircuitBreakerError(Exception):
    pass