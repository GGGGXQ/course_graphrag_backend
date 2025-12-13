from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class CaptchaRequest(BaseModel):
    email: str

class CaptchaResponse(BaseModel):
    message: str

class LoginRequest(BaseModel):
    email: str
    code: str

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    """用户基础信息"""

    id: Optional[UUID] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    account: Optional[str] = None
    password: Optional[str] = None
    avatar_url: Optional[str] = None
    is_deleted: bool = False

class UserAndToken(User, Token):
    pass

class UserInfoResponse(BaseModel):
    """用户信息响应"""
    id: str
    phone: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None


class RenameRequest(BaseModel):
    new_username: str
