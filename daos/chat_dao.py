import json
from uuid import UUID
from typing import List, Literal, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session
from openai.types.chat import ChatCompletionMessageParam
from openai import AsyncOpenAI

from db_schemas.schemas import DBUser, DBConversation, DBMessage, DBEBook
from domains.chats import (
    ConversationList, 
    Conversation, 
    EBookList, 
    EBook, 
    MessageList, 
    Message
)
from utils.logger_util import logger
from utils.retrival_util import (
    get_textbook_content,
    get_nano_local_relationship,
    get_nano_global_analysis
)
from utils.graph_text_parser import relationships_csv_to_text
import prompts
import config


client = AsyncOpenAI(
    base_url=config.ZHIPU_BASE_URL,
    api_key=config.ZHIPU_API_KEY
)


def get_ebooks(db: Session): 
    """获取电子书"""
    ebooks = db.query(DBEBook).filter(DBEBook.is_deteled == False).all()
    ebook_list = EBookList(
        ebooks=[
            EBook(
                id=e.id,
                title=e.title,
                author=e.author if e.author else None,
                collection=e.collection
            ) for e in ebooks
        ],
        total=len(ebooks)
    )
    return ebook_list


def get_user_conversations(db: Session, user_id: UUID) -> ConversationList:
    """
    获取指定用户的所有会话列表
    :param db: 数据库会话
    :param user_id: 用户ID
    :return: 会话列表 ConversationList
    """
    conversations = db.query(DBConversation).filter(DBConversation.user_id == user_id, DBConversation.is_deleted == False).order_by(desc(DBConversation.created_time)).all()
    conversation_list = ConversationList(
        conversations=[
            Conversation(
                id=conv.id,
                title=conv.title
            ) for conv in conversations
        ],
        total=len(conversations)
    )
    return conversation_list
    

def create_user_conversation(db: Session, user_id: UUID, new_title: str="新对话") -> DBConversation:
    """
    为指定用户创建一个新的会话
    :param db: 数据库会话
    :param user_id: 用户ID
    :return: 新创建的会话 DBConversation
    """
    new_conversation = DBConversation(
        user_id=user_id,
        title=new_title
    )
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    return new_conversation

def get_conversations_by_id(db: Session, conversation_id: int) -> DBConversation:
    """
    根据会话ID获取会话
    """
    conversation = db.query(DBConversation).filter(DBConversation.id == conversation_id).first()
    return conversation

def delete_user_conversation(db: Session, conversation_id: UUID, user_id: UUID):
    """
    根据会话ID删除会话(软删除)
    """
    conversation = db.query(DBConversation).filter(DBConversation.id == conversation_id).first()
    if not conversation or conversation.user_id != user_id:
        raise ValueError("conversation not found")
    try:
        conversation.is_deleted = True
        db.commit()
        db.refresh(conversation)
        return True
    except Exception:
        db.rollback()
        return False
    
def rename_conversation_title(db: Session, new_title: str, conversation_id: UUID, user_id: UUID) -> DBConversation:
    conv = db.query(DBConversation).filter(DBConversation.id == conversation_id).first()
    if not conv or conv.user_id != user_id:
        raise ValueError("conversation not found")
    conv.title = new_title
    db.commit()
    db.refresh(conv)
    return conv

def get_messages_by_conversation_id(db: Session, conversation_id: UUID, user_id: UUID, limit: int = None) -> List[DBMessage]:
    """根据会话ID获取消息列表"""
    conv = db.query(DBConversation).filter(DBConversation.id == conversation_id).first()
    if not conv or conv.user_id != user_id:
        raise ValueError("conversation not found")
    messages = db.query(DBMessage).filter(DBMessage.conversation_id == conversation_id).order_by(desc(DBMessage.created_time))
    if limit is not None:
        messages = messages.limit(limit)
    return messages.all()

def get_messages_and_ebook(db: Session, conversation_id: UUID, user_id: UUID, limit: int=None) -> MessageList:
    """获取当前会话消息及电子书信息"""
    conv = db.query(DBConversation).filter(DBConversation.id == conversation_id).first()
    if not conv or conv.user_id != user_id:
        raise ValueError("conversation not found")
    # 获取 ebook 信息
    ebook_obj = None
    if conv.ebook_id:
        ebook_rec = db.query(DBEBook).filter(DBEBook.id == conv.ebook_id, DBEBook.is_deteled == False).first()
        if ebook_rec:
            ebook_obj = EBook(
                id=ebook_rec.id,
                title=ebook_rec.title,
                author=ebook_rec.author if ebook_rec.author else None,
                collection=ebook_rec.collection
            )
    if ebook_obj is None:
        ebook_obj = EBook(id=conv.ebook_id, title="", author=None, collection="") if conv.ebook_id else EBook(id=None, title="", author=None, collection="")

    query = db.query(DBMessage).filter(DBMessage.conversation_id == conversation_id).order_by(desc(DBMessage.created_time))
    total_count = query.count()
    if limit:
        msgs_db = list(reversed(query.limit(limit).all()))
    else:
        msgs_db = list(reversed(query.all()))

    messages = [
        Message(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            created_time=msg.created_time
        )
        for msg in msgs_db
    ]

    return MessageList(messages=messages, ebook=ebook_obj, total=total_count)

