import os
from uuid import uuid4
from unittest.mock import AsyncMock
import pytest
from fastapi import HTTPException
from redis.asyncio import Redis
from app.auth import rate_limit


async def test_rate_limit_fails_closed(monkeypatch):
    redis = AsyncMock()
    redis.eval.side_effect = ConnectionError("unavailable")
    monkeypatch.setattr("app.auth.redis", redis)
    with pytest.raises(HTTPException) as result:
        await rate_limit("test", 3, 60)
    assert result.value.status_code == 503


async def test_redis_atomic_limit_and_expiry(monkeypatch):
    url = os.environ.get("TEST_REDIS_URL")
    if not url:
        pytest.skip("Set TEST_REDIS_URL for Redis integration")
    redis = Redis.from_url(url, decode_responses=True)
    monkeypatch.setattr("app.auth.redis", redis)
    key = "integration:" + str(uuid4())
    try:
        await rate_limit(key, 2, 60)
        await rate_limit(key, 2, 60)
        with pytest.raises(HTTPException) as result:
            await rate_limit(key, 2, 60)
        assert result.value.status_code == 429
        assert 0 < await redis.ttl("rate:" + key) <= 60
    finally:
        await redis.delete("rate:" + key)
        await redis.aclose()
