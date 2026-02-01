from contextlib import asynccontextmanager, contextmanager

from .settings import db_settings
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 비동기 DATABASE_URL (asyncpg 사용)
ASYNC_DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{db_settings.POSTGRES_USER}:{db_settings.POSTGRES_PASSWORD}@"
    f"{db_settings.POSTGRES_HOST}:{db_settings.POSTGRES_PORT}/"
    f"{db_settings.POSTGRES_DB}"
)

# 동기 DATABASE_URL (psycopg2 사용)
SYNC_DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{db_settings.POSTGRES_USER}:{db_settings.POSTGRES_PASSWORD}@"
    f"{db_settings.POSTGRES_HOST}:{db_settings.POSTGRES_PORT}/"
    f"{db_settings.POSTGRES_DB}"
)

# 비동기 엔진과 세션
# pool_pre_ping: 연결 사용 전에 유효성 검사
# pool_size: 기본 연결 풀 크기
# max_overflow: 풀이 가득 찼을 때 추가로 생성할 수 있는 연결 수
# pool_recycle: 연결 재사용 시간 (초) - PostgreSQL idle_session_timeout 전에 재연결
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, expire_on_commit=False)

# 동기 엔진과 세션
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)

Base = declarative_base()


# 비동기 세션 함수들
async def get_async_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_async_session_context():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 동기 세션 함수들
def get_sync_session():
    with SessionLocal() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


@contextmanager
def get_sync_session_context():
    with SessionLocal() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
