from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from redis.asyncio import Redis
from apis import api_router
from config import (
    BACKEND_CORS_ORIGINS,
    PROJECT_NAME,
    API_V1_STR,
    HOST,
    PORT,
    DEBUG_MODE,
    REDIS_URL,
)


app = FastAPI(
    title=PROJECT_NAME,
    # openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="CourseGraphRAG-API",
    version="1.0.0",
)

# 设置CORS
if BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.aioredis = await Redis.from_url(REDIS_URL, decode_responses=True)
    yield
    await app.state.aioredis.aclose()
    
app.router.lifespan_context = lifespan

app.include_router(api_router, prefix=API_V1_STR)

@app.get("/")
async def root():
    """
    根路径，返回API信息
    """
    return {
        "message": "Welcome to Course-GraphRAG API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG_MODE
    ) 
