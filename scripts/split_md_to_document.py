"""
预分块脚本
python scripts/split_md_to_document.py
"""
import sys
from typing import List
import json, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.documents import Document
from utils.spliter import Document_controller


def save_chunks_to_json(chunks: List[Document], file_path: str):
    """将chunks保存到JSON文件"""
    chunks_data = []
    for chunk in chunks:
        chunk_dict = {
            "page_content": chunk.page_content,
            "metadata": chunk.metadata
        }
        chunks_data.append(chunk_dict)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(chunks_data, f, ensure_ascii=False, indent=2)
    print(f"已保存 {len(chunks_data)} 个chunks到 {file_path}")


if __name__ == "__main__":
    # doc_controller = Document_controller()
    doc_controller = Document_controller(nlp="en_core_web_sm")  # 英文版用en_core_web_sm
    doc_path = "data/modern_control_system_en.md"
    chunks_json_path = "workspace/chunks_modern_control_system_en.json"
    documents = doc_controller.conver_md_to_document(doc_path)
    print(f"初步分块数量: {len(documents)}")
    for i, doc in enumerate(documents[-3:]):
        print(f"文档 {i+1}:")
        print(f"  Content: {doc.page_content[:100]}...")
        print(f"  Metadata: {doc.metadata}")
        print("-" * 30)
    chunks = doc_controller.split_text(documents)
    print(f"\n细化后分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks[-3:]):
        print(f"Chunk {i+1}:")
        print(f"  Content: {chunk.page_content}")
        print(f"  Metadata: {chunk.metadata}")
        print(f"  Content length: {len(chunk.page_content)}")
        print("-" * 50)
    save_chunks_to_json(chunks, chunks_json_path)
