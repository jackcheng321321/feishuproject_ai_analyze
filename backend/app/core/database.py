from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging
from typing import Generator

from app.core.config import settings

logger = logging.getLogger(__name__)

# 创建数据库引擎
engine = create_engine(
    settings.get_database_url(),
    pool_pre_ping=True,  # 连接前检查连接是否有效
    pool_recycle=300,    # 5分钟后回收连接
    pool_size=10,        # 连接池大小
    max_overflow=20,     # 最大溢出连接数
    echo=settings.is_development(),  # 开发环境下打印SQL
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 创建基础模型类
Base = declarative_base()


# 数据库连接事件监听器
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """为SQLite设置pragma（如果使用SQLite）"""
    if "sqlite" in settings.get_database_url():
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """SQL执行前的日志记录"""
    if settings.is_development():
        logger.debug(f"SQL执行: {statement}")
        if parameters:
            logger.debug(f"参数: {parameters}")


@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """SQL执行后的日志记录"""
    if settings.is_development():
        logger.debug(f"SQL执行完成，影响行数: {cursor.rowcount}")


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话的依赖注入函数"""
    db = SessionLocal()
    try:
        logger.debug("创建数据库会话")
        yield db
    except Exception as e:
        logger.error(f"数据库会话异常: {e}")
        db.rollback()
        raise
    finally:
        logger.debug("关闭数据库会话")
        db.close()


def create_tables():
    """创建所有数据库表"""
    try:
        logger.info("开始创建数据库表...")
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建完成")
    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")
        raise


def drop_tables():
    """删除所有数据库表（谨慎使用）"""
    try:
        logger.warning("开始删除所有数据库表...")
        Base.metadata.drop_all(bind=engine)
        logger.warning("所有数据库表已删除")
    except Exception as e:
        logger.error(f"删除数据库表失败: {e}")
        raise


def check_database_connection() -> bool:
    """检查数据库连接是否正常"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("数据库连接正常")
        return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    def health_check(self) -> dict:
        """数据库健康检查"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT version()"))
                version = result.fetchone()[0] if result.rowcount > 0 else "Unknown"
                
                # 获取连接池状态
                pool = self.engine.pool
                pool_status = {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                }
                
                return {
                    "status": "healthy",
                    "database_version": version,
                    "connection_pool": pool_status,
                    "url": settings.get_database_url().split("@")[-1],  # 隐藏密码
                }
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "url": settings.get_database_url().split("@")[-1],
            }
    
    def execute_raw_sql(self, sql: str, params: dict = None) -> list:
        """执行原始SQL查询"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(sql, params or {})
                if result.returns_rows:
                    return [dict(row) for row in result.fetchall()]
                return []
        except Exception as e:
            logger.error(f"执行SQL失败: {e}")
            raise
    
    def get_table_info(self, table_name: str) -> dict:
        """获取表信息"""
        try:
            # PostgreSQL查询
            sql = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = :table_name
            ORDER BY ordinal_position;
            """
            
            columns = self.execute_raw_sql(sql, {"table_name": table_name})
            
            # 获取表统计信息
            count_sql = f"SELECT COUNT(*) as row_count FROM {table_name}"
            count_result = self.execute_raw_sql(count_sql)
            row_count = count_result[0]["row_count"] if count_result else 0
            
            return {
                "table_name": table_name,
                "columns": columns,
                "row_count": row_count,
            }
        except Exception as e:
            logger.error(f"获取表信息失败: {e}")
            return {"error": str(e)}


# 创建全局数据库管理器实例
db_manager = DatabaseManager()