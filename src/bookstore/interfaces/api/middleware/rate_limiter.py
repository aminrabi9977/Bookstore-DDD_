from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import aioredis

redis = aioredis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if await self._should_limit_request(request):
            raise HTTPException(
                status_code=429,
                detail=" many request. Please try again ."
            )

        return await call_next(request)

    async def _should_limit_request(self, request: Request) -> bool:
        client_ip = request.client.host
        path = request.url.path
        if path.startswith("/api/users/login"):
            return await self._check_limit(
                f"login:{client_ip}",
                max_requests=5,
                window_seconds=300
            )
        elif path.startswith("/api/users/otp"):
            return await self._check_limit(
                f"otp:{client_ip}",
                max_requests=3,
                window_seconds=600
            )
        elif path.startswith("/api/books/search"):
            return await self._check_limit(
                f"search:{client_ip}",
                max_requests=30,
                window_seconds=60
            )

        return await self._check_limit(
            f"default:{client_ip}",
            max_requests=100,
            window_seconds=60
        )


    async def _check_limit(self,key: str,max_requests: int,window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds

        async with redis.pipeline() as pipe:
            await pipe.zremrangebyscore(key, 0, window_start)
            await pipe.zcard(key)
            await pipe.zadd(key, {str(now): now})
            await pipe.expire(key, window_seconds)
            
            results = await pipe.execute()

        request_count = results[1]
        return request_count >= max_requests