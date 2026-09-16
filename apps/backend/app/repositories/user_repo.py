from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_telegram_id(self, telegram_user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.telegram_user_id == telegram_user_id))
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_user_id: int,
        telegram_username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> User:
        user = await self.get_by_telegram_id(telegram_user_id)
        if user:
            changed = False
            if user.telegram_username != telegram_username:
                user.telegram_username = telegram_username
                changed = True
            if user.first_name != first_name:
                user.first_name = first_name
                changed = True
            if user.last_name != last_name:
                user.last_name = last_name
                changed = True
            if changed:
                await self.db.commit()
                await self.db.refresh(user)
            return user

        user = User(
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            first_name=first_name,
            last_name=last_name,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
