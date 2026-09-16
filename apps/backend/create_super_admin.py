"""CLI helper to bootstrap the first SUPER_ADMIN account.

Usage: python create_super_admin.py --email admin@example.com --password secret --name "Admin"
"""
import argparse
import asyncio

from app.auth.security import hash_password
from app.database import AsyncSessionLocal
from app.models.admin import Admin
from app.models.enums import AdminRole
from app.repositories.admin_repo import AdminRepository


async def main(email: str, password: str, name: str) -> None:
    async with AsyncSessionLocal() as db:
        repo = AdminRepository(db)
        existing = await repo.get_by_email(email.lower())
        if existing:
            print(f"Admin with email {email} already exists (id={existing.id}).")
            return

        admin = Admin(
            name=name,
            email=email.lower(),
            password_hash=hash_password(password),
            role=AdminRole.SUPER_ADMIN,
            active=True,
        )
        created = await repo.create(admin)
        print(f"Created SUPER_ADMIN #{created.id}: {created.email}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", default="Super Admin")
    args = parser.parse_args()
    asyncio.run(main(args.email, args.password, args.name))
