# 核心功能测试指南

## 🎯 测试目标

专注于验证**核心业务功能完整性**：
- ✅ Webhook接收 → 数据解析 → 文件获取 → AI分析 → 结果回写的完整流程
- ✅ 使用真实的线上AI API进行测试
- ✅ 确保主要功能路径正常工作

## 📋 测试前准备

### 1. 环境准备

```bash
# 确保开发环境正常运行
docker-compose -f docker-compose.dev.yml up -d

# 或者直接启动后端服务
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. API密钥配置

**重要：需要配置真实的AI API密钥才能完成完整测试**

编辑测试脚本中的API密钥：

```python
# 在 run_core_tests.py 中找到这些行并替换为真实密钥：

ai_models_config = [
    {
        "name": "Core Test OpenAI",
        "provider": "openai",
        "model_name": "gpt-3.5-turbo", 
        "api_key": "sk-xxxxxxxxxxxxxxxxxxxxx",  # 替换为真实OpenAI密钥
        "api_base": "https://api.openai.com/v1"
    },
    {
        "name": "Core Test Gemini",
        "provider": "gemini",
        "model_name": "gemini-pro",
        "api_key": "AIxxxxxxxxxxxxxxxxxxxxxx",  # 替换为真实Gemini密钥
        "api_base": "https://generativelanguage.googleapis.com/v1beta"
    }
]
```

### 3. 测试文件准备

测试脚本会自动创建测试文件到 `/tmp/core-test-files/` 目录，无需手动准备。

## 🚀 运行测试

### 方式1：完整核心功能测试（推荐）

```bash
cd backend
python run_core_tests.py
```

这个脚本会：
1. ✅ 初始化测试数据库
2. ✅ 创建测试用户
3. ✅ 配置AI模型（使用真实API）
4. ✅ 设置存储凭证和测试文件
5. ✅ 创建Webhook和分析任务
6. ✅ 触发完整的业务流程测试

### 方式2：API端点快速测试

```bash
cd backend  
python test_api_endpoints.py
```

这个脚本会测试所有API端点的基本功能。

### 方式3：pytest单元测试

```bash
cd backend
pytest tests/test_core_functionality.py -v -s
```

## 📊 测试重点检查项

### 🔴 P0 - 必须100%通过的核心功能

1. **完整业务流程**
   - [ ] Webhook成功接收事件
   - [ ] 数据解析正确提取字段
   - [ ] 文件成功获取和读取
   - [ ] AI模型成功调用并返回分析结果
   - [ ] 任务执行状态正确更新

2. **AI模型调用**
   - [ ] OpenAI API连接和调用
   - [ ] Gemini API连接和调用（如有密钥）
   - [ ] API响应正确解析
   - [ ] Token使用统计准确

3. **基础认证**
   - [ ] 用户登录获取token
   - [ ] 受保护资源访问验证

### 🟡 P1 - 重要但允许部分问题

1. **错误处理**
   - [ ] API调用失败的处理
   - [ ] 文件不存在的处理
   - [ ] 数据解析失败的处理

2. **数据持久化**
   - [ ] 任务执行记录保存
   - [ ] 统计信息更新
   - [ ] 数据关联正确性

## 🔍 问题排查

### 常见问题1：API密钥无效

**现象**：AI模型调用失败
```
❌ AI模型调用失败: API错误: Invalid API key
```

**解决**：
1. 检查API密钥是否正确配置
2. 验证API密钥是否有足够权限
3. 确认API服务商账户是否有余额

### 常见问题2：数据库连接失败

**现象**：测试启动时报数据库错误
```
❌ 数据库连接失败
```

**解决**：
1. 确认PostgreSQL服务正在运行
2. 检查数据库连接配置
3. 运行数据库迁移：`alembic upgrade head`

### 常见问题3：文件路径问题

**现象**：文件获取失败
```
❌ 文件获取失败: 文件不存在
```

**解决**：
1. 检查测试文件是否正确创建
2. 确认文件路径权限
3. 验证路径模板配置

### 常见问题4：Webhook签名验证失败

**现象**：Webhook触发被拒绝
```
❌ Webhook触发失败: 401 Unauthorized  
```

**解决**：
1. 检查签名计算是否正确
2. 确认密钥是否匹配
3. 验证请求格式

## 📈 测试结果分析

### 成功标准

**完全成功**：
```
🎉 核心功能测试全部通过！
✅ 创建用户: core_test_user
✅ 配置AI模型数量: 2
✅ 配置存储凭证: Core Test Storage  
✅ 创建Webhook: Core Test Webhook
✅ 创建分析任务数量: 2
```

**部分成功**：
- 核心流程通过但有次要功能问题
- 可以先修复核心问题，次要问题后续处理

**需要修复**：
- 核心业务流程中断
- AI模型调用完全失败
- 数据无法正确保存

## 🔧 测试结果使用

### 检查任务执行结果

测试完成后，可以通过以下方式查看详细结果：

1. **数据库检查**：
```sql
-- 查看任务执行记录
SELECT * FROM task_executions ORDER BY started_at DESC LIMIT 5;

-- 查看分析任务统计
SELECT name, total_executions, successful_executions, 
       total_tokens_used, total_cost 
FROM analysis_tasks;
```

2. **API查看**：
访问 http://localhost:8000/docs 查看API文档和测试接口

3. **日志检查**：
查看应用日志了解详细执行过程

## ⚡ 快速测试命令

```bash
# 快速验证基础功能
python -c "
import asyncio
from test_api_endpoints import APITester
tester = APITester()
asyncio.run(tester.test_health_check())
"

# 快速验证数据库连接
python -c "
from app.core.database import SessionLocal
db = SessionLocal()
print('✅ 数据库连接成功' if db.execute('SELECT 1').scalar() else '❌ 数据库连接失败')
db.close()
"

# 快速验证导入
python -c "
try:
    from app.main import app
    from app.services.ai_service import ai_service
    print('✅ 关键模块导入成功')
except ImportError as e:
    print(f'❌ 模块导入失败: {e}')
"
```

## 📞 如需帮助

如果测试过程中遇到问题：

1. **查看错误详情**：测试脚本会输出详细错误信息
2. **检查日志**：应用日志包含更多调试信息
3. **分步调试**：可以单独运行每个测试模块
4. **数据检查**：直接查看数据库中的记录状态

记住：**核心功能优先，边缘问题可以后续处理**！