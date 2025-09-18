from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import logging.config
from contextlib import asynccontextmanager
from typing import Callable

from app.core.config import settings
from app.core.database import create_tables, check_database_connection
from app.core.security import security_manager
from app.api.v1.api import api_router

# 配置日志
logging.config.dictConfig(settings.get_log_config())
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 记录请求信息
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        logger.info(
            f"请求开始 - {request.method} {request.url.path} - "
            f"IP: {client_ip} - User-Agent: {user_agent[:100]}"
        )
        
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            logger.info(
                f"请求完成 - {request.method} {request.url.path} - "
                f"状态码: {response.status_code} - 耗时: {process_time:.3f}s"
            )
            
            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"请求异常 - {request.method} {request.url.path} - "
                f"错误: {str(e)} - 耗时: {process_time:.3f}s"
            )
            raise


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 检查是否被限流（针对登录等敏感接口）
        if request.url.path in ["/api/v1/auth/login", "/api/v1/auth/register"]:
            if security_manager.is_rate_limited(client_ip):
                logger.warning(f"IP {client_ip} 被限流")
                return JSONResponse(
                    status_code=429,
                    content={"detail": "请求过于频繁，请稍后再试"}
                )
        
        response = await call_next(request)
        
        # 添加安全响应头
        security_headers = security_manager.get_security_headers()
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} 正在启动...")
    
    # 检查数据库连接
    if not check_database_connection():
        logger.error("❌ 数据库连接失败，应用启动中止")
        raise Exception("数据库连接失败")
    
    # 创建数据库表
    try:
        create_tables()
        logger.info("✅ 数据库表检查完成")
    except Exception as e:
        logger.error(f"❌ 数据库表创建失败: {e}")
        raise
    
    logger.info(f"✅ {settings.PROJECT_NAME} 启动完成")
    logger.info(f"📖 API文档地址: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"🔍 ReDoc文档地址: http://{settings.HOST}:{settings.PORT}/redoc")
    
    yield
    
    # 关闭时执行
    logger.info(f"🛑 {settings.PROJECT_NAME} 正在关闭...")
    logger.info("✅ 应用已安全关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="基于AI的自动化分析平台，通过Webhook接收事件，自动获取文件内容，使用AI模型进行分析，并将结果回写到飞书项目中。",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 添加CORS中间件 - 开发环境总是启用
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"✅ CORS已配置，允许的源: {settings.get_cors_origins()}")

# 添加可信主机中间件（生产环境）
if not settings.is_development():
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # 生产环境中应该配置具体的主机名
    )

# 添加自定义中间件
app.add_middleware(SecurityMiddleware)
app.add_middleware(LoggingMiddleware)

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


# 全局异常处理器
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理器"""
    logger.warning(
        f"HTTP异常 - {request.method} {request.url.path} - "
        f"状态码: {exc.status_code} - 详情: {exc.detail}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    logger.warning(
        f"请求验证失败 - {request.method} {request.url.path} - "
        f"错误: {exc.errors()}"
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "请求参数验证失败",
            "errors": exc.errors(),
            "status_code": 422,
            "path": request.url.path,
            "method": request.method,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(
        f"未处理异常 - {request.method} {request.url.path} - "
        f"错误: {str(exc)}",
        exc_info=True
    )
    
    # 开发环境返回详细错误信息
    if settings.is_development():
        return JSONResponse(
            status_code=500,
            content={
                "detail": "服务器内部错误",
                "error": str(exc),
                "type": type(exc).__name__,
                "status_code": 500,
                "path": request.url.path,
                "method": request.method,
            },
        )
    
    # 生产环境返回通用错误信息
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误，请稍后重试",
            "status_code": 500,
            "path": request.url.path,
            "method": request.method,
        },
    )


# 健康检查端点
@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查接口"""
    from app.core.database import db_manager
    
    # 检查数据库
    db_health = db_manager.health_check()
    
    # 检查Redis（如果需要）
    redis_health = {"status": "healthy"}  # 简化实现
    
    overall_status = "healthy" if (
        db_health["status"] == "healthy" and 
        redis_health["status"] == "healthy"
    ) else "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": time.time(),
        "version": settings.VERSION,
        "environment": "development" if settings.is_development() else "production",
        "services": {
            "database": db_health,
            "redis": redis_health,
        },
    }


# 根路径
@app.get("/", tags=["根路径"])
async def root():
    """根路径接口"""
    return {
        "message": f"欢迎使用 {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🚀 启动开发服务器...")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )