@echo off
chcp 65001 > nul
echo ====================================
echo AI综合分析管理平台 - 前端本地环境设置
echo ====================================

echo.
echo [1/4] 清理现有依赖...
if exist node_modules (
    rmdir /s /q node_modules
    echo 已清理旧的node_modules目录
)

if exist package-lock.json (
    del package-lock.json
    echo 已清理旧的package-lock.json
)

echo.
echo [2/4] 设置npm镜像源（使用淘宝镜像）...
npm config set registry https://registry.npmmirror.com
echo npm镜像源已设置为淘宝镜像

echo.
echo [3/4] 安装依赖包...
npm install
if %errorlevel% neq 0 (
    echo 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)

echo.
echo [4/4] 验证安装...
if exist node_modules\vite\bin\vite.js (
    echo ✓ Vite安装成功
) else (
    echo ✗ Vite安装失败
    pause
    exit /b 1
)

if exist node_modules\vue (
    echo ✓ Vue安装成功
) else (
    echo ✗ Vue安装失败
    pause
    exit /b 1
)

echo.
echo ====================================
echo 前端环境设置完成！
echo 现在可以使用 start-frontend.bat 启动前端服务
echo ====================================
pause