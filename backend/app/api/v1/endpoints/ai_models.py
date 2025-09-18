from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from app.core.database import get_db
from app.models.ai_model import AIModel, ModelType
from app.schemas.ai_model import (
    AIModelCreate,
    AIModelUpdate,
    AIModelResponse,
    AIModelTest,
    AIModelTestResponse,
    AIModelHealthCheck,
    AIModelUsage,
    AIModelStats,
    AIModelBatchTest,
    AIModelBatchTestResponse
)
from app.services.ai_service import AIService
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

# AI服务实例
ai_service = AIService()


@router.get("/")
async def get_ai_models(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(100, ge=1, le=1000, description="每页记录数"),
    active_only: bool = Query(False, description="仅返回激活的模型"),
    model_type: Optional[str] = Query(None, description="模型类型过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序顺序"),
    db: Session = Depends(get_db)
):
    """获取AI模型列表"""
    try:
        logger.info(f"获取AI模型列表，页码: {page}, 每页: {size}")
        
        query = db.query(AIModel)
        
        # 过滤条件
        if active_only:
            query = query.filter(AIModel.is_active == True)
        
        if model_type:
            try:
                model_type_enum = ModelType(model_type)
                query = query.filter(AIModel.model_type == model_type_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的模型类型: {model_type}")
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                AIModel.name.ilike(search_pattern) |
                AIModel.display_name.ilike(search_pattern) |
                AIModel.description.ilike(search_pattern)
            )
        
        # 排序
        if hasattr(AIModel, sort_by):
            order_column = getattr(AIModel, sort_by)
            if sort_order.lower() == "asc":
                query = query.order_by(asc(order_column))
            else:
                query = query.order_by(desc(order_column))
        
        # 获取总数
        total = query.count()
        
        # 分页
        skip = (page - 1) * size
        models = query.offset(skip).limit(size).all()
        
        # 转换为响应格式
        items = []
        for model in models:
            model_dict = model.to_dict(include_sensitive=False)
            # 映射字段到响应模式
            response_data = {
                **model_dict,
                "total_tokens": model_dict["total_tokens_used"],
                "total_cost": float(model_dict["total_cost"]) if model_dict["total_cost"] else 0.0
            }
            items.append(response_data)
        
        # 计算总页数
        pages = (total + size - 1) // size if total > 0 else 0
        
        result = {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }
        
        logger.info(f"成功返回 {len(items)} 个AI模型，总数: {total}")
        return result
        
    except Exception as e:
        logger.error(f"获取AI模型列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取AI模型列表失败")


@router.post("/", response_model=AIModelResponse)
async def create_ai_model(
    model_data: AIModelCreate,
    db: Session = Depends(get_db)
):
    """创建AI模型"""
    try:
        logger.info(f"创建AI模型: {model_data.name}")
        
        # 检查名称是否已存在
        existing_model = db.query(AIModel).filter(AIModel.name == model_data.name).first()
        if existing_model:
            raise HTTPException(status_code=400, detail="模型名称已存在")
        
        # 如果设置为默认模型，取消其他模型的默认状态
        if model_data.is_default:
            db.query(AIModel).filter(AIModel.is_default == True).update({"is_default": False})
        
        # 创建模型实例，直接使用传入的模型类型
        db_model = AIModel(
            name=model_data.name,
            display_name=model_data.name,  # 如果没有单独的display_name
            model_type=model_data.model_type,  # 直接使用用户选择的类型
            api_endpoint=model_data.api_endpoint,
            api_key=model_data.api_key,
            model_name=model_data.model_name,
            temperature=str(model_data.temperature),
            top_p=str(model_data.top_p),
            frequency_penalty=str(model_data.frequency_penalty),
            presence_penalty=str(model_data.presence_penalty),
            default_params=model_data.default_params,
            supports_streaming=model_data.supports_streaming,
            supports_function_calling=model_data.supports_function_calling,
            supports_vision=model_data.supports_vision,
            supports_multimodal=model_data.supports_multimodal,
            rate_limit_per_minute=model_data.rate_limit_rpm,
            rate_limit_per_day=model_data.rate_limit_rpd,
            cost_per_1k_input_tokens=str(model_data.cost_per_input_token) if model_data.cost_per_input_token else None,
            cost_per_1k_output_tokens=str(model_data.cost_per_output_token) if model_data.cost_per_output_token else None,
            is_active=model_data.is_active,
            is_default=model_data.is_default,
            description=model_data.description,
            usage_notes=model_data.usage_notes
        )
        
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
        
        # 异步健康检查
        # 这里可以添加后台任务进行健康检查
        
        logger.info(f"AI模型创建成功: {db_model.id}")
        
        # 返回响应
        model_dict = db_model.to_dict(include_sensitive=False)
        response_data = {
            **model_dict,
            "total_tokens": model_dict["total_tokens_used"],
            "total_cost": float(model_dict["total_cost"]) if model_dict["total_cost"] else 0.0
        }
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建AI模型失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建AI模型失败: {str(e)}")


