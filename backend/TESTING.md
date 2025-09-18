# 测试指南

本文档描述了AI综合分析管理平台的测试策略、测试套件和运行方法。

## 测试架构

### 测试分层
```
┌─────────────────────────────┐
│      集成测试 (Integration)    │  ← 端到端业务流程测试
├─────────────────────────────┤
│      API测试 (API Tests)      │  ← HTTP接口功能测试
├─────────────────────────────┤
│     单元测试 (Unit Tests)     │  ← 函数和类的独立测试
└─────────────────────────────┘
```

### 测试类型

1. **单元测试** (`@pytest.mark.unit`)
   - 测试独立的函数和类
   - 快速执行，高代码覆盖率
   - 使用mock隔离外部依赖

2. **集成测试** (`@pytest.mark.integration`)
   - 测试多个模块间的交互
   - 包含数据库操作和外部服务调用
   - 验证完整业务流程

3. **性能测试** (`@pytest.mark.performance`)
   - 测试响应时间和并发处理能力
   - 监控内存使用和资源消耗
   - 验证系统性能指标

4. **安全测试** (`@pytest.mark.security`)
   - 测试认证和授权机制
   - 验证数据加密和敏感信息保护
   - 检查安全漏洞和攻击防护

## 测试文件结构

```
backend/
├── tests/
│   ├── conftest.py              # 测试配置和通用fixtures
│   ├── test_auth_users.py       # 认证和用户管理测试
│   ├── test_ai_models.py        # AI模型管理测试
│   ├── test_system_configs.py   # 系统配置管理测试
│   ├── test_integration.py      # 综合集成测试
│   └── __init__.py
├── pytest.ini                  # pytest配置文件
├── run_tests.py                 # 测试运行脚本
└── TESTING.md                   # 本文档
```

## 快速开始

### 1. 安装测试依赖

```bash
pip install pytest pytest-asyncio pytest-cov pytest-html pytest-xdist pytest-mock httpx
```

或者使用requirements文件：
```bash
pip install -r requirements.txt
```

### 2. 运行测试

#### 使用测试脚本（推荐）
```bash
# 交互式菜单
python run_tests.py

# 快速测试（跳过慢速测试）
python run_tests.py --smoke

# 完整测试套件（包含覆盖率）
python run_tests.py --all --coverage

# 特定模块测试
python run_tests.py --auth --ai-models
```

#### 直接使用pytest
```bash
# 基本测试
pytest

# 详细输出
pytest -v

# 包含覆盖率
pytest --cov=app --cov-report=html

# 特定标记
pytest -m "unit and not slow"

# 特定文件
pytest tests/test_auth_users.py

# 特定测试函数
pytest tests/test_auth_users.py::TestAuth::test_login_success
```

## 测试配置

### pytest.ini 配置说明

```ini
[tool:pytest]
# 测试发现路径
testpaths = tests

# 标记定义
markers =
    unit: 单元测试
    integration: 集成测试
    performance: 性能测试
    security: 安全测试

# 基本选项
addopts = -v --tb=short --strict-markers
```

### 环境变量配置

测试运行时可以通过环境变量配置：

```bash
# 测试数据库
export DATABASE_URL="sqlite:///test.db"

# 测试Redis
export REDIS_URL="redis://localhost:6379/15"

# 禁用外部服务调用
export TESTING=true
```

## 测试工具和Fixtures

### 通用Fixtures (`conftest.py`)

```python
# 数据库会话
@pytest.fixture
def db_session():
    """提供测试数据库会话"""
    
# 测试客户端
@pytest.fixture
def client():
    """提供FastAPI测试客户端"""

# 认证令牌
@pytest.fixture
def auth_headers():
    """提供认证头"""

# 测试数据生成
@pytest.fixture
def test_data():
    """提供测试数据生成器"""
```

### 模拟数据

```python
# Mock AI响应
@pytest.fixture
def mock_ai_response():
    return {
        "content": "Mock AI response",
        "usage": {"total_tokens": 100},
        "cost": 0.001
    }

# Mock文件内容
@pytest.fixture
def mock_file_content():
    return {
        "content": "def hello(): print('world')",
        "file_info": {"size": 100}
    }
```

## 测试最佳实践

### 1. 测试命名约定

```python
class TestUserAuth:
    def test_login_success(self):           # 测试成功场景
        pass
    
    def test_login_invalid_credentials(self): # 测试失败场景
        pass
    
    def test_login_nonexistent_user(self):   # 测试边界情况
        pass
```

