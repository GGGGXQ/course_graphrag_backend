import sys, os, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio, time
from utils.chroma_util import ChromaManager
from nano_graphrag import QueryParam

from custom_nano_graph import get_graphrag_client
from utils.logger_util import logger
from utils.graph_text_parser import capture_relationships_csv


async def get_textbook_content(collection_name: str, user_message: str):
    """获取原文 TEXTBOOK_CONTENT"""
    # 使用asyncio.to_thread将同步的ChromaDB查询转换为异步任务
    return await asyncio.to_thread(_sync_get_textbook_content, collection_name, user_message)
    
def _sync_get_textbook_content(collection_name: str, text: str):
    """同步获取原文内容的内部函数"""
    manager = ChromaManager()
    similar_results = manager.search_similar(
        collection_name=collection_name,
        text=text,
        n_results=5,
        score_threshold=0.5
    )
    if similar_results is None:
        return ""
    # TODO 转换result为结构化字符串
    content = ""
    for i, result in enumerate(similar_results):
        detail = result["document"] + f"\n- metadata:{result['metadata']}" + f"\n- similarity_score{result["similarity_score"]}"
        content += f"document_{i}:\n{detail}\n\n"
    return content

async def get_nano_local_relationship(collection: str, user_message: str):
    """nano local query RELATIONSHIP"""
    # 根据collection确定workspace路径
    rag = get_graphrag_client(collection)
    result = await rag.aquery(
        user_message, 
        param=QueryParam(
            mode="local",
            only_need_context=True,
            local_max_token_for_text_unit=1000,      # 原始块 1k
            local_max_token_for_local_context=1000,  # 子图描述 1k
            local_max_token_for_community_report=1000 # 社区报告 1k
        )
    )
    return capture_relationships_csv(result)

async def get_nano_global_analysis(collection: str, user_message: str):
    """nano global query ANALYSIS"""
    rag = get_graphrag_client(collection)
    result = await rag.aquery(
        user_message, 
        param=QueryParam(
            mode="global",
            only_need_context=True,
            global_max_consider_community=40,
            global_min_community_rating=0.15,
            global_max_token_for_community_report=8192
        )
    )
    return result

async def query():
    collection_name = "computer_network"
    user_message = "互联网的特点是什么"
    start = time.time()
    textbook_content, local_relationship, global_analysis = await asyncio.gather(
        get_textbook_content(collection_name, user_message),
        get_nano_local_relationship(collection_name, user_message),
        get_nano_global_analysis(collection_name, user_message),
        return_exceptions=True
    )
    if isinstance(textbook_content, Exception):
        logger.error(f"获取原文内容失败: {textbook_content}")
        textbook_content = []
    if isinstance(local_relationship, Exception):
        logger.error(f"获取本地关系查询失败: {local_relationship}")
        local_relationship = ""
    if isinstance(global_analysis, Exception):
        logger.error(f"获取全局分析查询失败: {global_analysis}")
        global_analysis = ""
    logger.info(f"累计用时：{time.time() - start}")  # 此处为11.16秒
    print(global_analysis)
    return "sucess"

async def test():
    collection_name = "computer_network"
    user_message = "什么是UDP协议"
    start = time.time()
    textbook_content = await get_textbook_content(collection_name, user_message)
    logger.warning(f"获取textbook用时：{time.time() - start}")  # 此处结果为1.15
    local_relationship = await get_nano_local_relationship(collection_name, user_message)
    logger.warning(f"获取relationship用时：{time.time() - start}")  # 此处结果为2.07
    global_analysis = await get_nano_global_analysis(collection_name, user_message)
    logger.info(f"累计用时{time.time() - start}")  # 此处结果为13.74
    return textbook_content, local_relationship, global_analysis


if __name__ == "__main__":
    result = asyncio.run(query())
