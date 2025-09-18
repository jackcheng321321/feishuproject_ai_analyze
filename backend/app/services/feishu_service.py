#!/usr/bin/env python3
"""
飞书项目API集成服务
用于与飞书项目进行交互，包括获取和更新工作项
"""

import asyncio
import aiohttp
import json
import hashlib
import hmac
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FeishuAPIError(Exception):
    """飞书API异常"""
    pass


class FeishuAuthenticator:
    """飞书认证管理器"""
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
        self.token_expires_at = None
    
    async def get_access_token(self) -> str:
        """获取访问令牌"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        # 令牌已过期或不存在，需要重新获取
        await self._refresh_access_token()
        return self.access_token
    
    async def _refresh_access_token(self):
        """刷新访问令牌"""
        url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
        
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("code") == 0:
                        self.access_token = data["app_access_token"]
                        # 设置过期时间（提前5分钟刷新）
                        expires_in = data.get("expire", 7200) - 300
                        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                        
                        logger.info("飞书访问令牌刷新成功")
                    else:
                        raise FeishuAPIError(f"获取访问令牌失败: {data}")
                else:
                    raise FeishuAPIError(f"HTTP请求失败: {response.status}")


class FeishuProjectAPI:
    """飞书项目API客户端"""
    
    def __init__(self, host: str, app_id: str, app_secret: str, user_id: str):
        self.host = host.rstrip('/')
        self.user_id = user_id
        self.authenticator = FeishuAuthenticator(app_id, app_secret)
        self.session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """发送HTTP请求"""
        url = f"{self.host}{endpoint}"
        
        # 准备请求头
        request_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {await self.authenticator.get_access_token()}"
        }
        
        if headers:
            request_headers.update(headers)
        
        # 发送请求
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers, params=data) as response:
                    return await self._handle_response(response)
            
            elif method.upper() == "POST":
                async with self.session.post(url, headers=request_headers, json=data) as response:
                    return await self._handle_response(response)
            
            elif method.upper() == "PUT":
                async with self.session.put(url, headers=request_headers, json=data) as response:
                    return await self._handle_response(response)
            
            elif method.upper() == "PATCH":
                async with self.session.patch(url, headers=request_headers, json=data) as response:
                    return await self._handle_response(response)
            
            elif method.upper() == "DELETE":
                async with self.session.delete(url, headers=request_headers) as response:
                    return await self._handle_response(response)
            
            else:
                raise FeishuAPIError(f"不支持的HTTP方法: {method}")
                
        except aiohttp.ClientError as e:
            logger.error(f"飞书API请求失败 {method} {url}: {e}")
            raise FeishuAPIError(f"网络请求失败: {e}")
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """处理响应"""
        try:
            data = await response.json()
        except Exception:
            # 如果不是JSON响应，尝试获取文本
            text = await response.text()
            raise FeishuAPIError(f"无效的响应格式: {text}")
        
        if response.status >= 400:
            error_msg = data.get("msg", f"HTTP {response.status}")
            logger.error(f"飞书API错误 {response.status}: {error_msg}")
            raise FeishuAPIError(f"API请求失败: {error_msg}")
        
        # 检查飞书API响应中的错误码
        if data.get("code") != 0:
            error_msg = data.get("msg", "未知错误")
            logger.error(f"飞书API业务错误 {data.get('code')}: {error_msg}")
            raise FeishuAPIError(f"业务逻辑错误: {error_msg}")
        
        return data
    
    async def get_work_item(self, project_key: str, work_item_id: str) -> Dict[str, Any]:
        """获取工作项详情"""
        endpoint = f"/open_api/projects/{project_key}/work_items/{work_item_id}"
        
        try:
            response = await self._make_request("GET", endpoint)
            return response.get("data", {})
            
        except Exception as e:
            logger.error(f"获取工作项失败 {project_key}/{work_item_id}: {e}")
            raise FeishuAPIError(f"获取工作项失败: {e}")
    
    async def update_work_item(
        self, 
        project_key: str, 
        work_item_id: str, 
        fields: Dict[str, Any],
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新工作项字段"""
        endpoint = f"/open_api/projects/{project_key}/work_items/{work_item_id}"
        
        # 构建更新数据
        update_data = {
            "user_key": self.user_id,
            "fields": fields
        }
        
        # 添加评论
        if comment:
            update_data["comment"] = comment
        
        try:
            response = await self._make_request("PATCH", endpoint, update_data)
            logger.info(f"工作项更新成功 {project_key}/{work_item_id}")
            return response.get("data", {})
            
        except Exception as e:
            logger.error(f"更新工作项失败 {project_key}/{work_item_id}: {e}")
            raise FeishuAPIError(f"更新工作项失败: {e}")
    
    async def create_work_item_comment(
        self, 
        project_key: str, 
        work_item_id: str, 
        content: str,
        comment_type: str = "text"
    ) -> Dict[str, Any]:
        """创建工作项评论"""
        endpoint = f"/open_api/projects/{project_key}/work_items/{work_item_id}/comments"
        
        comment_data = {
            "user_key": self.user_id,
            "content": content,
            "type": comment_type
        }
        
        try:
            response = await self._make_request("POST", endpoint, comment_data)
            logger.info(f"工作项评论创建成功 {project_key}/{work_item_id}")
            return response.get("data", {})
            
        except Exception as e:
            logger.error(f"创建工作项评论失败 {project_key}/{work_item_id}: {e}")
            raise FeishuAPIError(f"创建工作项评论失败: {e}")
    
    async def get_project_fields(self, project_key: str) -> Dict[str, Any]:
        """获取项目字段定义"""
        endpoint = f"/open_api/projects/{project_key}/fields"
        
        try:
            response = await self._make_request("GET", endpoint)
            return response.get("data", {})
            
        except Exception as e:
            logger.error(f"获取项目字段失败 {project_key}: {e}")
            raise FeishuAPIError(f"获取项目字段失败: {e}")
    
    async def search_work_items(
        self, 
        project_key: str, 
        query: Dict[str, Any],
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """搜索工作项"""
        endpoint = f"/open_api/projects/{project_key}/work_items/search"
        
        search_data = {
            "query": query,
            "page": page,
            "page_size": page_size
        }
        
        try:
            response = await self._make_request("POST", endpoint, search_data)
            return response.get("data", {})
            
        except Exception as e:
            logger.error(f"搜索工作项失败 {project_key}: {e}")
            raise FeishuAPIError(f"搜索工作项失败: {e}")
    
    async def get_plugin_token(self, plugin_id: str, plugin_secret: str) -> str:
        """获取Plugin Token（用于富文本字段查询）"""
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
                                logger.info("Plugin Token获取成功")
                                return token
                            else:
                                raise FeishuAPIError("Plugin Token为空")
                        else:
                            error_info = data.get("error", {})
                            raise FeishuAPIError(f"获取Plugin Token失败: {error_info}")
                    else:
                        raise FeishuAPIError(f"HTTP请求失败: {response.status}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"获取Plugin Token请求失败: {e}")
            raise FeishuAPIError(f"网络请求失败: {e}")
    
    async def get_rich_text_field_details(
        self,
        project_key: str,
        work_item_type_key: str,
        work_item_id: str,
        field_key: str,
        plugin_token: str,
        user_key: str = ""
    ) -> Dict[str, Any]:
        """获取富文本字段详细信息"""
        url = f"https://project.feishu.cn/open_api/{project_key}/work_item/{work_item_type_key}/query"
        
        headers = {
            "Content-Type": "application/json",
            "X-PLUGIN-TOKEN": plugin_token,
            "X-USER-KEY": user_key
        }
        
        payload = {
            "work_item_ids": [int(work_item_id)],
            "fields": [field_key],
            "expand": {
                "need_workflow": False,
                "relation_fields_detail": False,
                "need_multi_text": True,
                "need_user_detail": False,
                "need_sub_task_parent": False
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("err_code") == 0:
                            work_items = data.get("data", [])
                            if work_items and len(work_items) > 0:
                                work_item = work_items[0]
                                
                                # 从multi_texts中提取富文本详情
                                multi_texts = work_item.get("multi_texts", [])
                                for multi_text in multi_texts:
                                    if multi_text.get("field_key") == field_key:
                                        field_value = multi_text.get("field_value", {})
                                        
                                        logger.info(f"富文本字段详情获取成功: {field_key}")
                                        return {
                                            "success": True,
                                            "field_key": field_key,
                                            "doc": field_value.get("doc"),
                                            "doc_text": field_value.get("doc_text"),
                                            "doc_html": field_value.get("doc_html"),
                                            "is_empty": field_value.get("is_empty", True),
                                            "work_item_id": work_item_id,
                                            "work_item_name": work_item.get("name"),
                                        }
                                
                                # 如果没有找到对应的富文本字段
                                logger.warning(f"未找到富文本字段: {field_key}")
                                return {
                                    "success": False,
                                    "message": f"未找到富文本字段: {field_key}",
                                    "available_fields": [mt.get("field_key") for mt in multi_texts]
                                }
                            else:
                                raise FeishuAPIError("未找到工作项数据")
                        else:
                            error_msg = data.get("err_msg", "未知错误")
                            raise FeishuAPIError(f"业务逻辑错误: {error_msg}")
                    else:
                        raise FeishuAPIError(f"HTTP请求失败: {response.status}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"获取富文本字段详情请求失败: {e}")
            raise FeishuAPIError(f"网络请求失败: {e}")
    
    async def query_rich_text_field(
        self,
        webhook_data: Dict[str, Any],
        plugin_id: str,
        plugin_secret: str,
        user_key: str = ""
    ) -> Dict[str, Any]:
        """
        基于Webhook数据查询富文本字段详情（高级封装）
        
        Args:
            webhook_data: Webhook数据，需要包含payload.id、payload.project_key、
                         payload.changed_fields.field_key、payload.work_item_type_key
            plugin_id: 插件ID
            plugin_secret: 插件密钥
            user_key: 用户标识
            
        Returns:
            富文本字段详情
        """
        try:
            # 提取必需的字段
            payload = webhook_data.get("payload", {})
            work_item_id = str(payload.get("id"))
            project_key = payload.get("project_key")
            work_item_type_key = payload.get("work_item_type_key")
            
            # 获取改变的字段
            changed_fields = payload.get("changed_fields", [])
            if not changed_fields:
                raise FeishuAPIError("Webhook数据中没有changed_fields")
            
            # 取第一个改变的字段（通常富文本字段只有一个）
            field_key = changed_fields[0].get("field_key")
            field_type = changed_fields[0].get("field_type_key")
            
            # 验证必需字段
            if not all([work_item_id, project_key, work_item_type_key, field_key]):
                missing_fields = []
                if not work_item_id: missing_fields.append("payload.id")
                if not project_key: missing_fields.append("payload.project_key")
                if not work_item_type_key: missing_fields.append("payload.work_item_type_key")
                if not field_key: missing_fields.append("payload.changed_fields[0].field_key")
                
                raise FeishuAPIError(f"Webhook数据缺少必需字段: {', '.join(missing_fields)}")
            
            # 第一步：获取plugin_token
            logger.info("步骤1: 获取plugin_token")
            plugin_token = await self.get_plugin_token(plugin_id, plugin_secret)
            
            # 第二步：查询富文本字段详情
            logger.info(f"步骤2: 查询富文本字段详情 - field_key: {field_key}")
            rich_text_details = await self.get_rich_text_field_details(
                project_key=project_key,
                work_item_type_key=work_item_type_key,
                work_item_id=work_item_id,
                field_key=field_key,
                plugin_token=plugin_token,
                user_key=user_key
            )
            
            # 添加额外的元信息
            rich_text_details.update({
                "webhook_info": {
                    "work_item_id": work_item_id,
                    "project_key": project_key,
                    "work_item_type_key": work_item_type_key,
                    "field_key": field_key,
                    "field_type": field_type,
                    "webhook_event_type": webhook_data.get("header", {}).get("event_type")
                },
                "timestamp": datetime.now().isoformat()
            })
            
            return rich_text_details
            
        except Exception as e:
            logger.error(f"查询富文本字段失败: {e}")
            return {
                "success": False,
                "message": f"查询富文本字段失败: {e}",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def query_multiple_fields(
        self,
        project_key: str,
        work_item_type_key: str,
        work_item_id: str,
        field_keys: List[str],
        plugin_token: str,
        user_key: str = ""
    ) -> Dict[str, Any]:
        """
        查询工作项的多个字段值

        Args:
            project_key: 项目标识
            work_item_type_key: 工作项类型标识
            work_item_id: 工作项ID
            field_keys: 要查询的字段列表
            plugin_token: 插件令牌
            user_key: 用户标识

        Returns:
            包含所有字段值的字典
        """
        url = f"https://project.feishu.cn/open_api/{project_key}/work_item/{work_item_type_key}/query"

        headers = {
            "Content-Type": "application/json",
            "X-PLUGIN-TOKEN": plugin_token,
            "X-USER-KEY": user_key
        }

        payload = {
            "work_item_ids": [int(work_item_id)],
            "fields": field_keys,
            "expand": {
                "need_workflow": False,
                "relation_fields_detail": True,
                "need_multi_text": True,
                "need_user_detail": True,
                "need_sub_task_parent": False
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get("err_code") == 0:
                            work_items = data.get("data", [])
                            if work_items and len(work_items) > 0:
                                work_item = work_items[0]

                                # 提取字段值
                                field_values = {}

                                # 处理基础字段
                                fields = work_item.get("fields", {})
                                for field_key in field_keys:
                                    if field_key in fields:
                                        field_values[field_key] = fields[field_key]

                                # 处理富文本字段
                                multi_texts = work_item.get("multi_texts", [])
                                for multi_text in multi_texts:
                                    field_key = multi_text.get("field_key")
                                    if field_key in field_keys:
                                        field_value = multi_text.get("field_value", {})
                                        field_values[field_key] = {
                                            "type": "rich_text",
                                            "doc": field_value.get("doc"),
                                            "doc_text": field_value.get("doc_text"),
                                            "doc_html": field_value.get("doc_html"),
                                            "is_empty": field_value.get("is_empty", True)
                                        }

                                # 处理用户字段
                                users = work_item.get("users", [])
                                for user_field in users:
                                    field_key = user_field.get("field_key")
                                    if field_key in field_keys:
                                        field_values[field_key] = {
                                            "type": "user",
                                            "users": user_field.get("users", [])
                                        }

                                # 处理关联字段
                                relations = work_item.get("relations", [])
                                for relation_field in relations:
                                    field_key = relation_field.get("field_key")
                                    if field_key in field_keys:
                                        field_values[field_key] = {
                                            "type": "relation",
                                            "relations": relation_field.get("relations", [])
                                        }

                                logger.info(f"多字段查询成功: {field_keys}")
                                return {
                                    "success": True,
                                    "work_item_id": work_item_id,
                                    "work_item_name": work_item.get("name"),
                                    "field_values": field_values,
                                    "requested_fields": field_keys,
                                    "found_fields": list(field_values.keys()),
                                    "missing_fields": [f for f in field_keys if f not in field_values]
                                }
                            else:
                                raise FeishuAPIError("未找到工作项数据")
                        else:
                            error_msg = data.get("err_msg", "未知错误")
                            raise FeishuAPIError(f"业务逻辑错误: {error_msg}")
                    else:
                        raise FeishuAPIError(f"HTTP请求失败: {response.status}")

        except aiohttp.ClientError as e:
            logger.error(f"多字段查询请求失败: {e}")
            raise FeishuAPIError(f"网络请求失败: {e}")

    async def query_rich_text_field_enhanced(
        self,
        webhook_data: Dict[str, Any],
        additional_fields: List[str] = None,
        plugin_id: str = "",
        plugin_secret: str = "",
        user_key: str = ""
    ) -> Dict[str, Any]:
        """
        增强版富文本字段查询，支持同时查询其他字段

        Args:
            webhook_data: Webhook数据
            additional_fields: 额外要查询的字段列表
            plugin_id: 插件ID
            plugin_secret: 插件密钥
            user_key: 用户标识

        Returns:
            包含触发字段和额外字段的完整数据
        """
        try:
            # 提取基础信息
            payload = webhook_data.get("payload", {})
            work_item_id = str(payload.get("id"))
            project_key = payload.get("project_key")
            work_item_type_key = payload.get("work_item_type_key")

            # 获取触发字段
            changed_fields = payload.get("changed_fields", [])
            if not changed_fields:
                raise FeishuAPIError("Webhook数据中没有changed_fields")

            trigger_field_key = changed_fields[0].get("field_key")

            # 验证必需字段
            if not all([work_item_id, project_key, work_item_type_key, trigger_field_key]):
                raise FeishuAPIError("Webhook数据缺少必需字段")

            # 获取plugin_token
            logger.info("获取plugin_token")
            plugin_token = await self.get_plugin_token(plugin_id, plugin_secret)

            # 构建查询字段列表
            query_fields = [trigger_field_key]
            if additional_fields:
                query_fields.extend(additional_fields)

            # 去除重复字段
            query_fields = list(set(query_fields))

            logger.info(f"多字段查询 - 字段列表: {query_fields}")

            # 查询多个字段
            query_result = await self.query_multiple_fields(
                project_key=project_key,
                work_item_type_key=work_item_type_key,
                work_item_id=work_item_id,
                field_keys=query_fields,
                plugin_token=plugin_token,
                user_key=user_key
            )

            if query_result.get("success"):
                # 整合结果
                result = {
                    "success": True,
                    "trigger_field": {
                        "field_key": trigger_field_key,
                        "field_value": query_result["field_values"].get(trigger_field_key)
                    },
                    "additional_fields": {},
                    "webhook_info": {
                        "work_item_id": work_item_id,
                        "project_key": project_key,
                        "work_item_type_key": work_item_type_key,
                        "webhook_event_type": webhook_data.get("header", {}).get("event_type")
                    },
                    "query_info": {
                        "requested_fields": query_fields,
                        "found_fields": query_result["found_fields"],
                        "missing_fields": query_result["missing_fields"]
                    },
                    "timestamp": datetime.now().isoformat()
                }

                # 分离额外字段
                if additional_fields:
                    for field_key in additional_fields:
                        if field_key in query_result["field_values"]:
                            result["additional_fields"][field_key] = query_result["field_values"][field_key]

                return result
            else:
                raise FeishuAPIError("多字段查询失败")

        except Exception as e:
            logger.error(f"增强版富文本字段查询失败: {e}")
            return {
                "success": False,
                "message": f"查询失败: {e}",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class FeishuResultWriter:
    """飞书结果写入器（高级封装）"""
    
    def __init__(self, feishu_config: Dict[str, Any]):
        """
        初始化飞书结果写入器
        
        Args:
            feishu_config: 飞书配置，包含：
                - host: 飞书项目主机地址
                - app_id: 应用ID
                - app_secret: 应用密钥
                - user_id: 用户ID
                - project_key: 项目标识（可选，可在写入时指定）
        """
        self.feishu_config = feishu_config
        self.api_client = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.api_client = FeishuProjectAPI(
            host=self.feishu_config["host"],
            app_id=self.feishu_config["app_id"],
            app_secret=self.feishu_config["app_secret"],
            user_id=self.feishu_config["user_id"]
        )
        
        await self.api_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.api_client:
            await self.api_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def write_analysis_result(
        self,
        project_key: str,
        work_item_id: str,
        analysis_result: str,
        field_mapping: Dict[str, str],
        add_comment: bool = True,
        comment_prefix: str = "🤖 AI分析结果"
    ) -> Dict[str, Any]:
        """
        将AI分析结果写入飞书工作项
        
        Args:
            project_key: 项目标识
            work_item_id: 工作项ID
            analysis_result: AI分析结果
            field_mapping: 字段映射配置
            add_comment: 是否添加评论
            comment_prefix: 评论前缀
            
        Returns:
            写入结果
        """
        try:
            # 解析字段映射并更新工作项
            update_fields = {}
            
            for feishu_field, mapping_rule in field_mapping.items():
                if isinstance(mapping_rule, str):
                    # 简单映射：直接使用分析结果
                    if mapping_rule == "analysis_result":
                        update_fields[feishu_field] = analysis_result
                    else:
                        # 尝试从分析结果中提取特定内容
                        update_fields[feishu_field] = self._extract_field_value(
                            analysis_result, 
                            mapping_rule
                        )
                
                elif isinstance(mapping_rule, dict):
                    # 复杂映射：基于规则处理
                    processed_value = self._process_complex_mapping(
                        analysis_result,
                        mapping_rule
                    )
                    update_fields[feishu_field] = processed_value
                
                else:
                    logger.warning(f"不支持的字段映射类型: {feishu_field} -> {mapping_rule}")
            
            # 更新工作项字段
            if update_fields:
                update_result = await self.api_client.update_work_item(
                    project_key=project_key,
                    work_item_id=work_item_id,
                    fields=update_fields,
                    comment=f"{comment_prefix}: 字段已更新" if add_comment else None
                )
                
                logger.info(f"字段更新成功: {update_fields}")
            else:
                logger.warning("没有需要更新的字段")
                update_result = {}
            
            # 添加详细评论
            comment_result = None
            if add_comment:
                comment_content = f"{comment_prefix}:\n\n{analysis_result}"
                comment_result = await self.api_client.create_work_item_comment(
                    project_key=project_key,
                    work_item_id=work_item_id,
                    content=comment_content
                )
            
            return {
                "success": True,
                "message": "AI分析结果写入成功",
                "project_key": project_key,
                "work_item_id": work_item_id,
                "updated_fields": update_fields,
                "update_result": update_result,
                "comment_result": comment_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"写入AI分析结果失败: {e}")
            return {
                "success": False,
                "message": f"写入失败: {e}",
                "project_key": project_key,
                "work_item_id": work_item_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_field_value(self, analysis_result: str, extraction_rule: str) -> str:
        """从分析结果中提取字段值"""
        # 支持不同的提取规则
        if extraction_rule == "first_line":
            return analysis_result.split('\n')[0].strip()
        
        elif extraction_rule == "last_line":
            lines = analysis_result.strip().split('\n')
            return lines[-1].strip() if lines else ""
        
        elif extraction_rule.startswith("regex:"):
            import re
            pattern = extraction_rule[6:]  # 去掉 "regex:" 前缀
            try:
                match = re.search(pattern, analysis_result)
                return match.group(1) if match and match.groups() else match.group(0) if match else ""
            except Exception as e:
                logger.error(f"正则表达式提取失败 {pattern}: {e}")
                return analysis_result
        
        elif extraction_rule.startswith("contains:"):
            keyword = extraction_rule[9:]  # 去掉 "contains:" 前缀
            return "是" if keyword in analysis_result else "否"
        
        elif extraction_rule == "length":
            return str(len(analysis_result))
        
        else:
            # 默认返回完整结果
            return analysis_result
    
    def _process_complex_mapping(self, analysis_result: str, mapping_rule: Dict[str, Any]) -> str:
        """处理复杂的字段映射规则"""
        if "conditions" in mapping_rule:
            # 条件映射
            for condition in mapping_rule["conditions"]:
                if self._evaluate_condition(analysis_result, condition["if"]):
                    return condition["then"]
            
            # 如果没有匹配的条件，返回默认值
            return mapping_rule.get("default", analysis_result)
        
        elif "transform" in mapping_rule:
            # 数据转换
            transform_type = mapping_rule["transform"]
            
            if transform_type == "uppercase":
                return analysis_result.upper()
            elif transform_type == "lowercase":
                return analysis_result.lower()
            elif transform_type == "title":
                return analysis_result.title()
            elif transform_type == "truncate":
                max_length = mapping_rule.get("max_length", 100)
                return analysis_result[:max_length] + "..." if len(analysis_result) > max_length else analysis_result
            else:
                return analysis_result
        
        else:
            return analysis_result
    
    def _evaluate_condition(self, text: str, condition: Dict[str, Any]) -> bool:
        """评估条件表达式"""
        condition_type = condition.get("type", "contains")
        
        if condition_type == "contains":
            return condition["value"] in text
        
        elif condition_type == "starts_with":
            return text.startswith(condition["value"])
        
        elif condition_type == "ends_with":
            return text.endswith(condition["value"])
        
        elif condition_type == "regex":
            import re
            return bool(re.search(condition["pattern"], text))
        
        elif condition_type == "length_gt":
            return len(text) > condition["value"]
        
        elif condition_type == "length_lt":
            return len(text) < condition["value"]
        
        else:
            return False
    
    async def test_connection(self, project_key: str) -> Dict[str, Any]:
        """测试飞书连接"""
        try:
            # 尝试获取项目字段信息
            fields = await self.api_client.get_project_fields(project_key)
            
            return {
                "success": True,
                "message": "飞书连接测试成功",
                "project_key": project_key,
                "available_fields": list(fields.keys()) if fields else [],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"飞书连接测试失败: {e}",
                "project_key": project_key,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }