from redis.asyncio import Redis
from fastapi import Request


async def get_aioredis(request: Request) -> Redis:
    return request.app.state.aioredis
