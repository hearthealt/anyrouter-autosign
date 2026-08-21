"""
数据库连接配置
"""
import logging
from sqlalchemy import create_engine, inspect, text
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
    from app.models import User, Account, AccountGroup, SignLog, NotifyChannel, AccountNotify, Setting, ApiToken, ApiEndpoint, Platform

    _migrate_api_endpoint_schema()
    Base.metadata.create_all(bind=engine)
    _migrate_removed_settings()
    _migrate_adapter_schema()
    _migrate_platform_schema()
    _migrate_account_login_schema()
    _migrate_account_note_schema()
    _migrate_account_proxy_schema()

    # 初始化默认管理员
    _init_default_admin()


def _migrate_api_endpoint_schema():
    """将 api_endpoints 从全局单表迁移成按平台隔离。

    旧表结构缺少 platform_id 且 endpoint_id 有 UNIQUE 约束。SQLite 无法
    直接 DROP CONSTRAINT，且数据可以通过平台同步重建，所以直接丢弃旧表。
    """
    try:
        inspector = inspect(engine)
        if not inspector.has_table("api_endpoints"):
            return

        columns = {column["name"] for column in inspector.get_columns("api_endpoints")}
        if "platform_id" in columns:
            return

        with engine.begin() as conn:
            conn.execute(text("DROP TABLE api_endpoints"))
        logger.info("已删除旧版 api_endpoints 表，将在平台同步时重建")
    except Exception as e:
        logger.error(f"迁移 api_endpoints 表失败: {e}")


def _add_missing_columns(table_name: str, columns: dict[str, str]) -> None:
    """为 SQLite 旧表补充缺失列；关键迁移失败时阻止应用继续启动。"""
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return
    existing = {column["name"] for column in inspector.get_columns(table_name)}
    missing = [(name, ddl) for name, ddl in columns.items() if name not in existing]
    if not missing:
        return
    with engine.begin() as conn:
        for name, ddl in missing:
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {name} {ddl}"))
            logger.info("已为 %s 表添加 %s 列", table_name, name)


def _migrate_adapter_schema():
    """补充通用平台适配器和账号认证字段。"""
    _add_missing_columns("platforms", {
        "adapter_type": "VARCHAR(30) DEFAULT 'new_api' NOT NULL",
        "adapter_config": "TEXT DEFAULT '{}'",
    })
    _add_missing_columns("accounts", {
        "external_user_id": "VARCHAR(255)",
        "auth_type": "VARCHAR(30)",
        "auth_data": "TEXT",
    })
    _add_missing_columns("sign_logs", {
        "reward_display": "VARCHAR(100)",
        "reward_unit": "VARCHAR(50)",
    })
    with engine.begin() as conn:
        if inspect(engine).has_table("platforms"):
            conn.execute(text(
                "UPDATE platforms SET adapter_type = 'new_api' "
                "WHERE adapter_type IS NULL OR adapter_type = ''"
            ))
            conn.execute(text(
                "UPDATE platforms SET adapter_config = '{}' "
                "WHERE adapter_config IS NULL OR adapter_config = ''"
            ))
        if inspect(engine).has_table("accounts"):
            conn.execute(text(
                "UPDATE accounts SET external_user_id = CAST(anyrouter_user_id AS VARCHAR) "
                "WHERE external_user_id IS NULL AND anyrouter_user_id IS NOT NULL"
            ))


def _migrate_removed_settings():
    """删除已废弃的全局代理设置。"""
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        if not inspector.has_table("settings"):
            return

        result = db.execute(text("""
            DELETE FROM settings
            WHERE key IN (
                'anyrouter_proxy_enabled',
                'anyrouter_proxy_url',
                'anrouter_proxy_enabled',
                'anrouter_proxy_url'
            )
        """))
        if result.rowcount:
            db.commit()
            logger.info(f"已删除 {result.rowcount} 条废弃全局代理设置")
    except Exception as e:
        db.rollback()
        logger.error(f"清理废弃设置失败: {e}")
    finally:
        db.close()


