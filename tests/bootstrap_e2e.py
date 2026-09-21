"""Creates only a test administrator; never imported by production services."""

import asyncio
from app.auth import password_hasher
from app.config import get_settings
from app.database import Session
from app.models import Admin, Role
from sqlalchemy import select


async def main():
    config = get_settings()
    if config.environment != "test" or "utility_e2e" not in config.database_url:
        raise SystemExit("Requires ENVIRONMENT=test and a dedicated utility_e2e database")
    async with Session() as db:
        if not await db.scalar(select(Admin).where(Admin.email == "e2e@example.com")):
            db.add(
                Admin(
                    name="E2E Administrator",
                    email="e2e@example.com",
                    role=Role.SUPER_ADMIN,
                    password_hash=password_hasher.hash("e2e-only-password-123"),
                )
            )
            await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
