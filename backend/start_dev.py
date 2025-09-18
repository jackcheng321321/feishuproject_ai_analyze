#!/usr/bin/env python3
"""
开发环境快速启动脚本
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_dependencies():
    """检查依赖是否已安装"""
    try:
        import fastapi
        import sqlalchemy
        import uvicorn
        import pydantic
        import aiohttp
        import aiofiles
        logger.info("✅ 核心依赖检查通过")
        return True
    except ImportError as e:
        logger.error(f"❌ 缺少依赖: {e}")
        logger.info("请运行: pip install -r requirements.txt")
        return False


def init_database():
    """初始化数据库"""
    try:
        logger.info("🔧 初始化数据库...")
        from app.scripts.init_db import init_database
        
        success = init_database()
        if success:
            logger.info("✅ 数据库初始化成功")
            return True
        else:
            logger.error("❌ 数据库初始化失败")
            return False
    except Exception as e:
        logger.error(f"❌ 数据库初始化异常: {e}")
        return False


def start_server():
    """启动开发服务器"""
    try:
        logger.info("🚀 启动开发服务器...")
        logger.info("服务器地址: http://localhost:8000")
        logger.info("API文档: http://localhost:8000/docs")
        logger.info("按 Ctrl+C 停止服务器")
        
        # 使用uvicorn启动服务器
        import uvicorn
        
        # 配置日志
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_config=log_config,
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("\n👋 服务器已停止")
    except Exception as e:
        logger.error(f"❌ 启动服务器失败: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 AI综合分析管理平台 - 开发环境启动")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        return False
    
    # 初始化数据库
    if not init_database():
        return False
    
    print("\n" + "=" * 60)
    print("✅ 系统初始化完成，正在启动服务器...")
    print("=" * 60)
    
    # 启动服务器
    start_server()
    
    return True


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)