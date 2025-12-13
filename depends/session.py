from typing import Generator
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from fastapi import Request
from database import SessionLocal, redis_pool


def get_db_dep() -> Generator:
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


async def get_aioredis(request: Request) -> AsyncRedis:
    return request.app.state.aioredis


def get_redis(request: Request) -> Generator[Redis, None, None]:
    redis_client = Redis(connection_pool=redis_pool, decode_responses=True)
    try:
        yield redis_client
    except Exception as e:
        raise e
    finally:
        pass
