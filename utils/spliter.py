from typing import List

from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
import spacy
import uuid


class Document_controller:
    def __init__(self, nlp: str = None):
        if nlp is None:
            self.nlp = spacy.load("zh_core_web_sm")  # python -m spacy download zh_core_web_sm
        else:
            self.nlp = spacy.load(nlp)  # 英文版书用en_core_web_sm
            
    def conver_md_to_document(self, md_path: str) -> List[Document]:
        """将markdown文件读取为文档列表"""
        with open(md_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        # 先用langchain-text-spliter的markdown_spliter进行初步划分
        headers_to_split_on = [
            ("#", "file_name"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
            ("#####", "Header 5"),
            ("######", "Header 6")
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )
        documents = markdown_splitter.split_text(markdown_text)
        return documents
        

    def split_text(self, documents: List[Document]) -> List[Document]:
        """
        对文档列表进行Spacy句子级细化处理
        Args:
            documents: LangChain Document对象列表

        Returns:
            List[Document]: 细化后的文档列表
        """
        refined_chunks = []
        for chunk in documents:
            refined_chunks.extend(self._refine_chunk_with_spacy(chunk))

        return refined_chunks

    def _refine_chunk_with_spacy(self, chunk: Document, max_sentences_per_chunk: int = 5) -> list:
        """
        使用Spacy对chunk进行句子级细化
        Args:
            chunk: LangChain Document对象

        Returns:
            List[Document]: 细化后的文档列表
        """
        content = chunk.page_content
        if not content.strip():
            return [chunk]
        doc = self.nlp(content)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

        if len(sentences) <= max_sentences_per_chunk:
            chunk.metadata['chunk_id'] = str(uuid.uuid4())
            return [chunk]
        
        refined_chunks = []
        for i in range(0, len(sentences), max_sentences_per_chunk):
            sentences_chunk = sentences[i:i + max_sentences_per_chunk]
            chunk_content = ''.join(sentences_chunk)
            new_metadata = chunk.metadata.copy()
            new_metadata['chunk_id'] = str(uuid.uuid4())

            new_chunk = Document(page_content=chunk_content, metadata=new_metadata)
            refined_chunks.append(new_chunk)
        return refined_chunks
    