def add_message(db: Session, conversation_id: UUID, role: Literal["user", "assistant", "system", "tool"], content: str, user_id: UUID):
    """创建消息"""
    conv = db.query(DBConversation).filter(DBConversation.id == conversation_id).first()
    if not conv or conv.user_id != user_id:
        raise ValueError("conversation not found")
    new_message = DBMessage(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

async def _build_messages(
    db: Session, 
    conversation_id: int, 
    user_message: str, 
    textbook: str,
    relationships: str,
    analysts: str,
    user_id: UUID
) -> tuple[List[ChatCompletionMessageParam], dict]:
    """构建发送给 OpenAI 的消息列表"""
    messages: List[ChatCompletionMessageParam] = []

    # 拼凑system_content
    system_content = prompts.SYSTEM_PROMPT +\
    prompts.TEXTBOOK_CONTENT.format(textbook_content=textbook) +\
    prompts.RELATIONSHIP.format(relationship=relationships) +\
    prompts.ANALYSIS.format(analysis=analysts)

    messages.append({"role": "system", "content": system_content})

    history_messages = get_messages_by_conversation_id(
        db=db, conversation_id=conversation_id, user_id=user_id, limit=5
    )

    for msg in history_messages:
        if msg.role != "system":
            messages.append({"role": msg.role, "content": msg.content})
    user_question = prompts.USER_QUERY.format(user_query=user_message)
    # 添加当前用户消息
    messages.append({"role": "user", "content": user_question})

    return messages

# async def chat(
#     db: Session,
#     conversation_id: UUID, 
#     user_id: UUID,
#     message: str,
#     collection: str
# ):
#     """非流式聊天"""
#     # 构建上下文
#     messages = await _build_messages(
#         db=db, conversation_id=conversation_id,
#         user_message=message,
#         collection=collection
#     )
#     # 保存用户消息
#     user_msg = add_message(db, conversation_id, "user", message, user_id)

async def streaming_query(
    db: Session,
    conversation_id: UUID, 
    user_id: UUID,
    collection: str, 
    message: str,
):
    """流式查询，逐步返回结果"""
    textbook_content = []      # 默认为空列表
    local_relationship = []    # 默认为空列表 (或者空字符串 "", 取决于你后续怎么处理)
    global_analysis = ""       # 默认为空字符串
    # 1. 返回教科书内容
    try:
        textbook_content = await get_textbook_content(collection, message)
        yield f"data: {json.dumps({'type': 'textbook_content', 'data': textbook_content, 'step': 1})}\n\n"
    except Exception as e:
        logger.error(f"获取原文内容失败: {e}")
        yield f"data: {json.dumps({'type': 'textbook_content', 'data': [], 'step': 1, 'error': str(e)})}\n\n"

    # 2. 返回本地关系查询结果
    try:
        local_relationship = await get_nano_local_relationship(collection, message)
        yield f"data: {json.dumps({'type': 'local_relationship', 'data': relationships_csv_to_text(local_relationship), 'step': 2})}\n\n"
    except Exception as e:
        logger.error(f"获取本地关系查询失败: {e}")
        yield f"data: {json.dumps({'type': 'local_relationship', 'data': '', 'step': 2, 'error': str(e)})}\n\n"

    # 3. 返回全局分析结果
    try:
        global_analysis = await get_nano_global_analysis(collection, message)
        yield f"data: {json.dumps({'type': 'global_analysis', 'data': global_analysis, 'step': 3})}\n\n"
    except Exception as e:
        logger.error(f"获取全局分析查询失败: {e}")
        yield f"data: {json.dumps({'type': 'global_analysis', 'data': '', 'step': 3, 'error': str(e)})}\n\n"

    # 4. 最终的LLM回答
    messages = await _build_messages(
        db=db, 
        conversation_id=conversation_id,
        user_id=user_id,
        user_message=message,
        textbook=textbook_content,
        relationships=local_relationship,
        analysts=global_analysis
    )
    logger.info(f"\n\nprompt:\n{messages}")
    # 保存用户消息
    add_message(db, conversation_id, "user", message, user_id)
    try:
        stream_response  = await client.chat.completions.create(
            model=config.ZHIPU_CHAT_MODEL,
            messages=messages,
            temperature=0.5,
            stream=True
        )
        full_content = ""
        async for chunk in stream_response:
            # 取出内容，注意做判空处理
            delta = chunk.choices[0].delta
            content = delta.content
            
            if content:
                full_content += content
                # 实时推送给前端
                yield f"data: {json.dumps({'type': 'answer_chunk', 'data': content, 'step': 4})}\n\n"

        # 循环结束后，保存完整消息
        assistant_msg = add_message(
            db=db, 
            conversation_id=conversation_id,
            role="assistant", 
            content=full_content,
            user_id=user_id
        )
        logger.info(f"\n\nanswer: {assistant_msg}\n")
        # 生成完成后，保存完整消息到数据库
        # assistant_msg = await asyncio.to_thread(add_message, db, conversation_id, "assistant", full_content)
        
        # 发送一个结束标记或者带有 ID 的最终包
        yield f"data: {json.dumps({'type': 'answer_done', 'data': full_content, 'step': 5, 'conversation_id': str(conversation_id), 'message_id': str(assistant_msg.id)})}\n\n"
            
    except Exception as e:
        error_content = f"错误：{str(e)}"
        yield f"data: {json.dumps({'type': 'error', 'data': error_content})}\n\n"
