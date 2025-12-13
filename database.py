from contextlib import contextmanager
from redis import ConnectionPool
import redis
from redis.asyncio import ConnectionPool as AsyncConnectionPool
import redis.exceptions
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import config

engine = create_engine(
    config.SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# 创建 Redis 连接池
redis_pool = ConnectionPool.from_url(
    config.REDIS_URL,
    max_connections=50,
    retry_on_timeout=True,
    health_check_interval=30,
    socket_connect_timeout=5,
    socket_timeout=5,
    socket_keepalive=True,
    socket_keepalive_options={},
    retry_on_error=[redis.exceptions.ConnectionError, redis.exceptions.TimeoutError],
)

aio_redis_pool = AsyncConnectionPool.from_url(
    config.REDIS_URL,
    max_connections=50,
    retry_on_timeout=True,
    health_check_interval=30,
    socket_connect_timeout=5,
    socket_timeout=5,
    socket_keepalive=True,
    socket_keepalive_options={},
    retry_on_error=[redis.exceptions.ConnectionError, redis.exceptions.TimeoutError],
)


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        raise e
    finally:
        db.close()
