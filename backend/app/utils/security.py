"""
安全工具模块
"""
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError

from app.config import settings


def hash_password(password: str) -> str:
    """
    加密密码

    Args:
        password: 明文密码

    Returns:
        str: 加密后的密码哈希
    """
    # bcrypt 最大支持 72 字节
    if len(password.encode('utf-8')) > 72:
        password = password[:72]

    import bcrypt
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 密码哈希

    Returns:
        bool: 密码是否正确
    """
    # bcrypt 最大支持 72 字节
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password[:72]

    import bcrypt
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT Token

    Args:
        data: Token 中的数据
        expires_delta: 过期时间增量

    Returns:
        str: JWT Token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    解析 JWT Token

    Args:
        token: JWT Token

    Returns:
        Optional[dict]: Token 中的数据，解析失败返回 None
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        logger.error(f"Token 解析失败: {e}")
        return None
