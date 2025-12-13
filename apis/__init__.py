from fastapi import APIRouter
from apis.user import user_router
from apis.chat import chat_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(user_router)
api_router.include_router(chat_router)
