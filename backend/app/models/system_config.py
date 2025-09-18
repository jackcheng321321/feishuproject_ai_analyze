from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
import enum
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.database import Base


class ConfigType(str, enum.Enum):
    """配置类型枚举"""
    STRING = "string"        # 字符串
    INTEGER = "integer"      # 整数
    FLOAT = "float"          # 浮点数
    BOOLEAN = "boolean"      # 布尔值
    JSON = "json"            # JSON对象
    TEXT = "text"            # 长文本
    PASSWORD = "password"    # 密码（加密存储）
    URL = "url"              # URL地址
    EMAIL = "email"          # 邮箱地址
    FILE_PATH = "file_path"  # 文件路径


class ConfigCategory(str, enum.Enum):
    """配置分类枚举"""
    SYSTEM = "system"                # 系统配置
    DATABASE = "database"            # 数据库配置
    REDIS = "redis"                  # Redis配置
    SECURITY = "security"            # 安全配置
    AI_MODEL = "ai_model"            # AI模型配置
    WEBHOOK = "webhook"              # Webhook配置
    FILE_STORAGE = "file_storage"    # 文件存储配置
    NOTIFICATION = "notification"    # 通知配置
    LOGGING = "logging"              # 日志配置
    MONITORING = "monitoring"        # 监控配置
    FEISHU = "feishu"                # 飞书配置
    TASK = "task"                    # 任务配置
    UI = "ui"                        # 界面配置
    INTEGRATION = "integration"      # 集成配置
    PERFORMANCE = "performance"      # 性能配置


