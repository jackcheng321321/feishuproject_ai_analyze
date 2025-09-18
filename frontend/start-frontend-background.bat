@echo off
chcp 65001 > nul
echo ====================================
echo AI综合分析管理平台 - 前端后台服务启动
echo ====================================

echo.
echo 检查环境...

REM 检查依赖
if not exist node_modules (
    echo ✗ 依赖未安装，请先运行 setup-local.bat
    pause
    exit /b 1
)

echo ✓ 依赖已安装

REM 检查是否已经有前端服务在运行
tasklist /fi "imagename eq node.exe" /fi "windowtitle eq *vite*" > nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠ 检测到前端服务可能已在运行
    echo 如需重启，请先运行 stop-frontend.bat
    echo.
)

echo.
echo 启动前端后台服务...
echo 服务将在后台运行，关闭此窗口不影响前端服务

REM 创建日志目录
if not exist logs mkdir logs

REM 后台启动前端服务
start /min "AI前端服务" cmd /c "npm run dev > logs\frontend-%date:~0,4%%date:~5,2%%date:~8,2%.log 2>&1"

echo.
echo ====================================
echo 前端服务已在后台启动！
echo 访问地址: http://localhost:3000
echo 日志文件: logs\frontend-%date:~0,4%%date:~5,2%%date:~8,2%.log
echo 停止服务: 运行 stop-frontend.bat
echo ====================================

REM 等待几秒钟让服务启动
echo 等待服务启动...
timeout /t 5 /nobreak > nul

REM 检查服务是否成功启动
curl -s http://localhost:3000 > nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ 前端服务启动成功！
    echo 可以在浏览器中访问 http://localhost:3000
) else (
    echo ⚠ 前端服务可能需要更多时间启动
    echo 请稍后手动检查 http://localhost:3000
)

echo.
pause