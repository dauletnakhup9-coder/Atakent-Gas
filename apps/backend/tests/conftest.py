import os
import tempfile

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("BOT_INTERNAL_API_KEY", "test-internal-key")
os.environ.setdefault("BOT_TOKEN", "")
os.environ.setdefault("UPLOAD_DIR", os.path.join(tempfile.gettempdir(), "gas_service_test_uploads"))

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.auth.security import hash_password
from app.core.rate_limit import limiter
from app.database import Base, get_db
from app.main import app
from app.models.admin import Admin
from app.models.enums import AdminRole

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    limiter.reset()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def super_admin(db_session):
    admin = Admin(
        name="Super Admin",
        email="super@example.com",
        password_hash=hash_password("password123"),
        role=AdminRole.SUPER_ADMIN,
        active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def operator_admin(db_session):
    admin = Admin(
        name="Operator",
        email="operator@example.com",
        password_hash=hash_password("password123"),
        role=AdminRole.OPERATOR,
        active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    return TestClient(app)


def auth_header(client, email: str, password: str) -> dict:
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
