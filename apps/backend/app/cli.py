import argparse
import asyncio
import getpass
from sqlalchemy import select
from app.auth import password_hasher
from app.database import Session
from app.models import Admin, Role
from app.schemas import CreateAdmin


async def create_admin():
    parser = argparse.ArgumentParser(description="Create SUPER_ADMIN (password entered securely)")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    password = getpass.getpass("Password (12+ characters): ")
    if password != getpass.getpass("Repeat password: "):
        raise SystemExit("Passwords differ")
    data = CreateAdmin(email=args.email, name=args.name, password=password, role=Role.SUPER_ADMIN)
    async with Session() as db:
        if await db.scalar(select(Admin).where(Admin.email == str(data.email).lower())):
            raise SystemExit("Email already exists")
        db.add(
            Admin(
                email=str(data.email).lower(),
                name=data.name,
                password_hash=password_hasher.hash(password),
                role=data.role,
            )
        )
        await db.commit()
    print("SUPER_ADMIN created")


if __name__ == "__main__":
    asyncio.run(create_admin())
