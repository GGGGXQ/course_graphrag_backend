from sqlalchemy.orm import Session
from db_schemas.schemas import DBUser
from uuid import UUID

from domains.users import User


def get_user_by_email(db: Session, email: str) -> User:
    """根据邮箱获取用户"""
    if not email:
        return None
    dbuser = (
        db.query(DBUser)
        .filter(
            DBUser.email == email,
            DBUser.is_deleted.is_(False),
        )
        .first()
    )

    if not dbuser:
        raise ValueError(f"User {email} does not exist")
    user = User(**dbuser.to_dict())
    return user


# TODO 后面换手机号注册登录再用上
# def get_user_by_phone(db: Session, phone: str) -> DBUser:
#     """根据手机号获取用户"""
#     return db.query(DBUser).filter(DBUser.phone == phone).first()


def create_user(db: Session, user: User) -> User:
    """创建新用户"""
    dbuser = (
            db.query(DBUser)
            .filter(DBUser.email == user.email, DBUser.is_deleted.is_(False))
            .first()
        )
    if dbuser:
        if dbuser.is_deleted is True:
            dbuser.is_deleted = False
        else:
            raise ValueError(f"User {dbuser.id} already exists")
    else:
        dbuser = DBUser(
            **user.model_dump(
                mode="json",
                exclude=["id", "code", "share_user_id", "member_end_date", "is_member"],
            ),
        )
        db.add(dbuser)
        db.flush()
        db.commit()
    user.id = dbuser.id
    return user


def get_user_by_id(db: Session, user_id: UUID) -> User:
    """根据用户ID获取用户"""
    dbuser = (
        db.query(DBUser)
        .filter(
            DBUser.id == user_id,
            DBUser.is_deleted.__eq__(False),
        )
        .first()
    )
    if not dbuser:
        raise ValueError(f"User {user_id} does not exist")
    user_dict = dbuser.to_dict()
    user = User(**user_dict)
    return user

def rename_username(db: Session, user_id: UUID, new_username: str) -> User:
    """修改用户名"""
    dbuser = (
        db.query(DBUser)
        .filter(
            DBUser.id == user_id,
            DBUser.is_deleted.__eq__(False),
        )
        .first()
    )
    if not dbuser:
        raise ValueError(f"User {user_id} does not exist")
    dbuser.username = new_username
    db.commit()
    db.refresh(dbuser)
    user_dict = dbuser.to_dict()
    user = User(**user_dict)
    return user
    