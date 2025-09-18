"""图片下载API端点"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
import logging

from app.services.image_download_service import feishu_image_service
from app.schemas.base import BaseResponse

logger = logging.getLogger(__name__)

router = APIRouter()


class AttachmentDownloadRequest(BaseModel):
    """附件下载请求"""
    project_key: str
    work_item_type_key: str
    work_item_id: str
    file_uuid: str
    plugin_id: str
    plugin_secret: str
    user_key: Optional[str] = ""
    save_to_file: Optional[bool] = True


class AttachmentDownloadTestRequest(BaseModel):
    """附件下载测试请求"""
    plugin_id: str
    plugin_secret: str
    project_key: str
    work_item_type_key: str
    work_item_id: str
    file_uuid: str
    user_key: Optional[str] = ""


@router.post("/download", response_model=BaseResponse)
async def download_feishu_attachment(request: AttachmentDownloadRequest):
    """
    下载飞书项目中的附件（基于UUID）
    使用与富文本字段查询相同的认证机制
    """
    try:
        logger.info(f"接收到附件下载请求: project={request.project_key}, work_item={request.work_item_id}, uuid={request.file_uuid}")
        
        result = await feishu_image_service.download_attachment_with_auto_auth(
            project_key=request.project_key,
            work_item_type_key=request.work_item_type_key,
            work_item_id=request.work_item_id,
            file_uuid=request.file_uuid,
            plugin_id=request.plugin_id,
            plugin_secret=request.plugin_secret,
            user_key=request.user_key,
            save_to_file=request.save_to_file
        )
        
        if result.get("success"):
            return BaseResponse(
                success=True,
                message="附件下载成功",
                data=result
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"附件下载失败: {result.get('error', '未知错误')}"
            )
            
    except Exception as e:
        logger.error(f"附件下载API失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test", response_model=BaseResponse)
async def test_attachment_download(request: AttachmentDownloadTestRequest):
    """
    测试附件下载功能
    基于UUID的附件下载
    """
    try:
        logger.info("开始执行附件下载测试")
        
        test_config = {
            "plugin_id": request.plugin_id,
            "plugin_secret": request.plugin_secret,
            "user_key": request.user_key,
            "project_key": request.project_key,
            "work_item_type_key": request.work_item_type_key,
            "work_item_id": request.work_item_id,
            "file_uuid": request.file_uuid
        }
        
        result = await feishu_image_service.test_attachment_download(
            test_config=test_config
        )
        
        return BaseResponse(
            success=result.get("test_success", False),
            message=result.get("message", "测试完成"),
            data=result
        )
        
    except Exception as e:
        logger.error(f"附件下载测试API失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plugin-token/{plugin_id}")
async def get_plugin_token(plugin_id: str, plugin_secret: str):
    """
    获取Plugin Token（调试用）
    """
    try:
        logger.info(f"获取Plugin Token: {plugin_id}")
        
        token = await feishu_image_service.get_plugin_token(
            plugin_id=plugin_id,
            plugin_secret=plugin_secret
        )
        
        return BaseResponse(
            success=True,
            message="Plugin Token获取成功",
            data={
                "plugin_id": plugin_id,
                "token": token,
                "token_preview": f"{token[:10]}...{token[-10:]}" if len(token) > 20 else token
            }
        )
        
    except Exception as e:
        logger.error(f"获取Plugin Token失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))