### 2. 使用参数化测试

```python
@pytest.mark.parametrize("provider,model", [
    ("openai", "gpt-3.5-turbo"),
    ("anthropic", "claude-3-sonnet"),
    ("google", "gemini-pro")
])
def test_ai_providers(provider, model):
    # 测试多个AI服务商
    pass
```

### 3. Mock外部依赖

```python
@patch('app.services.ai_service.generate_completion')
def test_ai_analysis(mock_generate):
    mock_generate.return_value = {"content": "test"}
    # 测试逻辑
```

### 4. 异步测试

```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

### 5. 性能测试

```python
@pytest.mark.performance
def test_response_time(performance_monitor):
    performance_monitor.start("api_call")
    # 执行操作
    duration = performance_monitor.stop("api_call", max_duration=1.0)
```

## 测试覆盖率

### 生成覆盖率报告

```bash
# HTML报告
pytest --cov=app --cov-report=html

# 终端报告
pytest --cov=app --cov-report=term-missing

# 设置最低覆盖率
pytest --cov=app --cov-fail-under=80
```

### 覆盖率目标

- **单元测试**: >= 90%
- **集成测试**: >= 70%
- **总体覆盖率**: >= 80%

### 排除文件

在`.coveragerc`中配置：
```ini
[run]
omit = 
    */migrations/*
    */venv/*
    */tests/*
    */conftest.py
```

## 持续集成

### GitHub Actions配置

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          
      - name: Run tests
        run: |
          python run_tests.py --all --coverage
          
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## 测试数据管理

### 数据库清理

```python
@pytest.fixture(autouse=True)
def cleanup_database(db_session):
    """自动清理测试数据"""
    yield
    db_session.rollback()
```

### 临时文件处理

```python
@pytest.fixture
def temp_file():
    """创建临时文件"""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        yield f.name
    os.unlink(f.name)
```

## 调试测试

### 1. 使用pdb调试

```python
def test_debug_example():
    import pdb; pdb.set_trace()
    # 调试代码
```

### 2. 增加日志输出

```python
def test_with_logging(caplog):
    with caplog.at_level(logging.INFO):
        # 测试代码
    assert "expected message" in caplog.text
```

### 3. 保留测试数据

```bash
# 运行失败后保留数据库
pytest --lf --pdb
```

## 常见问题

### 1. 测试数据库连接问题

```python
# 确保使用测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
```

### 2. 异步测试错误

```python
# 确保正确配置异步模式
# pytest.ini
asyncio_mode = auto
```

### 3. Mock不生效

```python
# 确保Mock路径正确
@patch('app.services.actual_module.function_name')  # 正确
# 而不是
@patch('some_package.function_name')  # 错误
```

### 4. 测试隔离问题

```python
# 使用事务回滚确保测试隔离
@pytest.fixture(autouse=True)
def isolate_tests(db_session):
    db_session.begin()
    yield
    db_session.rollback()
```

## 性能优化

### 1. 并行运行

```bash
# 使用pytest-xdist并行运行
pip install pytest-xdist
pytest -n auto
```

### 2. 测试分组

```bash
# 先运行快速测试
pytest -m "not slow"

# 再运行慢速测试
pytest -m "slow"
```

### 3. 缓存结果

```bash
# 启用测试结果缓存
pytest --cache-clear  # 清理缓存
pytest --lf          # 只运行上次失败的测试
```

## 测试报告

### HTML报告

```bash
pip install pytest-html
pytest --html=reports/report.html --self-contained-html
```

### JUnit XML报告

```bash
pytest --junitxml=reports/junit.xml
```

### 自定义报告

```python
# conftest.py
def pytest_configure(config):
    """配置自定义报告"""
    pass

def pytest_html_report_title(report):
    report.title = "AI平台测试报告"
```

## 总结

这个测试套件提供了：

1. **完整的测试覆盖** - 从单元测试到集成测试
2. **便捷的运行方式** - 多种运行脚本和配置
3. **详细的报告** - 覆盖率和HTML报告
4. **性能监控** - 响应时间和资源使用
5. **安全验证** - 认证和数据保护测试
6. **持续集成支持** - CI/CD配置示例

通过这个测试套件，可以确保AI分析平台的质量和稳定性，支持快速开发和部署。