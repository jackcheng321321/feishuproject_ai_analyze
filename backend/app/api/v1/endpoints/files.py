from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.file_service import FileService
from app.services.ai_service import AIService
import logging
import os
import tempfile

logger = logging.getLogger(__name__)
router = APIRouter()

# 服务实例
file_service = FileService()
ai_service = AIService()


class NetworkFileRequest(BaseModel):
    """网络文件请求模型"""
    network_path: str
    copy_to_local: bool = True


class DirectoryListRequest(BaseModel):
    """目录列表请求模型"""
    directory_path: str


class FileAnalysisRequest(BaseModel):
    """文件分析请求模型"""
    file_path: str
    model_id: Optional[int] = None
    analysis_type: str = "content"
    custom_prompt: Optional[str] = None


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    subfolder: Optional[str] = Query(None, description="子文件夹"),
    auto_analyze: bool = Query(False, description="自动分析文件"),
    model_id: Optional[int] = Query(None, description="用于分析的模型ID"),
    db: Session = Depends(get_db)
):
    """上传文件"""
    try:
        logger.info(f"上传文件: {file.filename}")
        
        # 读取文件内容
        content = await file.read()
        
        # 保存文件
        file_info = await file_service.save_uploaded_file(
            file_content=content,
            filename=file.filename,
            subfolder=subfolder
        )
        
        # 如果需要自动分析
        if auto_analyze and model_id:
            try:
                # 这里可以调用分析服务
                logger.info(f"自动分析文件: {file.filename}")
                # 分析逻辑将在后续实现
                file_info["auto_analysis"] = "scheduled"
            except Exception as analysis_error:
                logger.warning(f"自动分析失败: {analysis_error}")
                file_info["auto_analysis"] = f"failed: {str(analysis_error)}"
        
        logger.info(f"文件上传成功: {file.filename}")
        return {
            "success": True,
            "message": "文件上传成功",
            "file_info": file_info
        }
        
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/network")
async def get_network_file(
    request: NetworkFileRequest,
    db: Session = Depends(get_db)
):
    """获取网络文件"""
    try:
        logger.info(f"获取网络文件: {request.network_path}")
        
        # 获取网络文件
        file_info = await file_service.get_network_file(request.network_path)
        
        logger.info(f"网络文件获取成功: {request.network_path}")
        return {
            "success": True,
            "message": "网络文件获取成功",
            "file_info": file_info,
            "source_path": request.network_path
        }
        
    except Exception as e:
        logger.error(f"获取网络文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取网络文件失败: {str(e)}")


@router.post("/directory/list")
async def list_directory(
    request: DirectoryListRequest,
    include_hidden: bool = Query(False, description="包含隐藏文件"),
    file_types: Optional[str] = Query(None, description="文件类型过滤，逗号分隔"),
    db: Session = Depends(get_db)
):
    """列出目录内容"""
    try:
        logger.info(f"列出目录: {request.directory_path}")
        
        # 列出目录内容
        items = await file_service.list_network_directory(request.directory_path)
        
        # 应用过滤器
        if not include_hidden:
            items = [item for item in items if not item["name"].startswith('.')]
        
        if file_types:
            allowed_types = set(ft.strip().lower() for ft in file_types.split(','))
            items = [
                item for item in items 
                if item["is_directory"] or (item["file_type"] and item["file_type"].lower() in allowed_types)
            ]
        
        logger.info(f"目录列出成功，项目数量: {len(items)}")
        return {
            "success": True,
            "message": "目录列出成功",
            "directory_path": request.directory_path,
            "items": items,
            "total_items": len(items),
            "directories": len([item for item in items if item["is_directory"]]),
            "files": len([item for item in items if item["is_file"]])
        }
        
    except Exception as e:
        logger.error(f"列出目录失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出目录失败: {str(e)}")


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """下载文件"""
    try:
        # 这里应该根据file_id从数据库查找文件路径
        # 现在简化为直接使用file_id作为文件路径的一部分
        logger.info(f"下载文件: {file_id}")
        
        # 构建文件路径（这里需要根据实际的文件存储方式调整）
        file_path = os.path.join(file_service.temp_dir, file_id)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 获取文件名
        filename = os.path.basename(file_path)
        
        logger.info(f"文件下载开始: {file_path}")
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件下载失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")


@router.get("/info/{file_id}")
async def get_file_info(
    file_id: str,
    include_content: bool = Query(False, description="包含文件内容"),
    db: Session = Depends(get_db)
):
    """获取文件信息"""
    try:
        logger.info(f"获取文件信息: {file_id}")
        
        # 构建文件路径
        file_path = os.path.join(file_service.temp_dir, file_id)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if include_content:
            # 读取文件内容
            file_info = await file_service.read_file_content(file_path)
        else:
            # 只获取文件信息
            stat = os.stat(file_path)
            from datetime import datetime
            file_info = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": stat.st_size,
                "file_type": file_service.get_file_type(file_path),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
            }
        
        logger.info(f"文件信息获取成功: {file_id}")
        return {
            "success": True,
            "file_info": file_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}")


