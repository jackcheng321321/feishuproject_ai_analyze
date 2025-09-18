#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本 - 用于Windows环境快速测试
避免复杂依赖的编译问题
"""

import subprocess
import sys
import os
from pathlib import Path

def install_basic_deps():
    """安装基础依赖"""
    basic_deps = [
        "fastapi",
        "uvicorn[standard]",
        "python-dotenv",
        "loguru"
    ]
    
    print("正在安装基础依赖...")
    for dep in basic_deps:
        print(f"安装 {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✓ {dep} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"✗ {dep} 安装失败: {e}")
            return False
    return True

def create_simple_app():
    """创建简单的FastAPI应用"""
    app_content = '''
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from loguru import logger
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建FastAPI应用
app = FastAPI(
    title="AI综合分析管理平台",
    description="快速启动版本 - 用于开发测试",
    version="0.1.0"
)

# 配置日志
logger.add("logs/app.log", rotation="1 day", retention="7 days")

@app.get("/")
async def root():
    """根路径"""
    logger.info("访问根路径")
    return {
        "message": "AI综合分析管理平台 - 快速启动版本",
        "status": "running",
        "version": "0.1.0"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "服务运行正常"}

@app.get("/api/test")
async def test_api():
    """测试API"""
    logger.info("测试API被调用")
    return {
        "message": "API测试成功",
        "data": {
            "timestamp": "2024-01-01T00:00:00Z",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # 创建日志目录
    os.makedirs("logs", exist_ok=True)
    
    logger.info("启动AI综合分析管理平台...")
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
'''
    
    with open("simple_main.py", "w", encoding="utf-8") as f:
        f.write(app_content)
    
    print("✓ 创建简单应用文件: simple_main.py")

def main():
    """主函数"""
    print("=" * 50)
    print("AI综合分析管理平台 - 快速启动")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        return False
    
    print(f"Python版本: {sys.version}")
    print(f"当前目录: {os.getcwd()}")
    
    # 安装依赖
    if not install_basic_deps():
        print("依赖安装失败，请检查网络连接")
        return False
    
    # 创建简单应用
    create_simple_app()
    
    print("\n" + "=" * 50)
    print("安装完成！")
    print("启动命令: python simple_main.py")
    print("访问地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    main()