@router.get("/{model_id}", response_model=AIModelResponse)
async def get_ai_model(
    model_id: int,
    include_stats: bool = Query(False, description="包含统计信息"),
    db: Session = Depends(get_db)
):
    """获取指定AI模型"""
    try:
        model = db.query(AIModel).filter(AIModel.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="AI模型不存在")
        
        model_dict = model.to_dict(include_sensitive=False)
        response_data = {
            **model_dict,
            "total_tokens": model_dict["total_tokens_used"],
            "total_cost": float(model_dict["total_cost"]) if model_dict["total_cost"] else 0.0
        }
        
        logger.info(f"成功获取AI模型: {model_id}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取AI模型失败: {e}")
        raise HTTPException(status_code=500, detail="获取AI模型失败")


@router.put("/{model_id}", response_model=AIModelResponse)
async def update_ai_model(
    model_id: int,
    model_data: AIModelUpdate,
    db: Session = Depends(get_db)
):
    """更新AI模型"""
    try:
        model = db.query(AIModel).filter(AIModel.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="AI模型不存在")
        
        logger.info(f"更新AI模型: {model_id}")
        
        # 如果设置为默认模型，取消其他模型的默认状态
        if model_data.is_default:
            db.query(AIModel).filter(
                AIModel.is_default == True, 
                AIModel.id != model_id
            ).update({"is_default": False})
        
        # 更新字段
        update_data = model_data.dict(exclude_unset=True)

        # API密钥处理：如果为空字符串或None，则不更新（保持原有密钥）
        if 'api_key' in update_data:
            if not update_data['api_key'] or update_data['api_key'].strip() == '':
                del update_data['api_key']  # 删除空密钥，保持原有密钥不变

        # API密钥直接保存，无需加密
        
        # 映射字段名称
        field_mapping = {
            "rate_limit_rpm": "rate_limit_per_minute",
            "rate_limit_rpd": "rate_limit_per_day",
            "cost_per_input_token": "cost_per_1k_input_tokens",
            "cost_per_output_token": "cost_per_1k_output_tokens"
        }
        
        for old_field, new_field in field_mapping.items():
            if old_field in update_data:
                if old_field.startswith("cost_") and update_data[old_field] is not None:
                    update_data[new_field] = str(update_data[old_field])
                else:
                    update_data[new_field] = update_data[old_field]
                del update_data[old_field]
        
        # 转换数字字段为字符串（适应数据库模型）
        string_fields = ["temperature", "top_p", "frequency_penalty", "presence_penalty"]
        for field in string_fields:
            if field in update_data and update_data[field] is not None:
                update_data[field] = str(update_data[field])
        
        # 更新模型
        for field, value in update_data.items():
            if hasattr(model, field):
                setattr(model, field, value)
        
        db.commit()
        db.refresh(model)
        
        logger.info(f"AI模型更新成功: {model_id}")
        
        # 返回响应
        model_dict = model.to_dict(include_sensitive=False)
        response_data = {
            **model_dict,
            "total_tokens": model_dict["total_tokens_used"],
            "total_cost": float(model_dict["total_cost"]) if model_dict["total_cost"] else 0.0
        }
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新AI模型失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新AI模型失败: {str(e)}")


@router.delete("/{model_id}")
async def delete_ai_model(
    model_id: int,
    force: bool = Query(False, description="强制删除"),
    db: Session = Depends(get_db)
):
    """删除AI模型"""
    try:
        model = db.query(AIModel).filter(AIModel.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="AI模型不存在")
        
        # 检查是否为默认模型
        if model.is_default and not force:
            raise HTTPException(status_code=400, detail="不能删除默认模型，请先设置其他模型为默认")
        
        # 这里可以检查是否有关联的任务正在使用此模型
        # 如果有，根据force参数决定是否允许删除
        
        logger.info(f"删除AI模型: {model_id}")
        
        db.delete(model)
        db.commit()
        
        logger.info(f"AI模型删除成功: {model_id}")
        return {"message": "AI模型删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除AI模型失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除AI模型失败: {str(e)}")