@router.post("/analyze")
async def analyze_file(
    request: FileAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """分析文件内容"""
    try:
        logger.info(f"分析文件: {request.file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 读取文件内容
        file_info = await file_service.read_file_content(request.file_path)
        
        if not file_info.get("content"):
            raise HTTPException(status_code=400, detail="文件类型不支持内容分析")
        
        # 如果指定了模型ID，从数据库获取模型信息
        if request.model_id:
            from app.models.ai_model import AIModel
            model = db.query(AIModel).filter(AIModel.id == request.model_id).first()
            if not model:
                raise HTTPException(status_code=404, detail="AI模型不存在")
            
            if not model.is_active:
                raise HTTPException(status_code=400, detail="AI模型未激活")
            
            # 解密API密钥
            from app.core.security import decrypt_sensitive_data
            api_key = decrypt_sensitive_data(model.api_key_encrypted)
            
            # 执行分析
            analysis_result = await ai_service.analyze_file_content(
                api_key=api_key,
                model_name=model.model_name,
                file_content=file_info["content"],
                file_type=file_info["file_type"],
                analysis_type=request.analysis_type,
                custom_prompt=request.custom_prompt,
                model_type="gemini" if "gemini" in model.model_name.lower() else "openai",
                api_endpoint=model.api_endpoint if "gemini" not in model.model_name.lower() else None
            )
            
            # 更新模型使用统计
            if analysis_result.get("success"):
                token_usage = analysis_result.get("token_usage", {})
                cost = model.calculate_cost(
                    token_usage.get("input_tokens", 0),
                    token_usage.get("output_tokens", 0)
                )
                model.update_usage_stats(
                    tokens_used=token_usage.get("total_tokens", 0),
                    cost=cost
                )
                db.commit()
            
        else:
            # 没有指定模型，返回基础文件信息
            analysis_result = {
                "success": True,
                "analysis": f"文件基础信息分析完成。文件类型: {file_info['file_type']}, 大小: {file_info['file_size']} 字节",
                "file_info": file_info
            }
        
        logger.info(f"文件分析完成: {request.file_path}")
        return {
            "success": True,
            "message": "文件分析完成",
            "file_path": request.file_path,
            "analysis_result": analysis_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件分析失败: {str(e)}")


@router.delete("/cleanup")
async def cleanup_temp_files(
    background_tasks: BackgroundTasks,
    max_age_hours: int = Query(24, ge=1, le=168, description="文件最大保留时间（小时）"),
    db: Session = Depends(get_db)
):
    """清理临时文件"""
    try:
        logger.info(f"清理临时文件，最大保留时间: {max_age_hours}小时")
        
        # 在后台执行清理任务
        background_tasks.add_task(
            file_service.cleanup_temp_files,
            max_age_hours=max_age_hours
        )
        
        return {
            "success": True,
            "message": f"临时文件清理任务已启动，将清理超过 {max_age_hours} 小时的文件"
        }
        
    except Exception as e:
        logger.error(f"启动文件清理失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动文件清理失败: {str(e)}")


@router.get("/stats")
async def get_file_stats(
    db: Session = Depends(get_db)
):
    """获取文件统计信息"""
    try:
        logger.info("获取文件统计信息")
        
        temp_dir = file_service.temp_dir
        total_files = 0
        total_size = 0
        file_types = {}
        
        for root, dirs, files in os.walk(temp_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                try:
                    file_size = os.path.getsize(file_path)
                    file_type = file_service.get_file_type(filename)
                    
                    total_files += 1
                    total_size += file_size
                    
                    if file_type in file_types:
                        file_types[file_type]["count"] += 1
                        file_types[file_type]["size"] += file_size
                    else:
                        file_types[file_type] = {"count": 1, "size": file_size}
                        
                except Exception:
                    continue
        
        stats = {
            "total_files": total_files,
            "total_size": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "temp_directory": temp_dir,
            "file_types": file_types,
            "allowed_extensions": list(file_service.allowed_extensions),
            "max_file_size_mb": file_service.max_file_size / 1024 / 1024
        }
        
        logger.info(f"文件统计信息获取成功: {total_files} 个文件")
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"获取文件统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文件统计失败: {str(e)}")


# 网络文件浏览器相关端点
@router.get("/network/explore")
async def explore_network_path(
    path: str = Query(..., description="网络路径"),
    db: Session = Depends(get_db)
):
    """浏览网络路径"""
    try:
        logger.info(f"浏览网络路径: {path}")
        
        # 列出目录内容
        items = await file_service.list_network_directory(path)
        
        # 分类统计
        directories = [item for item in items if item["is_directory"]]
        files = [item for item in items if item["is_file"]]
        allowed_files = [item for item in files if item.get("allowed", False)]
        
        result = {
            "success": True,
            "path": path,
            "items": items,
            "summary": {
                "total_items": len(items),
                "directories": len(directories),
                "files": len(files),
                "allowed_files": len(allowed_files),
                "file_types": {}
            }
        }
        
        # 统计文件类型
        for file_item in files:
            file_type = file_item.get("file_type", "unknown")
            if file_type in result["summary"]["file_types"]:
                result["summary"]["file_types"][file_type] += 1
            else:
                result["summary"]["file_types"][file_type] = 1
        
        logger.info(f"网络路径浏览成功: {len(items)} 个项目")
        return result
        
    except Exception as e:
        logger.error(f"浏览网络路径失败: {e}")
        raise HTTPException(status_code=500, detail=f"浏览网络路径失败: {str(e)}")


@router.get("/proxy/image")
async def proxy_image(
    url: str = Query(..., description="图片URL"),
    plugin_token: Optional[str] = Query(None, description="飞书插件令牌（用于飞书图片认证）"),
    db: Session = Depends(get_db)
):
    """代理下载图片（用于前端富文本图片下载）"""
    import requests
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    
    try:
        logger.info(f"代理下载图片: {url}")
        
        # 验证URL格式
        if not url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="无效的图片URL")
        
        # 使用用户浏览器的完全相同的请求头（从curl命令复制）
        headers = {
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        # 如果是飞书图片且提供了plugin_token，优先使用新的UUID下载方式
        if 'project.feishu.cn' in url and plugin_token:
            logger.info(f"检测到飞书项目图片URL，尝试使用UUID下载方式")
            
            # 尝试从URL中提取UUID和项目信息
            try:
                from urllib.parse import urlparse, parse_qs
                parsed_url = urlparse(url)
                
                # 从URL路径中提取UUID（通常在文件名中）
                path_parts = parsed_url.path.split('/')
                potential_uuid = None
                for part in path_parts:
                    if len(part) == 36 and '-' in part:  # UUID格式检测
                        potential_uuid = part.split('.')[0]  # 去掉扩展名
                        break
                
                if potential_uuid:
                    logger.info(f"从URL提取到UUID: {potential_uuid}")
                    
                    # TODO: 需要项目信息才能使用UUID下载
                    # 现在先回退到传统方式，添加认证头
                    headers.update({
                        'X-PLUGIN-TOKEN': plugin_token,
                        'X-USER-KEY': os.getenv("FEISHU_USER_KEY", "")
                    })
                    logger.info(f"暂时使用传统认证方式，已添加认证头")
                else:
                    # 没有找到UUID，使用传统认证
                    headers.update({
                        'X-PLUGIN-TOKEN': plugin_token,
                        'X-USER-KEY': os.getenv("FEISHU_USER_KEY", "")
                    })
                    logger.info(f"未找到UUID，使用传统认证方式")
                    
            except Exception as e:
                logger.warning(f"UUID提取失败，回退到传统认证: {e}")
                headers.update({
                    'X-PLUGIN-TOKEN': plugin_token,
                    'X-USER-KEY': os.getenv("FEISHU_USER_KEY", "")
                })
                logger.info(f"回退到传统认证方式，已添加认证头")
        
        logger.info(f"使用requests下载图片: {url}")
        
        # 直接请求，30秒超时
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        
        # 详细记录响应信息用于调试
        logger.info(f"图片请求响应: 状态码={response.status_code}, 内容长度={len(response.content)} 字节")
        
        if response.status_code == 404:
            logger.warning(f"图片URL返回404，可能已过期: {url}")
            raise HTTPException(status_code=404, detail="图片URL无效或已过期，请刷新富文本内容获取最新的图片链接")
        elif response.status_code == 401:
            logger.warning(f"图片URL需要认证: {url}")  
            raise HTTPException(status_code=401, detail="图片需要认证访问，请检查飞书登录状态")
        
        response.raise_for_status()  # 如果状态码不是2xx会抛异常
        
        # 读取图片数据
        image_data = response.content
        content_type = response.headers.get('content-type', 'image/jpeg')
        
        logger.info(f"图片下载成功: {url}")
        logger.info(f"- 数据大小: {len(image_data)} 字节")
        logger.info(f"- 内容类型: {content_type}")
        
        # 返回图片数据
        return StreamingResponse(
            BytesIO(image_data),
            media_type=content_type,
            headers={
                'Cache-Control': 'public, max-age=3600',  # 缓存1小时
                'Content-Length': str(len(image_data))
            }
        )
                
    except requests.exceptions.RequestException as e:
        logger.error(f"requests下载图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载图片失败: {str(e)}")
    except Exception as e:
        logger.error(f"代理下载图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"代理下载图片失败: {str(e)}")