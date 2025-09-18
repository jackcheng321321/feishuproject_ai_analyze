#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版最简HTTP服务器 - 包含前端所需的API模拟接口
"""

import http.server
import socketserver
import json
import urllib.parse
from datetime import datetime
import os
from typing import Dict, List, Any

# 内存数据存储
class DataStore:
    def __init__(self):
        self.data = {
            "ai_models": [
                {
                    "id": 1,
                    "name": "GPT-4",
                    "provider": "OpenAI",
                    "model_type": "chat",
                    "api_endpoint": "https://api.openai.com/v1/chat/completions",
                    "status": "active",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                {
                    "id": 2,
                    "name": "Claude-3",
                    "provider": "Anthropic",
                    "model_type": "chat",
                    "api_endpoint": "https://api.anthropic.com/v1/messages",
                    "status": "active",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            ],
            "storage_credentials": [
                {
                    "id": 1,
                    "name": "测试SMB",
                    "storage_type": "smb",
                    "host": "192.168.1.100",
                    "status": "active",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ],
            "webhooks": [
                {
                    "id": 1,
                    "name": "飞书项目Webhook",
                    "url": "https://example.com/webhook/123",
                    "event_types": ["file_upload", "comment_added"],
                    "status": "active",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ],
            "tasks": [
                {
                    "id": 1,
                    "name": "AI分析任务-文档1.pdf",
                    "status": "completed",
                    "ai_model": "GPT-4",
                    "created_at": "2024-01-01T00:00:00Z",
                    "completed_at": "2024-01-01T00:01:00Z"
                }
            ],
            "users": [],
            "executions": [],
            "monitoring": []
        }
        self.next_ids = {
            "ai_models": 3,
            "storage_credentials": 2,
            "webhooks": 2,
            "tasks": 2,
            "users": 1,
            "executions": 1,
            "monitoring": 1
        }
    
    def get_table_name(self, path):
        """从路径获取表名"""
        if "ai-models" in path or path.startswith("/ai-models"):
            return "ai_models"
        elif "storage-credentials" in path or path.startswith("/storage-credentials"):
            return "storage_credentials"
        elif "webhooks" in path or path.startswith("/webhooks"):
            return "webhooks"
        elif "tasks" in path or path.startswith("/tasks"):
            return "tasks"
        elif "users" in path or path.startswith("/users"):
            return "users"
        elif "executions" in path or path.startswith("/executions"):
            return "executions"
        elif "monitoring" in path or path.startswith("/monitoring"):
            return "monitoring"
        else:
            return "ai_models"  # 默认
    
    def get_list(self, table_name, page=1, size=20):
        """获取列表数据"""
        items = self.data.get(table_name, [])
        start = (page - 1) * size
        end = start + size
        return {
            "items": items[start:end],  # 改为 items 匹配前端期望
            "total": len(items),
            "page": page,
            "page_size": size,
            "total_pages": (len(items) + size - 1) // size if items else 0
        }
    
    def create_item(self, table_name, item_data):
        """创建新项目"""
        new_id = self.next_ids[table_name]
        self.next_ids[table_name] += 1
        
        new_item = {
            "id": new_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            **item_data
        }
        
        self.data[table_name].append(new_item)
        return new_item
    
    def update_item(self, table_name, item_id, update_data):
        """更新项目"""
        items = self.data.get(table_name, [])
        for item in items:
            if item["id"] == item_id:
                # 更新数据
                for key, value in update_data.items():
                    item[key] = value
                item["updated_at"] = datetime.now().isoformat()
                return item
        return None
    
    def delete_item(self, table_name, item_id):
        """删除项目"""
        items = self.data.get(table_name, [])
        for i, item in enumerate(items):
            if item["id"] == item_id:
                deleted_item = items.pop(i)
                return deleted_item
        return None
    
    def get_item_by_id(self, table_name, item_id):
        """根据ID获取项目"""
        items = self.data.get(table_name, [])
        for item in items:
            if item["id"] == item_id:
                return item
        return None

# 全局数据存储实例
data_store = DataStore()

class APIHandler(http.server.BaseHTTPRequestHandler):
    """API处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        # 解析URL和查询参数
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        if path == '/':
            self.send_json_response({
                "message": "AI综合分析管理平台 - 增强版",
                "status": "running",
                "version": "0.2.0",
                "timestamp": datetime.now().isoformat()
            })
        elif path == '/health':
            self.send_json_response({
                "status": "healthy",
                "message": "服务运行正常",
                "timestamp": datetime.now().isoformat()
            })
        elif path == '/api/test':
            self.send_json_response({
                "message": "API测试成功",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "environment": os.getenv("ENVIRONMENT", "development"),
                    "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
                }
            })
        # 直接处理前端API请求（无论是否有/api/v1/前缀）
        elif self.is_data_api_path(path):
            # 检查是否是单个项目查询 (如 /ai-models/123)
            path_parts = path.strip('/').split('/')
            if len(path_parts) >= 2 and path_parts[-1].isdigit():
                # 单个项目查询
                item_id = int(path_parts[-1])
                table_name = data_store.get_table_name(path)
                item = data_store.get_item_by_id(table_name, item_id)
                
                if item:
                    self.send_json_response(item)
                else:
                    self.send_json_response({
                        "error": "Not Found",
                        "message": f"项目 {item_id} 不存在"
                    }, status=404)
            else:
                # 列表查询
                page = int(query_params.get('page', ['1'])[0])
                size = int(query_params.get('size', ['20'])[0])
                
                table_name = data_store.get_table_name(path)
                result = data_store.get_list(table_name, page, size)
                self.send_json_response(result)
        
        elif path == '/docs':
            self.send_html_response(self.get_docs_html())
        elif path.startswith('/api/') or self.is_api_path(path):
            # 对所有API请求返回空数据，避免404错误
            page = int(query_params.get('page', ['1'])[0])
            size = int(query_params.get('size', ['20'])[0])
            
            self.send_json_response({
                "items": [],  # 改为 items 匹配前端期望
                "total": 0,
                "page": page,
                "page_size": size,
                "total_pages": 0,
                "message": f"接口 {path} 暂无数据"
            })
        else:
            self.send_json_response({
                "error": "Not Found",
                "message": f"路径 {path} 不存在",
                "available_paths": [
                    "/",
                    "/health", 
                    "/api/test",
                    "/api/v1/ai-models",
                    "/api/v1/storage-credentials", 
                    "/api/v1/webhooks",
                    "/api/v1/tasks",
                    "/api/v1/analysis",
                    "/docs"
                ]
            }, status=404)
    
    def do_POST(self):
        """处理POST请求"""
        content_length = int(self.headers.get('Content-Length', 0))
        
        if content_length > 0:
            try:
                post_data = self.rfile.read(content_length)
                # 尝试多种编码方式解析
                try:
                    data = json.loads(post_data.decode('utf-8'))
                except UnicodeDecodeError:
                    try:
                        data = json.loads(post_data.decode('gbk'))
                    except UnicodeDecodeError:
                        data = json.loads(post_data.decode('utf-8', errors='ignore'))
            except json.JSONDecodeError:
                data = {"error": "JSON解析失败", "raw_length": content_length}
            except Exception as e:
                data = {"error": f"数据读取失败: {str(e)}", "raw_length": content_length}
        else:
            data = {}
        
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        if path == '/api/echo':
            self.send_json_response({
                "message": "Echo API",
                "received_data": data,
                "timestamp": datetime.now().isoformat()
            })
        elif self.is_data_api_path(path):
            # 检查是否是特殊操作路径
            if path.endswith('/test-connection'):
                # 测试连接功能
                table_name = data_store.get_table_name(path)
                if table_name == 'ai_models':
                    self.send_json_response({
                        "success": True,
                        "message": f"AI模型连接测试成功: {data.get('model_type', 'Unknown')} - {data.get('api_endpoint', 'N/A')}"
                    })
                elif table_name == 'storage_credentials':
                    self.send_json_response({
                        "success": True,
                        "message": f"存储连接测试成功: {data.get('protocol_type', 'Unknown')} - {data.get('server_address', 'N/A')}"
                    })
                elif table_name == 'webhooks':
                    self.send_json_response({
                        "success": True,
                        "message": f"Webhook连接测试成功: {data.get('url', 'N/A')}"
                    })
                else:
                    self.send_json_response({
                        "success": False,
                        "message": "不支持的连接测试类型"
                    })
            else:
                # 真正保存数据到数据存储
                table_name = data_store.get_table_name(path)
                try:
                    new_item = data_store.create_item(table_name, data)
                    self.send_json_response({
                        "code": 200,
                        "message": "创建成功",
                        "data": new_item
                    }, status=201)
                except Exception as e:
                    self.send_json_response({
                        "message": f"创建失败: {str(e)}",
                        "success": False
                    }, status=400)
        elif path.startswith('/api/'):
            # 其他API请求返回通用成功响应
            self.send_json_response({
                "message": f"操作成功",
                "path": path,
                "method": "POST",
                "received_data": data,
                "result": {
                    "id": 123,
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                }
            }, status=200)
        else:
            self.send_json_response({
                "error": "Not Found",
                "message": f"POST路径 {path} 不存在"
            }, status=404)
    
    def do_PUT(self):
        """处理PUT请求"""
        content_length = int(self.headers.get('Content-Length', 0))
        
        if content_length > 0:
            try:
                post_data = self.rfile.read(content_length)
                try:
                    data = json.loads(post_data.decode('utf-8'))
                except UnicodeDecodeError:
                    try:
                        data = json.loads(post_data.decode('gbk'))
                    except UnicodeDecodeError:
                        data = json.loads(post_data.decode('utf-8', errors='ignore'))
            except json.JSONDecodeError:
                data = {"error": "JSON解析失败", "raw_length": content_length}
            except Exception as e:
                data = {"error": f"数据读取失败: {str(e)}", "raw_length": content_length}
        else:
            data = {}
        
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        if self.is_data_api_path(path):
            # 检查是否是单个项目更新 (如 /ai-models/123)
            path_parts = path.strip('/').split('/')
            if len(path_parts) >= 2 and path_parts[-1].isdigit():
                item_id = int(path_parts[-1])
                table_name = data_store.get_table_name(path)
                
                try:
                    updated_item = data_store.update_item(table_name, item_id, data)
                    if updated_item:
                        self.send_json_response(updated_item)
                    else:
                        self.send_json_response({
                            "error": "Not Found",
                            "message": f"项目 {item_id} 不存在"
                        }, status=404)
                except Exception as e:
                    self.send_json_response({
                        "error": "Update Failed",
                        "message": str(e)
                    }, status=400)
            else:
                self.send_json_response({
                    "error": "Bad Request",
                    "message": "PUT请求需要指定项目ID"
                }, status=400)
        else:
            self.send_json_response({
                "error": "Not Found",
                "message": f"PUT路径 {path} 不存在"
            }, status=404)
    
    def do_DELETE(self):
        """处理DELETE请求"""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        if self.is_data_api_path(path):
            # 检查是否是单个项目删除 (如 /ai-models/123)
            path_parts = path.strip('/').split('/')
            if len(path_parts) >= 2 and path_parts[-1].isdigit():
                item_id = int(path_parts[-1])
                table_name = data_store.get_table_name(path)
                
                try:
                    deleted_item = data_store.delete_item(table_name, item_id)
                    if deleted_item:
                        self.send_json_response({
                            "message": "删除成功",
                            "deleted_item": deleted_item,
                            "success": True
                        })
                    else:
                        self.send_json_response({
                            "error": "Not Found",
                            "message": f"项目 {item_id} 不存在"
                        }, status=404)
                except Exception as e:
                    self.send_json_response({
                        "error": "Delete Failed",
                        "message": str(e)
                    }, status=400)
            else:
                self.send_json_response({
                    "error": "Bad Request",
                    "message": "DELETE请求需要指定项目ID"
                }, status=400)
        else:
            self.send_json_response({
                "error": "Not Found",
                "message": f"DELETE路径 {path} 不存在"
            }, status=404)
    
    def send_json_response(self, data, status=200):
        """发送JSON响应"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        
        response = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def send_html_response(self, html, status=200):
        """发送HTML响应"""
        self.send_response(status)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def do_OPTIONS(self):
        """处理OPTIONS请求（CORS预检）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def is_data_api_path(self, path):
        """判断是否是需要数据存储的API路径"""
        data_patterns = [
            'ai-models', 'storage-credentials', 'webhooks', 'tasks',
            'users', 'executions', 'monitoring'
        ]
        
        clean_path = path.lstrip('/')
        
        # 直接匹配路径（如 /ai-models）
        for pattern in data_patterns:
            if clean_path.startswith(pattern) or f"/{pattern}" in path or f"/api/v1/{pattern}" in path:
                return True
        return False
    
    def is_specific_api_path(self, path):
        """判断是否是特定的API路径（需要数据存储的）- 兼容方法"""
        return self.is_data_api_path(path)
    
    def is_api_path(self, path):
        """判断是否是API路径"""
        api_patterns = [
            'ai-models', 'storage-credentials', 'webhooks', 'tasks', 
            'executions', 'monitoring', 'analysis', 'dashboard',
            'users', 'auth', 'config', 'settings', 'files',
            'projects', 'reports', 'statistics', 'logs'
        ]
        
        # 移除开头的斜杠
        clean_path = path.lstrip('/')
        
        # 检查路径是否以这些API模式开头
        for pattern in api_patterns:
            if clean_path.startswith(pattern):
                return True
        
        # 检查是否包含典型的API特征
        if any(keyword in clean_path.lower() for keyword in ['api', 'v1', 'v2', 'rest']):
            return True
            
        return False
    
    def get_docs_html(self):
        """生成API文档HTML"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI综合分析管理平台 - API文档</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; }
        .endpoint { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .method { display: inline-block; padding: 5px 10px; border-radius: 3px; color: white; font-weight: bold; }
        .get { background: #61affe; }
        .post { background: #49cc90; }
        code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>AI综合分析管理平台 - API文档</h1>
        <p>增强版本 - 包含完整的API模拟接口</p>
        <p><strong>状态:</strong> 运行中 | <strong>版本:</strong> 0.2.0</p>
    </div>
    
    <h2>基础接口</h2>
    <div class="endpoint">
        <h3><span class="method get">GET</span> /</h3>
        <p>根路径，返回服务基本信息</p>
    </div>
    
    <div class="endpoint">
        <h3><span class="method get">GET</span> /health</h3>
        <p>健康检查接口</p>
    </div>
    
    <div class="endpoint">
        <h3><span class="method get">GET</span> /api/test</h3>
        <p>测试API接口</p>
    </div>
    
    <h2>业务接口</h2>
    <div class="endpoint">
        <h3><span class="method get">GET</span> /api/v1/ai-models</h3>
        <p>获取AI模型列表，支持分页参数: ?page=1&size=20</p>
    </div>
    
    <div class="endpoint">
        <h3><span class="method get">GET</span> /api/v1/storage-credentials</h3>
        <p>获取存储凭证列表，支持分页参数</p>
    </div>
    
    <div class="endpoint">
        <h3><span class="method get">GET</span> /api/v1/webhooks</h3>
        <p>获取Webhook列表，支持分页参数</p>
    </div>
    
    <div class="endpoint">
        <h3><span class="method get">GET</span> /api/v1/tasks</h3>
        <p>获取任务列表，支持分页参数</p>
    </div>
    
    <div class="endpoint">
        <h3><span class="method get">GET</span> /api/v1/analysis</h3>
        <p>获取分析统计数据</p>
    </div>
    
    <div class="endpoint">
        <h3><span class="method post">POST</span> /api/echo</h3>
        <p>回显接口，返回发送的数据</p>
    </div>
    
    <div class="endpoint">
        <h3><span class="method post">POST</span> /api/v1/*</h3>
        <p>所有业务模块的创建接口（模拟）</p>
    </div>
    
    <h2>测试示例</h2>
    <p>使用curl测试：</p>
    <code>curl http://localhost:8000/api/v1/ai-models?page=1&size=10</code><br>
    <code>curl http://localhost:8000/api/v1/tasks</code><br>
    <code>curl -X POST -H "Content-Type: application/json" -d '{"name": "test"}' http://localhost:8000/api/v1/ai-models</code>
</body>
</html>
        """
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def main():
    """主函数"""
    PORT = 8001
    
    print("=" * 70)
    print("AI综合分析管理平台 - 增强版HTTP服务器")
    print("=" * 70)
    print(f"启动端口: {PORT}")
    print(f"访问地址: http://localhost:{PORT}")
    print(f"API文档: http://localhost:{PORT}/docs")
    print(f"健康检查: http://localhost:{PORT}/health")
    print("")
    print("支持的API接口:")
    print("  - AI模型管理: /api/v1/ai-models")
    print("  - 存储凭证: /api/v1/storage-credentials")
    print("  - Webhook管理: /api/v1/webhooks")
    print("  - 任务管理: /api/v1/tasks")
    print("  - 分析统计: /api/v1/analysis")
    print("按 Ctrl+C 停止服务器")
    print("=" * 70)
    
    try:
        with socketserver.TCPServer(("", PORT), APIHandler) as httpd:
            print(f"服务器已启动，监听端口 {PORT}...")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except OSError as e:
        if e.errno == 10048:  # Windows端口被占用
            print(f"错误: 端口 {PORT} 已被占用，请尝试其他端口或关闭占用该端口的程序")
        else:
            print(f"启动失败: {e}")

if __name__ == "__main__":
    main()