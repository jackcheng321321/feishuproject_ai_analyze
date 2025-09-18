@echo off
chcp 65001 > nul
echo ====================================
echo AI综合分析管理平台 - 前端服务启动
echo ====================================

echo.
echo 检查环境...

REM 检查Node.js
node --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Node.js未安装或不在PATH中
    echo 请安装Node.js 18+版本
    pause
    exit /b 1
)

echo ✓ Node.js版本:
node --version

REM 检查npm
npm --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ npm未安装
    pause
    exit /b 1
)

echo ✓ npm版本:
npm --version

REM 检查依赖
if not exist node_modules (
    echo ✗ 依赖未安装，请先运行 setup-local.bat
    pause
    exit /b 1
)

echo ✓ 依赖已安装

echo.
echo 检查后端服务...
curl -s http://localhost:8000/health > nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠ 警告: 后端服务(http://localhost:8000)似乎未运行
    echo 请确保后端Docker服务已启动
    echo.
)

echo.
echo ====================================
echo 启动前端开发服务器...
echo 访问地址: http://localhost:3000
echo 按 Ctrl+C 停止服务
echo ====================================
echo.

REM 启动前端服务
npm run dev