"""测试配置和共用fixtures

提供测试环境配置、数据库设置、认证令牌等共用组件
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.models.ai_model import AIModel
from app.models.storage_credential import StorageCredential
from app.models.webhook import Webhook
from app.models.analysis_task import AnalysisTask
from app.models.system_config import SystemConfig


# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """测试数据库会话"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# 覆盖数据库依赖
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # 清理所有表
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """创建测试客户端"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client(db_session):
    """创建异步测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user(db_session) -> User:
    """创建测试用户"""
    from app.core.security import get_password_hash
    
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session) -> User:
    """创建管理员用户"""
    from app.core.security import get_password_hash
    
    user = User(
        email="admin@example.com", 
        username="admin",
        full_name="Admin User",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_superuser=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_token(test_user: User) -> str:
    """创建用户访问令牌"""
    return create_access_token(subject=test_user.id)


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """创建管理员访问令牌"""
    return create_access_token(subject=admin_user.id)


@pytest.fixture
def auth_headers(user_token: str) -> dict:
    """用户认证headers"""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """管理员认证headers"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def test_ai_model(db_session, test_user: User) -> AIModel:
    """创建测试AI模型"""
    model = AIModel(
        name="Test GPT Model",
        provider="openai",
        model_name="gpt-3.5-turbo",
        api_key="test-api-key",
        api_base="https://api.openai.com/v1",
        config={
            "temperature": 0.7,
            "max_tokens": 1000
        },
        created_by=test_user.username,
        is_active=True
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    return model


@pytest.fixture
def test_storage_credential(db_session, test_user: User) -> StorageCredential:
    """创建测试存储凭证"""
    from app.core.security import encrypt_sensitive_data
    
    credential = StorageCredential(
        name="Test Storage",
        protocol="smb",
        host="test.example.com",
        port=445,
        username="testuser",
        password=encrypt_sensitive_data("testpass"),
        share_path="/test-share",
        created_by=test_user.username,
        is_active=True
    )
    db_session.add(credential)
    db_session.commit()
    db_session.refresh(credential)
    return credential


@pytest.fixture
def test_webhook(db_session, test_user: User) -> Webhook:
    """创建测试Webhook"""
    from app.core.security import generate_webhook_secret
    
    webhook = Webhook(
        name="Test Webhook",
        description="Test webhook for integration",
        url_path="test-webhook",
        secret_key=generate_webhook_secret(),
        is_active=True,
        created_by=test_user.username
    )
    db_session.add(webhook)
    db_session.commit()
    db_session.refresh(webhook)
    return webhook


@pytest.fixture
def test_analysis_task(
    db_session, 
    test_user: User,
    test_webhook: Webhook,
    test_ai_model: AIModel,
    test_storage_credential: StorageCredential
) -> AnalysisTask:
    """创建测试分析任务"""
    task = AnalysisTask(
        name="Test Analysis Task",
        description="Test task for AI analysis",
        webhook_id=test_webhook.id,
        ai_model_id=test_ai_model.id,
        storage_credential_id=test_storage_credential.id,
        data_parsing_config={
            "project_key": "$.repository.name",
            "commit_id": "$.head_commit.id"
        },
        file_path_template="/{{project_key}}/{{commit_id}}/",
        system_prompt="You are a code reviewer.",
        user_prompt_template="Please review: {{file_content}}",
        analysis_config={
            "max_tokens": 1000,
            "temperature": 0.3
        },
        status="active",
        created_by=test_user.username
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def test_system_config(db_session, test_user: User) -> SystemConfig:
    """创建测试系统配置"""
    from app.models.system_config import ConfigType, ConfigCategory
    
    config = SystemConfig(
        key="test.config.value",
        name="Test Config",
        display_name="Test Configuration",
        description="Test configuration item",
        value="test_value",
        default_value="default_value",
        config_type=ConfigType.STRING,
        category=ConfigCategory.SYSTEM,
        is_required=False,
        is_sensitive=False,
        is_active=True,
        created_by=test_user.username
    )
    db_session.add(config)
    db_session.commit()
    db_session.refresh(config)
    return config


# 测试数据生成器
class TestDataGenerator:
    """测试数据生成器"""
    
    @staticmethod
    def user_data(**kwargs):
        """生成用户测试数据"""
        default_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "newpass123",
            "is_active": True,
            "is_superuser": False
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def ai_model_data(**kwargs):
        """生成AI模型测试数据"""
        default_data = {
            "name": "Test AI Model",
            "provider": "openai",
            "model_name": "gpt-3.5-turbo",
            "api_key": "test-key",
            "api_base": "https://api.openai.com/v1",
            "config": {
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "is_active": True
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def storage_credential_data(**kwargs):
        """生成存储凭证测试数据"""
        default_data = {
            "name": "Test Storage",
            "protocol": "smb",
            "host": "test.example.com",
            "port": 445,
            "username": "testuser",
            "password": "testpass",
            "share_path": "/test",
            "is_active": True
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def webhook_data(**kwargs):
        """生成Webhook测试数据"""
        default_data = {
            "name": "Test Webhook",
            "description": "Test webhook",
            "is_active": True,
            "allowed_ips": ["127.0.0.1"],
            "rate_limit": 100
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def analysis_task_data(webhook_id, ai_model_id, storage_credential_id=None, **kwargs):
        """生成分析任务测试数据"""
        default_data = {
            "name": "Test Task",
            "description": "Test analysis task",
            "webhook_id": webhook_id,
            "ai_model_id": ai_model_id,
            "storage_credential_id": storage_credential_id,
            "data_parsing_config": {
                "key1": "$.value1",
                "key2": "$.value2"
            },
            "system_prompt": "Test system prompt",
            "user_prompt_template": "Test: {{key1}}",
            "analysis_config": {
                "max_tokens": 1000,
                "temperature": 0.3
            },
            "status": "active"
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def system_config_data(**kwargs):
        """生成系统配置测试数据"""
        default_data = {
            "key": "test.config",
            "name": "Test Config",
            "display_name": "Test Configuration",
            "description": "Test configuration",
            "value": "test_value",
            "config_type": "string",
            "category": "system",
            "required": False,
            "sensitive": False,
            "readonly": False
        }
        default_data.update(kwargs)
        return default_data


# 常用断言helper
class AssertHelpers:
    """测试断言帮助器"""
    
    @staticmethod
    def assert_response_success(response, status_code=200):
        """断言响应成功"""
        assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}: {response.text}"
        return response.json()
    
    @staticmethod
    def assert_response_error(response, status_code=400):
        """断言响应错误"""
        assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}: {response.text}"
        return response.json()
    
    @staticmethod
    def assert_model_fields(data, model_dict, fields):
        """断言模型字段"""
        for field in fields:
            assert data[field] == model_dict[field], f"Field {field} mismatch: {data[field]} != {model_dict[field]}"
    
    @staticmethod
    def assert_pagination_response(data, expected_items=None):
        """断言分页响应格式"""
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        
        if expected_items is not None:
            assert len(data["items"]) == expected_items


@pytest.fixture
def test_data():
    """测试数据生成器fixture"""
    return TestDataGenerator()


@pytest.fixture
def assert_helpers():
    """测试断言帮助器fixture"""
    return AssertHelpers()


# Mock数据
@pytest.fixture
def mock_webhook_payload():
    """Mock webhook payload"""
    return {
        "repository": {
            "name": "test-repo",
            "full_name": "user/test-repo"
        },
        "head_commit": {
            "id": "abc123",
            "message": "Test commit",
            "author": {
                "name": "Test User",
                "email": "test@example.com"
            },
            "modified": ["file1.py", "file2.py"]
        },
        "pusher": {
            "name": "testuser",
            "email": "test@example.com"
        }
    }


@pytest.fixture  
def mock_ai_response():
    """Mock AI API响应"""
    return {
        "content": "This is a mock AI analysis response.",
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        },
        "cost": 0.001,
        "model": "gpt-3.5-turbo"
    }


@pytest.fixture
def mock_file_content():
    """Mock文件内容"""
    return {
        "content": "def hello_world():\n    print('Hello, World!')\n",
        "file_info": {
            "name": "hello.py",
            "size": 45,
            "modified_time": "2024-01-01T12:00:00Z",
            "type": "text/python"
        }
    }


# 测试环境清理
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """自动清理测试文件"""
    import os
    import tempfile
    import shutil
    
    # 测试前的准备
    temp_dirs = []
    
    yield temp_dirs
    
    # 测试后的清理
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


# 测试性能监控
@pytest.fixture
def performance_monitor():
    """性能监控fixture"""
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.measurements = {}
        
        def start(self, name="default"):
            self.start_time = time.time()
            self.measurements[name] = {"start": self.start_time}
        
        def stop(self, name="default", max_duration=None):
            end_time = time.time()
            if name in self.measurements:
                duration = end_time - self.measurements[name]["start"]
                self.measurements[name]["duration"] = duration
                
                if max_duration and duration > max_duration:
                    pytest.fail(f"Performance test failed: {name} took {duration:.2f}s, max allowed {max_duration}s")
                
                return duration
            return None
        
        def get_duration(self, name="default"):
            if name in self.measurements and "duration" in self.measurements[name]:
                return self.measurements[name]["duration"]
            return None
    
    return PerformanceMonitor()