#!/usr/bin/env python3
"""
Webhook异步处理器
整合数据解析、文件获取、AI分析、结果回写的完整流程
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.core.database import SessionLocal
from app.models.webhook import Webhook
from app.models.analysis_task import AnalysisTask
from app.models.task_execution_simple import TaskExecution, ExecutionStatus
from app.models.ai_model import AIModel
from app.models.storage_credential import StorageCredential
from app.services.data_parser import webhook_data_parser
from app.services.file_service import FileService, file_service
from app.services.ai_service import AIService, ai_service
from app.services.feishu_writer import FeishuWriteService

logger = logging.getLogger(__name__)


def _get_provider_from_model_type(model_type):
    """根据模型类型获取提供商名称"""
    from app.models.ai_model import ModelType
    
    type_mapping = {
        ModelType.GEMINI: "google",
        ModelType.OPENAI_COMPATIBLE: "openai",
        ModelType.CLAUDE: "anthropic",
        ModelType.OTHER: "openai"  # 默认使用OpenAI格式
    }
    
    return type_mapping.get(model_type, "openai")


class WebhookProcessorError(Exception):
    """Webhook处理器异常"""
    pass


class WebhookTaskProcessor:
    """Webhook任务处理器"""
    
    def __init__(self):
        self.db = None
    
    def __enter__(self):
        """上下文管理器入口"""
        self.db = SessionLocal()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if self.db:
            self.db.close()
    
    async def process_webhook_task(
        self,
        webhook_id: int,
        payload_data: Dict[str, Any],
        execution_id: str,
        client_ip: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """
        处理单个Webhook任务的完整流程

        Args:
            webhook_id: Webhook数据库ID
            payload_data: 从webhook接收的原始数据
            execution_id: 执行ID
            client_ip: 客户端IP
            user_agent: 用户代理

        Returns:
            处理结果
        """
        start_time = time.time()
        execution_log = []
        result = {
            "success": False,
            "execution_id": execution_id,
            "webhook_id": webhook_id,
            "start_time": datetime.utcnow().isoformat(),
            "steps": [],
            "error": None
        }

        task_execution = None

        try:
            # 1. 获取Webhook和关联的分析任务
            print(f"\n📋 [DEBUG] 步骤1: 获取Webhook和关联任务")
            logger.info(f"开始处理Webhook任务 {execution_id}")
            execution_log.append("开始处理Webhook任务")
            
            webhook = self.db.query(Webhook).filter(Webhook.id == webhook_id).first()
            if not webhook:
                error_msg = f"Webhook不存在: {webhook_id}"
                print(f"❌ [DEBUG] {error_msg}")
                raise WebhookProcessorError(error_msg)
            
            print(f"✅ [DEBUG] 找到Webhook: {webhook.name} (ID: {webhook.id})")
            
            # 获取关联的分析任务 - 优化：确保一对一关系，避免多任务冲突
            from app.models.analysis_task import TaskStatus
            from sqlalchemy import desc

            # 查找所有活跃任务，按更新时间排序（最新的优先）
            all_active_tasks = self.db.query(AnalysisTask).filter(
                AnalysisTask.webhook_id == webhook_id,
                AnalysisTask.status == TaskStatus.ACTIVE
            ).order_by(desc(AnalysisTask.updated_at)).all()

            print(f"🔍 [DEBUG] 查找活跃任务: webhook_id={webhook_id}, status='active'")
            print(f"📊 [DEBUG] 找到 {len(all_active_tasks)} 个活跃的分析任务")

            if not all_active_tasks:
                error_msg = f"没有找到活跃的分析任务: webhook {webhook_id}"
                print(f"❌ [DEBUG] {error_msg}")
                print(f"   - 尝试查找所有状态的任务...")
                all_tasks = self.db.query(AnalysisTask).filter(
                    AnalysisTask.webhook_id == webhook_id
                ).all()
                print(f"   - 所有任务数量: {len(all_tasks)}")
                for task in all_tasks:
                    print(f"     * 任务 {task.id}: {task.name}, 状态: {task.status}")
                raise WebhookProcessorError(error_msg)

            # 只执行最新的一个任务，确保一对一关系
            if len(all_active_tasks) > 1:
                print(f"⚠️ [DEBUG] 发现多个活跃任务，只执行最新的任务以避免冲突")
                for i, task in enumerate(all_active_tasks):
                    status_icon = "🎯" if i == 0 else "⏸️"
                    print(f"   {status_icon} 任务 {task.id}: {task.name} (更新时间: {task.updated_at})")

            # 只取最新的一个任务
            analysis_tasks = [all_active_tasks[0]]

            execution_log.append(f"找到 {len(analysis_tasks)} 个活跃的分析任务")
            result["steps"].append({"step": "load_tasks", "success": True, "task_count": len(analysis_tasks)})

            # 1.5. 预检查和验证阶段 - 防止重复执行
            print(f"\n🛡️ [DEBUG] 步骤1.5: 执行预检查验证")
            validation_result = await self._validate_webhook_execution(
                payload_data=payload_data,
                analysis_tasks=analysis_tasks,
                execution_id=execution_id,
                execution_log=execution_log
            )

            if not validation_result["should_execute"]:
                # 任务被跳过，记录原因并返回成功状态（避免重复触发）
                skip_reason = validation_result["skip_reason"]
                print(f"⏭️ [DEBUG] 任务执行被跳过: {skip_reason}")

                # 记录跳过事件到WebhookLog
                from app.models.webhook_log_simple import WebhookLog
                skip_log = WebhookLog(
                    webhook_id=webhook_id,
                    request_id=f"skip_{execution_id}",
                    source_ip=client_ip,
                    user_agent=user_agent,
                    request_headers={"Content-Type": "application/json"},
                    request_payload=payload_data,
                    request_size_bytes=len(str(payload_data)),
                    response_status=200,  # 成功状态，但跳过执行
                    response_time_ms=int((time.time() - start_time) * 1000),
                    is_valid=False,  # 标记为无效，表示被跳过
                    validation_errors=[skip_reason]
                )
                self.db.add(skip_log)
                self.db.commit()

                result.update({
                    "success": True,  # 返回成功避免重复触发
                    "skipped": True,
                    "skip_reason": skip_reason,
                    "validation_details": validation_result.get("details", {}),
                    "processing_time_seconds": time.time() - start_time,
                    "end_time": datetime.utcnow().isoformat(),
                    "execution_log": execution_log + [f"任务跳过: {skip_reason}"]
                })

                logger.info(f"Webhook任务被跳过 {execution_id}: {skip_reason}")
                return result

            # 2. 处理每个分析任务
            print(f"\n🔄 [DEBUG] 步骤2: 开始处理 {len(analysis_tasks)} 个分析任务")
            task_results = []
            
            for task in analysis_tasks:
                print(f"\n📝 [DEBUG] 处理任务: {task.name} (ID: {task.id})")
                print(f"   - AI模型ID: {task.ai_model_id}")
                print(f"   - 存储凭证: {task.enable_storage_credential}")
                print(f"   - 提示词设置: {'是' if task.prompt_template else '否'}")
                
                try:
                    # 创建任务执行记录
                    print(f"💾 [DEBUG] 创建任务执行记录...")
                    task_execution = TaskExecution(
                        task_id=task.id,  # 现在可以安全设置task_id了
                        execution_id=execution_id,
                        execution_status=ExecutionStatus.PENDING,
                        webhook_payload=payload_data,
                        started_at=datetime.utcnow()
                    )
                    self.db.add(task_execution)
                    self.db.commit()
                    print(f"✅ [DEBUG] 任务执行记录创建成功")
                    
                    # 更新状态为处理中
                    task_execution.execution_status = ExecutionStatus.PROCESSING
                    self.db.commit()
                    print(f"🔄 [DEBUG] 任务状态更新为PROCESSING")
                    
                    # 处理单个任务
                    print(f"🎯 [DEBUG] 开始执行单个任务处理逻辑...")
                    task_result = await self._process_single_task(
                        task, 
                        payload_data, 
                        execution_id,
                        execution_log,
                        task_execution
                    )
                    print(f"🏁 [DEBUG] 单个任务处理完成: 成功={task_result['success']}")
                    
                    task_results.append(task_result)
                    
                    # 更新任务执行状态
                    task_execution.execution_status = ExecutionStatus.SUCCESS if task_result["success"] else ExecutionStatus.FAILED
                    task_execution.error_message = task_result.get("error")
                    task_execution.completed_at = datetime.utcnow()
                    
                    # 更新任务统计
                    processing_time = time.time() - start_time
                    task.update_execution_stats(
                        success=task_result["success"],
                        execution_time=processing_time,
                        tokens_used=task_result.get("tokens_used", 0),
                        cost=task_result.get("cost", 0.0)
                    )
                    
                    self.db.commit()
                    
                except Exception as e:
                    print(f"❌ [DEBUG] 处理任务失败 {task.id}: {e}")
                    print(f"   - 异常类型: {type(e).__name__}")
                    import traceback
                    print(f"   - 异常详情: {traceback.format_exc()}")
                    logger.error(f"处理任务失败 {task.id}: {e}", exc_info=True)
                    
                    if task_execution:
                        task_execution.execution_status = ExecutionStatus.FAILED
                        task_execution.error_message = str(e)
                        task_execution.completed_at = datetime.utcnow()
                        
                        task.update_execution_stats(success=False)
                        self.db.commit()
                    
                    task_results.append({
                        "success": False,
                        "task_id": task.id,
                        "task_name": task.name,
                        "error": str(e)
                    })
            
            # 3. 汇总结果
            successful_tasks = [r for r in task_results if r["success"]]
            failed_tasks = [r for r in task_results if not r["success"]]
            
            result.update({
                "success": len(successful_tasks) > 0,
                "total_tasks": len(task_results),
                "successful_tasks": len(successful_tasks),
                "failed_tasks": len(failed_tasks),
                "task_results": task_results,
                "processing_time_seconds": time.time() - start_time,
                "end_time": datetime.utcnow().isoformat(),
                "execution_log": execution_log
            })
            
            logger.info(f"Webhook任务处理完成 {execution_id}: {len(successful_tasks)}/{len(task_results)} 成功")
            
            return result
            
        except Exception as e:
            logger.error(f"Webhook任务处理失败 {execution_id}: {e}")
            
            result.update({
                "success": False,
                "error": str(e),
                "processing_time_seconds": time.time() - start_time,
                "end_time": datetime.utcnow().isoformat(),
                "execution_log": execution_log
            })
            
            return result
    
    async def _process_single_task(
        self,
        task: AnalysisTask,
        payload_data: Dict[str, Any],
        execution_id: str,
        execution_log: list,
        task_execution: TaskExecution
    ) -> Dict[str, Any]:
        """
        处理单个分析任务
        
        Args:
            task: 分析任务对象
            payload_data: 原始webhook数据
            execution_id: 执行ID
            execution_log: 执行日志列表
            
        Returns:
            任务处理结果
        """
        task_start_time = time.time()
        task_result = {
            "success": False,
            "task_id": task.id,
            "task_name": task.name,
            "steps": [],
            "tokens_used": 0,
            "cost": 0.0
        }
        
        try:
            # 初始化变量避免作用域问题
            source_field_key = None  # 从webhook中提取的触发字段key
            target_field_key = None  # 任务配置中的目标写入字段key
            
            print(f"\n🚀 [TASK] 开始处理分析任务: {task.name} (ID: {task.id})")
            logger.info(f"开始处理分析任务: {task.name} (ID: {task.id})")
            execution_log.append(f"开始处理任务: {task.name}")
            
            # 第1步：数据解析 - 从飞书Webhook中提取关键字段
            print(f"\n🔍 [TASK] 步骤1: 解析飞书Webhook数据")
            logger.info("步骤1: 解析飞书Webhook数据")
            parsed_data = {}
            
            try:
                # 从payload中提取关键字段
                if isinstance(payload_data, dict):
                    # 提取记录ID (payload.id)
                    record_id = None
                    if "payload" in payload_data and isinstance(payload_data["payload"], dict):
                        record_id = payload_data["payload"].get("id")
                    
                    # 提取字段值 (payload.changed_fields[0].cur_field_value)
                    field_value = None
                    if ("payload" in payload_data and 
                        isinstance(payload_data["payload"], dict) and
                        "changed_fields" in payload_data["payload"] and
                        isinstance(payload_data["payload"]["changed_fields"], list) and
                        len(payload_data["payload"]["changed_fields"]) > 0):
                        # changed_fields是数组，取第一个元素的cur_field_value
                        first_changed_field = payload_data["payload"]["changed_fields"][0]
                        field_value = first_changed_field.get("cur_field_value")
                    else:
                        logger.warning(f"changed_fields数据结构不正确: {type(payload_data.get('payload', {}).get('changed_fields'))}")
                    
                    parsed_data = {
                        "record_id": record_id,
                        "field_value": field_value,
                        "raw_payload": payload_data
                    }
                    
                    print(f"✅ [TASK] 飞书数据解析: record_id={record_id}, field_value={'已获取' if field_value else '未获取'}")
                    execution_log.append(f"飞书数据解析成功: record_id={record_id}, field_value={'已获取' if field_value else '未获取'}")
                    task_result["steps"].append({
                        "step": "data_parsing",
                        "success": True,
                        "extracted_fields": {
                            "record_id": record_id is not None,
                            "field_value": field_value is not None
                        }
                    })
                    
                    if not record_id:
                        logger.warning("未能从payload中提取record_id")
                    if not field_value:
                        logger.warning("未能从payload中提取field_value")
                        
                else:
                    raise WebhookProcessorError("payload数据格式不正确")
                    
            except Exception as e:
                logger.error(f"飞书数据解析失败: {e}")
                raise WebhookProcessorError(f"飞书数据解析失败: {e}")
            
            # 第2步：文件获取（如果启用）
            file_content = None
            file_info = {}
            
            # 检查是否启用存储凭证功能
            if task.enable_storage_credential and task.storage_credential_id:
                logger.info("步骤2: 获取文件内容")
                task_execution.update_file_info()  # 记录开始文件获取
                
                # 获取存储凭证
                storage_credential = self.db.query(StorageCredential).filter(
                    StorageCredential.id == task.storage_credential_id
                ).first()
                
                if not storage_credential:
                    raise WebhookProcessorError(f"存储凭证不存在: {task.storage_credential_id}")
                
                # 从提取的数据中构建文件URL或路径
                # 这里可以基于payload.changed_fields.pre_field_value来构建文件路径
                file_path = None
                if field_value and isinstance(field_value, str):
                    # 如果pre_field_value是文件URL或路径
                    file_path = field_value
                elif record_id:
                    # 或者基于record_id构建文件路径
                    file_path = f"records/{record_id}/attachment"
                
                if file_path:
                    try:
                        # 获取文件内容
                        file_result = await file_service.get_file_with_credential(
                            file_path=file_path,
                            credential=storage_credential
                        )
                        
                        file_content = file_result["content"]
                        file_info = file_result["file_info"]
                        
                        # 更新执行记录
                        task_execution.update_file_info(
                            file_url=file_path,
                            file_size=file_info.get("size", 0),
                            file_type=file_info.get("type"),
                            content_preview=file_content[:200] if file_content else None
                        )
                        
                        execution_log.append(f"文件获取成功: {file_path} ({file_info.get('size', 0)} bytes)")
                        task_result["steps"].append({
                            "step": "file_retrieval",
                            "success": True,
                            "file_path": file_path,
                            "file_size": file_info.get("size", 0),
                            "file_type": file_info.get("type")
                        })
                        
                    except Exception as e:
                        logger.error(f"文件获取失败: {e}")
                        task_execution.error_message = f"文件获取失败: {str(e)}"
                        raise WebhookProcessorError(f"文件获取失败: {e}")
                else:
                    execution_log.append("跳过文件获取（未找到文件路径）")
            else:
                execution_log.append("跳过文件获取（功能未启用或无存储凭证配置）")
            
            # 第2.5步：富文本字段解析（如果启用）
            rich_text_images = []
            if task.enable_rich_text_parsing:
                try:
                    print(f"\n🖼️ [TASK] 步骤2.5: 处理富文本字段解析")
                    logger.info("步骤2.5: 处理富文本字段解析")
                    
                    # 检查是否有必要的数据来解析富文本
                    if not (field_value and record_id):
                        print(f"⚠️ [TASK] 缺少富文本解析所需数据 (record_id: {record_id}, field_value: {'有' if field_value else '无'})")
                        execution_log.append("富文本解析: 缺少必要数据，跳过处理")
                    else:
                        # 从webhook数据中提取必要的项目信息
                        if 'payload' in payload_data:
                            payload = payload_data['payload']
                            project_key = payload.get('project_key')
                            work_item_type_key = payload.get('work_item_type_key')
                            work_item_id = str(payload.get('id', ''))
                            
                            # 提取字段key（从changed_fields中获取）
                            if 'changed_fields' in payload and payload['changed_fields']:
                                # 通常取第一个changed_field的field_key
                                source_field_key = payload['changed_fields'][0].get('field_key')
                            else:
                                source_field_key = None  # 确保变量有定义
                            
                            print(f"🔍 [TASK] 从Webhook中提取项目信息:")
                            print(f"   - project_key: {project_key}")
                            print(f"   - work_item_type_key: {work_item_type_key}")
                            print(f"   - work_item_id: {work_item_id}")
                            print(f"   - source_field_key: {source_field_key}")
                            
                            # 检查是否有足够的项目信息
                            if not all([project_key, work_item_type_key, work_item_id, source_field_key]):
                                print(f"⚠️ [TASK] 缺少富文本解析必需的项目信息")
                                execution_log.append("富文本解析: 缺少项目信息，跳过处理")
                            else:
                                # 从环境变量读取飞书API配置
                                import os
                                fixed_api_config = {
                                    "plugin_id": os.getenv("FEISHU_PLUGIN_ID", ""),
                                    "plugin_secret": os.getenv("FEISHU_PLUGIN_SECRET", ""),
                                    "user_key": os.getenv("FEISHU_USER_KEY", "")
                                }
                                
                                # 检查必需的配置是否存在
                                if not all(fixed_api_config.values()):
                                    print(f"⚠️ [TASK] 飞书API配置不完整，请检查环境变量: FEISHU_PLUGIN_ID, FEISHU_PLUGIN_SECRET, FEISHU_USER_KEY")
                                    execution_log.append("富文本解析: 飞书API配置缺失，跳过处理")
                                else:
                                    print(f"🔧 [TASK] 开始查询富文本详情...")

                                    # 导入富文本详情查询服务（json已在文件头部导入）
                                    from app.services.image_download_service import FeishuImageDownloadService
                                    import aiohttp

                                    # 第一步: 获取plugin_token
                                    plugin_token = None
                                    try:
                                        download_service = FeishuImageDownloadService()
                                        plugin_token = await download_service.get_plugin_token(
                                            plugin_id=fixed_api_config["plugin_id"],
                                            plugin_secret=fixed_api_config["plugin_secret"]
                                        )
                                        print(f"✅ [TASK] Plugin Token获取成功")
                                    except Exception as token_error:
                                        print(f"❌ [TASK] Plugin Token获取失败: {token_error}")
                                        execution_log.append(f"富文本解析: Plugin Token获取失败 - {token_error}")
                                
                                    # 第二步: 查询富文本字段详情
                                    if plugin_token:
                                        try:
                                            # 构建查询富文本详情的请求
                                            rich_text_url = f"https://project.feishu.cn/open_api/{project_key}/work_item/{work_item_type_key}/query"

                                            headers = {
                                                "X-PLUGIN-TOKEN": plugin_token,
                                                "X-USER-KEY": fixed_api_config["user_key"],
                                                "Content-Type": "application/json"
                                            }

                                            request_body = {
                                                "work_item_ids": [int(work_item_id)],
                                                "fields": [source_field_key],
                                                "expand": {
                                                    "need_workflow": False,
                                                    "relation_fields_detail": False,
                                                    "need_multi_text": True,
                                                    "need_user_detail": False,
                                                    "need_sub_task_parent": False
                                                }
                                            }

                                            print(f"📡 [TASK] 查询富文本详情: {rich_text_url}")
                                            print(f"   - 请求体: {json.dumps(request_body, ensure_ascii=False)}")

                                            async with aiohttp.ClientSession() as session:
                                                async with session.post(rich_text_url, headers=headers, json=request_body) as response:
                                                    if response.status == 200:
                                                        rich_text_response = await response.json()
                                                        print(f"✅ [TASK] 富文本详情查询成功")

                                                        # 解析富文本中的图片信息
                                                        await self._parse_rich_text_images(
                                                            rich_text_response=rich_text_response,
                                                            field_key=source_field_key,
                                                            project_key=project_key,
                                                            work_item_type_key=work_item_type_key,
                                                            work_item_id=work_item_id,
                                                            fixed_api_config=fixed_api_config,
                                                            rich_text_images=rich_text_images,
                                                            execution_log=execution_log
                                                        )
                                                    else:
                                                        error_text = await response.text()
                                                        print(f"❌ [TASK] 富文本详情查询失败: {response.status} - {error_text}")
                                                        execution_log.append(f"富文本解析: 详情查询失败 - {response.status}")
                                        except Exception as query_error:
                                            print(f"❌ [TASK] 富文本详情查询异常: {query_error}")
                                            execution_log.append(f"富文本解析: 查询异常 - {query_error}")
                        else:
                            print(f"⚠️ [TASK] Webhook数据中缺少payload信息")
                            execution_log.append("富文本解析: Webhook数据格式错误")
                            
                    print(f"📊 [TASK] 富文本解析完成: 成功处理 {len(rich_text_images)} 张图片")
                    execution_log.append(f"富文本解析: 处理了 {len(rich_text_images)} 张图片")
                    
                except Exception as rich_error:
                    print(f"❌ [TASK] 富文本解析失败: {rich_error}")
                    logger.error(f"富文本解析失败: {rich_error}")
                    execution_log.append(f"富文本解析失败: {rich_error}")
                    # 不中断主流程，继续执行AI分析
            else:
                print(f"ℹ️ [TASK] 富文本解析未启用或未配置")
                execution_log.append("跳过富文本解析（未启用或未配置）")

            # 第2.7步：多字段查询（如果启用）
            additional_field_data = {}
            if task.enable_multi_field_analysis and task.multi_field_config:
                try:
                    print(f"\n🔍 [TASK] 步骤2.7: 执行多字段查询")
                    logger.info("步骤2.7: 执行多字段查询")

                    # 调用多字段查询方法
                    additional_field_data = await self._query_additional_fields(
                        task=task,
                        payload_data=payload_data,
                        execution_log=execution_log
                    )

                    print(f"✅ [TASK] 多字段查询完成: 获取到 {len(additional_field_data)} 个字段")
                    execution_log.append(f"多字段查询: 获取到 {len(additional_field_data)} 个字段")
                    task_result["steps"].append({
                        "step": "multi_field_query",
                        "success": True,
                        "fields_count": len(additional_field_data),
                        "fields": list(additional_field_data.keys())
                    })

                except Exception as multi_field_error:
                    print(f"❌ [TASK] 多字段查询失败: {multi_field_error}")
                    logger.error(f"多字段查询失败: {multi_field_error}")
                    execution_log.append(f"多字段查询失败: {multi_field_error}")
                    # 不中断主流程，继续执行AI分析
            else:
                print(f"ℹ️ [TASK] 多字段查询未启用或未配置")
                execution_log.append("跳过多字段查询（未启用或未配置）")

            # 第3步：AI分析
            print(f"\n🤖 [TASK] 步骤3: 执行AI分析")
            logger.info("步骤3: 执行AI分析")
            
            # 获取AI模型
            print(f"🔍 [TASK] 查找AI模型: {task.ai_model_id}")
            ai_model = self.db.query(AIModel).filter(
                AIModel.id == task.ai_model_id
            ).first()
            
            if not ai_model:
                error_msg = f"AI模型不存在: {task.ai_model_id}"
                print(f"❌ [TASK] {error_msg}")
                raise WebhookProcessorError(error_msg)
            
            print(f"✅ [TASK] 找到AI模型: {ai_model.name} ({ai_model.model_type})")
            print(f"   - API密钥: {'已设置' if ai_model.api_key else '未设置'}")
            
            # 构建分析内容 - 包含webhook数据和文件内容（如果有）
            analysis_content = {
                "record_id": record_id,
                "field_value": field_value,
                "file_content": file_content or None,
                "webhook_payload": payload_data
            }
            
            # 构建最终的分析提示词（支持多字段模板渲染）
            user_prompt = task.user_prompt_template or "综合对比分析一下这些图片数据的情况"

            # 准备富文本字段的纯文本内容
            rich_text_content = ""
            if field_value:
                rich_text_content = self._extract_rich_text_content(field_value)

            if task.enable_multi_field_analysis and additional_field_data:
                # 使用多字段模板渲染
                print(f"🔄 [TASK] 使用多字段模板渲染")
                print(f"   - 可用字段: {list(additional_field_data.keys())}")

                # 将富文本触发字段添加到字段数据中，支持占位符使用
                additional_field_data['field_value'] = rich_text_content
                additional_field_data['trigger_field'] = rich_text_content  # 提供别名

                print(f"   - 富文本内容长度: {len(rich_text_content)} 字符")
                print(f"   - 可用占位符: {list(additional_field_data.keys())}")

                # 渲染用户提示词模板（现在支持 {field_value} 和 {trigger_field} 占位符）
                rendered_prompt = self._render_template_with_fields(user_prompt, additional_field_data)

                # 如果用户在提示词中使用了占位符，则直接使用渲染结果
                # 否则保持兼容性，在末尾添加触发字段内容
                if '{field_value}' in user_prompt or '{trigger_field}' in user_prompt:
                    # 用户主动使用了富文本占位符，完全由用户控制位置
                    final_prompt = rendered_prompt
                    print(f"   - 检测到富文本占位符使用，由用户控制位置")
                else:
                    # 向后兼容：在末尾添加触发字段内容
                    final_prompt = f"""{rendered_prompt}

