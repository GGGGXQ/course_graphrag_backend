from openai import OpenAI

client = OpenAI(
    base_url='https://api-inference.modelscope.cn/v1',
    api_key='ms-298df566-5cb6-4c60-8599-d20fe1885cad', # ModelScope Token
)

response = client.embeddings.create(
    model='Qwen/Qwen3-Embedding-8B', # ModelScope Model-Id, required
    input='你好',
    encoding_format="float"
)

print(response.data[0].embedding)
