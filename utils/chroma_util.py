from uuid import uuid4
import chromadb
import time
import random
from chromadb import EmbeddingFunction, QueryResult
from chromadb.config import Settings as ChromaSettings
from typing import Optional, Dict, List, Any, Union
import logging
from pydantic import BaseModel
from zai import ZhipuAiClient
from openai import OpenAI
from config import (
    CHROMA_HOST,
    CHROMA_PORT, 
    ZHIPU_API_KEY, 
    MS_API_KEY, 
    MS_BASE_URL, 
    MS_EMB_MODEL_NAME,
    DASHSCOPE_BASE_URL,
    DASHSCOPE_API_KEY,
    DASHSCOPE_EMB_MODEL
)
from utils.logger_util import logger


class ChromaConfig(BaseModel):
    """ChromaDB配置类"""
    host: str = CHROMA_HOST
    port: int = CHROMA_PORT
    embedding_model: str = DASHSCOPE_EMB_MODEL
    api_key: str = DASHSCOPE_API_KEY
    base_url: Optional[str] = DASHSCOPE_BASE_URL
    collection_metadata: Optional[Dict[str, Any]] = None


class CustomEmbeddingFunction(EmbeddingFunction):
    """ModelScope Embedding Model"""

    def __init__(self, model_name: str, api_key: str, base_url: str=None):
        self.model_name = model_name
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

    def __call__(self, texts: List[str]) -> List[List[float]]:
        try:
            embeddings = []
            for i, text in enumerate(texts):
                # 添加延迟避免429错误，每个请求间隔0.5秒
                if i > 0:
                    time.sleep(0.5)
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        emb = self.client.embeddings.create(
                            model=self.model_name,
                            input=text,
                            encoding_format="float"
                        )
                        embeddings.append(emb.data[0].embedding)
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            logger.error(f"嵌入生成失败，已重试{max_retries}次: {e}")
                            raise
                        logger.warning(f"嵌入生成失败(尝试{attempt+1}/{max_retries}): {e}, 1秒后重试")
                        time.sleep(1)
            return embeddings
        except Exception as e:
            logger.error(f"嵌入生成失败: {e}")
            raise


