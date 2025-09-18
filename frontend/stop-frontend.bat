@echo off
chcp 65001 > nul
echo ====================================
echo AI综合分析管理平台 - 停止前端服务
echo ====================================

echo.
echo 查找前端进程...

REM 查找并终止npm和node进程（Vue/Vite相关）
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq node.exe" /fo table /nh 2^>nul') do (
    tasklist /fi "pid eq %%i" /fo csv /nh | findstr /i "vite\|vue\|npm" > nul
    if not errorlevel 1 (
        echo 终止进程 %%i
        taskkill /f /pid %%i > nul 2>&1
    )
)

REM 查找并终止可能的npm进程
tasklist /fi "imagename eq npm.exe" > nul 2>&1
if %errorlevel% equ 0 (
    echo 终止npm进程...
    taskkill /f /im npm.exe > nul 2>&1
)

REM 检查3000端口是否被占用
netstat -ano | findstr ":3000" > nul 2>&1
if %errorlevel% equ 0 (
    echo 检查3000端口占用...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":3000"') do (
        echo 终止占用3000端口的进程 %%i
        taskkill /f /pid %%i > nul 2>&1
    )
)

echo.
echo ====================================
echo 前端服务已停止
echo ====================================
pause