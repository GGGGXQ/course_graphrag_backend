from pydantic import BaseModel
from typing import List, Literal, Optional
from uuid import UUID
from datetime import datetime

class EBook(BaseModel):
    """电子书列表"""
    id: UUID
    title: str
    author: str
    collection: str

class EBookList(BaseModel):
    """电子书列表响应"""
    ebooks: List[EBook]
    total: int


class Conversation(BaseModel):
    """会话"""
    id: UUID
    title: str


class ConversationList(BaseModel):
    """会话列表"""
    total: int
    conversations: List[Conversation]


class CreateConversationRequest(BaseModel):
    """创建会话请求"""
    new_title: str


class Message(BaseModel):
    """消息"""
    id: UUID
    role: str
    content: str
    created_time: datetime

class MessageList(BaseModel):
    """消息列表响应"""
    messages: List[Message]
    ebook: EBook
    total: int

class CreateMessageRequest(BaseModel):
    """创建消息测试请求"""
    conversation_id: UUID
    role: Literal["user", "assistant", "system", "tool"]
    content: str


class ChatRequest(BaseModel):
    """会话"""
    content: str
    collection: str
    conversation_id: Optional[UUID] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    conversation_id: UUID
    message_id: UUID
    content: str
    is_streaming: bool
