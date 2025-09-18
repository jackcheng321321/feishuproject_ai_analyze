#!/usr/bin/env python3
"""应用启动脚本

提供便捷的启动方式和环境检查。
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app.core.config import settings
    from app.core.logger import logger
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所有依赖: pip install -r requirements.txt")
    sys.exit(1)


def check_environment():
    """检查环境配置"""
    logger.info("检查环境配置...")
    
    # 检查必需的环境变量
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"缺少必需的环境变量: {', '.join(missing_vars)}")
        logger.info("请复制 .env.example 到 .env 并配置相应的值")
        return False
    
    logger.info("环境配置检查通过")
    return True


def check_database():
    """检查数据库连接"""
    logger.info("检查数据库连接...")
    
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.info("数据库连接正常")
        return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        logger.info("请确保数据库服务已启动并且连接配置正确")
        return False


def run_migrations():
    """运行数据库迁移"""
    logger.info("运行数据库迁移...")
    
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        logger.info("数据库迁移完成")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"数据库迁移失败: {e}")
        return False
    except FileNotFoundError:
        logger.error("未找到 alembic 命令，请确保已安装 alembic")
        return False


def start_server(host="0.0.0.0", port=8000, reload=False, workers=1):
    """启动服务器"""
    logger.info(f"启动服务器 {host}:{port}...")
    
    cmd = [
        "uvicorn",
        "app.main:app",
        "--host", host,
        "--port", str(port),
    ]
    
    if reload:
        cmd.append("--reload")
    elif workers > 1:
        cmd.extend(["--workers", str(workers)])
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"启动服务器失败: {e}")


def create_superuser():
    """创建超级用户"""
    logger.info("创建超级用户...")
    
    try:
        from app.models.user import User
        from app.core.database import SessionLocal
        from app.core.security import get_password_hash
        import uuid
        
        db = SessionLocal()
        
        # 检查是否已存在超级用户
        existing_user = db.query(User).filter(User.is_superuser == True).first()
        if existing_user:
            logger.info(f"超级用户已存在: {existing_user.email}")
            return
        
        # 获取用户输入
        email = input("请输入超级用户邮箱: ")
        password = input("请输入密码: ")
        full_name = input("请输入全名 (可选): ") or "Super User"
        
        # 创建用户
        user = User(
            id=uuid.uuid4(),
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_superuser=True,
        )
        
        db.add(user)
        db.commit()
        
        logger.info(f"超级用户创建成功: {email}")
        
    except Exception as e:
        logger.error(f"创建超级用户失败: {e}")
    finally:
        db.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="飞书项目AI后端启动脚本")
    parser.add_argument(
        "command",
        choices=["dev", "prod", "check", "migrate", "createsuperuser"],
        help="执行的命令"
    )
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数量")
    parser.add_argument("--skip-checks", action="store_true", help="跳过环境检查")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.command == "dev":
        os.environ.setdefault("LOG_LEVEL", "DEBUG")
    
    logger.info(f"执行命令: {args.command}")
    
    if args.command == "check":
        # 只进行环境检查
        success = True
        success &= check_environment()
        success &= check_database()
        
        if success:
            logger.info("所有检查通过")
            sys.exit(0)
        else:
            logger.error("检查失败")
            sys.exit(1)
    
    elif args.command == "migrate":
        # 只运行迁移
        if not args.skip_checks:
            if not check_environment():
                sys.exit(1)
        
        if run_migrations():
            logger.info("迁移完成")
        else:
            sys.exit(1)
    
    elif args.command == "createsuperuser":
        # 创建超级用户
        if not args.skip_checks:
            if not check_environment() or not check_database():
                sys.exit(1)
        
        create_superuser()
    
    elif args.command in ["dev", "prod"]:
        # 启动服务器
        if not args.skip_checks:
            if not check_environment():
                sys.exit(1)
            
            if not check_database():
                logger.warning("数据库连接失败，但仍将启动服务器")
        
        # 开发模式
        if args.command == "dev":
            start_server(
                host=args.host,
                port=args.port,
                reload=True
            )
        # 生产模式
        else:
            start_server(
                host=args.host,
                port=args.port,
                workers=args.workers
            )


if __name__ == "__main__":
    main()