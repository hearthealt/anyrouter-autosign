"""
数据库连接配置
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

logger = logging.getLogger(__name__)

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # SQLite 需要
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库"""
    # 导入所有模型以确保表被创建
    from app.models import User, Account, AccountGroup, SignLog, NotifyChannel, AccountNotify, Setting, ApiToken, ApiEndpoint

    Base.metadata.create_all(bind=engine)

    # 初始化默认管理员
    _init_default_admin()


def _init_default_admin():
    """初始化默认管理员账号"""
    # 延迟导入避免循环依赖
    from app.models import User
    from app.utils import hash_password

    db = SessionLocal()
    try:
        # 检查是否已存在用户
        user_count = db.query(User).count()
        if user_count == 0:
            # 创建默认管理员
            admin = User(
                username=settings.default_admin_username,
                password_hash=hash_password(settings.default_admin_password),
                is_active=True
            )
            db.add(admin)
            db.commit()
            logger.info(f"已创建默认管理员账号: {settings.default_admin_username}")
    except Exception as e:
        logger.error(f"初始化默认管理员失败: {e}")
    finally:
        db.close()