def _migrate_platform_schema():
    """将旧数据库迁移到平台化结构。"""
    from app.models import Platform
    from app.utils.platform import (
        DEFAULT_BASE_URL,
        DEFAULT_CHECKIN_API,
        DEFAULT_CONSOLE_URL,
        DEFAULT_GROUPS_API,
        DEFAULT_MODELS_API,
        DEFAULT_SIGN_MODE,
        DEFAULT_SIGN_API,
        DEFAULT_STATUS_API,
        DEFAULT_TOKEN_API,
        DEFAULT_USER_API,
    )

    db = SessionLocal()
    try:
        inspector = inspect(engine)
        if not inspector.has_table("accounts"):
            return

        account_columns = {column["name"] for column in inspector.get_columns("accounts")}
        if "platform_id" not in account_columns:
            db.execute(text("ALTER TABLE accounts ADD COLUMN platform_id INTEGER"))
            db.commit()
            logger.info("已为 accounts 表添加 platform_id 列")

        if inspector.has_table("platforms"):
            platform_columns = {column["name"] for column in inspector.get_columns("platforms")}
            if "sign_mode" not in platform_columns:
                db.execute(text("ALTER TABLE platforms ADD COLUMN sign_mode VARCHAR(20)"))
                db.commit()
                logger.info("已为 platforms 表添加 sign_mode 列")

            result = db.execute(
                text("UPDATE platforms SET sign_mode = :sign_mode WHERE sign_mode IS NULL OR sign_mode = ''"),
                {"sign_mode": DEFAULT_SIGN_MODE}
            )
            if result.rowcount:
                db.commit()
                logger.info(f"已为 {result.rowcount} 个平台回填 sign_mode")

            if "checkin_api" not in platform_columns:
                db.execute(text("ALTER TABLE platforms ADD COLUMN checkin_api VARCHAR(255)"))
                db.commit()
                logger.info("已为 platforms 表添加 checkin_api 列")

            result = db.execute(
                text("UPDATE platforms SET checkin_api = :checkin_api WHERE checkin_api IS NULL OR checkin_api = ''"),
                {"checkin_api": DEFAULT_CHECKIN_API}
            )
            if result.rowcount:
                db.commit()
                logger.info(f"已为 {result.rowcount} 个平台回填 checkin_api")

            if "captcha_api" not in platform_columns:
                db.execute(text("ALTER TABLE platforms ADD COLUMN captcha_api VARCHAR(255)"))
                db.commit()
                logger.info("已为 platforms 表添加 captcha_api 列")

        default_platform = db.query(Platform).filter(Platform.is_default == True).first()
        if default_platform is None:
            anyrouter_platform = db.query(Platform).filter(Platform.base_url == DEFAULT_BASE_URL).first()
            if anyrouter_platform is None:
                anyrouter_platform = Platform(
                    name="AnyRouter",
                    base_url=DEFAULT_BASE_URL,
                    adapter_type="new_api",
                    adapter_config="{}",
                    sign_mode=DEFAULT_SIGN_MODE,
                    sign_api=DEFAULT_SIGN_API,
                    checkin_api=DEFAULT_CHECKIN_API,
                    user_api=DEFAULT_USER_API,
                    console_url=DEFAULT_CONSOLE_URL,
                    models_api=DEFAULT_MODELS_API,
                    groups_api=DEFAULT_GROUPS_API,
                    token_api=DEFAULT_TOKEN_API,
                    status_api=DEFAULT_STATUS_API,
                    captcha_api="",
                    is_default=True,
                )
                db.add(anyrouter_platform)
                db.commit()
                db.refresh(anyrouter_platform)
                logger.info("已创建默认平台 AnyRouter")
            else:
                anyrouter_platform.is_default = True
                db.commit()
                db.refresh(anyrouter_platform)
                logger.info("已将现有 AnyRouter 平台设为默认平台")
            default_platform = anyrouter_platform

        result = db.execute(
            text("UPDATE accounts SET platform_id = :platform_id WHERE platform_id IS NULL"),
            {"platform_id": default_platform.id}
        )
        if result.rowcount:
            db.commit()
            logger.info(f"已为 {result.rowcount} 个旧账号回填默认平台")

    except Exception as e:
        db.rollback()
        logger.error(f"平台结构迁移失败: {e}")
    finally:
        db.close()


def _migrate_account_login_schema():
    """为旧数据库补充账号登录凭证字段。"""
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        if not inspector.has_table("accounts"):
            return

        account_columns = {column["name"] for column in inspector.get_columns("accounts")}

        if "login_username" not in account_columns:
            db.execute(text("ALTER TABLE accounts ADD COLUMN login_username VARCHAR(255)"))
            db.commit()
            logger.info("已为 accounts 表添加 login_username 列")

        if "login_password" not in account_columns:
            db.execute(text("ALTER TABLE accounts ADD COLUMN login_password TEXT"))
            db.commit()
            logger.info("已为 accounts 表添加 login_password 列")

    except Exception as e:
        db.rollback()
        logger.error(f"账号登录字段迁移失败: {e}")
    finally:
        db.close()


def _migrate_account_note_schema():
    """为旧数据库补充账号备注字段。"""
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        if not inspector.has_table("accounts"):
            return

        account_columns = {column["name"] for column in inspector.get_columns("accounts")}

        if "note" not in account_columns:
            db.execute(text("ALTER TABLE accounts ADD COLUMN note VARCHAR(255)"))
            db.commit()
            logger.info("已为 accounts 表添加 note 列")

    except Exception as e:
        db.rollback()
        logger.error(f"账号备注字段迁移失败: {e}")
    finally:
        db.close()


def _migrate_account_proxy_schema():
    """为旧数据库补充账号级代理字段。"""
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        if not inspector.has_table("accounts"):
            return

        account_columns = {column["name"] for column in inspector.get_columns("accounts")}

        if "proxy_mode" not in account_columns:
            db.execute(text("ALTER TABLE accounts ADD COLUMN proxy_mode VARCHAR(20)"))
            db.commit()
            logger.info("已为 accounts 表添加 proxy_mode 列")

        if "proxy_url" not in account_columns:
            db.execute(text("ALTER TABLE accounts ADD COLUMN proxy_url TEXT"))
            db.commit()
            logger.info("已为 accounts 表添加 proxy_url 列")

        result = db.execute(
            text("UPDATE accounts SET proxy_mode = 'direct' WHERE proxy_mode IS NULL OR proxy_mode = '' OR proxy_mode = 'global'")
        )
        if result.rowcount:
            db.commit()
            logger.info(f"已为 {result.rowcount} 个账号回填默认代理模式")

    except Exception as e:
        db.rollback()
        logger.error(f"账号代理字段迁移失败: {e}")
    finally:
        db.close()


def _init_default_admin():
    """初始化默认管理员账号"""
    from app.models import User
    from app.utils import hash_password

    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
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
