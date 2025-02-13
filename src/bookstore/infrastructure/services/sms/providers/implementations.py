import aiohttp
from bookstore.infrastructure.services.sms.providers.base import SMSProvider, SMSProviderError


class KavenegarProvider(SMSProvider):
    BASE_URL = "https://api.kavenegar.com/v1"
    async def send_sms(self, phone: str, message: str) -> bool:
        try:
            url = f"{self.BASE_URL}/{self.api_key}/sms/send.json"
            params = {
                "receptor": phone,
                "message": message
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as response:
                    if response.status == 200:
                        return True
                    raise SMSProviderError(
                        f"Kavenegar API error: {response.status}",
                        provider="kavenegar"
                    )
        except aiohttp.ClientError as e:
            raise SMSProviderError(
                f"Kavenegar connection error: {str(e)}",
                provider="kavenegar"
            )


