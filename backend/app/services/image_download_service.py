"""飞书图片下载服务模块 - 专门处理富文本字段中的图片下载"""

import asyncio
import aiohttp
import aiofiles
import logging
import os
import tempfile
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


class FeishuImageDownloadError(Exception):
    """飞书图片下载异常"""
    pass


class FeishuImageDownloadService:
    """飞书图片下载服务"""
    
    def __init__(self, temp_dir: str = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        # 确保临时目录存在
        os.makedirs(os.path.join(self.temp_dir, "images"), exist_ok=True)
        
    async def get_plugin_token(self, plugin_id: str, plugin_secret: str) -> str:
        """获取Plugin Token（用于图片下载认证）"""
        url = "https://project.feishu.cn//open_api/authen/plugin_token"
        
        payload = {
            "plugin_id": plugin_id,
            "plugin_secret": plugin_secret
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("error", {}).get("code") == 0:
                            token = data.get("data", {}).get("token")
                            if token:
                                logger.info("Plugin Token获取成功用于图片下载")
                                return token
                            else:
                                raise FeishuImageDownloadError("Plugin Token为空")
                        else:
                            error_info = data.get("error", {})
                            raise FeishuImageDownloadError(f"获取Plugin Token失败: {error_info}")
                    else:
                        raise FeishuImageDownloadError(f"HTTP请求失败: {response.status}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"获取Plugin Token请求失败: {e}")
            raise FeishuImageDownloadError(f"网络请求失败: {e}")

    async def download_feishu_attachment(
        self,
        project_key: str,
        work_item_type_key: str,
        work_item_id: str,
        file_uuid: str,
        plugin_token: str,
        user_key: str = "",
        save_to_file: bool = True
    ) -> Dict[str, Any]:
        """
        下载飞书项目中的附件（图片）
        
        Args:
            project_key: 项目标识
            work_item_type_key: 工作项类型
            work_item_id: 工作项ID
            file_uuid: 文件UUID（从富文本内容中获取）
            plugin_token: 插件Token
            user_key: 用户标识
            save_to_file: 是否保存到文件
            
        Returns:
            下载结果，包含图片数据或文件路径
        """
        try:
            logger.info(f"开始下载飞书附件: project={project_key}, work_item={work_item_id}, uuid={file_uuid}")
            
            # 构建附件下载URL
            download_url = f"https://project.feishu.cn/open_api/{project_key}/work_item/{work_item_type_key}/{work_item_id}/file/download"
            
            # 构建请求头，使用与富文本字段查询相同的认证方式
            headers = {
                "Content-Type": "application/json",
                "X-PLUGIN-TOKEN": plugin_token,
                "X-USER-KEY": user_key,
                "User-Agent": "FeishuProject-AttachmentDownloader/1.0"
            }
            
            # 构建请求体
            request_body = {
                "uuid": file_uuid
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(download_url, headers=headers, json=request_body) as response:
                    logger.info(f"图片下载响应状态: {response.status}")
                    logger.info(f"响应头: {dict(response.headers)}")
                    
                    if response.status == 200:
                        content_type = response.headers.get('content-type', 'image/png')
                        content_length = response.headers.get('content-length', 0)
                        
                        # 读取图片内容
                        image_data = await response.read()
                        
                        logger.info(f"图片下载成功，大小: {len(image_data)} bytes, Content-Type: {content_type}")
                        
                        result = {
                            "success": True,
                            "project_key": project_key,
                            "work_item_id": work_item_id,
                            "file_uuid": file_uuid,
                            "download_url": download_url,
                            "content_type": content_type,
                            "content_length": int(content_length) if content_length else len(image_data),
                            "actual_size": len(image_data),
                            "download_at": datetime.now().isoformat()
                        }
                        
                        if save_to_file:
                            # 生成文件名，优先使用UUID
                            filename = f"{file_uuid}.png"  # 默认使用png扩展名
                            
                            # 如果文件名没有扩展名，根据content-type添加
                            if '.' not in filename:
                                if 'png' in content_type:
                                    filename += '.png'
                                elif 'jpg' in content_type or 'jpeg' in content_type:
                                    filename += '.jpg'
                                elif 'gif' in content_type:
                                    filename += '.gif'
                                else:
                                    filename += '.png'  # 默认
                            
                            # 生成唯一文件名，避免冲突
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            safe_filename = f"{timestamp}_{filename}"
                            
                            # 保存文件
                            file_path = os.path.join(self.temp_dir, "images", safe_filename)
                            
                            async with aiofiles.open(file_path, 'wb') as f:
                                await f.write(image_data)
                            
                            result.update({
                                "file_path": file_path,
                                "filename": safe_filename,
                                "saved": True
                            })
                            
                            logger.info(f"图片已保存到: {file_path}")
                        else:
                            # 返回base64编码的图片数据
                            import base64
                            result.update({
                                "image_data_base64": base64.b64encode(image_data).decode(),
                                "saved": False
                            })
                        
                        return result
                        
                    elif response.status == 401:
                        error_text = await response.text()
                        raise FeishuImageDownloadError(f"认证失败 (401): {error_text}")
                        
                    elif response.status == 403:
                        error_text = await response.text()
                        raise FeishuImageDownloadError(f"权限不足 (403): {error_text}")
                        
                    elif response.status == 404:
                        error_text = await response.text()
                        raise FeishuImageDownloadError(f"图片不存在 (404): {error_text}")
                        
                    else:
                        error_text = await response.text()
                        raise FeishuImageDownloadError(f"下载失败 ({response.status}): {error_text}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败: {e}")
            raise FeishuImageDownloadError(f"网络请求失败: {e}")
        except Exception as e:
            logger.error(f"下载图片失败: {e}")
            raise FeishuImageDownloadError(f"下载图片失败: {e}")

    async def download_attachment_with_auto_auth(
        self,
        project_key: str,
        work_item_type_key: str,
        work_item_id: str,
        file_uuid: str,
        plugin_id: str,
        plugin_secret: str,
        user_key: str = "",
        save_to_file: bool = True
    ) -> Dict[str, Any]:
        """
        自动认证并下载附件（完整流程）
        
        Args:
            project_key: 项目标识
            work_item_type_key: 工作项类型
            work_item_id: 工作项ID
            file_uuid: 文件UUID
            plugin_id: 插件ID
            plugin_secret: 插件密钥
            user_key: 用户标识
            save_to_file: 是否保存到文件
            
        Returns:
            下载结果
        """
        try:
            logger.info("步骤1: 获取plugin_token用于附件下载")
            plugin_token = await self.get_plugin_token(plugin_id, plugin_secret)
            
            logger.info("步骤2: 使用plugin_token下载附件")
            result = await self.download_feishu_attachment(
                project_key=project_key,
                work_item_type_key=work_item_type_key,
                work_item_id=work_item_id,
                file_uuid=file_uuid,
                plugin_token=plugin_token,
                user_key=user_key,
                save_to_file=save_to_file
            )
            
            result["authentication_method"] = "plugin_token"
            result["plugin_id"] = plugin_id
            
            return result
            
        except Exception as e:
            logger.error(f"自动认证下载附件失败: {e}")
            return {
                "success": False,
                "project_key": project_key,
                "work_item_id": work_item_id,
                "file_uuid": file_uuid,
                "error": str(e),
                "message": f"自动认证下载附件失败: {e}",
                "download_at": datetime.now().isoformat()
            }

    async def test_attachment_download(
        self,
        test_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        测试附件下载功能
        
        Args:
            test_config: 测试配置，包含plugin_id, plugin_secret, user_key, project_key等
            
        Returns:
            测试结果
        """
        try:
            logger.info(f"开始测试附件下载功能")
            
            # 从配置中提取必需参数
            plugin_id = test_config.get("plugin_id")
            plugin_secret = test_config.get("plugin_secret")
            user_key = test_config.get("user_key", "")
            project_key = test_config.get("project_key")
            work_item_type_key = test_config.get("work_item_type_key")
            work_item_id = test_config.get("work_item_id")
            file_uuid = test_config.get("file_uuid")
            
            # 验证必需参数
            missing_params = []
            if not plugin_id: missing_params.append("plugin_id")
            if not plugin_secret: missing_params.append("plugin_secret")
            if not project_key: missing_params.append("project_key")
            if not work_item_type_key: missing_params.append("work_item_type_key")
            if not work_item_id: missing_params.append("work_item_id")
            if not file_uuid: missing_params.append("file_uuid")
            
            if missing_params:
                raise FeishuImageDownloadError(f"缺少必需参数: {', '.join(missing_params)}")
            
            # 执行下载测试
            download_result = await self.download_attachment_with_auto_auth(
                project_key=project_key,
                work_item_type_key=work_item_type_key,
                work_item_id=work_item_id,
                file_uuid=file_uuid,
                plugin_id=plugin_id,
                plugin_secret=plugin_secret,
                user_key=user_key,
                save_to_file=True
            )
            
            # 构建测试结果
            test_result = {
                "test_success": download_result.get("success", False),
                "test_at": datetime.now().isoformat(),
                "config_used": {
                    "plugin_id": plugin_id,
                    "user_key": user_key,
                    "project_key": project_key,
                    "work_item_type_key": work_item_type_key,
                    "work_item_id": work_item_id,
                    "file_uuid": file_uuid,
                    "plugin_secret": "***masked***"
                },
                "download_result": download_result
            }
            
            if download_result.get("success"):
                logger.info("附件下载测试成功")
                test_result["message"] = "附件下载测试成功"
            else:
                logger.error(f"附件下载测试失败: {download_result.get('error')}")
                test_result["message"] = f"附件下载测试失败: {download_result.get('error')}"
            
            return test_result
            
        except Exception as e:
            logger.error(f"测试附件下载功能失败: {e}")
            return {
                "test_success": False,
                "test_at": datetime.now().isoformat(),
                "error": str(e),
                "message": f"测试失败: {e}"
            }


# 创建全局图片下载服务实例
feishu_image_service = FeishuImageDownloadService()