class ChromaManager:
    """ChromaDB管理类"""

    def __init__(self, config: Optional[ChromaConfig] = None):
        """
        初始化ChromaDB管理器
        Args:
            config: ChromaDB配置，如果为None则使用默认配置
        """
        self.config = config or ChromaConfig()
        self._client: Optional[chromadb.Client] = None
        self._embedding_function: Optional[CustomEmbeddingFunction] = None
        self._collections: Dict[str, chromadb.Collection] = {}

        self._initialize()

    def _initialize(self):
        """初始化ChromaDB客户端和嵌入函数"""
        try:
            self._client = chromadb.HttpClient(
                host=self.config.host,
                port=self.config.port
            )
            logger.info(f"ChromaDB客户端连接成功: {self.config.host}:{self.config.port}")

            self._embedding_function = CustomEmbeddingFunction(
                model_name=self.config.embedding_model,
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )

        except Exception as e:
            logger.error(f"ChromaDB初始化失败: {e}")
            raise

    @property
    def client(self) -> chromadb.Client:
        """获取ChromaDB客户端"""
        if self._client is None:
            self._initialize()
        return self._client

    @property
    def embedding_function(self) -> CustomEmbeddingFunction:
        """获取嵌入函数"""
        if self._embedding_function is None:
            self._embedding_function = CustomEmbeddingFunction(
                model_name=self.config.embedding_model,
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )   
        return self._embedding_function

    def create_collection(
        self,
        name: str,
        metadata: Optional[List[Dict[str, Any]]] = None,
        reset_if_exists: bool = False
    ) -> chromadb.Collection:
        """
        创建集合

        Args:
            name: 集合名称
            metadata: 集合元数据
            reset_if_exists: 如果集合存在是否重置

        Returns:
            chromadb.Collection: 创建的集合对象
        """
        try:
            if reset_if_exists and name in self.client.list_collections():
                logger.info(f"删除已存在的集合: {name}")
                self.client.delete_collection(name)

            collection = self.client.get_or_create_collection(
                name=name,
                embedding_function=self.embedding_function,
                metadata=metadata or self.config.collection_metadata
            )

            self._collections[name] = collection
            logger.info(f"集合创建成功: {name}")
            return collection

        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            raise

    def get_collection(self, name: str) -> chromadb.Collection:
        """
        获取集合

        Args:
            name: 集合名称

        Returns:
            chromadb.Collection: 集合对象
        """
        try:
            if name in self._collections:
                return self._collections[name]

            collection = self.client.get_collection(
                name=name,
                embedding_function=self.embedding_function
            )
            self._collections[name] = collection
            return collection
        except Exception as e:
            logger.error(f"获取集合失败: {e}")
            raise

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        ids: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        批量添加文档

        Args:
            collection_name: 集合名称
            documents: 文档列表
            ids: 文档ID列表，如果为None则自动生成
            metadatas: 元数据列表
            batch_size: 批量处理大小

        Returns:
            Dict[str, Any]: 添加结果
        """
        try:
            collection = self.get_collection(collection_name)

            if ids is None:
                ids = [str(uuid4()) for _ in range(len(documents))]

            # 分批处理
            total_docs = len(documents)
            result = {"added": 0, "errors": []}

            for i in range(0, total_docs, batch_size):
                batch_end = min(i + batch_size, total_docs)
                batch_docs = documents[i:batch_end]
                batch_ids = ids[i:batch_end]
                batch_metas = metadatas[i:batch_end] if metadatas else None

                try:
                    collection.add(
                        documents=batch_docs,
                        ids=batch_ids,
                        metadatas=batch_metas
                    )
                    result["added"] += len(batch_docs)
                    logger.info(f"已添加文档批次: {i+1}-{batch_end}")

                except Exception as e:
                    error_msg = f"批次 {i+1}-{batch_end} 添加失败: {e}"
                    result["errors"].append(error_msg)
                    logger.error(error_msg)

            logger.info(f"文档添加完成: {result}")
            return result

        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise

    def query(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None
    ) -> QueryResult:
        """
        查询集合

        Args:
            collection_name: 集合名称
            query_texts: 查询文本列表
            n_results: 返回结果数量
            where: 元数据过滤条件
            where_document: 文档内容过滤条件
            include: 返回字段列表

        Returns:
            QueryResult: 查询结果
        """
        try:
            collection = self.get_collection(collection_name)

            if include is None:
                include = ["documents", "metadatas", "distances"]

            result = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=include
            )

            logger.info(f"查询完成: {len(query_texts)} 个查询，返回 {n_results} 个结果")
            return result

        except Exception as e:
            logger.error(f"查询失败: {e}")
            raise

    def search_similar(
        self,
        collection_name: str,
        text: str,
        n_results: int = 5,
        score_threshold: float = 0.5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        相似性搜索

        Args:
            collection_name: 集合名称
            text: 搜索文本
            n_results: 返回结果数量
            score_threshold: 相似度阈值
            **kwargs: 其他查询参数

        Returns:
            List[Dict[str, Any]]: 格式化的搜索结果
        """
        try:
            result = self.query(
                collection_name=collection_name,
                query_texts=[text],
                n_results=n_results,
            )

            formatted_results = []
            for i in range(len(result['documents'][0])):
                doc = result['documents'][0][i]
                metadata = result['metadatas'][0][i] if result['metadatas'] else {}
                distance = result['distances'][0][i] if result['distances'] else 0.0

                similarity_score = 1.0 - min(distance / 2.0, 1.0)

                if similarity_score >= score_threshold:
                    formatted_result = {
                        "document": doc,
                        "metadata": metadata,
                        "similarity_score": similarity_score,
                        "distance": distance
                    }
                    formatted_results.append(formatted_result)

            formatted_results.sort(key=lambda x: x['similarity_score'], reverse=True)

            logger.info(f"相似性搜索完成: 找到 {len(formatted_results)} 个相似结果")
            return formatted_results

        except Exception as e:
            logger.error(f"相似性搜索失败: {e}")
            raise

    def update_documents(
        self,
        collection_name: str,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        更新文档
        Args:
            collection_name: 集合名称
            ids: 文档ID列表
            documents: 新文档内容
            metadatas: 新元数据

        Returns:
            bool: 更新是否成功
        """
        try:
            collection = self.get_collection(collection_name)
            update_dict = {"ids": ids}
            if documents:
                update_dict["documents"] = documents
            if metadatas:
                update_dict["metadatas"] = metadatas
            collection.update(**update_dict)
            logger.info(f"文档更新成功: {len(ids)} 个文档")
            return True
        except Exception as e:
            logger.error(f"文档更新失败: {e}")
            return False

    def delete_documents(
        self,
        collection_name: str,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        删除文档
        Args:
            collection_name: 集合名称
            ids: 文档ID列表
            where: 元数据过滤条件
        Returns:
            bool: 删除是否成功
        """
        try:
            collection = self.get_collection(collection_name)
            if ids:
                collection.delete(ids=ids)
                logger.info(f"文档删除成功: {len(ids)} 个文档")
            elif where:
                collection.delete(where=where)
                logger.info("基于条件的文档删除成功")
            else:
                logger.warning("未指定删除条件")
                return False

            return True
        except Exception as e:
            logger.error(f"文档删除失败: {e}")
            return False

    def list_collections(self) -> List[str]:
        """
        列出所有集合
        Returns:
            List[str]: 集合名称列表
        """
        try:
            collections = self.client.list_collections()
            logger.info(f"获取集合列表: {len(collections)} 个集合")
            return collections
        except Exception as e:
            logger.error(f"获取集合列表失败: {e}")
            raise

    def delete_collection(self, name: str) -> bool:
        """
        删除集合
        Args:
            name: 集合名称
        Returns:
            bool: 删除是否成功
        """
        try:
            self.client.delete_collection(name)
            if name in self._collections:
                del self._collections[name]
            logger.info(f"集合删除成功: {name}")
            return True

        except Exception as e:
            logger.error(f"集合删除失败: {e}")
            return False

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        获取集合统计信息
        """
        try:
            collection = self.get_collection(collection_name)
            count = collection.count()

            stats = {
                "collection_name": collection_name,
                "document_count": count,
                "embedding_function": self.config.embedding_model,
                "client_info": {
                    "host": self.config.host,
                    "port": self.config.port
                }
            }
            logger.info(f"获取集合统计信息: {stats}")
            return stats

        except Exception as e:
            logger.error(f"获取集合统计信息失败: {e}")
            raise

    def clear_cache(self):
        """清空集合缓存"""
        self._collections.clear()
        logger.info("集合缓存已清空")
