from abc import ABC, abstractmethod
from typing import Optional

class SMSProvider(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def send_sms(self, phone: str, message: str) -> bool:
        raise NotImplementedError




class SMSProviderError(Exception):    
    def __init__(self, message: str, provider: Optional[str] = None):
        self.provider = provider
        super().__init__(message)