触发字段内容：{rich_text_content}

注意：以上信息包含了工作项的多个字段数据，请综合分析。"""
                    print(f"   - 未检测到富文本占位符，使用兼容模式")

                print(f"   - 渲染后的提示词长度: {len(final_prompt)}")
            else:
                # 使用原有的单字段方式，但支持 {field_value} 占位符
                if '{field_value}' in user_prompt:
                    # 用户在单字段模式下使用了占位符
                    field_data = {'field_value': rich_text_content}
                    final_prompt = self._render_template_with_fields(user_prompt, field_data)
                    print(f"🔄 [TASK] 单字段模式使用占位符渲染")
                else:
                    # 向后兼容：保持原有的固定格式
                    final_prompt = f"""{user_prompt}

富文本字段内容：{rich_text_content}"""
                    print(f"ℹ️ [TASK] 单字段兼容模式")
            
            # 记录AI请求
            print(f"📝 [TASK] 记录AI请求提示词 (长度: {len(final_prompt)})")
            print(f"📝 [TASK] 使用的用户提示词: {user_prompt[:100]}...")
            task_execution.update_ai_request(final_prompt)
            
            try:
                # 调用AI服务
                print(f"🤖 [TASK] 调用AI服务...")
                print(f"   - 模型ID: {ai_model.id}")
                print(f"   - max_tokens: {task.max_tokens or 1000}")
                print(f"   - temperature: {task.temperature or 0.7}")
                
                # 构建AI分析请求参数（任务配置优先）
                model_config = {
                    "provider": _get_provider_from_model_type(ai_model.model_type),
                    "model_name": ai_model.model_name or ai_model.name,
                    "api_key": ai_model.api_key,
                    "api_endpoint": ai_model.api_endpoint,
                    "temperature": float(task.temperature) if task.temperature is not None else (float(ai_model.temperature) if ai_model.temperature else 0.7),
                    "max_tokens": task.max_tokens or 1000,
                    "use_proxy": getattr(ai_model, 'use_proxy', False),
                    "proxy_url": getattr(ai_model, 'proxy_url', None) if getattr(ai_model, 'use_proxy', False) else None
                }
                
                print(f"⚙️ [TASK] 使用温度: {model_config['temperature']} (任务:{task.temperature}/模型:{ai_model.temperature})")
                
                # 构建分析请求
                analysis_request = {
                    "model_config": model_config,
                    "prompt": final_prompt,
                    "data_content": file_content or "",
                    "file_contents": [],
                    "rich_text_images": rich_text_images,  # 包含从富文本字段解析的图片
                    "context": {
                        "record_id": record_id,
                        "field_value": field_value,
                        "rich_text_enabled": task.enable_rich_text_parsing,
                        "images_count": len(rich_text_images)
                    }
                }
                
                print(f"📝 [TASK] AI分析请求: 富文本图片{len(rich_text_images)}张, 提示词{len(final_prompt)}字符")
                
                ai_result = await ai_service.analyze_content(analysis_request)
                
                
                # 检查AI分析是否成功
                if not ai_result.get("success", False):
                    error_msg = ai_result.get("error", "AI分析失败：未知错误")
                    raise Exception(error_msg)
                
                analysis_result = ai_result["content"]
                
                # 处理token使用情况 - analyze_content返回的usage结构
                usage_info = ai_result.get("usage", {})
                tokens_used = usage_info.get("total_tokens", 0)
                if not tokens_used:
                    # 尝试备用字段
                    tokens_used = (usage_info.get("input_tokens", 0) + 
                                 usage_info.get("output_tokens", 0))
                
                # 计算基本成本（简化版本，实际应根据模型定价）
                cost = 0.0  # 暂时设为0，后续可以根据模型配置计算
                
                print(f"📊 [TASK] AI分析完成: {len(analysis_result)}字符, {tokens_used}tokens, 成本${cost:.4f}")
                logger.info(f"AI分析结果预览: {analysis_result[:200]}...")
                
                # 记录AI响应
                task_execution.update_ai_response(
                    response=analysis_result,
                    metadata=ai_result,
                    tokens_used=tokens_used,
                    cost=cost
                )
                
                task_result["analysis_result"] = analysis_result
                task_result["tokens_used"] = tokens_used
                task_result["cost"] = cost
                
                execution_log.append(f"AI分析完成: {tokens_used} tokens, 成本: ${cost:.4f}")
                task_result["steps"].append({
                    "step": "ai_analysis", 
                    "success": True,
                    "model_name": ai_model.name,
                    "tokens_used": tokens_used,
                    "cost": cost
                })
                
            except Exception as e:
                print(f"❌ [TASK] AI分析失败: {e}")
                print(f"   - 异常类型: {type(e).__name__}")
                import traceback
                print(f"   - 异常详情: {traceback.format_exc()}")
                
                logger.error(f"AI分析失败: {e}", exc_info=True)
                task_execution.error_message = f"AI分析失败: {str(e)}"
                raise WebhookProcessorError(f"AI分析失败: {e}")
            
            # 第4步：飞书结果回写
            print(f"\n🚀 [TASK] 步骤4: 检查飞书回写配置")
            print(f"   - 飞书配置: {'已设置' if task.feishu_write_config else '未设置'}")
            print(f"   - record_id: {record_id}")
            
            if task.feishu_write_config and record_id:
                print(f"🚀 [TASK] 开始回写分析结果到飞书...")
                logger.info("步骤4: 回写分析结果到飞书")
                
                try:
                    # 从webhook数据中提取必要的项目信息（与富文本解析中的逻辑相同）
                    if 'payload' in payload_data:
                        payload = payload_data['payload']
                        project_key = payload.get('project_key')
                        work_item_type_key = payload.get('work_item_type_key')
                        work_item_id = str(payload.get('id', ''))
                        
                        # 从任务配置中获取目标字段ID（不是webhook中的field_key）
                        target_field_key = None
                        if task.feishu_write_config and isinstance(task.feishu_write_config, dict):
                            target_field_key = task.feishu_write_config.get('field_id')
                        
                        print(f"🎯 [TASK] 回写目标字段检查:")
                        print(f"   - 任务配置的目标字段: {target_field_key}")
                        print(f"   - feishu_write_config: {task.feishu_write_config}")
                        
                        print(f"🔍 [TASK] 从Webhook中提取飞书回写信息:")
                        print(f"   - project_key: {project_key}")
                        print(f"   - work_item_type_key: {work_item_type_key}")
                        print(f"   - work_item_id: {work_item_id}")
                        print(f"   - 目标字段: {target_field_key}")
                        
                        # 检查是否有足够的项目信息（使用目标字段）
                        if not all([project_key, work_item_type_key, work_item_id, target_field_key]):
                            missing = []
                            if not project_key: missing.append('project_key')
                            if not work_item_type_key: missing.append('work_item_type_key')
                            if not work_item_id: missing.append('work_item_id')
                            if not target_field_key: missing.append('target_field_key(任务配置)')
                            raise WebhookProcessorError(f"缺少飞书回写必需的项目信息: {', '.join(missing)}")
                        
                        # 从环境变量读取飞书API配置（与富文本解析相同）
                        import os
                        fixed_api_config = {
                            "plugin_id": os.getenv("FEISHU_PLUGIN_ID", ""),
                            "plugin_secret": os.getenv("FEISHU_PLUGIN_SECRET", ""),
                            "user_key": os.getenv("FEISHU_USER_KEY", "")
                        }
                        
                        # 检查必需的配置是否存在
                        if not all(fixed_api_config.values()):
                            raise WebhookProcessorError("飞书API配置不完整，请检查环境变量: FEISHU_PLUGIN_ID, FEISHU_PLUGIN_SECRET, FEISHU_USER_KEY")
                        
                        # 第一步：获取plugin_token
                        print(f"📡 [TASK] 获取Plugin Token...")
                        from app.services.image_download_service import FeishuImageDownloadService
                        
                        download_service = FeishuImageDownloadService()
                        plugin_token = await download_service.get_plugin_token(
                            plugin_id=fixed_api_config["plugin_id"],
                            plugin_secret=fixed_api_config["plugin_secret"]
                        )
                        print(f"✅ [TASK] Plugin Token获取成功")
                        
                        # 第二步：将AI分析结果转换为富文本格式
                        print(f"📝 [TASK] 转换AI分析结果为飞书富文本格式...")
                        
                        try:
                            from app.utils.markdown_converter import convert_markdown_to_feishu
                            rich_text_content = convert_markdown_to_feishu(analysis_result)
                            print(f"✅ [TASK] 成功转换为富文本，包含 {len(rich_text_content) if isinstance(rich_text_content, list) else 1} 个内容块")
                            field_value = rich_text_content
                        except Exception as convert_error:
                            print(f"⚠️ [TASK] 富文本转换失败，使用纯文本格式: {convert_error}")
                            field_value = analysis_result
                        
                        # 第三步：构建飞书项目数据写入请求
                        update_url = f"https://project.feishu.cn/open_api/{project_key}/work_item/{work_item_type_key}/{work_item_id}"
                        
                        headers = {
                            "Content-Type": "application/json",
                            "X-PLUGIN-TOKEN": plugin_token,
                            "X-USER-KEY": fixed_api_config["user_key"]
                        }
                        
                        # 按照文档要求的请求体格式（使用目标字段）
                        request_body = {
                            "update_fields": [{
                                "field_key": target_field_key,
                                "field_value": field_value,
                                "target_state": {
                                    "state_key": "",
                                    "transition_id": 0
                                },
                                "field_type_key": "",
                                "field_alias": "",
                                "help_description": ""
                            }]
                        }
                        
                        print(f"📡 [TASK] 发送飞书写入请求到: {update_url}")
                        print(f"   - 请求头: X-PLUGIN-TOKEN已设置, X-USER-KEY={fixed_api_config['user_key']}")
                        
                        # 第四步：发送PUT请求到飞书项目API
                        import aiohttp
                        async with aiohttp.ClientSession() as session:
                            async with session.put(update_url, headers=headers, json=request_body) as response:
                                response_text = await response.text()
                                print(f"📊 [TASK] 飞书API响应状态: {response.status}")
                                print(f"📊 [TASK] 飞书API响应内容: {response_text[:200]}...")
                                
                                try:
                                    response_json = await response.json() if response.status != 204 else {}
                                except:
                                    response_json = {"raw_response": response_text}
                                
                                # 记录飞书更新结果
                                task_execution.update_feishu_result(
                                    feishu_task_id=work_item_id,
                                    feishu_response=response_json,
                                    fields_updated={target_field_key: str(field_value)[:200] + "..." if len(str(field_value)) > 200 else str(field_value)}
                                )
                                
                                if response.status in [200, 204]:
                                    print(f"✅ [TASK] 飞书数据写入成功")
                                    execution_log.append(f"飞书回写成功: work_item_id={work_item_id}, target_field={target_field_key}")
                                    task_result["steps"].append({
                                        "step": "feishu_writeback",
                                        "success": True,
                                        "work_item_id": work_item_id,
                                        "target_field_key": target_field_key,
                                        "response_status": response.status
                                    })
                                else:
                                    error_msg = f"飞书API错误 ({response.status}): {response_text}"
                                    print(f"❌ [TASK] {error_msg}")
                                    raise WebhookProcessorError(error_msg)
                    else:
                        raise WebhookProcessorError("Webhook数据中缺少payload信息")
                        
                except Exception as e:
                    print(f"❌ [TASK] 飞书回写失败: {e}")
                    logger.error(f"飞书回写失败: {e}")
                    execution_log.append(f"飞书回写失败: {e}")
                    # 不中断主流程，标记为部分成功
                    task_result["steps"].append({
                        "step": "feishu_writeback",
                        "success": False,
                        "error": str(e)
                    })
            else:
                print(f"ℹ️ [TASK] 跳过飞书回写：配置未启用或缺少record_id")
                execution_log.append("跳过飞书回写：配置未启用或缺少必要信息")
            
            # 任务处理成功 - 标记执行完成
            print(f"\n🎉 [TASK] 任务处理成功! 标记为完成状态")
            # 保存执行日志
            task_execution.update_execution_log(execution_log)
            task_execution.mark_completed(
                status=ExecutionStatus.SUCCESS,
                error_message=None,
                error_code=None
            )
            
            task_result.update({
                "success": True,
                "analysis_result": analysis_result,
                "processing_time_seconds": time.time() - task_start_time,
                "message": "任务处理成功",
                "execution_id": execution_id
            })
            
            # 提交数据库变更
            self.db.commit()
            
            logger.info(f"分析任务处理成功: {task.name}")
            return task_result
            
        except Exception as e:
            print(f"\n❌ [TASK] 分析任务处理失败 {task.name}: {e}")
            print(f"   - 异常类型: {type(e).__name__}")
            import traceback
            print(f"   - 异常详情: {traceback.format_exc()}")
            
            logger.error(f"分析任务处理失败 {task.name}: {e}", exc_info=True)
            
            # 标记执行失败
            if 'task_execution' in locals():
                # 在失败日志中添加错误信息
                execution_log.append(f"任务执行失败: {str(e)}")
                # 保存执行日志
                task_execution.update_execution_log(execution_log)
                task_execution.mark_completed(
                    status=ExecutionStatus.FAILED,
                    error_message=str(e),
                    error_code=type(e).__name__
                )
                self.db.commit()
            
            task_result.update({
                "success": False,
                "error": str(e),
                "processing_time_seconds": time.time() - task_start_time,
                "execution_id": execution_id if 'execution_id' in locals() else None
            })
            
            return task_result
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """渲染模板字符串"""
        if not template:
            return ""
        
        try:
            # 简单的模板替换，使用 {{variable}} 语法
            import re
            
            def replace_var(match):
                var_name = match.group(1)
                return str(context.get(var_name, f"{{{{{var_name}}}}}"))
            
            return re.sub(r'\{\{([^}]+)\}\}', replace_var, template)
            
        except Exception as e:
            logger.error(f"模板渲染失败: {e}")
            return template

    async def _parse_rich_text_images(
        self,
        rich_text_response: Dict[str, Any],
        field_key: str,
        project_key: str,
        work_item_type_key: str,
        work_item_id: str,
        fixed_api_config: Dict[str, str],
        rich_text_images: list,
        execution_log: list
    ) -> None:
        """
        从富文本详情响应中解析图片信息并下载图片
        
        Args:
            rich_text_response: 富文本详情API响应
            field_key: 字段key
            project_key: 项目key
            work_item_type_key: 工作项类型key
            work_item_id: 工作项ID
            fixed_api_config: 固定API配置
            rich_text_images: 图片列表（输出）
            execution_log: 执行日志
        """
        try:
            # 从响应中提取multi_texts数据
            if 'data' not in rich_text_response or not rich_text_response['data']:
                print(f"❌ [TASK] 富文本详情响应中无data字段")
                return
            
            work_item_data = rich_text_response['data'][0] if rich_text_response['data'] else None
            if not work_item_data or 'multi_texts' not in work_item_data:
                print(f"❌ [TASK] 富文本详情中无multi_texts数据")
                return
            
            # 查找对应field_key的富文本数据
            target_multi_text = None
            for multi_text in work_item_data['multi_texts']:
                if multi_text.get('field_key') == field_key:
                    target_multi_text = multi_text
                    break
            
            if not target_multi_text:
                print(f"❌ [TASK] 未找到字段 {field_key} 的富文本数据")
                return
            
            field_value = target_multi_text.get('field_value', {})
            doc_content = field_value.get('doc', '')
            
            if not doc_content:
                print(f"❌ [TASK] 富文本字段 {field_key} 无doc内容")
                return
            
            print(f"✅ [TASK] 找到富文本doc内容: {len(doc_content)} 字符")
            
            # 解析doc内容中的图片信息
            import json
            import re
            
            try:
                # doc是JSON字符串，需要解析
                doc_data = json.loads(doc_content)
                images_found = []
                
                # 递归搜索所有ops中的image属性
                def find_images_in_ops(ops_data):
                    if isinstance(ops_data, dict):
                        if ops_data.get('attributes', {}).get('image') == 'true':
                            # 找到图片
                            uuid = ops_data['attributes'].get('uuid')
                            src = ops_data['attributes'].get('src')
                            if uuid:
                                images_found.append({
                                    'uuid': uuid,
                                    'src': src,
                                    'width': ops_data['attributes'].get('width'),
                                })
                        
                        # 递归搜索子对象
                        for value in ops_data.values():
                            if isinstance(value, (dict, list)):
                                find_images_in_ops(value)
                    elif isinstance(ops_data, list):
                        for item in ops_data:
                            find_images_in_ops(item)
                
                find_images_in_ops(doc_data)
                
                print(f"📊 [TASK] 解析到 {len(images_found)} 张图片")
                
                if not images_found:
                    print(f"ℹ️ [TASK] 富文本字段中未发现图片")
                    execution_log.append("富文本解析: 未发现图片内容")
                    return
                
                # 下载每张图片
                from app.services.image_download_service import FeishuImageDownloadService
                download_service = FeishuImageDownloadService()
                
                for i, img_info in enumerate(images_found):
                    try:
                        img_uuid = img_info['uuid']
                        print(f"📥 [TASK] 下载图片 {i+1}/{len(images_found)}: {img_uuid}")
                        
                        # 使用附件下载API
                        download_result = await download_service.download_attachment_with_auto_auth(
                            project_key=project_key,
                            work_item_type_key=work_item_type_key,
                            work_item_id=work_item_id,
                            file_uuid=img_uuid,
                            plugin_id=fixed_api_config["plugin_id"],
                            plugin_secret=fixed_api_config["plugin_secret"],
                            user_key=fixed_api_config["user_key"],
                            save_to_file=False  # 不保存文件，直接获取base64数据
                        )
                        
                        if download_result.get('success') and download_result.get('image_data_base64'):
                            # 添加到图片列表
                            rich_text_images.append({
                                "uuid": img_uuid,
                                "base64": download_result['image_data_base64'],
                                "size": download_result.get('actual_size', 0),
                                "type": download_result.get('content_type', 'image/png'),
                                "source": "rich_text_field",
                                "src": img_info.get('src', ''),
                                "width": img_info.get('width')
                            })
                            print(f"✅ [TASK] 图片下载成功: {img_uuid}, 大小: {download_result.get('actual_size', 0)} bytes")
                        else:
                            print(f"❌ [TASK] 图片下载失败: {img_uuid} - {download_result.get('error', '未知错误')}")
                            
                    except Exception as img_error:
                        print(f"❌ [TASK] 处理图片 {img_info.get('uuid', 'unknown')} 失败: {img_error}")
                        logger.warning(f"处理富文本图片失败: {img_error}")
                        continue
                        
                print(f"📊 [TASK] 富文本解析完成: 成功处理 {len(rich_text_images)} 张图片")
                execution_log.append(f"富文本解析: 成功处理 {len(rich_text_images)} 张图片")
                        
            except json.JSONDecodeError as json_error:
                print(f"❌ [TASK] 富文本doc内容JSON解析失败: {json_error}")
                execution_log.append(f"富文本解析: JSON解析失败 - {json_error}")
                
        except Exception as parse_error:
            print(f"❌ [TASK] 富文本图片解析异常: {parse_error}")
            logger.error(f"富文本图片解析异常: {parse_error}")
            execution_log.append(f"富文本解析: 解析异常 - {parse_error}")

    async def _query_additional_fields(
        self,
        task: AnalysisTask,
        payload_data: Dict[str, Any],
        execution_log: list
    ) -> Dict[str, Any]:
        """
        查询任务配置的额外字段

        Args:
            task: 分析任务对象
            payload_data: webhook原始数据
            execution_log: 执行日志列表

        Returns:
            字段数据字典
        """
        try:
            # 解析多字段配置
            multi_field_config = task.multi_field_config
            if not multi_field_config or 'fields' not in multi_field_config:
                return {}

            field_configs = multi_field_config['fields']
            if not field_configs:
                return {}

            # 提取webhook基础信息
            payload = payload_data.get('payload', {})
            project_key = payload.get('project_key')
            work_item_type_key = payload.get('work_item_type_key')
            work_item_id = str(payload.get('id', ''))

            if not all([project_key, work_item_type_key, work_item_id]):
                logger.warning("多字段查询: 缺少必要的项目信息")
                return {}

            # 获取飞书API配置
            import os
            plugin_id = os.getenv("FEISHU_PLUGIN_ID", "")
            plugin_secret = os.getenv("FEISHU_PLUGIN_SECRET", "")
            user_key = os.getenv("FEISHU_USER_KEY", "")

            if not all([plugin_id, plugin_secret]):
                logger.warning("多字段查询: 飞书API配置缺失")
                return {}

            # 使用飞书服务查询多字段
            from app.services.feishu_service import FeishuProjectAPI

            feishu_api = FeishuProjectAPI(
                host="https://project.feishu.cn",
                app_id=plugin_id,
                app_secret=plugin_secret,
                user_id=user_key
            )

            # 提取要查询的字段列表
            field_keys = [field_config['field_key'] for field_config in field_configs]

            async with feishu_api:
                # 获取plugin token
                plugin_token = await feishu_api.get_plugin_token(plugin_id, plugin_secret)

                # 查询多字段
                query_result = await feishu_api.query_multiple_fields(
                    project_key=project_key,
                    work_item_type_key=work_item_type_key,
                    work_item_id=work_item_id,
                    field_keys=field_keys,
                    plugin_token=plugin_token,
                    user_key=user_key
                )

                if query_result.get('success'):
                    field_values = query_result.get('field_values', {})

                    # 将field_key映射为placeholder名称
                    placeholder_data = {}
                    for field_config in field_configs:
                        field_key = field_config['field_key']
                        placeholder = field_config['placeholder']

                        if field_key in field_values:
                            # 处理不同类型的字段值
                            field_value = field_values[field_key]
                            if isinstance(field_value, dict):
                                # 复杂字段类型，提取文本内容
                                if field_value.get('type') == 'rich_text':
                                    placeholder_data[placeholder] = field_value.get('doc_text', '')
                                elif field_value.get('type') == 'user':
                                    users = field_value.get('users', [])
                                    placeholder_data[placeholder] = ', '.join([user.get('name', '') for user in users])
                                elif field_value.get('type') == 'relation':
                                    relations = field_value.get('relations', [])
                                    placeholder_data[placeholder] = ', '.join([rel.get('name', '') for rel in relations])
                                else:
                                    placeholder_data[placeholder] = str(field_value)
                            else:
                                # 简单字段类型
                                placeholder_data[placeholder] = str(field_value) if field_value is not None else ''
                        else:
                            placeholder_data[placeholder] = ''

                    print(f"✅ [TASK] 多字段查询成功: {placeholder_data}")
                    return placeholder_data

                else:
                    logger.error(f"多字段查询失败: {query_result}")
                    return {}

        except Exception as e:
            logger.error(f"多字段查询异常: {e}")
            return {}

    def _extract_rich_text_content(self, field_value: Any) -> str:
        """
        从富文本字段值中提取纯文本内容

        Args:
            field_value: 富文本字段值，可能是字符串或复杂对象

        Returns:
            提取的纯文本内容
        """
        try:
            if not field_value:
                return ""

            # 如果是字符串，直接返回
            if isinstance(field_value, str):
                # 尝试解析是否为JSON格式的富文本
                try:
                    import json
                    rich_data = json.loads(field_value)
                    return self._extract_text_from_rich_json(rich_data)
                except:
                    # 不是JSON，直接返回字符串
                    return field_value

            # 如果是字典对象，提取文本内容
            elif isinstance(field_value, dict):
                # 检查是否有doc字段（富文本格式）
                if 'doc' in field_value:
                    doc_content = field_value['doc']
                    if isinstance(doc_content, str):
                        try:
                            import json
                            doc_data = json.loads(doc_content)
                            return self._extract_text_from_rich_json(doc_data)
                        except:
                            return doc_content
                    elif isinstance(doc_content, dict):
                        return self._extract_text_from_rich_json(doc_content)

                # 检查是否有doc_text字段（纯文本提取）
                elif 'doc_text' in field_value:
                    return str(field_value['doc_text'])

                # 其他情况，转换为字符串
                else:
                    return str(field_value)

            # 其他类型，直接转换为字符串
            else:
                return str(field_value)

        except Exception as e:
            logger.warning(f"富文本内容提取失败: {e}")
            return str(field_value) if field_value else ""

    def _extract_text_from_rich_json(self, rich_data: dict) -> str:
        """
        从富文本JSON结构中递归提取纯文本内容

        Args:
            rich_data: 富文本JSON数据

        Returns:
            提取的纯文本
        """
        try:
            text_parts = []

            def extract_from_ops(ops_data):
                if isinstance(ops_data, dict):
                    # 检查是否有insert字段（文本内容）
                    if 'insert' in ops_data and isinstance(ops_data['insert'], str):
                        # 跳过图片等非文本内容
                        attributes = ops_data.get('attributes', {})
                        if not attributes.get('image'):  # 不是图片
                            text_parts.append(ops_data['insert'])

                    # 递归处理子对象
                    for value in ops_data.values():
                        if isinstance(value, (dict, list)):
                            extract_from_ops(value)

                elif isinstance(ops_data, list):
                    for item in ops_data:
                        extract_from_ops(item)

            # 检查ops字段（Delta格式）
            if 'ops' in rich_data:
                extract_from_ops(rich_data['ops'])
            else:
                # 直接处理整个数据
                extract_from_ops(rich_data)

            # 合并文本并清理
            result = ''.join(text_parts).strip()
            # 清理多余的换行符
            import re
            result = re.sub(r'\n\s*\n', '\n', result)

            return result

        except Exception as e:
            logger.warning(f"富文本JSON解析失败: {e}")
            return ""

    def _render_template_with_fields(self, template: str, field_data: Dict[str, Any]) -> str:
        """
        使用字段数据渲染提示词模板

        Args:
            template: 提示词模板，包含 {字段占位符} 格式的占位符
            field_data: 字段数据字典，键为占位符名称，值为字段值

        Returns:
            渲染后的提示词
        """
        try:
            import re

            rendered_template = template

            # 处理字段占位符 {placeholder_name}
            for placeholder, value in field_data.items():
                # 转换为安全的字符串
                safe_value = str(value) if value is not None else ''
                # 替换占位符
                rendered_template = rendered_template.replace(f'{{{placeholder}}}', safe_value)

            # 清理未匹配的占位符（可选）
            # rendered_template = re.sub(r'\{[^}]+\}', '[未找到字段]', rendered_template)

            return rendered_template

        except Exception as e:
            logger.error(f"模板渲染失败: {e}")
            return template

    async def _validate_webhook_execution(
        self,
        payload_data: Dict[str, Any],
        analysis_tasks: list,
        execution_id: str,
        execution_log: list
    ) -> Dict[str, Any]:
        """
        验证Webhook是否应该执行任务，防止重复执行

        Args:
            payload_data: Webhook载荷数据
            analysis_tasks: 要执行的分析任务列表
            execution_id: 当前执行ID
            execution_log: 执行日志列表

        Returns:
            验证结果字典，包含 should_execute, skip_reason, details
        """
        try:
            print(f"🔍 [VALIDATION] 开始执行预检查验证...")

            # 从payload中提取关键数据
            record_id = None
            field_value = None
            if isinstance(payload_data, dict) and "payload" in payload_data:
                inner_payload = payload_data["payload"]
                if isinstance(inner_payload, dict):
                    record_id = inner_payload.get("id")
                    changed_fields = inner_payload.get("changed_fields", [])
                    if isinstance(changed_fields, list) and len(changed_fields) > 0:
                        field_value = changed_fields[0].get("cur_field_value")

            print(f"📊 [VALIDATION] 提取数据: record_id={record_id}, field_value={'已获取' if field_value else '未获取'}")

            # 验证1: 富文本解析检查
            for task in analysis_tasks:
                if task.enable_rich_text_parsing:
                    print(f"🖼️ [VALIDATION] 检查任务 {task.name} 的富文本解析配置...")

                    # 检查是否有有效的富文本内容
                    if not field_value:
                        skip_reason = f"富文本解析已启用但字段值为空 (任务: {task.name})"
                        print(f"⚠️ [VALIDATION] {skip_reason}")
                        execution_log.append(f"验证失败: {skip_reason}")

                        return {
                            "should_execute": False,
                            "skip_reason": skip_reason,
                            "details": {
                                "validation_type": "rich_text_empty",
                                "task_id": task.id,
                                "task_name": task.name,
                                "record_id": record_id,
                                "field_value_present": False
                            }
                        }

                    # 检查富文本内容中是否包含图片
                    has_images = await self._check_rich_text_has_images(field_value, task, payload_data)
                    print(f"🔍 [VALIDATION] 富文本图片检查结果: has_images={has_images}")

                    if not has_images:
                        skip_reason = f"富文本解析已启用但内容中无图片 (任务: {task.name})"
                        print(f"⚠️ [VALIDATION] {skip_reason}")
                        execution_log.append(f"验证失败: {skip_reason}")

                        return {
                            "should_execute": False,
                            "skip_reason": skip_reason,
                            "details": {
                                "validation_type": "rich_text_no_images",
                                "task_id": task.id,
                                "task_name": task.name,
                                "record_id": record_id,
                                "field_value_present": True,
                                "images_found": False
                            }
                        }

            # 验证2: 重复执行检查
            if record_id:
                print(f"🔄 [VALIDATION] 检查record_id={record_id}的重复执行情况...")

                # 查询是否有相同record_id的任务正在执行中
                from app.models.task_execution_simple import TaskExecution, ExecutionStatus
                from sqlalchemy import and_

                # 检查所有正在执行的任务中是否有相同的record_id
                running_executions = self.db.query(TaskExecution).filter(
                    and_(
                        TaskExecution.execution_status.in_([ExecutionStatus.PENDING, ExecutionStatus.PROCESSING]),
                        TaskExecution.webhook_payload.is_not(None)
                    )
                ).all()

                conflicting_executions = []
                for exec_record in running_executions:
                    if exec_record.webhook_payload and isinstance(exec_record.webhook_payload, dict):
                        exec_payload = exec_record.webhook_payload.get("payload", {})
                        if isinstance(exec_payload, dict) and exec_payload.get("id") == record_id:
                            # 排除当前执行
                            if exec_record.execution_id != execution_id:
                                conflicting_executions.append(exec_record)

                print(f"📊 [VALIDATION] 发现 {len(conflicting_executions)} 个冲突的执行记录")

                if conflicting_executions:
                    conflict_info = []
                    for conflict in conflicting_executions:
                        conflict_info.append({
                            "execution_id": conflict.execution_id,
                            "task_id": conflict.task_id,
                            "status": conflict.execution_status.value,
                            "started_at": conflict.started_at.isoformat() if conflict.started_at else None
                        })

                    skip_reason = f"检测到record_id={record_id}的任务正在执行中，避免重复处理"
                    print(f"⚠️ [VALIDATION] {skip_reason}")
                    execution_log.append(f"验证失败: {skip_reason}")

                    return {
                        "should_execute": False,
                        "skip_reason": skip_reason,
                        "details": {
                            "validation_type": "duplicate_execution",
                            "record_id": record_id,
                            "conflicting_executions": conflict_info,
                            "conflict_count": len(conflicting_executions)
                        }
                    }

            # 所有验证通过
            print(f"✅ [VALIDATION] 预检查验证通过，可以执行任务")
            execution_log.append("预检查验证: 通过")

            return {
                "should_execute": True,
                "skip_reason": None,
                "details": {
                    "validation_type": "passed",
                    "record_id": record_id,
                    "rich_text_tasks_count": sum(1 for task in analysis_tasks if task.enable_rich_text_parsing),
                    "all_validations_passed": True
                }
            }

        except Exception as e:
            error_msg = f"预检查验证异常: {str(e)}"
            print(f"❌ [VALIDATION] {error_msg}")
            logger.error(error_msg, exc_info=True)
            execution_log.append(error_msg)

            # 验证异常时允许执行，避免阻塞正常流程
            return {
                "should_execute": True,
                "skip_reason": None,
                "details": {
                    "validation_type": "error",
                    "error": error_msg
                }
            }

    async def _check_rich_text_has_images(
        self,
        field_value: Any,
        task: AnalysisTask,
        payload_data: Dict[str, Any]
    ) -> bool:
        """
        检查富文本字段值中是否包含图片

        Args:
            field_value: 富文本字段值
            task: 分析任务对象
            payload_data: 完整的webhook载荷数据

        Returns:
            bool: 是否包含图片
        """
        try:
            if not field_value:
                return False

            # 如果是字符串，尝试解析为JSON
            if isinstance(field_value, str):
                try:
                    import json
                    field_data = json.loads(field_value)
                except json.JSONDecodeError:
                    # 不是JSON格式，检查是否包含图片相关的文本标识
                    return any(keyword in field_value.lower() for keyword in ['image', 'img', '图片', '图像'])
            else:
                field_data = field_value

            # 检查富文本结构中的图片信息
            if isinstance(field_data, dict):
                # 检查doc字段（富文本格式）
                if 'doc' in field_data:
                    doc_content = field_data['doc']
                    if isinstance(doc_content, str):
                        try:
                            import json
                            doc_data = json.loads(doc_content)
                        except json.JSONDecodeError:
                            return False
                    else:
                        doc_data = doc_content

                    # 递归搜索ops中的image属性
                    if isinstance(doc_data, dict) and 'ops' in doc_data:
                        return self._search_images_in_ops(doc_data['ops'])

            return False

        except Exception as e:
            logger.warning(f"检查富文本图片时发生异常: {e}")
            # 异常时返回True，避免误判
            return True

    def _search_images_in_ops(self, ops_data) -> bool:
        """
        在ops数据结构中递归搜索图片

        Args:
            ops_data: ops数据结构

        Returns:
            bool: 是否找到图片
        """
        try:
            if isinstance(ops_data, dict):
                # 检查是否有image属性
                if ops_data.get('attributes', {}).get('image') == 'true':
                    return True

                # 递归检查子对象
                for value in ops_data.values():
                    if isinstance(value, (dict, list)):
                        if self._search_images_in_ops(value):
                            return True

            elif isinstance(ops_data, list):
                for item in ops_data:
                    if self._search_images_in_ops(item):
                        return True

            return False

        except Exception as e:
            logger.warning(f"搜索ops中的图片时发生异常: {e}")
            return True  # 异常时返回True，避免误判


# 全局任务处理函数（供FastAPI BackgroundTasks使用）
async def process_webhook_async(
    webhook_id: int,
    payload_data: Dict[str, Any],
    execution_id: str,
    client_ip: str,
    user_agent: str
) -> Dict[str, Any]:
    """
    异步处理Webhook任务
    这是被FastAPI BackgroundTasks调用的入口函数
    """
    print(f"\n🚀 [DEBUG] 开始异步处理Webhook任务")
    print(f"   - Webhook ID: {webhook_id}")
    print(f"   - 执行ID: {execution_id}")
    print(f"   - 客户端IP: {client_ip}")
    print(f"   - Payload大小: {len(str(payload_data))} 字符")
    
    try:
        with WebhookTaskProcessor() as processor:
            print(f"✅ [DEBUG] WebhookTaskProcessor 创建成功")
            
            result = await processor.process_webhook_task(
                webhook_id=webhook_id,
                payload_data=payload_data,
                execution_id=execution_id,
                client_ip=client_ip,
                user_agent=user_agent
            )
            
            print(f"🎉 [DEBUG] 异步任务处理完成 {execution_id}: 成功={result['success']}")
            logger.info(f"异步任务处理完成 {execution_id}: {result['success']}")
            return result
            
    except Exception as e:
        print(f"❌ [DEBUG] 异步任务处理异常 {execution_id}: {e}")
        print(f"   - 异常类型: {type(e).__name__}")
        import traceback
        print(f"   - 异常堆栈: {traceback.format_exc()}")
        
        logger.error(f"异步任务处理异常 {execution_id}: {e}", exc_info=True)
        
        return {
            "success": False,
            "execution_id": execution_id,
            "webhook_id": webhook_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }