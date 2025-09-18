#!/usr/bin/env python3
"""
数据库初始化脚本
创建初始用户和示例数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, create_tables
from app.core.security import get_password_hash, encrypt_sensitive_data
from app.models.user import User
from app.models.ai_model import AIModel, ModelType
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_initial_user(db: Session):
    """创建初始管理员用户"""
    try:
        # 检查是否已有用户
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            logger.info("管理员用户已存在，跳过创建")
            return existing_user
        
        # 创建管理员用户
        hashed_password = get_password_hash("admin123")
        
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hashed_password,
            full_name="系统管理员",
            is_superuser=True,
            is_active=True,
            is_verified=True,
            can_manage_config=True,
            can_manage_webhooks=True,
            can_manage_tasks=True,
            can_view_logs=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"创建管理员用户成功: {admin_user.username}")
        return admin_user
        
    except Exception as e:
        logger.error(f"创建管理员用户失败: {e}")
        db.rollback()
        raise


def create_sample_ai_model(db: Session):
    """创建示例AI模型配置"""
    try:
        # 检查是否已有示例模型
        existing_model = db.query(AIModel).filter(AIModel.name == "Gemini Pro").first()
        if existing_model:
            logger.info("示例AI模型已存在，跳过创建")
            return existing_model
        
        # 创建示例Gemini模型（需要用户后续配置API密钥）
        sample_api_key = "YOUR_GEMINI_API_KEY_HERE"
        encrypted_api_key = encrypt_sensitive_data(sample_api_key)
        
        gemini_model = AIModel(
            name="Gemini Pro",
            display_name="Google Gemini Pro",
            model_type=ModelType.GOOGLE,
            api_endpoint="https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
            api_key_encrypted=encrypted_api_key,
            model_name="gemini-pro",
            max_tokens=8192,
            temperature="0.7",
            top_p="0.95",
            frequency_penalty="0.0",
            presence_penalty="0.0",
            default_params={
                "topK": 64,
                "temperature": 0.7,
                "maxOutputTokens": 8192
            },
            supports_streaming=False,
            supports_function_calling=False,
            supports_vision=False,
            supports_multimodal=True,
            rate_limit_per_minute=60,
            rate_limit_per_day=1000,
            max_concurrent_requests=5,
            cost_per_1k_input_tokens="0.0005",
            cost_per_1k_output_tokens="0.0015",
            currency="USD",
            is_active=False,  # 默认不激活，等待用户配置API密钥
            is_default=False,
            description="Google Gemini Pro模型，支持文本生成和分析",
            usage_notes="请在激活前配置正确的Google AI API密钥。访问 https://ai.google.dev/ 获取API密钥。",
            health_status="unknown"
        )
        
        db.add(gemini_model)
        db.commit()
        db.refresh(gemini_model)
        
        logger.info(f"创建示例AI模型成功: {gemini_model.name}")
        return gemini_model
        
    except Exception as e:
        logger.error(f"创建示例AI模型失败: {e}")
        db.rollback()
        raise


def init_database():
    """初始化数据库"""
    try:
        logger.info("开始初始化数据库...")
        
        # 创建数据库表
        logger.info("创建数据库表...")
        create_tables()
        
        # 创建数据库会话
        db = SessionLocal()
        
        try:
            # 创建初始用户
            logger.info("创建初始用户...")
            admin_user = create_initial_user(db)
            
            # 创建示例AI模型
            logger.info("创建示例AI模型...")
            sample_model = create_sample_ai_model(db)
            
            logger.info("数据库初始化完成！")
            logger.info(f"管理员账号: admin / admin123")
            logger.info(f"请访问 http://localhost:8000/docs 查看API文档")
            logger.info(f"记得配置 {sample_model.name} 的API密钥以开始使用AI功能")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("AI综合分析管理平台 - 数据库初始化")
    print("=" * 60)
    
    success = init_database()
    
    if success:
        print("\n✅ 初始化成功！")
        print("\n后续步骤：")
        print("1. 启动后端服务: python -m uvicorn app.main:app --reload")
        print("2. 访问API文档: http://localhost:8000/docs")
        print("3. 使用 admin/admin123 登录")
        print("4. 配置AI模型的API密钥")
        print("5. 开始使用系统功能")
    else:
        print("\n❌ 初始化失败！请检查错误信息并重试。")
        sys.exit(1)