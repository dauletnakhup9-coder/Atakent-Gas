import asyncio
import json
import logging

import redis.asyncio as aioredis
from fastapi import WebSocket

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("realtime")

REDIS_CHANNEL = "applications_events"


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast_local(self, message: dict) -> None:
        payload = json.dumps(message, default=str)
        dead = []
        for ws in list(self._connections):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)


manager = ConnectionManager()
_redis_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def publish_event(event_type: str, payload: dict) -> None:
    """Publishes an event to Redis so every backend replica's websocket clients get it."""
    message = {"type": event_type, "data": payload}
    try:
        await get_redis().publish(REDIS_CHANNEL, json.dumps(message, default=str))
    except Exception:
        logger.exception("Failed to publish realtime event to redis, broadcasting locally only")
        await manager.broadcast_local(message)


async def redis_listener() -> None:
    """Background task: subscribes to Redis and fans out to local websocket connections."""
    while True:
        try:
            pubsub = get_redis().pubsub()
            await pubsub.subscribe(REDIS_CHANNEL)
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                data = json.loads(message["data"])
                await manager.broadcast_local(data)
        except Exception:
            logger.exception("Realtime redis listener crashed, retrying in 5s")
            await asyncio.sleep(5)
