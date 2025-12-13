from typing import Dict
import asyncio
import numpy as np
import chromadb
from dataclasses import dataclass

from chromadb.api.models.Collection import Collection
from nano_graphrag.base import BaseVectorStorage
from utils.logger_util import logger


@dataclass
class ChromaVectorDBStorage(BaseVectorStorage):
    """Custom vector database with chroma"""
    def __post_init__(self):
        chroma_parms = self.global_config.get("vector_db_storage_cls_kwargs", {})
        self._max_batch_size = self.global_config.get("embedding_batch_num", 32)
        self._client = chromadb.HttpClient(
            host=chroma_parms.get("chroma_host", "localhost"),
            port=chroma_parms.get("chroma_port", 8001)
        )
        self._embedding_func = self.embedding_func
        self._collection: Collection = self._client.get_or_create_collection(
            name=self.namespace
        )
    
    async def upsert(self, data: Dict[str, dict]):
        if not data:
            logger.warning("Empty data, nothing to insert.")
            return []
        logger.info(f"Inserting {len(data)} vectors to chroma:{self.namespace}")
        
        ids = list(data.keys())
        contents = [v["content"] for v in data.values()]
        list_data = [
            {
                "id": k,
                **{k1: v1 for k1, v1 in v.items() if k1 in self.meta_fields},
            }
            for k, v in data.items()
        ]
        batches = [
            contents[i:i+self._max_batch_size] for i in range(0, len(contents), self._max_batch_size)
        ]
        embeddings_list = await asyncio.gather(
            *[self._embedding_func(batch) for batch in batches]
        )
        embeddings = np.concatenate(embeddings_list)
        metadatas = [
            {k: v for k, v in d.items() if k in self.meta_fields or k == "id"}
            for d in list_data
        ]
        collection = self._client.get_or_create_collection(name=self.namespace)
        collection.upsert(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=contents,
            metadatas=metadatas,
        )

        return ids

    async def query(self, query: str, top_k=5):
        embedding = await self._embedding_func([query])
        embedding = embedding[0]

        include = ["documents", "metadatas", "distances"]
        results = self._collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=top_k,
            include=include
        )
        formatted_results = []
        for i in range(len(results['ids'][0])):
            record_id = results['ids'][0][i]
            meta = results['metadatas'][0][i] or {}
            distance = results['distances'][0][i]

            formatted_results.append({
                **meta,
                "id": record_id,
                "distance": distance,
                "similarity": 1 - distance
            })

        return formatted_results
