from uuid import  UUID
from fastapi import APIRouter, Depends, HTTPException, status, Body, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from redis.asyncio import Redis

from depends.session import get_db_dep
from depends.redis import get_aioredis
from utils.api_record_util import RequestRecordRoute
from utils.logger_util import logger
from utils.jwt_util import get_current_user
from domains.users import User
from domains.chats import (
    EBookList,
    Conversation,
    ConversationList,
    CreateConversationRequest,
    Message,
    MessageList,
    CreateMessageRequest,
    ChatRequest,
    ChatResponse,
)
from domains.operation import OperationResult
from daos import chat_dao


chat_router = APIRouter(prefix="/chat", tags=["chat"], route_class=RequestRecordRoute)

@chat_router.get("/books", response_model=EBookList, summary="获取电子书列表")
async def get_ebooks(db: Session=Depends(get_db_dep)):
    """
    获取电子书列表
    电子书的collection对应相应的chroma collection name 和 nanographrag workspace
    """
    return chat_dao.get_ebooks(db)

@chat_router.get("/conversations", response_model=ConversationList)
async def get_conversations(
    db: Session = Depends(get_db_dep),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的所有会话列表
    """
    return chat_dao.get_user_conversations(db, current_user.id)

@chat_router.post("/create", response_model=Conversation, summary="创建新对话")
async def create_conversation(
    conv_req: CreateConversationRequest = Body(...),
    db: Session = Depends(get_db_dep),
    current_user: User = Depends(get_current_user)
):
    """
    新建创建空对话
    """
    new_conversation = chat_dao.create_user_conversation(db, current_user.id, conv_req.new_title)
    return Conversation(
        id=new_conversation.id,
        title=new_conversation.title
    )

@chat_router.delete("/conversation/{conversation_id}", response_model=OperationResult, summary="删除会话")
async def delete_conversation(
    conversation_id: UUID = Path(..., description="会话ID"),
    db: Session = Depends(get_db_dep),
    current_user: User = Depends(get_current_user)
):
    """
    删除指定会话
    """
    try:
        result = chat_dao.delete_user_conversation(db, conversation_id, current_user.id)
        if result:
            return OperationResult(success=True, message="删除会话成功")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除会话失败，请稍后再试")
    
@chat_router.post("/rename/{conversation_id}", response_model=Conversation, summary="修改会话标题")
async def rename_conversation(
    rename_req: CreateConversationRequest,
    conversation_id: UUID = Path(..., description="会话ID"),
    db: Session = Depends(get_db_dep),
    current_user: User = Depends(get_current_user)
):
    conv = chat_dao.rename_conversation_title(db, rename_req.new_title, conversation_id, current_user.id)
    return Conversation(
        id=conv.id,
        title=conv.title
    )

@chat_router.get("/messages/{conversation_id}", response_model=MessageList, summary="获取会话消息列表")
async def get_conversation_messages(
    conversation_id: UUID = Path(..., description="会话ID"),
    db: Session = Depends(get_db_dep),
    current_user: User = Depends(get_current_user) 
):
    """"根据会话ID获取消息列表"""
    try:
        message_item = chat_dao.get_messages_and_ebook(db, conversation_id=conversation_id, user_id=current_user.id)
        return message_item
    
    except ValueError:
        logger.error(f"会话{conversation_id}不存在")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    
    except Exception as e:
        logger.error(f"查询会话{conversation_id}发生错误\n{e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="发生错误,请稍后再试!")

# @chat_router.post("/create-message", response_model=Message, summary="创建消息测试接口")
# async def create_message(
#     msg_req: CreateMessageRequest = Body(...),
#     db: Session = Depends(get_db_dep),
#     current_user:User = Depends(get_current_user)
# ):
#     """创建消息测试接口"""
#     mes = chat_dao.create_message(db, msg_req.conversation_id, msg_req.role, msg_req.content, current_user.id)
#     return Message(
#         id=mes.id,
#         role=mes.role,
#         content=mes.content,
#         created_time=mes.created_time
#     )

@chat_router.post("/chat")
async def chat(
    *,
    db: Session = Depends(get_db_dep),
    current_user: User = Depends(get_current_user),
    chat_request: ChatRequest
):
    """
    非流式聊天
    """
    if not chat_request.conversation_id:
        title = chat_request.content[:10]
        conv_result = chat_dao.create_user_conversation(
            db=db, user_id=current_user.id, new_title=title
        )
        conversation_id = conv_result.id
    else:
        conversation_id = chat_request.conversation_id
        conv = chat_dao.get_conversations_by_id(
            db=db, conversation_id=conversation_id, user_id=current_user.id
        )
        if not conv or conv.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
    
    # 发送消息并获取响应
    # response = await chat_dao.streaming_query(
    #     db=db,
    #     conversation_id=conversation_id,
    #     collection=chat_request.collection,
    #     user_id=current_user.id,
    #     message=chat_request.content
    # )
    return StreamingResponse(
        chat_dao.streaming_query(
            db=db,
            conversation_id=conversation_id,
            ebook_id=chat_request.ebook_id,
            collection=chat_request.collection,
            user_id=current_user.id,
            message=chat_request.content
        ),
        media_type="text/event-stream", # 标准 SSE 类型
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no", # 防止 Nginx 缓存流
        }
    )
