import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

DEFAULT_THROTTLE_SECONDS = 0.7


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = DEFAULT_THROTTLE_SECONDS) -> None:
        self.rate_limit = rate_limit
        self._last_seen: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        now = time.monotonic()
        last = self._last_seen.get(user.id)
        if last is not None and (now - last) < self.rate_limit:
            return None

        self._last_seen[user.id] = now
        return await handler(event, data)