class SystemConfig(Base):
    """系统配置模型"""
    
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, index=True, comment="配置ID")
    
    # 配置标识
    key = Column(String(100), unique=True, nullable=False, comment="配置键")
    name = Column(String(200), nullable=False, comment="配置名称")
    display_name = Column(String(200), comment="显示名称")
    
    # 配置值
    value = Column(Text, comment="配置值")
    default_value = Column(Text, comment="默认值")
    
    # 配置类型和分类
    config_type = Column(
        SQLEnum(ConfigType), 
        default=ConfigType.STRING, 
        comment="配置类型"
    )
    category = Column(
        SQLEnum(ConfigCategory), 
        default=ConfigCategory.SYSTEM, 
        comment="配置分类"
    )
    
    # 配置属性
    is_required = Column(Boolean, default=False, comment="是否必需")
    is_sensitive = Column(Boolean, default=False, comment="是否敏感")
    is_encrypted = Column(Boolean, default=False, comment="是否加密存储")
    is_readonly = Column(Boolean, default=False, comment="是否只读")
    is_system = Column(Boolean, default=False, comment="是否系统配置")
    is_public = Column(Boolean, default=False, comment="是否公开")
    
    # 验证规则
    validation_rules = Column(JSON, comment="验证规则")
    allowed_values = Column(JSON, comment="允许的值列表")
    min_value = Column(String(50), comment="最小值")
    max_value = Column(String(50), comment="最大值")
    pattern = Column(String(200), comment="正则表达式模式")
    
    # 描述信息
    description = Column(Text, comment="配置描述")
    help_text = Column(Text, comment="帮助文本")
    example_value = Column(Text, comment="示例值")
    
    # 分组和排序
    group_name = Column(String(100), comment="分组名称")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    
    # 依赖关系
    depends_on = Column(JSON, comment="依赖的配置项")
    affects = Column(JSON, comment="影响的配置项")
    
    # 环境配置
    environment = Column(String(20), default="all", comment="适用环境")
    
    # 版本控制
    version = Column(Integer, default=1, comment="版本号")
    previous_value = Column(Text, comment="上一个值")
    change_reason = Column(Text, comment="变更原因")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_deprecated = Column(Boolean, default=False, comment="是否已弃用")
    deprecation_message = Column(Text, comment="弃用消息")
    
    # 重启要求
    requires_restart = Column(Boolean, default=False, comment="是否需要重启")
    restart_components = Column(JSON, comment="需要重启的组件")
    
    # 缓存配置
    cache_ttl = Column(Integer, comment="缓存TTL（秒）")
    cache_key = Column(String(100), comment="缓存键")
    
    # 审计信息
    created_by = Column(String(100), comment="创建者")
    updated_by = Column(String(100), comment="更新者")
    last_accessed_at = Column(DateTime(timezone=True), comment="最后访问时间")
    access_count = Column(Integer, default=0, comment="访问次数")
    
    # 标签和元数据
    tags = Column(JSON, comment="标签")
    meta_data = Column(JSON, comment="元数据")
    custom_fields = Column(JSON, comment="自定义字段")
    
    # 备注信息
    notes = Column(Text, comment="备注")
    admin_notes = Column(Text, comment="管理员备注")
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        comment="更新时间"
    )
    
    def __repr__(self):
        return f"<SystemConfig(id={self.id}, key='{self.key}', category='{self.category}')>"
    
    def to_dict(self, include_sensitive=False, include_meta_data=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "display_name": self.display_name,
            "config_type": self.config_type.value if self.config_type else None,
            "category": self.category.value if self.category else None,
            "is_required": self.is_required,
            "is_sensitive": self.is_sensitive,
            "is_encrypted": self.is_encrypted,
            "is_readonly": self.is_readonly,
            "is_system": self.is_system,
            "is_public": self.is_public,
            "description": self.description,
            "help_text": self.help_text,
            "example_value": self.example_value,
            "group_name": self.group_name,
            "sort_order": self.sort_order,
            "environment": self.environment,
            "version": self.version,
            "is_active": self.is_active,
            "is_deprecated": self.is_deprecated,
            "deprecation_message": self.deprecation_message,
            "requires_restart": self.requires_restart,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "access_count": self.access_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # 配置值处理
        if self.is_sensitive and not include_sensitive:
            data["value"] = "***" if self.value else None
        else:
            data["value"] = self.get_typed_value()
        
        data["default_value"] = self.get_typed_default_value()
        
        # 元数据只在需要时包含
        if include_meta_data:
            data.update({
                "validation_rules": self.validation_rules,
                "allowed_values": self.allowed_values,
                "min_value": self.min_value,
                "max_value": self.max_value,
                "pattern": self.pattern,
                "depends_on": self.depends_on,
                "affects": self.affects,
                "previous_value": self.previous_value,
                "change_reason": self.change_reason,
                "restart_components": self.restart_components,
                "cache_ttl": self.cache_ttl,
                "cache_key": self.cache_key,
                "tags": self.tags,
                "meta_data": self.meta_data,
                "custom_fields": self.custom_fields,
                "notes": self.notes,
                "admin_notes": self.admin_notes,
            })
        
        return data
    
    def get_typed_value(self) -> Any:
        """获取类型化的配置值"""
        if self.value is None:
            return None
        
        try:
            if self.config_type == ConfigType.INTEGER:
                return int(self.value)
            elif self.config_type == ConfigType.FLOAT:
                return float(self.value)
            elif self.config_type == ConfigType.BOOLEAN:
                return self.value.lower() in ('true', '1', 'yes', 'on')
            elif self.config_type == ConfigType.JSON:
                import json
                return json.loads(self.value)
            else:
                return self.value
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.value
    
    def get_typed_default_value(self) -> Any:
        """获取类型化的默认值"""
        if self.default_value is None:
            return None
        
        try:
            if self.config_type == ConfigType.INTEGER:
                return int(self.default_value)
            elif self.config_type == ConfigType.FLOAT:
                return float(self.default_value)
            elif self.config_type == ConfigType.BOOLEAN:
                return self.default_value.lower() in ('true', '1', 'yes', 'on')
            elif self.config_type == ConfigType.JSON:
                import json
                return json.loads(self.default_value)
            else:
                return self.default_value
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.default_value
    
    def set_value(self, value: Any, updated_by: str = None, change_reason: str = None):
        """设置配置值"""
        # 保存上一个值
        self.previous_value = self.value
        
        # 转换值为字符串存储
        if value is None:
            self.value = None
        elif self.config_type == ConfigType.JSON:
            import json
            self.value = json.dumps(value, ensure_ascii=False)
        elif self.config_type == ConfigType.BOOLEAN:
            self.value = str(bool(value)).lower()
        else:
            self.value = str(value)
        
        # 更新元信息
        if updated_by:
            self.updated_by = updated_by
        
        if change_reason:
            self.change_reason = change_reason
        
        # 增加版本号
        self.version += 1
    
    def validate_value(self, value: Any) -> Dict[str, Any]:
        """验证配置值"""
        errors = []
        warnings = []
        
        # 必需值检查
        if self.is_required and (value is None or value == ""):
            errors.append(f"配置项 {self.key} 是必需的")
        
        # 类型检查
        if value is not None:
            try:
                if self.config_type == ConfigType.INTEGER:
                    int_value = int(value)
                    if self.min_value and int_value < int(self.min_value):
                        errors.append(f"值不能小于 {self.min_value}")
                    if self.max_value and int_value > int(self.max_value):
                        errors.append(f"值不能大于 {self.max_value}")
                
                elif self.config_type == ConfigType.FLOAT:
                    float_value = float(value)
                    if self.min_value and float_value < float(self.min_value):
                        errors.append(f"值不能小于 {self.min_value}")
                    if self.max_value and float_value > float(self.max_value):
                        errors.append(f"值不能大于 {self.max_value}")
                
                elif self.config_type == ConfigType.JSON:
                    import json
                    json.loads(str(value))
                
                elif self.config_type == ConfigType.EMAIL:
                    import re
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, str(value)):
                        errors.append("无效的邮箱地址格式")
                
                elif self.config_type == ConfigType.URL:
                    import re
                    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
                    if not re.match(url_pattern, str(value)):
                        errors.append("无效的URL格式")
            
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                errors.append(f"类型转换错误: {str(e)}")
        
        # 允许值检查
        if self.allowed_values and value not in self.allowed_values:
            errors.append(f"值必须是以下之一: {', '.join(map(str, self.allowed_values))}")
        
        # 正则表达式检查
        if self.pattern and value:
            import re
            if not re.match(self.pattern, str(value)):
                errors.append(f"值不匹配模式: {self.pattern}")
        
        # 自定义验证规则
        if self.validation_rules:
            # 这里可以实现更复杂的验证逻辑
            pass
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
    
    def is_changed(self) -> bool:
        """检查配置是否已更改"""
        return self.value != self.previous_value
    
    def reset_to_default(self, updated_by: str = None):
        """重置为默认值"""
        self.set_value(self.get_typed_default_value(), updated_by, "重置为默认值")
    
    def access(self):
        """记录访问"""
        self.last_accessed_at = datetime.utcnow()
        self.access_count += 1
    
    def deprecate(self, message: str = None, updated_by: str = None):
        """标记为弃用"""
        self.is_deprecated = True
        self.deprecation_message = message or "此配置项已弃用"
        if updated_by:
            self.updated_by = updated_by
    
    def get_display_value(self) -> str:
        """获取显示值"""
        if self.is_sensitive:
            return "***" if self.value else ""
        
        value = self.get_typed_value()
        if value is None:
            return ""
        
        if self.config_type == ConfigType.JSON:
            import json
            return json.dumps(value, ensure_ascii=False, indent=2)
        
        return str(value)
    
    def get_dependencies(self) -> list:
        """获取依赖项"""
        return self.depends_on or []
    
    def get_affected_configs(self) -> list:
        """获取受影响的配置项"""
        return self.affects or []
    
    def needs_restart(self) -> bool:
        """检查是否需要重启"""
        return self.requires_restart and self.is_changed()
    
    def get_restart_components(self) -> list:
        """获取需要重启的组件"""
        return self.restart_components or []
    
    @classmethod
    def get_by_key(cls, db_session, key: str) -> Optional['SystemConfig']:
        """根据键获取配置"""
        config = db_session.query(cls).filter(cls.key == key).first()
        if config:
            config.access()
        return config
    
    @classmethod
    def get_by_category(cls, db_session, category: ConfigCategory) -> list:
        """根据分类获取配置"""
        return db_session.query(cls).filter(
            cls.category == category,
            cls.is_active == True
        ).order_by(cls.sort_order, cls.name).all()
    
    @classmethod
    def get_public_configs(cls, db_session) -> list:
        """获取公开配置"""
        return db_session.query(cls).filter(
            cls.is_public == True,
            cls.is_active == True
        ).order_by(cls.category, cls.sort_order, cls.name).all()
    
    @classmethod
    def get_configs_requiring_restart(cls, db_session) -> list:
        """获取需要重启的配置"""
        return db_session.query(cls).filter(
            cls.requires_restart == True,
            cls.is_active == True
        ).all()