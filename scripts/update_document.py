"""
更新chroma db文档脚本
python scripts/update_document.py
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.spliter import Document_controller
from utils.chroma_util import ChromaManager
from typing import List
from langchain_core.documents import Document
import json

from split_md_to_document import save_chunks_to_json


def load_chunks_from_json(file_path: str) -> List[Document]:
    """从JSON文件读取chunks"""
    if not os.path.exists(file_path):
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        chunks_data = json.load(f)

    chunks = []
    for chunk_dict in chunks_data:
        chunk = Document(
            page_content=chunk_dict["page_content"],
            metadata=chunk_dict["metadata"]
        )
        chunks.append(chunk)

    print(f"已从 {file_path} 读取 {len(chunks)} 个chunks")
    return chunks


def batch_add_documents(manager: ChromaManager, chunks: List[Document], name: str):
    """批量添加文档到chroma db"""
    docs = []
    metas=[]
    for chunk in chunks:
        docs.append(chunk.page_content)
        metas.append(chunk.metadata)
    print(f"加载文档成功，文档数量{len(docs)}\n元数据数量{len(metas)}")
    print("开始添加文档")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = manager.add_documents(
                collection_name=name,
                documents=docs,
                metadatas=metas
            )
            print(result)
            break
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"添加文档失败，已重试{max_retries}次：{e}")
                raise
            print(f"添加文档失败(尝试{attempt+1}/{max_retries})：{e}，5秒后重试...")
            import time
            time.sleep(5)

if __name__ == "__main__":
    doc_controller = Document_controller()
    chroma_manager = ChromaManager()
    collection_name = "modern_control_system_zh"
    doc_path = "data/现代控制系统(第12版)_zh.md"
    chunks_json_path = "workspace/chunks_modern_control_system_zh.json"

    # 测试时候出现错误，删除合集重新添加文档
    # chroma_manager.delete_collection(name=collection_name)
    collection = chroma_manager.create_collection(
        name=collection_name,
        metadata={"description": "现代控制系统(第12版)_zh.md", "version": "1.0"}
    )
    # collection = chroma_manager.get_collection(name=collection_name)

    # 尝试从JSON文件读取chunks，如果不存在则重新处理文档
    chunks = load_chunks_from_json(chunks_json_path)

    if not chunks:
        print("未找到chunks缓存文件，开始重新处理文档...")
        documents = doc_controller.conver_md_to_document(doc_path)
        # print(f"初步分块数量: {len(documents)}")
        # print("\n初步分块示例:")
        # for i, doc in enumerate(documents[-3:]):
        #     print(f"文档 {i+1}:")
        #     print(f"  Content: {doc.page_content[:100]}...")
        #     print(f"  Metadata: {doc.metadata}")
        #     print("-" * 30)

        chunks = doc_controller.split_text(documents)

        # 保存chunks到JSON文件
        save_chunks_to_json(chunks, chunks_json_path)
    else:
        print("使用已缓存的chunks文件")
    # print(f"\n细化后分块数量: {len(chunks)}")
    # print("\n细化后分块示例:")
    # for i, chunk in enumerate(chunks[-3:]):
    #     print(f"Chunk {i+1}:")
    #     print(f"  Content: {chunk.page_content}")
    #     print(f"  Metadata: {chunk.metadata}")
    #     print(f"  Content length: {len(chunk.page_content)}")
    #     print("-" * 50)
    
    # TODO 前20个文档无法生成embedding，查看一下有没有必要存储
    # for i in range(20):
    #     print(chunks[i].page_content)
    #     print("-" * 30)

    # 分批处理文档，减小批处理大小避免限流，每批20个
    batch_size = 40
    for i in range(1521, len(chunks), batch_size):
        batch_chunks = chunks[i:i+batch_size]
        print(f"处理第 {i//batch_size + 1} 批，包含 {len(batch_chunks)} 个文档块")
        batch_add_documents(chroma_manager, batch_chunks, name=collection_name)
        # 批次之间添加延迟
        if i + batch_size < len(chunks):
            print("批次间等待3秒...")
            import time
            time.sleep(3)
    print("更新chroma db完毕")
    print("=== 统计信息 ===")
    stats = chroma_manager.get_collection_stats(collection_name=collection_name)
    print(f"集合统计: {stats}")
    # 获取集合中的数据
    # collection = chroma_manager.get_collection(name=collection_name)
    # data = collection.peek()  # 获取集合中的前10条数据
    # print(data)