@router.post("/{model_id}/test", response_model=AIModelTestResponse)
async def test_ai_model(
    model_id: int,
    test_data: AIModelTest,
    db: Session = Depends(get_db)
):
    """测试AI模型"""
    try:
        model = db.query(AIModel).filter(AIModel.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="AI模型不存在")
        
        if not model.is_active:
            raise HTTPException(status_code=400, detail="模型未激活")
        
        logger.info(f"测试AI模型: {model_id}")
        
        # 获取API密钥
        api_key = model.api_key
        
        # 使用AI服务进行测试
        start_time = datetime.utcnow()
        
        try:
            # 这里需要根据模型类型调用不同的AI服务
            if "gemini" in model.model_name.lower():
                response_text, token_usage = await ai_service.test_gemini_model(
                    api_key=api_key,
                    model_name=model.model_name,
                    prompt=test_data.prompt,
                    max_tokens=test_data.max_tokens or 4000,  # 使用默认值
                    temperature=test_data.temperature or float(model.temperature),
                    stream=test_data.stream
                )
            else:
                # 其他模型类型的处理
                response_text, token_usage = await ai_service.test_generic_model(
                    api_endpoint=model.api_endpoint,
                    api_key=api_key,
                    model_name=model.model_name,
                    prompt=test_data.prompt,
                    max_tokens=test_data.max_tokens or 4000,  # 使用默认值
                    temperature=test_data.temperature or float(model.temperature)
                )
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000  # 转换为毫秒
            
            # 计算成本
            cost = model.calculate_cost(
                token_usage.get("input_tokens", 0),
                token_usage.get("output_tokens", 0)
            )
            
            # 更新模型使用统计
            model.update_usage_stats(
                tokens_used=token_usage.get("total_tokens", 0),
                cost=cost
            )
            model.health_status = "healthy"
            model.health_message = "模型测试成功"
            model.last_health_check = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"AI模型测试成功: {model_id}")
            
            return AIModelTestResponse(
                success=True,
                response=response_text,
                input_tokens=token_usage.get("input_tokens"),
                output_tokens=token_usage.get("output_tokens"),
                total_tokens=token_usage.get("total_tokens"),
                cost=cost,
                response_time=response_time,
                tested_at=end_time
            )
            
        except Exception as ai_error:
            # AI调用失败
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # 更新健康状态
            model.health_status = "unhealthy"
            model.health_message = str(ai_error)
            model.last_health_check = datetime.utcnow()
            
            db.commit()
            
            logger.error(f"AI模型测试失败: {model_id}, 错误: {ai_error}")
            
            return AIModelTestResponse(
                success=False,
                response=None,
                error_message=str(ai_error),
                response_time=response_time,
                tested_at=end_time
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试AI模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"测试AI模型失败: {str(e)}")


