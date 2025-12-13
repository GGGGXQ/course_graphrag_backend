from nano_graphrag import GraphRAG
from ._llm import (
    custom_best_model_if_cache,
    custom_cheap_model_if_cache, 
    custom_embedding,
)
from ._storage import RedisKVStorage, ChromaVectorDBStorage
from config import WORKING_DIR, CHROMA_HOST, CHROMA_PORT, REDIS_URL

def get_graphrag_client(collection_name: str):
    workspace_path = f"{WORKING_DIR}/{collection_name}"
    return GraphRAG(
        working_dir=workspace_path,
        enable_llm_cache=True,
        best_model_func=custom_best_model_if_cache,
        cheap_model_func=custom_cheap_model_if_cache,
        embedding_func=custom_embedding,
        # key_string_value_json_storage_cls=RedisKVStorage,
        # vector_db_storage_cls=ChromaVectorDBStorage,
        # vector_db_storage_cls_kwargs={"chroma_host": CHROMA_HOST, "chroma_port": CHROMA_PORT},
        best_model_max_async=4,
        cheap_model_max_async=4,
        # addon_params={"redis_url": REDIS_URL},
    )
