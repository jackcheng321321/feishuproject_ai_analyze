"""系统配置管理API端点

提供完整的系统配置管理功能，包括CRUD操作、验证、导入导出、统计等。
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import logging
import json
import yaml
import configparser
from io import StringIO
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_active_user
from app.models.user import User
from app.models.system_config import SystemConfig, ConfigType, ConfigCategory
from app.schemas.system_config import (
    SystemConfigCreate,
    SystemConfigUpdate, 
    SystemConfigResponse,
    SystemConfigPublicResponse,
    SystemConfigValue,
    SystemConfigValidation,
    SystemConfigValidationResponse,
    SystemConfigReset,
    SystemConfigResetResponse,
    SystemConfigExport,
    SystemConfigImport,
    SystemConfigImportResponse,
    SystemConfigStats,
    SystemConfigHealth,
    SystemConfigFilter,
    SystemConfigSort,
    ConfigStatus
)
from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[SystemConfigResponse])
async def get_system_configs(
    request: Request,
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="限制记录数"),
    # 过滤参数
    category: Optional[ConfigCategory] = Query(None, description="配置分类"),
    config_type: Optional[ConfigType] = Query(None, description="配置类型"),
    status: Optional[ConfigStatus] = Query(None, description="配置状态"),
    group: Optional[str] = Query(None, description="配置组"),
    environment: Optional[str] = Query(None, description="环境"),
    required: Optional[bool] = Query(None, description="是否必需"),
    sensitive: Optional[bool] = Query(None, description="是否敏感"),
    encrypted: Optional[bool] = Query(None, description="是否加密"),
    readonly: Optional[bool] = Query(None, description="是否只读"),
    system: Optional[bool] = Query(None, description="是否系统配置"),
    public: Optional[bool] = Query(None, description="是否公开"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    # 排序参数
    sort_field: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序顺序"),
    # 依赖
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取系统配置列表"""
    
    try:
        # 构建查询
        query = db.query(SystemConfig)
        
        # 应用过滤条件
        filters = []
        
        if category:
            filters.append(SystemConfig.category == category)
        
        if config_type:
            filters.append(SystemConfig.config_type == config_type)
            
        if status:
            if status == ConfigStatus.ACTIVE:
                filters.append(SystemConfig.is_active == True)
                filters.append(SystemConfig.is_deprecated == False)
            elif status == ConfigStatus.DEPRECATED:
                filters.append(SystemConfig.is_deprecated == True)
            elif status == ConfigStatus.DISABLED:
                filters.append(SystemConfig.is_active == False)
        
        if group:
            filters.append(SystemConfig.group_name == group)
            
        if environment:
            filters.append(or_(
                SystemConfig.environment == environment,
                SystemConfig.environment == "all"
            ))
        
        # 属性过滤
        if required is not None:
            filters.append(SystemConfig.is_required == required)
        
        if sensitive is not None:
            filters.append(SystemConfig.is_sensitive == sensitive)
            
        if encrypted is not None:
            filters.append(SystemConfig.is_encrypted == encrypted)
            
        if readonly is not None:
            filters.append(SystemConfig.is_readonly == readonly)
            
        if system is not None:
            filters.append(SystemConfig.is_system == system)
            
        if public is not None:
            filters.append(SystemConfig.is_public == public)
        
        # 搜索过滤
        if search:
            search_filter = or_(
                SystemConfig.key.ilike(f"%{search}%"),
                SystemConfig.name.ilike(f"%{search}%"),
                SystemConfig.display_name.ilike(f"%{search}%"),
                SystemConfig.description.ilike(f"%{search}%")
            )
            filters.append(search_filter)
        
        # 应用过滤条件
        if filters:
            query = query.filter(and_(*filters))
        
        # 排序
        sort_column = getattr(SystemConfig, sort_field, SystemConfig.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # 分页
        configs = query.offset(skip).limit(limit).all()
        
        # 转换为响应格式
        result = []
        for config in configs:
            config_dict = config.to_dict(
                include_sensitive=(not config.is_sensitive),
                include_metadata=True
            )
            result.append(SystemConfigResponse(**config_dict))
        
        return result
        
    except Exception as e:
        logger.error(f"获取系统配置列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统配置列表失败: {str(e)}")


@router.get("/public", response_model=List[SystemConfigPublicResponse])
async def get_public_configs(
    db: Session = Depends(get_db)
):
    """获取公开配置列表（无需认证）"""
    
    try:
        configs = SystemConfig.get_public_configs(db)
        
        result = []
        for config in configs:
            config_dict = config.to_dict(include_sensitive=False)
            result.append(SystemConfigPublicResponse(
                key=config_dict["key"],
                name=config_dict["name"],
                display_name=config_dict["display_name"],
                description=config_dict["description"],
                value=config_dict["value"],
                config_type=config_dict["config_type"],
                category=config_dict["category"],
                required=config_dict["is_required"],
                min_value=config.min_value,
                max_value=config.max_value,
                pattern=config.pattern,
                allowed_values=config.allowed_values,
                group=config_dict["group_name"],
                status=config_dict.get("status", ConfigStatus.ACTIVE)
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"获取公开配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取公开配置失败: {str(e)}")


@router.get("/stats", response_model=SystemConfigStats)
async def get_config_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取系统配置统计信息"""
    
    try:
        # 基础统计
        total_configs = db.query(SystemConfig).count()
        active_configs = db.query(SystemConfig).filter(
            SystemConfig.is_active == True,
            SystemConfig.is_deprecated == False
        ).count()
        deprecated_configs = db.query(SystemConfig).filter(
            SystemConfig.is_deprecated == True
        ).count()
        disabled_configs = db.query(SystemConfig).filter(
            SystemConfig.is_active == False
        ).count()
        
        # 按分类统计
        category_stats = db.query(
            SystemConfig.category,
            func.count(SystemConfig.id)
        ).group_by(SystemConfig.category).all()
        
        configs_by_category = {
            str(category): count for category, count in category_stats
        }
        
        # 按类型统计
        type_stats = db.query(
            SystemConfig.config_type,
            func.count(SystemConfig.id)
        ).group_by(SystemConfig.config_type).all()
        
        configs_by_type = {
            str(config_type): count for config_type, count in type_stats
        }
        
        # 属性统计
        required_configs = db.query(SystemConfig).filter(
            SystemConfig.is_required == True
        ).count()
        sensitive_configs = db.query(SystemConfig).filter(
            SystemConfig.is_sensitive == True
        ).count()
        encrypted_configs = db.query(SystemConfig).filter(
            SystemConfig.is_encrypted == True
        ).count()
        readonly_configs = db.query(SystemConfig).filter(
            SystemConfig.is_readonly == True
        ).count()
        system_configs = db.query(SystemConfig).filter(
            SystemConfig.is_system == True
        ).count()
        public_configs = db.query(SystemConfig).filter(
            SystemConfig.is_public == True
        ).count()
        
        # 访问统计
        total_accesses = db.query(func.sum(SystemConfig.access_count)).scalar() or 0
        
        # 最常访问的配置（前5个）
        most_accessed = db.query(SystemConfig).filter(
            SystemConfig.access_count > 0
        ).order_by(SystemConfig.access_count.desc()).limit(5).all()
        
        most_accessed_configs = []
        for config in most_accessed:
            most_accessed_configs.append({
                "key": config.key,
                "name": config.name,
                "access_count": config.access_count,
                "last_accessed_at": config.last_accessed_at.isoformat() if config.last_accessed_at else None
            })
        
        # 最近更新统计（7天内）
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recently_updated_configs = db.query(SystemConfig).filter(
            SystemConfig.updated_at >= seven_days_ago
        ).count()
        
        # 从未访问的配置
        never_accessed_configs = db.query(SystemConfig).filter(
            or_(
                SystemConfig.access_count == 0,
                SystemConfig.last_accessed_at.is_(None)
            )
        ).count()
        
        return SystemConfigStats(
            total_configs=total_configs,
            active_configs=active_configs,
            deprecated_configs=deprecated_configs,
            disabled_configs=disabled_configs,
            configs_by_category=configs_by_category,
            configs_by_type=configs_by_type,
            required_configs=required_configs,
            sensitive_configs=sensitive_configs,
            encrypted_configs=encrypted_configs,
            readonly_configs=readonly_configs,
            system_configs=system_configs,
            public_configs=public_configs,
            total_accesses=total_accesses,
            most_accessed_configs=most_accessed_configs,
            recently_updated_configs=recently_updated_configs,
            never_accessed_configs=never_accessed_configs
        )
        
    except Exception as e:
        logger.error(f"获取配置统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置统计失败: {str(e)}")


@router.get("/health", response_model=SystemConfigHealth)
async def check_config_health(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """检查系统配置健康状态"""
    
    try:
        total_configs = db.query(SystemConfig).count()
        issues = []
        warnings = []
        recommendations = []
        
        # 检查必需配置是否有值
        required_configs_without_value = db.query(SystemConfig).filter(
            SystemConfig.is_required == True,
            or_(
                SystemConfig.value.is_(None),
                SystemConfig.value == ""
            )
        ).all()
        
        missing_required_configs = len(required_configs_without_value)
        for config in required_configs_without_value:
            issues.append({
                "type": "missing_required",
                "key": config.key,
                "message": f"必需配置 '{config.key}' 缺少值"
            })
        
        # 检查无效配置
        invalid_configs = []
        all_configs = db.query(SystemConfig).all()
        
        for config in all_configs:
            if config.value is not None:
                validation_result = config.validate_value(config.value)
                if not validation_result["valid"]:
                    invalid_configs.append(config)
                    issues.append({
                        "type": "invalid_value",
                        "key": config.key,
                        "message": f"配置 '{config.key}' 值无效: {', '.join(validation_result['errors'])}"
                    })
        
        # 检查弃用配置
        deprecated_configs = db.query(SystemConfig).filter(
            SystemConfig.is_deprecated == True
        ).all()
        
        for config in deprecated_configs:
            warnings.append({
                "type": "deprecated",
                "key": config.key,
                "message": f"配置 '{config.key}' 已弃用: {config.deprecation_message or '建议使用替代方案'}"
            })
        
        # 检查从未访问的配置
        never_accessed_configs = db.query(SystemConfig).filter(
            or_(
                SystemConfig.access_count == 0,
                SystemConfig.last_accessed_at.is_(None)
            )
        ).count()
        
        if never_accessed_configs > 0:
            warnings.append({
                "type": "unused_config",
                "count": never_accessed_configs,
                "message": f"有 {never_accessed_configs} 个配置从未被访问"
            })
        
        # 生成建议
        if missing_required_configs > 0:
            recommendations.append(f"请为 {missing_required_configs} 个必需配置设置值")
        
        if len(invalid_configs) > 0:
            recommendations.append(f"请修复 {len(invalid_configs)} 个无效配置")
        
        if len(deprecated_configs) > 0:
            recommendations.append(f"考虑替换或移除 {len(deprecated_configs)} 个弃用配置")
        
        if never_accessed_configs > total_configs * 0.3:  # 超过30%未使用
            recommendations.append("考虑清理未使用的配置项")
        
        healthy = (missing_required_configs == 0 and len(invalid_configs) == 0)
        
        return SystemConfigHealth(
            healthy=healthy,
            total_configs=total_configs,
            missing_required_configs=missing_required_configs,
            invalid_configs=len(invalid_configs),
            deprecated_configs=len(deprecated_configs),
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            checked_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"配置健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"配置健康检查失败: {str(e)}")


@router.post("/", response_model=SystemConfigResponse)
async def create_system_config(
    config_data: SystemConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建系统配置"""
    
    try:
        # 检查配置键是否已存在
        existing_config = db.query(SystemConfig).filter(
            SystemConfig.key == config_data.key
        ).first()
        
        if existing_config:
            raise HTTPException(
                status_code=400,
                detail=f"配置键 '{config_data.key}' 已存在"
            )
        
        # 创建配置对象
        db_config = SystemConfig(
            key=config_data.key,
            name=config_data.name,
            display_name=config_data.display_name,
            description=config_data.description,
            default_value=config_data.default_value,
            config_type=config_data.config_type,
            category=config_data.category,
            is_required=config_data.required,
            is_sensitive=config_data.sensitive,
            is_encrypted=config_data.encrypted,
            is_readonly=config_data.readonly,
            is_system=config_data.system,
            is_public=config_data.public,
            min_value=str(config_data.min_value) if config_data.min_value is not None else None,
            max_value=str(config_data.max_value) if config_data.max_value is not None else None,
            pattern=config_data.pattern,
            allowed_values=config_data.allowed_values,
            group_name=config_data.group,
            depends_on=config_data.dependencies,
            environment=config_data.environment or "all",
            requires_restart=config_data.requires_restart,
            cache_ttl=config_data.cache_ttl,
            tags=config_data.tags,
            metadata=config_data.metadata,
            custom_fields=config_data.custom_fields,
            created_by=config_data.created_by or current_user.username
        )
        
        # 设置初始值
        if config_data.value is not None:
            # 验证值
            validation_result = db_config.validate_value(config_data.value)
            if not validation_result["valid"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"配置值无效: {', '.join(validation_result['errors'])}"
                )
            
            # 设置值（处理加密）
            if config_data.encrypted and config_data.sensitive:
                encrypted_value = encrypt_sensitive_data(config_data.value)
                db_config.value = encrypted_value
            else:
                db_config.set_value(config_data.value, current_user.username, "初始创建")
        
        # 添加到数据库
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        
        # 转换为响应格式
        config_dict = db_config.to_dict(
            include_sensitive=(not db_config.is_sensitive),
            include_metadata=True
        )
        
        return SystemConfigResponse(**config_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建系统配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建系统配置失败: {str(e)}")


@router.get("/{config_key}", response_model=SystemConfigResponse)
async def get_system_config(
    config_key: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取系统配置详情"""
    
    try:
        config = SystemConfig.get_by_key(db, config_key)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"系统配置不存在: {config_key}"
            )
        
        # 记录访问
        config.access()
        db.commit()
        
        # 转换为响应格式
        config_dict = config.to_dict(
            include_sensitive=(not config.is_sensitive),
            include_metadata=True
        )
        
        return SystemConfigResponse(**config_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取系统配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统配置失败: {str(e)}")


@router.get("/{config_key}/value", response_model=SystemConfigValue)
async def get_config_value(
    config_key: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取配置值（类型化）"""
    
    try:
        config = SystemConfig.get_by_key(db, config_key)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"系统配置不存在: {config_key}"
            )
        
        # 检查是否有访问权限（敏感配置）
        if config.is_sensitive and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="无权访问敏感配置"
            )
        
        # 记录访问
        config.access()
        db.commit()
        
        # 获取类型化值
        typed_value = config.get_typed_value()
        
        return SystemConfigValue(
            key=config.key,
            value=typed_value,
            config_type=config.config_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置值失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置值失败: {str(e)}")


@router.put("/{config_key}", response_model=SystemConfigResponse)
async def update_system_config(
    config_key: str,
    config_update: SystemConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新系统配置"""
    
    try:
        config = SystemConfig.get_by_key(db, config_key)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"系统配置不存在: {config_key}"
            )
        
        # 检查是否只读
        if config.is_readonly:
            raise HTTPException(
                status_code=400,
                detail="只读配置不能修改"
            )
        
        # 更新字段
        update_data = config_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "value" and value is not None:
                # 验证新值
                validation_result = config.validate_value(value)
                if not validation_result["valid"]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"配置值无效: {', '.join(validation_result['errors'])}"
                    )
                
                # 设置新值
                config.set_value(
                    value, 
                    config_update.updated_by or current_user.username,
                    "API更新"
                )
            else:
                # 映射字段名
                field_mapping = {
                    "required": "is_required",
                    "sensitive": "is_sensitive", 
                    "encrypted": "is_encrypted",
                    "readonly": "is_readonly",
                    "system": "is_system",
                    "public": "is_public",
                    "group": "group_name",
                    "dependencies": "depends_on"
                }
                
                db_field = field_mapping.get(field, field)
                if hasattr(config, db_field):
                    setattr(config, db_field, value)
        
        # 更新元信息
        config.updated_by = config_update.updated_by or current_user.username
        
        db.commit()
        db.refresh(config)
        
        # 转换为响应格式
        config_dict = config.to_dict(
            include_sensitive=(not config.is_sensitive),
            include_metadata=True
        )
        
        return SystemConfigResponse(**config_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新系统配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新系统配置失败: {str(e)}")


@router.delete("/{config_key}")
async def delete_system_config(
    config_key: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除系统配置"""
    
    try:
        config = SystemConfig.get_by_key(db, config_key)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"系统配置不存在: {config_key}"
            )
        
        # 检查是否是系统配置
        if config.is_system:
            raise HTTPException(
                status_code=400,
                detail="系统配置不能删除"
            )
        
        # 检查依赖关系
        dependent_configs = db.query(SystemConfig).filter(
            SystemConfig.depends_on.contains([config_key])
        ).all()
        
        if dependent_configs:
            dependent_keys = [c.key for c in dependent_configs]
            raise HTTPException(
                status_code=400,
                detail=f"无法删除，有其他配置依赖此项: {', '.join(dependent_keys)}"
            )
        
        db.delete(config)
        db.commit()
        
        return {"message": f"系统配置 '{config_key}' 已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除系统配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除系统配置失败: {str(e)}")


@router.post("/validate", response_model=SystemConfigValidationResponse)
async def validate_config_value(
    validation_data: SystemConfigValidation,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """验证配置值"""
    
    try:
        config = SystemConfig.get_by_key(db, validation_data.key)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"系统配置不存在: {validation_data.key}"
            )
        
        # 执行验证
        validation_result = config.validate_value(validation_data.value)
        
        # 获取解析后的值
        parsed_value = None
        if validation_result["valid"]:
            try:
                # 创建临时配置对象来解析值
                temp_config = SystemConfig(
                    config_type=config.config_type,
                    value=validation_data.value
                )
                parsed_value = temp_config.get_typed_value()
            except Exception:
                parsed_value = validation_data.value
        
        return SystemConfigValidationResponse(
            key=validation_data.key,
            valid=validation_result["valid"],
            errors=validation_result["errors"],
            warnings=validation_result["warnings"],
            parsed_value=parsed_value
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证配置值失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证配置值失败: {str(e)}")


@router.post("/reset", response_model=SystemConfigResetResponse)
async def reset_configs(
    reset_data: SystemConfigReset,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """重置配置值"""
    
    try:
        results = []
        reset_count = 0
        failed_count = 0
        
        for config_key in reset_data.keys:
            try:
                config = SystemConfig.get_by_key(db, config_key)
                
                if not config:
                    results.append({
                        "key": config_key,
                        "success": False,
                        "message": "配置不存在"
                    })
                    failed_count += 1
                    continue
                
                # 检查是否只读
                if config.is_readonly:
                    results.append({
                        "key": config_key,
                        "success": False,
                        "message": "只读配置不能重置"
                    })
                    failed_count += 1
                    continue
                
                # 重置为默认值
                if reset_data.reset_to_default:
                    config.reset_to_default(current_user.username)
                else:
                    config.set_value(None, current_user.username, reset_data.reason or "手动重置")
                
                results.append({
                    "key": config_key,
                    "success": True,
                    "message": "重置成功",
                    "old_value": config.previous_value,
                    "new_value": config.value
                })
                reset_count += 1
                
            except Exception as e:
                results.append({
                    "key": config_key,
                    "success": False,
                    "message": str(e)
                })
                failed_count += 1
        
        db.commit()
        
        return SystemConfigResetResponse(
            total_configs=len(reset_data.keys),
            reset_configs=reset_count,
            failed_configs=failed_count,
            results=results,
            reset_at=datetime.utcnow()
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"重置配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置配置失败: {str(e)}")


@router.post("/export")
async def export_configs(
    export_data: SystemConfigExport,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """导出配置"""
    
    try:
        # 构建查询
        query = db.query(SystemConfig)
        
        # 应用过滤条件
        filters = []
        
        if export_data.categories:
            filters.append(SystemConfig.category.in_(export_data.categories))
        
        if export_data.groups:
            filters.append(SystemConfig.group_name.in_(export_data.groups))
        
        if export_data.keys:
            filters.append(SystemConfig.key.in_(export_data.keys))
        
        if not export_data.include_sensitive:
            filters.append(SystemConfig.is_sensitive == False)
        
        if not export_data.include_system:
            filters.append(SystemConfig.is_system == False)
        
        if filters:
            query = query.filter(and_(*filters))
        
        configs = query.all()
        
        # 准备导出数据
        export_configs_data = []
        for config in configs:
            config_dict = config.to_dict(
                include_sensitive=export_data.include_sensitive,
                include_metadata=True
            )
            export_configs_data.append(config_dict)
        
        # 根据格式导出
        if export_data.format == "json":
            content = json.dumps(export_configs_data, ensure_ascii=False, indent=2)
            media_type = "application/json"
            filename = f"system_configs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        elif export_data.format == "yaml":
            content = yaml.dump(export_configs_data, allow_unicode=True, default_flow_style=False)
            media_type = "application/x-yaml"
            filename = f"system_configs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        
        elif export_data.format == "env":
            lines = []
            for config in export_configs_data:
                if config["value"] is not None:
                    # 环境变量格式
                    env_key = config["key"].upper().replace(".", "_")
                    env_value = str(config["value"])
                    if " " in env_value or "\n" in env_value:
                        env_value = f'"{env_value}"'
                    lines.append(f"{env_key}={env_value}")
            content = "\n".join(lines)
            media_type = "text/plain"
            filename = f"system_configs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.env"
        
        elif export_data.format == "ini":
            config_parser = configparser.ConfigParser()
            
            # 按分类分组
            for config in export_configs_data:
                section = str(config["category"])
                if section not in config_parser:
                    config_parser.add_section(section)
                
                if config["value"] is not None:
                    config_parser.set(section, config["key"], str(config["value"]))
            
            string_io = StringIO()
            config_parser.write(string_io)
            content = string_io.getvalue()
            media_type = "text/plain"
            filename = f"system_configs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ini"
        
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
        
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出配置失败: {str(e)}")


@router.post("/import", response_model=SystemConfigImportResponse)
async def import_configs(
    import_data: SystemConfigImport,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """导入配置"""
    
    try:
        # 解析导入数据
        if import_data.format == "json":
            configs_data = json.loads(import_data.data)
        elif import_data.format == "yaml":
            configs_data = yaml.safe_load(import_data.data)
        elif import_data.format == "env":
            configs_data = []
            for line in import_data.data.strip().split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip().lower().replace("_", ".")
                        value = value.strip().strip('"')
                        configs_data.append({
                            "key": key,
                            "value": value,
                            "config_type": ConfigType.STRING,
                            "category": ConfigCategory.CUSTOM
                        })
        elif import_data.format == "ini":
            config_parser = configparser.ConfigParser()
            config_parser.read_string(import_data.data)
            
            configs_data = []
            for section_name in config_parser.sections():
                for key, value in config_parser.items(section_name):
                    configs_data.append({
                        "key": key,
                        "value": value,
                        "config_type": ConfigType.STRING,
                        "category": section_name
                    })
        else:
            raise HTTPException(status_code=400, detail="不支持的导入格式")
        
        # 处理导入
        results = []
        imported_count = 0
        updated_count = 0
        failed_count = 0
        
        for config_data in configs_data:
            try:
                config_key = config_data.get("key")
                if not config_key:
                    results.append({
                        "key": "unknown",
                        "success": False,
                        "message": "缺少配置键"
                    })
                    failed_count += 1
                    continue
                
                # 检查是否存在
                existing_config = SystemConfig.get_by_key(db, config_key)
                
                if existing_config:
                    if import_data.overwrite:
                        if not import_data.validate_only:
                            # 更新现有配置
                            if "value" in config_data:
                                existing_config.set_value(
                                    config_data["value"],
                                    current_user.username,
                                    "批量导入更新"
                                )
                            
                            # 更新其他字段
                            for field in ["name", "description", "config_type", "category"]:
                                if field in config_data:
                                    if field == "category":
                                        existing_config.category = ConfigCategory(config_data[field])
                                    elif field == "config_type":
                                        existing_config.config_type = ConfigType(config_data[field])
                                    else:
                                        setattr(existing_config, field, config_data[field])
                        
                        results.append({
                            "key": config_key,
                            "success": True,
                            "message": "更新成功" if not import_data.validate_only else "验证通过（更新）"
                        })
                        updated_count += 1
                    else:
                        results.append({
                            "key": config_key,
                            "success": False,
                            "message": "配置已存在，未覆盖"
                        })
                        failed_count += 1
                else:
                    # 创建新配置
                    if not import_data.validate_only:
                        new_config = SystemConfig(
                            key=config_key,
                            name=config_data.get("name", config_key),
                            display_name=config_data.get("display_name", config_key),
                            description=config_data.get("description"),
                            config_type=ConfigType(config_data.get("config_type", ConfigType.STRING)),
                            category=ConfigCategory(config_data.get("category", ConfigCategory.CUSTOM)),
                            created_by=current_user.username
                        )
                        
                        if "value" in config_data:
                            new_config.set_value(
                                config_data["value"],
                                current_user.username,
                                "批量导入创建"
                            )
                        
                        db.add(new_config)
                    
                    results.append({
                        "key": config_key,
                        "success": True,
                        "message": "创建成功" if not import_data.validate_only else "验证通过（创建）"
                    })
                    imported_count += 1
                    
            except Exception as e:
                results.append({
                    "key": config_data.get("key", "unknown"),
                    "success": False,
                    "message": str(e)
                })
                failed_count += 1
        
        if not import_data.validate_only:
            db.commit()
        
        return SystemConfigImportResponse(
            total_configs=len(configs_data),
            imported_configs=imported_count,
            updated_configs=updated_count,
            failed_configs=failed_count,
            results=results,
            imported_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        if not import_data.validate_only:
            db.rollback()
        logger.error(f"导入配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"导入配置失败: {str(e)}")