import sys
import os
sys.path.append(os.path.dirname(__file__))

from nano_graphrag import GraphRAG, QueryParam
from custom_nano_graph import (
    RedisKVStorage, 
    ChromaVectorDBStorage,
    custom_best_model_if_cache, 
    custom_cheap_model_if_cache,
    custom_embedding
)
from config import WORKING_DIR, CHROMA_HOST, CHROMA_PORT, REDIS_URL
from utils.graph_text_parser import relationships_csv_to_text, capture_relationships_csv

def remove_if_exist(file):
    if os.path.exists(file):
        os.remove(file)

def query():
    rag = GraphRAG(
        working_dir=WORKING_DIR,
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
    # TODO global模式为llm作为分析师进行总结，用于视角观点支撑（不能用于证据支撑）
    # result = rag.query(
    #     "互联网为什么被称为‘网络的网络’，并且它是通过怎样的三个阶段发展成为今天全球性的互联网的？", 
    #     param=QueryParam(
    #         mode="global", 
    #         only_need_context=True,
    #         global_max_consider_community=128,
    #         global_min_community_rating=0.15,
    #         global_max_token_for_community_report=8192
    #     )
    # )
    # TODO 捕获出relationship作为证据支撑的一部分
    result = rag.query(
        "互联网为什么被称为‘网络的网络’，并且它是通过怎样的三个阶段发展成为今天全球性的互联网的？", 
        param=QueryParam(
            mode="local",
            only_need_context=True,
            local_max_token_for_text_unit=1000,      # 原始块 1k
            local_max_token_for_local_context=1000,  # 子图描述 1k
            local_max_token_for_community_report=1000 # 社区报告 1k
        )
    )
    print("=" * 20)
    # print(capture_relationships_csv(str(result)))
    csv_block = capture_relationships_csv(str(result))
    par_csv = relationships_csv_to_text(csv_block=csv_block)
    for line in par_csv[:5]:
        print(line)


def insert():
    from time import time

    with open(r"E:\Code\Graph-RAG\course_graphrag\data\计算机网络 (第8版) copy.md", encoding="utf-8-sig") as f:
        result = f.read()

    remove_if_exist(f"{WORKING_DIR}/vdb_entities.json")
    remove_if_exist(f"{WORKING_DIR}/kv_store_full_docs.json")
    remove_if_exist(f"{WORKING_DIR}/kv_store_text_chunks.json")
    remove_if_exist(f"{WORKING_DIR}/kv_store_community_reports.json")
    remove_if_exist(f"{WORKING_DIR}/graph_chunk_entity_relation.graphml")

    rag = GraphRAG(
        working_dir=WORKING_DIR,
        enable_llm_cache=True,
        best_model_func=custom_best_model_if_cache,
        cheap_model_func=custom_cheap_model_if_cache,
        embedding_func=custom_embedding,
        key_string_value_json_storage_cls=RedisKVStorage,
        vector_db_storage_cls=ChromaVectorDBStorage,
        vector_db_storage_cls_kwargs={"chroma_host": CHROMA_HOST, "chroma_port": CHROMA_PORT},
        best_model_max_async=4,
        cheap_model_max_async=4,
        addon_params={"redis_url": REDIS_URL},
    )
    start = time()
    rag.insert(result[:1000])
    print("indexing time:", time() - start)
    # rag = GraphRAG(working_dir=WORKING_DIR, enable_llm_cache=True)
    # rag.insert(result[half_len:])


if __name__ == "__main__":
    # insert()
    query()
