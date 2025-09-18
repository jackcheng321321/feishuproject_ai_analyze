"""
飞书数据回写服务

该服务负责将AI分析结果回写到飞书项目中，支持多种写入方式：
1. 更新指定字段
2. 添加评论
3. 创建子任务
4. 修改状态
"""

import json
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class FeishuWriteError(Exception):
    """飞书写入服务异常"""
    pass


class FeishuWriteService:
    """飞书数据回写服务"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化飞书写入服务
        
        Args:
            config: 飞书写入配置，包含：
                - base_url: 飞书API基础URL
                - app_id: 飞书应用ID
                - app_secret: 飞书应用密钥
                - tenant_access_token: 租户访问令牌（可选）
                - retry_count: 重试次数，默认3
                - timeout: 超时时间，默认30秒
                - field_mapping: 字段映射配置
                - write_mode: 写入模式 (field_update/comment/subtask/status)
        """
        self.config = config
        self.base_url = config.get("base_url", "https://open.feishu.cn")
        self.app_id = config.get("app_id")
        self.app_secret = config.get("app_secret")
        self.tenant_access_token = config.get("tenant_access_token")
        self.retry_count = config.get("retry_count", 3)
        self.timeout = config.get("timeout", 30)
        self.field_mapping = config.get("field_mapping", {})
        self.write_mode = config.get("write_mode", "field_update")
        
        if not self.app_id or not self.app_secret:
            raise FeishuWriteError("缺少必要的飞书应用配置")
    
    async def _get_tenant_access_token(self) -> str:
        """获取租户访问令牌"""
        if self.tenant_access_token:
            return self.tenant_access_token
            
        url = f"{self.base_url}/open-apis/auth/v3/tenant_access_token/internal"
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=data, timeout=self.timeout) as response:
                    if response.status != 200:
                        raise FeishuWriteError(f"获取访问令牌失败: HTTP {response.status}")
                    
                    result = await response.json()
                    
                    if result.get("code") != 0:
                        raise FeishuWriteError(f"获取访问令牌失败: {result.get('msg', '未知错误')}")
                    
                    token = result.get("tenant_access_token")
                    if not token:
                        raise FeishuWriteError("未获得有效的访问令牌")
                    
                    # 缓存令牌
                    self.tenant_access_token = token
                    return token
                    
            except asyncio.TimeoutError:
                raise FeishuWriteError("获取访问令牌超时")
            except Exception as e:
                raise FeishuWriteError(f"获取访问令牌异常: {str(e)}")
    
    async def _make_api_request(self, method: str, url: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """发起API请求"""
        access_token = await self._get_tenant_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            for attempt in range(self.retry_count):
                try:
                    async with session.request(
                        method, url, json=data, headers=headers, timeout=self.timeout
                    ) as response:
                        result = await response.json()
                        
                        if response.status == 200 and result.get("code") == 0:
                            return {
                                "success": True,
                                "data": result.get("data", {}),
                                "message": "操作成功"
                            }
                        else:
                            error_msg = f"API请求失败: HTTP {response.status}, {result.get('msg', '未知错误')}"
                            if attempt == self.retry_count - 1:
                                return {
                                    "success": False,
                                    "message": error_msg,
                                    "error_code": result.get("code")
                                }
                            logger.warning(f"API请求失败，第{attempt + 1}次重试: {error_msg}")
                            await asyncio.sleep(2 ** attempt)  # 指数退避
                            
                except asyncio.TimeoutError:
                    error_msg = "API请求超时"
                    if attempt == self.retry_count - 1:
                        return {"success": False, "message": error_msg}
                    logger.warning(f"API请求超时，第{attempt + 1}次重试")
                    await asyncio.sleep(2 ** attempt)
                    
                except Exception as e:
                    error_msg = f"API请求异常: {str(e)}"
                    if attempt == self.retry_count - 1:
                        return {"success": False, "message": error_msg}
                    logger.warning(f"API请求异常，第{attempt + 1}次重试: {error_msg}")
                    await asyncio.sleep(2 ** attempt)
        
        return {"success": False, "message": "所有重试均失败"}
    
    async def write_to_record(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        写入数据到飞书记录
        
        Args:
            record_id: 记录ID 
            data: 要写入的数据
            
        Returns:
            写入结果
        """
        try:
            if self.write_mode == "field_update":
                return await self._update_record_fields(record_id, data)
            elif self.write_mode == "comment":
                return await self._add_record_comment(record_id, data)
            elif self.write_mode == "subtask":
                return await self._create_subtask(record_id, data)
            elif self.write_mode == "status":
                return await self._update_record_status(record_id, data)
            else:
                return {"success": False, "message": f"不支持的写入模式: {self.write_mode}"}
                
        except Exception as e:
            logger.error(f"写入飞书记录失败: {e}")
            return {"success": False, "message": str(e)}
    
    async def _update_record_fields(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新记录字段"""
        # 构建字段更新数据
        fields_to_update = {}
        
        # 应用字段映射
        for source_field, target_field in self.field_mapping.items():
            if source_field in data:
                fields_to_update[target_field] = data[source_field]
        
        # 如果没有映射配置，直接使用原始数据
        if not fields_to_update and data.get("analysis_result"):
            fields_to_update["analysis_result"] = data["analysis_result"]
        
        if not fields_to_update:
            return {"success": False, "message": "没有需要更新的字段"}
        
        # 构建API URL和数据
        url = f"{self.base_url}/open-apis/bitable/v1/apps/{self.config.get('app_token')}/tables/{self.config.get('table_id')}/records/{record_id}"
        update_data = {
            "fields": fields_to_update
        }
        
        return await self._make_api_request("PUT", url, update_data)
    
    async def _add_record_comment(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """添加记录评论"""
        comment_content = data.get("analysis_result", "")
        if not comment_content:
            return {"success": False, "message": "评论内容为空"}
        
        # 构建评论内容
        comment_text = f"🤖 AI分析结果 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n\n{comment_content}"
        
        # 构建API URL和数据
        url = f"{self.base_url}/open-apis/bitable/v1/apps/{self.config.get('app_token')}/tables/{self.config.get('table_id')}/records/{record_id}/comments"
        comment_data = {
            "content": {
                "text": comment_text
            }
        }
        
        return await self._make_api_request("POST", url, comment_data)
    
    async def _create_subtask(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建子任务"""
        analysis_result = data.get("analysis_result", "")
        if not analysis_result:
            return {"success": False, "message": "分析结果为空"}
        
        # 构建子任务数据
        subtask_data = {
            "fields": {
                "title": f"AI分析结果 - {data.get('task_name', '未知任务')}",
                "description": analysis_result,
                "parent_id": record_id,
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
        }
        
        # 构建API URL
        url = f"{self.base_url}/open-apis/bitable/v1/apps/{self.config.get('app_token')}/tables/{self.config.get('table_id')}/records"
        
        return await self._make_api_request("POST", url, subtask_data)
    
    async def _update_record_status(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新记录状态"""
        target_status = self.config.get("target_status", "analyzed")
        
        # 构建状态更新数据
        status_data = {
            "fields": {
                "status": target_status,
                "analysis_completed_at": datetime.now().isoformat(),
                "analysis_result": data.get("analysis_result", "")
            }
        }
        
        # 构建API URL
        url = f"{self.base_url}/open-apis/bitable/v1/apps/{self.config.get('app_token')}/tables/{self.config.get('table_id')}/records/{record_id}"
        
        return await self._make_api_request("PUT", url, status_data)
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置"""
        errors = []
        
        if not self.app_id:
            errors.append("缺少app_id")
        if not self.app_secret:
            errors.append("缺少app_secret")
        if not self.config.get("app_token"):
            errors.append("缺少app_token")
        if not self.config.get("table_id"):
            errors.append("缺少table_id")
        
        if self.write_mode not in ["field_update", "comment", "subtask", "status"]:
            errors.append(f"不支持的写入模式: {self.write_mode}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


class FeishuWriteServiceFactory:
    """飞书写入服务工厂"""
    
    @staticmethod
    def create_service(config: Dict[str, Any]) -> FeishuWriteService:
        """创建飞书写入服务实例"""
        service = FeishuWriteService(config)
        
        # 验证配置
        validation = service.validate_config()
        if not validation["valid"]:
            raise FeishuWriteError(f"配置验证失败: {', '.join(validation['errors'])}")
        
        return service
    
    @staticmethod
    async def test_service(config: Dict[str, Any]) -> Dict[str, Any]:
        """测试飞书写入服务"""
        try:
            service = FeishuWriteServiceFactory.create_service(config)
            
            # 测试获取访问令牌
            token = await service._get_tenant_access_token()
            
            return {
                "success": True,
                "message": "服务测试成功",
                "access_token": token[:20] + "..." if token else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"服务测试失败: {str(e)}"
            }