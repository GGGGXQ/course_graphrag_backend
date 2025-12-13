import random
from uuid import UUID
from datetime import timedelta
from traceback import format_exc

from fastapi import APIRouter, Body, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from depends.session import get_db_dep
from depends.redis import get_aioredis
from utils.api_record_util import RequestRecordRoute
from utils.email_util import EmailUtil
from daos import user_dao
from domains import users
from utils.jwt_util import create_access_token, verify_email_format, get_current_user
from utils.logger_util import logger
from constant import ACCESS_TOKEN_EXPIRE_MINUTES

user_router = APIRouter(prefix="/users", tags=["user"], route_class=RequestRecordRoute)

@user_router.post("/captcha", response_model=users.CaptchaResponse, summary="获取邮箱验证码")
async def create_captcha(
    captcha_request: users.CaptchaRequest,
    db: Session = Depends(get_db_dep),
    redis_dep: Redis = Depends(get_aioredis),
):
    """发送邮箱验证码"""
    # 邮箱格式校验
    if not verify_email_format(captcha_request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="请输入有效的邮箱地址！"
        )
    code = str(random.randint(0, 999999)).zfill(6)
    redis_code = captcha_request.email + ":" + code
    success, message = EmailUtil.send_email(captcha_request.email, code)
    await redis_dep.setex(redis_code, 300, code)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return users.CaptchaResponse(message=message)

@user_router.post("/login", response_model=users.UserAndToken, summary="用户登录或注册，未注册则自动注册")
async def login_or_register(
    login_request: users.LoginRequest = Body(..., description="登录或注册请求体"),
    db: Session = Depends(get_db_dep),
    redis_dep: Redis = Depends(get_aioredis),
):
    """用户登录或注册，未注册则自动注册"""
    try:
        if not verify_email_format(login_request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="请输入有效的邮箱地址！"
            )
        # 验证码校验
        redis_code = login_request.email + ":" + login_request.code
        stored_code = await redis_dep.get(redis_code)
        if not stored_code or stored_code != login_request.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误或已过期"
            )
        try:
            existing_user = user_dao.get_user_by_email(
                db, email=login_request.email
            )
            # 用户已注册，直接登录
            access_token = create_access_token(
                data={"sub": str(existing_user.id)},
                expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            )
            # 保存token到Redis
            await redis_dep.setex(
                str(existing_user.id), ACCESS_TOKEN_EXPIRE_MINUTES * 60, access_token
            )

            await redis_dep.delete(redis_code)
            token = users.Token(access_token=access_token, token_type="bearer")
            return users.UserAndToken(**existing_user.model_dump(), **token.model_dump())
        except ValueError:
            # 用户不存在，可以继续注册
            pass

        new_user = users.User(email=login_request.email, username=login_request.email)
        created_user = user_dao.create_user(db, new_user)

        access_token = create_access_token(
                data={"sub": str(created_user.id)},
                expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            )

        # 保存token到Redis
        await redis_dep.setex(
            str(created_user.id), ACCESS_TOKEN_EXPIRE_MINUTES * 60, access_token
        )

        await redis_dep.delete(redis_code)
        token = users.Token(access_token=access_token, token_type="bearer")
        return users.UserAndToken(**created_user.model_dump(), **token.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录或注册失败: {str(e)}")
        logger.error(format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录或注册失败，请稍后重试",
        )

@user_router.get("/me", response_model=users.UserInfoResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: users.User = Depends(get_current_user),
    db: Session = Depends(get_db_dep)
):
    """
    获取当前用户信息
    """
    return users.UserInfoResponse(
        id=str(current_user.id),
        phone=current_user.phone,
        username=current_user.username or current_user.email,
        email=current_user.email,
        avatar_url=current_user.avatar_url
    )

@user_router.post("/logout", summary="用户退出登录")
async def logout(
    current_user: users.User = Depends(get_current_user),
    redis_dep: Redis = Depends(get_aioredis),
):
    try:
        await redis_dep.delete(str(current_user.id))
        return "success"
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

@user_router.post("/rename", response_model=users.UserInfoResponse, summary="修改用户名")
async def rename_user(
    rename_request: users.RenameRequest = Body(..., description="修改用户名请求体"),
    current_user: users.User = Depends(get_current_user),
    db: Session = Depends(get_db_dep),
    redis_dep: Redis = Depends(get_aioredis)
):
    """修改用户名"""
    try:
        user = user_dao.rename_username(db, current_user.id, rename_request.new_username)
        return users.UserInfoResponse(
            id=str(user.id),
            phone=user.phone,
            username=user.username or user.email,
            email=user.email,
            avatar_url=user.avatar_url
        )
    except Exception as e:
        logger.error(f"修改用户名失败: {str(e)}")
        logger.error(format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改用户名失败，请稍后重试",
        )
