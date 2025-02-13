import logging
from typing import List, Dict, Optional
from bookstore.infrastructure.services.sms.circuit_breaker import CircuitBreaker
from bookstore.infrastructure.services.sms.providers.base import SMSProvider, SMSProviderError
from bookstore.infrastructure.services.sms.providers.implementations import KavenegarProvider


logger = logging.getLogger(__name__)


class SMSService:
    def __init__(self,providers_config: Dict[str, str],failure_threshold: int = 3, recovery_timeout: int = 60):
        self._providers: List[SMSProvider] = []
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        if 'kavenegar' in providers_config:
            self._providers.append(
                KavenegarProvider(providers_config['kavenegar'])
            )
            self._circuit_breakers['kavenegar'] = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout
            )

        if not self._providers:
            raise ValueError("No SMS providers")

    async def send_sms(self, phone: str, message: str) -> bool:

        errors = []
        
        for provider in self._providers:
            provider_name = provider.__class__.__name__.lower()
            circuit_breaker = self._circuit_breakers[provider_name]
            
            try:
                success = await circuit_breaker.call(
                    provider.send_sms,
                    phone,
                    message
                )
                
                if success:
                    logger.info(
                        f"SMS with provider: {provider_name}"
                    )
                    return True
                    
            except Exception as e:
                error_msg = f"Provider {provider_name} failed: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        raise SMSServiceError(
            errors=errors
        )

    async def send_otp(self, phone: str, otp: str) -> bool:
        message = f"Your verification code is: {otp}"
        return await self.send_sms(phone, message)


class SMSServiceError(Exception):
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        self.errors = errors or []
        error_details = "\n".join(self.errors)
        super().__init__(f"{message}\nDetails:\n{error_details}")