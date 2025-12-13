import os 
import dotenv
dotenv.load_dotenv()

# Example of creating an authenticated HTTP client
# import chromadb

# client = chromadb.HttpClient(host="127.0.0.1",
#                                port=8001,
#                                settings=chromadb.Settings(
#                                   chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
#                                    chroma_client_auth_credentials="your_token"))

import chromadb
# # 持久化存储客户端
# client = chromadb.PersistentClient(path="./chroma_db")
client = chromadb.HttpClient(host="127.0.0.1", port=8001)
print(client.heartbeat())

from chromadb import EmbeddingFunction
from zai import ZhipuAiClient


# Define a custom embedding function using ZhipuAI
class ZhipuEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.client = ZhipuAiClient(api_key=api_key)
    
    def __call__(self, texts: list[str]) -> list[list[float]]:
        resp = self.client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        return [d.embedding for d in resp.data]

zhipu_ef = ZhipuEmbeddingFunction(api_key=os.getenv('ZHIPU_API_KEY'), model_name="embedding-3")


# example for using the client
# ChromaDB 默认使用 all-MiniLM-L6-v2 模型进行嵌入
# collection = client.get_or_create_collection(name="Students")
collection = client.get_or_create_collection(
    name="Students",
    embedding_function=zhipu_ef  # 使用自定义的 ZhipuAI 嵌入函数
)
# student_info = """
# Alexandra Thompson, a 19-year-old computer science sophomore with a 3.7 GPA,
# is a member of the programming and chess clubs who enjoys pizza, swimming, and hiking
# in her free time in hopes of working at a tech company after graduating from the University of Washington.
# """

# club_info = """
# The university chess club provides an outlet for students to come together and enjoy playing
# the classic strategy game of chess. Members of all skill levels are welcome, from beginners learning
# the rules to experienced tournament players. The club typically meets a few times per week to play casual games,
# participate in tournaments, analyze famous chess matches, and improve members' skills.
# """

# university_info = """
# The University of Washington, founded in 1861 in Seattle, is a public research university
# with over 45,000 students across three campuses in Seattle, Tacoma, and Bothell.
# As the flagship institution of the six public universities in Washington state,
# UW encompasses over 500 buildings and 20 million square feet of space,
# including one of the largest library systems in the world.
# """

# 添加数据到集合
# collection.add(
#     documents=[student_info, club_info, university_info],
#     metadatas=[{"source": "student info"}, {"source": "club info"}, {"source": "university info"}],
#     ids=["id1", "id2", "id3"]
# )

# results = collection.query(
#     query_texts=["What is the student name?"],
#     n_results=2
# )

# print(results)

# # 更新数据
# collection.update(
#     ids=["id1"],
#     documents=["Kristiane Carina, a 19-year-old computer science sophomore with a 3.7 GPA"],
#     metadatas=[{"source": "student info"}]
# )

# # 查询以验证更新
# results = collection.query(
#     query_texts=["What is the student name?"],
#     n_results=2
# )
# print(results)

# collection.delete(ids=["id1"])

# # 查询以验证删除
results = collection.query(
    query_texts=["What is the student name?"],
    n_results=2
)

print(results)

# 获取集合列表
# collections = client.list_collections()
# print(collections)

# # 获取集合中的数据
# collection = client.get_collection(name="Students")
# data = collection.peek()  # 获取集合中的前10条数据
# print(data)