@router.post("/{model_id}/health-check", response_model=AIModelHealthCheck)
async def health_check_ai_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """AI模型健康检查"""
    try:
        model = db.query(AIModel).filter(AIModel.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="AI模型不存在")
        
        logger.info(f"健康检查AI模型: {model_id}")
        
        start_time = datetime.utcnow()
        
        try:
            # 使用简单的提示进行健康检查
            test_prompt = "Hello, please respond with 'OK' to confirm you are working."
            
            # 获取API密钥
            api_key = model.api_key
            
            # 执行简单测试
            if "gemini" in model.model_name.lower():
                response_text, _ = await ai_service.test_gemini_model(
                    api_key=api_key,
                    model_name=model.model_name,
                    prompt=test_prompt,
                    max_tokens=10,
                    temperature=0.1
                )
            else:
                response_text, _ = await ai_service.test_generic_model(
                    api_endpoint=model.api_endpoint,
                    api_key=api_key,
                    model_name=model.model_name,
                    prompt=test_prompt,
                    max_tokens=10,
                    temperature=0.1
                )
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # 更新健康状态
            model.health_status = "healthy"
            model.health_message = "健康检查通过"
            model.last_health_check = end_time
            
            db.commit()
            
            logger.info(f"AI模型健康检查成功: {model_id}")
            
            return AIModelHealthCheck(
                model_id=model_id,
                status="healthy",
                response_time=response_time,
                checked_at=end_time
            )
            
        except Exception as health_error:
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # 更新健康状态
            model.health_status = "unhealthy"
            model.health_message = str(health_error)
            model.last_health_check = end_time
            
            db.commit()
            
            logger.error(f"AI模型健康检查失败: {model_id}, 错误: {health_error}")
            
            return AIModelHealthCheck(
                model_id=model_id,
                status="unhealthy",
                response_time=response_time,
                error_message=str(health_error),
                checked_at=end_time
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.post("/test-connection", response_model=AIModelTestResponse)
async def test_connection(
    test_data: AIModelTest,
    db: Session = Depends(get_db)
):
    """测试AI模型连接"""
    try:
        # 从测试数据中获取必要信息
        model_id = getattr(test_data, 'model_id', None)
        if not model_id:
            # 如果没有模型ID，从请求数据中获取模型配置信息直接测试
            if not all([test_data.api_endpoint, test_data.api_key, test_data.model_name]):
                raise HTTPException(status_code=400, detail="缺少必需的模型配置信息")
            
            logger.info(f"直接测试AI模型连接: {test_data.model_name}")
            
            start_time = datetime.utcnow()
            
            try:
                # 根据模型名称判断类型
                proxy_url = getattr(test_data, 'proxy_url', None)
                
                if "gemini" in test_data.model_name.lower():
                    response_text, token_usage = await ai_service.test_gemini_model(
                        api_key=test_data.api_key,
                        model_name=test_data.model_name,
                        prompt=test_data.prompt,
                        max_tokens=test_data.max_tokens or 4000,
                        temperature=test_data.temperature or 0.7,
                        stream=test_data.stream,
                        proxy_url=proxy_url
                    )
                else:
                    response_text, token_usage = await ai_service.test_generic_model(
                        api_endpoint=test_data.api_endpoint,
                        api_key=test_data.api_key,
                        model_name=test_data.model_name,
                        prompt=test_data.prompt,
                        max_tokens=test_data.max_tokens or 4000,
                        temperature=test_data.temperature or 0.7,
                        proxy_url=proxy_url
                    )
                
                end_time = datetime.utcnow()
                response_time = (end_time - start_time).total_seconds() * 1000
                
                logger.info(f"AI模型连接测试成功: {test_data.model_name}")
                
                return AIModelTestResponse(
                    success=True,
                    response=response_text,
                    input_tokens=token_usage.get("input_tokens"),
                    output_tokens=token_usage.get("output_tokens"),
                    total_tokens=token_usage.get("total_tokens"),
                    cost=0.0,  # 直接测试不计算成本
                    response_time=response_time,
                    tested_at=end_time
                )
                
            except Exception as ai_error:
                end_time = datetime.utcnow()
                response_time = (end_time - start_time).total_seconds() * 1000
                
                logger.error(f"AI模型连接测试失败: {test_data.model_name}, 错误: {ai_error}")
                
                return AIModelTestResponse(
                    success=False,
                    response=None,
                    error_message=str(ai_error),
                    response_time=response_time,
                    tested_at=end_time
                )
        else:
            # 如果有模型ID，使用现有的test端点逻辑
            return await test_ai_model(model_id, test_data, db)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试连接失败: {e}")
        raise HTTPException(status_code=500, detail=f"测试连接失败: {str(e)}")


@router.get("/stats/summary", response_model=AIModelStats)
async def get_ai_models_stats(
    db: Session = Depends(get_db)
):
    """获取AI模型统计信息"""
    try:
        logger.info("获取AI模型统计信息")
        
        total_models = db.query(AIModel).count()
        active_models = db.query(AIModel).filter(AIModel.is_active == True).count()
        
        # 聚合统计
        models = db.query(AIModel).all()
        
        total_requests = sum(model.total_requests for model in models)
        total_tokens = sum(model.total_tokens_used for model in models)
        total_cost = sum(float(model.total_cost) if model.total_cost else 0.0 for model in models)
        
        # 找到最常用的模型
        most_used_model = None
        if models:
            most_used = max(models, key=lambda m: m.total_requests)
            if most_used.total_requests > 0:
                most_used_model = most_used.name
        
        # 计算成功率（简化版本）
        healthy_models = sum(1 for model in models if model.is_healthy())
        success_rate = (healthy_models / total_models * 100) if total_models > 0 else 0.0
        
        logger.info("成功获取AI模型统计信息")
        
        return AIModelStats(
            total_models=total_models,
            active_models=active_models,
            total_requests=total_requests,
            total_tokens=total_tokens,
            total_cost=total_cost,
            success_rate=success_rate,
            most_used_model=most_used_model
        )
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")