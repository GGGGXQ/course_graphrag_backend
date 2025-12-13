import os
import json
from dataclasses import dataclass

from nano_graphrag.base import BaseKVStorage
import redis.asyncio as aioredis

from utils.logger_util import logger


@dataclass
class RedisKVStorage(BaseKVStorage):
    """Custom redis key-value storage"""
    def __post_init__(self):
        redis_parms = self.global_config.get("addon_params", {})
        self.redis_url = redis_parms.get("redis_url", "redis://:@localhost:6379/1")
        self._namespace = f"kv_store:{self.namespace}"
        self._redis = aioredis.from_url(self.redis_url)
        logger.info(f"Prepared Redis client for namespace: {self._namespace} (connection not tested yet)")
    
    async def all_keys(self) -> list[str]:
        keys = await self._redis.hkeys(self._namespace)
        return [k.decode("utf-8") for k in keys]
    
    async def get_by_id(self, id):
        """
        根据 id 获取数据
        Redis 存储中每个字段的值是 JSON 字符串
        """
        value = await self._redis.hget(self._namespace, id)
        return json.loads(value) if value else None

    async def get_by_ids(self, ids, fields=None):
        """
        批量获取多个 id 对应的记录
        若指定 fields，则仅返回部分字段
        """
        if not ids:
            return []
        values = await self._redis.hmget(self._namespace, ids)
        results = []
        for val in values:
            if val is None:
                results.append(None)
                continue
            data = json.loads(val)
            if fields is not None:
                data = {k: v for k, v in data.items() if k in fields}
            results.append(data)
        return results
    
    async def filter_keys(self, data: list[str]) -> set[str]:
        """
        返回 data 中不在 Redis hash 中的 key
        """
        if not data:
            return set()
        existing_keys = await self._redis.hkeys(self._namespace)
        existing_keys = {k.decode("utf-8") for k in existing_keys}
        return set([k for k in data if k not in existing_keys])
    
    async def upsert(self, data: dict[str, dict]):
        """
        将多个键值对插入或更新到 Redis
        """
        if not data:
            return {}
        serialized = {k: json.dumps(v) for k, v in data.items()}
        await self._redis.hset(self._namespace, mapping=serialized)

    async def drop(self):
        """
        删除当前命名空间下所有数据
        """
        await self._redis.delete(self._namespace)
        logger.info(f"Dropped Redis namespace: {self._namespace}")
