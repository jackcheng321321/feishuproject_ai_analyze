#!/usr/bin/env python3
"""
快速设置测试服务脚本
自动启动PostgreSQL、Redis等依赖服务
"""

import os
import sys
import subprocess
import time
import psycopg2
import redis
from pathlib import Path

def check_docker():
    """检查Docker是否可用"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] Docker可用: {result.stdout.strip()}")
            return True
        else:
            print("[ERROR] Docker不可用")
            return False
    except FileNotFoundError:
        print("[ERROR] 未找到Docker命令")
        return False

def start_postgresql():
    """启动PostgreSQL容器"""
    print("\n[POSTGRES] 启动PostgreSQL服务...")
    
    # 检查是否已运行
    check_cmd = ["docker", "ps", "--filter", "name=postgres_test", "--format", "{{.Names}}"]
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    
    if "postgres_test" in result.stdout:
        print("   [INFO] PostgreSQL容器已在运行")
        return True
    
    # 启动新容器
    docker_cmd = [
        "docker", "run", "-d",
        "--name", "postgres_test",
        "-e", "POSTGRES_DB=ai_analysis_test",
        "-e", "POSTGRES_USER=postgres", 
        "-e", "POSTGRES_PASSWORD=postgres",
        "-p", "5432:5432",
        "postgres:15-alpine"
    ]
    
    try:
        result = subprocess.run(docker_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("   [OK] PostgreSQL容器启动成功")
            
            # 等待数据库就绪
            print("   [INFO] 等待数据库就绪...")
            for i in range(30):
                try:
                    conn = psycopg2.connect(
                        host="localhost",
                        port=5432,
                        database="ai_analysis_test",
                        user="postgres",
                        password="postgres"
                    )
                    conn.close()
                    print("   [OK] 数据库连接测试成功")
                    return True
                except psycopg2.OperationalError:
                    time.sleep(2)
                    print(f"   [WAIT] 等待中... ({i+1}/30)")
            
            print("   [ERROR] 数据库启动超时")
            return False
        else:
            print(f"   [ERROR] 容器启动失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   [ERROR] 启动异常: {e}")
        return False

def start_redis():
    """启动Redis容器"""
    print("\n[REDIS] 启动Redis服务...")
    
    # 检查是否已运行
    check_cmd = ["docker", "ps", "--filter", "name=redis_test", "--format", "{{.Names}}"]
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    
    if "redis_test" in result.stdout:
        print("   [INFO] Redis容器已在运行")
        return True
    
    # 启动新容器
    docker_cmd = [
        "docker", "run", "-d",
        "--name", "redis_test",
        "-p", "6379:6379",
        "redis:7-alpine",
        "redis-server", "--appendonly", "yes"
    ]
    
    try:
        result = subprocess.run(docker_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("   [OK] Redis容器启动成功")
            
            # 测试Redis连接
            for i in range(10):
                try:
                    r = redis.Redis(host="localhost", port=6379, db=1, decode_responses=True)
                    r.ping()
                    print("   [OK] Redis连接测试成功")
                    return True
                except redis.ConnectionError:
                    time.sleep(1)
                    print(f"   [WAIT] 等待中... ({i+1}/10)")
            
            print("   [ERROR] Redis启动超时")
            return False
        else:
            print(f"   [ERROR] 容器启动失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   [ERROR] 启动异常: {e}")
        return False

def stop_test_services():
    """停止测试服务"""
    print("\n[CLEANUP] 停止测试服务...")
    
    services = ["postgres_test", "redis_test"]
    for service in services:
        try:
            # 停止容器
            subprocess.run(["docker", "stop", service], capture_output=True)
            # 删除容器
            subprocess.run(["docker", "rm", service], capture_output=True)
            print(f"   [OK] {service} 已停止并删除")
        except Exception as e:
            print(f"   [WARNING] {service} 清理失败: {e}")

def show_connection_info():
    """显示连接信息"""
    print("\n" + "="*60)
    print("测试服务连接信息")
    print("="*60)
    print("PostgreSQL:")
    print("  主机: localhost")
    print("  端口: 5432") 
    print("  数据库: ai_analysis_test")
    print("  用户名: postgres")
    print("  密码: postgres")
    print("  连接URL: postgresql://postgres:postgres@localhost:5432/ai_analysis_test")
    print()
    print("Redis:")
    print("  主机: localhost")
    print("  端口: 6379")
    print("  数据库: 1")
    print("  连接URL: redis://localhost:6379/1")
    print("="*60)

def install_dependencies():
    """安装必要的Python依赖"""
    print("\n[DEPS] 检查Python依赖...")
    
    dependencies = [
        "psycopg2-binary",
        "redis", 
        "asyncpg"  # 异步PostgreSQL驱动
    ]
    
    for dep in dependencies:
        try:
            __import__(dep.replace("-", "_"))
            print(f"   [OK] {dep} 已安装")
        except ImportError:
            print(f"   [INSTALL] 安装 {dep}...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", dep])
            if result.returncode == 0:
                print(f"   [OK] {dep} 安装成功")
            else:
                print(f"   [ERROR] {dep} 安装失败")
                return False
    
    return True

def main():
    """主函数"""
    print("AI分析平台 - 测试服务设置")
    print("="*60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        stop_test_services()
        return
    
    # 检查前置条件
    if not check_docker():
        print("\n[ERROR] 请先安装Docker Desktop并确保其正在运行")
        return
    
    # 安装依赖
    if not install_dependencies():
        print("\n[ERROR] 依赖安装失败，请检查网络连接")
        return
    
    # 启动服务
    postgres_ok = start_postgresql()
    redis_ok = start_redis()
    
    if postgres_ok and redis_ok:
        show_connection_info()
        print("\n[SUCCESS] 所有测试服务已就绪!")
        print("\n下一步:")
        print("1. 编辑 run_production_test.py 配置真实的AI API密钥")
        print("2. 运行: python run_production_test.py")
        print("\n要停止服务，运行: python setup_test_services.py stop")
    else:
        print("\n[ERROR] 部分服务启动失败，请检查Docker环境")

if __name__ == "__main__":
    main()