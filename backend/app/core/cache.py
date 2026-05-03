import time
from typing import Any


class InMemoryCache:
    """開發用記憶體快取，生產環境替換為 Redis。"""

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}

    async def get(self, key: str) -> Any | None:
        if key in self._store:
            value, expiry = self._store[key]
            if expiry == 0 or time.time() < expiry:
                return value
            del self._store[key]
        return None

    async def set(self, key: str, value: Any, ttl: int = 0) -> None:
        expiry = time.time() + ttl if ttl > 0 else 0
        self._store[key] = (value, expiry)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def increment(self, key: str, ttl: int = 0) -> int:
        current = await self.get(key)
        new_val = (current or 0) + 1
        await self.set(key, new_val, ttl)
        return new_val


# Singleton
cache = InMemoryCache()
