# -----AI platform api-----
import os
import dotenv

dotenv.load_dotenv()

# ZhipuAI
ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY', 'dummy_key')
ZHIPU_CHAT_MODEL = "glm-4.5-flash"
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"

# ModelScope
MS_API_KEY = os.getenv('MS_API_KEY', 'dummy_key')
MS_BASE_URL = 'https://api-inference.modelscope.cn/v1'
MS_EMB_MODEL_NAME = "Qwen/Qwen3-Embedding-8B"
MS_CHAT_MODEL_NAME = "MiniMax/MiniMax-M2"

# DASHSCOPE
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', 'dummy_key')
DASHSCOPE_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_EMB_MODEL = "text-embedding-v4"
DASHSCOPE_CHAT_MODEL = "qwen-max"
DASHSCOPE_BATCH_SIZE = 10  # DashScope embedding limit

# -----FASTAPI SETTINGS-----
PROJECT_NAME = "CourseGraphRAG"
API_V1_STR = "/course-graphrag"
HOST = "0.0.0.0"
PORT = 8717
BACKEND_CORS_ORIGINS = ["*"]
ENABLE_DOCS = True
DEBUG_MODE = True

ALGORITHM = "HS256"
SECRET_KEY = "04c2c380-5511-4e78-b176-3d5475dd3bce"

# logger
LOG_LEVEL = "DEBUG"
LOG_FILE_TYPE = "SizeRotating"

# working dir
WORKING_DIR = r"E:\Code\Graph-RAG\course_graphrag\workspace"


# -----DATABASE-----

# ChromaDB
CHROMA_HOST = "127.0.0.1"
CHROMA_PORT = 8001

# postgresql
DB_NAME = "course_rag"
DB_HOST = "127.0.0.1"
DB_PORT = 5432
DB_USERNAME = "postgres"
DB_PASSWORD = "admin123"

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?client_encoding=utf8"


# redis
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_USERNAME = ""
REDIS_PASSWORD = ""
REDIS_DB = 1
# REDIS_CELERY_DB = 2
REDIS_URL = f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
# REDIS_CELERY_URL = f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"


# -----EMAIL SETTINGS-----
SENDER_EMAIL = "19860599289@163.com"
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', 'dummy_key')
