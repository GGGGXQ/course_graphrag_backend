from datetime import datetime, timedelta
from jose import JWTError, jwt
from contextlib import contextmanager
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from redis.asyncio import Redis

from database import SessionLocal
from depends.session import  get_db_dep
from depends.redis import get_aioredis
from config import SECRET_KEY, ALGORITHM
from domains.users import User
from daos import user_dao

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="course-graphrag/v1//users/login")
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


@contextmanager
def get_db_context(session_maker=SessionLocal):
    db = session_maker()
    try:
        yield db
    except Exception as e:
        raise e
    finally:
        db.close()


def create_access_token(data: dict, expires_delta):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_id_from_token(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    userid: str = payload.get("sub")
    return userid

async def get_current_user(
    db: Session = Depends(get_db_dep),
    token: str = Depends(oauth2_scheme),
    redis_dep: Redis = Depends(get_aioredis),
) -> User:
    try:
        userid = get_user_id_from_token(token)
        if not userid:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    if not redis_dep.get(userid):
        raise credentials_exception
    try:
        user = user_dao.get_user_by_id(db, userid)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    if user is None:
        raise credentials_exception
    return user

def verify_email_format(email: str) -> bool:
    """简单验证邮箱格式"""
    if "@" not in email or "." not in email:
        return False
    return True