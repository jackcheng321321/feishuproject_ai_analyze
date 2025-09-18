#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最简HTTP服务器 - 用于快速测试
不依赖任何第三方库，使用Python标准库
"""

import http.server
import socketserver
import json
import urllib.parse
from datetime import datetime
import os

class APIHandler(http.server.BaseHTTPRequestHandler):
    """API处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/':
            self.send_json_response({
                "message": "AI综合分析管理平台 - 最简版本",
                "status": "running",
                "version": "0.1.0",
                "timestamp": datetime.now().isoformat()
            })
        elif self.path == '/health':
            self.send_json_response({
                "status": "healthy",
                "message": "服务运行正常",
                "timestamp": datetime.now().isoformat()
            })
        elif self.path == '/api/test':
            self.send_json_response({
                "message": "API测试成功",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "environment": os.getenv("ENVIRONMENT", "development"),
                    "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
                }
            })
        elif self.path == '/docs':
            self.send_html_response(self.get_docs_html())
        else:
            self.send_json_response({
                "error": "Not Found",
                "message": f"路径 {self.path} 不存在"
            }, status=404)
    
    def do_POST(self):
        """处理POST请求"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            data = {"raw_data": post_data.decode('utf-8', errors='ignore')}
        
        if self.path == '/api/echo':
            self.send_json_response({
                "message": "Echo API",
                "received_data": data,
                "timestamp": datetime.now().isoformat()
            })
        else:
            self.send_json_response({
                "error": "Not Found",
                "message": f"POST路径 {self.path} 不存在"
            }, status=404)
    
    def send_json_response(self, data, status=200):
        """发送JSON响应"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def send_html_response(self, html, status=200):
        """发送HTML响应"""
        self.send_response(status)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
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
        <p>最简版本 - 使用Python标准库实现</p>
    </div>
    
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
    
    <div class="endpoint">
        <h3><span class="method post">POST</span> /api/echo</h3>
        <p>回显接口，返回发送的数据</p>
        <p><strong>请求体:</strong> JSON格式数据</p>
    </div>
    
    <div class="endpoint">
        <h3><span class="method get">GET</span> /docs</h3>
        <p>API文档页面（当前页面）</p>
    </div>
    
    <h2>测试示例</h2>
    <p>使用curl测试：</p>
    <code>curl http://localhost:8000/</code><br>
    <code>curl http://localhost:8000/health</code><br>
    <code>curl -X POST -H "Content-Type: application/json" -d '{"test": "data"}' http://localhost:8000/api/echo</code>
</body>
</html>
        """
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def main():
    """主函数"""
    PORT = 8000
    
    print("=" * 60)
    print("AI综合分析管理平台 - 最简HTTP服务器")
    print("=" * 60)
    print(f"启动端口: {PORT}")
    print(f"访问地址: http://localhost:{PORT}")
    print(f"API文档: http://localhost:{PORT}/docs")
    print(f"健康检查: http://localhost:{PORT}/health")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    
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