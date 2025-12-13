"""
测试验证chroma db
"""
import sys, os, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.chroma_util import ChromaManager

if __name__ == '__main__':
    start = time.time()
    manager = ChromaManager()
    collection_name = "computer_network"
    # collections = manager.get_collection(name=collection_name)
    # data = collections.peek(1)
    # print(data)
    # print("=== 统计信息 ===")
    # stats = manager.get_collection_stats(collection_name=collection_name)
    # print(f"集合统计: {stats}")
    # query_result = manager.query(
    #     collection_name=collection_name,
    #     query_texts=["什么是广播域？"],
    #     n_results=5
    # )
    # print(f"查询结果: {query_result}")
    print("\n=== 相似性搜索 ===")
    similar_results = manager.search_similar(
        collection_name=collection_name,
        text="互联网为什么被称为‘网络的网络’",
        n_results=5,
        score_threshold=0.5
    )
    print(f"用时：{time.time() - start}")
    for i, result in enumerate(similar_results, 1):
        print(f"结果 {i}:")
        print(f"  文档: {result['document']}")
        print(f"  相似度: {result['similarity_score']:.3f}")
        print(f"  元数据: {result['metadata']}")
        print("="*20)
