import json
from typing import Optional, Any, Dict
from uuid import UUID
import aioredis
from datetime import datetime, timedelta

from bookstore.infrastructure.persistence.repository.base import CacheableRepository


class RedisCacheRepository(CacheableRepository):

    def __init__(self, redis: aioredis.Redis):
        self._redis = redis
        self._pending_operations: list = []

    async def get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        value = await self._redis.get(key)
        if value:
            return json.loads(value)
        return None



    async def set_cached(self, key: str,value: Dict[str, Any], ttl_seconds: int = 3600) -> None:
        self._pending_operations.append({
            'type': 'set',
            'key': key,
            'value': json.dumps(value),
            'ttl': ttl_seconds
        })

    async def invalidate_cached(self, key: str) -> None:
        self._pending_operations.append({
            'type': 'delete',
            'key': key
        })



    async def store_otp(self,phone: str, otp: str,ttl_seconds: int = 120 ) -> None:
        key = f"otp:{phone}"
        self._pending_operations.append({
            'type': 'set',
            'key': key,
            'value': otp,
            'ttl': ttl_seconds
        })
    async def verify_otp(self, phone: str, otp: str) -> bool:
        key = f"otp:{phone}"
        stored_otp = await self._redis.get(key)
        if stored_otp and stored_otp.decode() == otp:
            await self._redis.delete(key)
            return True
        return False



    async def track_otp_requests(self, phone: str) -> bool:
        key = f"otp_requests:{phone}"
        data = await self._redis.get(key)
        current_time = datetime.utcnow()
        
        if data:
            stored_data = json.loads(data)
            count = stored_data['count']
            last_request = datetime.fromisoformat(stored_data['timestamp'])

            if current_time - last_request < timedelta(minutes=2):
                if count >= 5:  # 5 darkhast dar 2 saniye
                    return False
            elif current_time - last_request < timedelta(hours=1):
                if count >= 10:  # 10 darkhast dar saat
                    return False
            else:
                count = 0
        else:
            count = 0
        new_data = {
            'count': count + 1,
            'timestamp': current_time.isoformat()
        }
        await self._redis.set(key,json.dumps(new_data), ex=3600)  # ba'de 1 saat monghazi mishe
        return True

    async def flush(self) -> None:
        if not self._pending_operations:
            return

        pipeline = self._redis.pipeline()
        for op in self._pending_operations:
            if op['type'] == 'set':
                pipeline.set(op['key'],
                    op['value'],
                    ex=op['ttl']
                )
            elif op['type'] == 'delete':
                pipeline.delete(op['key'])
        
        await pipeline.execute()
        self._pending_operations.clear()


    async def rollback(self) -> None:
        self._pending_operations.clear()