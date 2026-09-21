from datetime import datetime, timezone
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with Session() as db:
        yield db
