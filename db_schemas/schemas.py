from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Text
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import text


class Base(DeclarativeBase):
    __name__: str
    __abstract__ = True

    created_time = Column(
        TIMESTAMP(timezone=True, precision=0),
        server_default=text("(now())::timestamp(0) with time zone"),
    )
    updated_time = Column(
        TIMESTAMP(timezone=True, precision=0),
        server_default=text("(now())::timestamp(0) with time zone"),
        onupdate=text("(now())::timestamp(0) with time zone"),
    )

    def to_dict(self, include=None, exclude=[], name_map={}):
        return {
            (c.name if not name_map.get(c.name) else name_map.get(c.name)): getattr(
                self, c.name, None
            )
            for c in self.__table__.columns
            if (c.name not in exclude) and (include is None or c.name in include)
        }
    
class DBUser(Base):
    """用户"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    username = Column(String, nullable=True)
    account = Column(String, nullable=True)
    password = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)


class DBEBook(Base):
    """电子书"""
    __tablename__ = "ebooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=False)
    collection = Column(String(255), nullable=False)
    author = Column(String(255), nullable=True)
    is_deteled = Column(Boolean, nullable=False, default=False)


class DBConversation(Base):
    """对话"""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    ebook_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)


class DBMessage(Base):
    """消息"""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant' or 'system'
    content = Column(Text, nullable=False)
