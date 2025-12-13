"""
Custom llms for nano-graphrag settings
"""

from openai import AsyncOpenAI
from nano_graphrag.base import BaseKVStorage
from nano_graphrag._utils import compute_args_hash
from nano_graphrag._utils import wrap_embedding_func_with_attrs
from nano_graphrag.prompt import PROMPTS
import numpy as np

from config import (
    ZHIPU_API_KEY, 
    ZHIPU_CHAT_MODEL, 
    ZHIPU_BASE_URL,
    DASHSCOPE_API_KEY, 
    DASHSCOPE_BASE_URL, 
    DASHSCOPE_CHAT_MODEL,
    DASHSCOPE_EMB_MODEL,
    DASHSCOPE_BATCH_SIZE,
    MS_API_KEY,
    MS_BASE_URL,
    MS_CHAT_MODEL_NAME
)


async def custom_cheap_model_if_cache(
    prompt, system_prompt=None, history_messages=[], **kwargs
) -> str:
    openai_async_client = AsyncOpenAI(
        api_key=ZHIPU_API_KEY, base_url=ZHIPU_BASE_URL
    )
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # Get the cached response if having-------------------
    hashing_kv: BaseKVStorage = kwargs.pop("hashing_kv", None)
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})
    if hashing_kv is not None:
        args_hash = compute_args_hash(ZHIPU_CHAT_MODEL, messages)
        if_cache_return = await hashing_kv.get_by_id(args_hash)
        if if_cache_return is not None:
            return if_cache_return["return"]
    # -----------------------------------------------------

    response = await openai_async_client.chat.completions.create(
        model=ZHIPU_CHAT_MODEL, messages=messages, **kwargs
    )

    # Cache the response if having-------------------
    if hashing_kv is not None:
        await hashing_kv.upsert(
            {args_hash: {"return": response.choices[0].message.content, "model": ZHIPU_CHAT_MODEL}}
        )
    # -----------------------------------------------------
    return response.choices[0].message.content


async def custom_best_model_if_cache(
    prompt, system_prompt=None, history_messages=[], **kwargs
) -> str:
    openai_async_client = AsyncOpenAI(
        api_key=DASHSCOPE_API_KEY, base_url=DASHSCOPE_BASE_URL
    )
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # Get the cached response if having-------------------
    hashing_kv: BaseKVStorage = kwargs.pop("hashing_kv", None)
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})
    if hashing_kv is not None:
        args_hash = compute_args_hash(DASHSCOPE_CHAT_MODEL, messages)
        if_cache_return = await hashing_kv.get_by_id(args_hash)
        if if_cache_return is not None:
            return if_cache_return["return"]
    # -----------------------------------------------------

    response = await openai_async_client.chat.completions.create(
        model=DASHSCOPE_CHAT_MODEL, messages=messages, **kwargs
    )

    # Cache the response if having-------------------
    if hashing_kv is not None:
        await hashing_kv.upsert(
            {args_hash: {"return": response.choices[0].message.content, "model": DASHSCOPE_CHAT_MODEL}}
        )
    # -----------------------------------------------------
    return response.choices[0].message.content


@wrap_embedding_func_with_attrs(embedding_dim=1024, max_token_size=8192)
async def custom_embedding(texts: list[str]) -> np.ndarray:
    openai_async_client = AsyncOpenAI(base_url=DASHSCOPE_BASE_URL, api_key=DASHSCOPE_API_KEY)
    all_embeddings = []
    for i in range(0, len(texts), DASHSCOPE_BATCH_SIZE):
        batch = texts[i:i+DASHSCOPE_BATCH_SIZE]
        response = await openai_async_client.embeddings.create(
            model=DASHSCOPE_EMB_MODEL,
            input=batch,
            encoding_format="float"
        )
        all_embeddings.extend([dp.embedding for dp in response.data])
    
    return np.array(all_embeddings)
