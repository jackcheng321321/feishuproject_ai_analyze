"""系统配置相关Pydantic模式

定义系统配置的创建、更新、响应等数据验证模式。
"""

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class ConfigType(str, Enum):
    """配置类型枚举"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    LIST = "list"
    PASSWORD = "password"
    EMAIL = "email"
    URL = "url"
    FILE_PATH = "file_path"
    ENUM = "enum"


class ConfigCategory(str, Enum):
    """配置分类枚举"""
    SYSTEM = "system"
    DATABASE = "database"
    AI_MODEL = "ai_model"
    STORAGE = "storage"
    WEBHOOK = "webhook"
    NOTIFICATION = "notification"
    SECURITY = "security"
    LOGGING = "logging"
    PERFORMANCE = "performance"
    UI = "ui"
    INTEGRATION = "integration"
    CUSTOM = "custom"


class ConfigStatus(str, Enum):
    """配置状态枚举"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"
    TESTING = "testing"


class SystemConfigBase(BaseModel):
    """系统配置基础模式"""
    
    key: str = Field(..., max_length=200, description="配置键")
    name: str = Field(..., max_length=200, description="配置名称")
    display_name: str = Field(..., max_length=200, description="显示名称")
    description: Optional[str] = Field(None, max_length=1000, description="配置描述")
    
    # 配置值
    value: Optional[str] = Field(None, description="配置值")
    default_value: Optional[str] = Field(None, description="默认值")
    
    # 配置类型和分类
    config_type: ConfigType = Field(..., description="配置类型")
    category: ConfigCategory = Field(..., description="配置分类")
    
    # 配置属性
    required: bool = Field(False, description="是否必需")
    sensitive: bool = Field(False, description="是否敏感")
    encrypted: bool = Field(False, description="是否加密")
    readonly: bool = Field(False, description="是否只读")
    system: bool = Field(False, description="是否系统配置")
    public: bool = Field(False, description="是否公开")
    
    # 验证规则
    min_value: Optional[float] = Field(None, description="最小值")
    max_value: Optional[float] = Field(None, description="最大值")
    pattern: Optional[str] = Field(None, max_length=500, description="正则表达式")
    allowed_values: Optional[List[str]] = Field(None, description="允许的值")
    
    # 分组和依赖
    group: Optional[str] = Field(None, max_length=100, description="配置组")
    dependencies: Optional[List[str]] = Field(None, description="依赖配置")
    
    # 环境和版本
    environment: Optional[str] = Field(None, max_length=50, description="环境")
    version: Optional[str] = Field(None, max_length=50, description="版本")
    
    # 状态和重启
    status: ConfigStatus = Field(ConfigStatus.ACTIVE, description="配置状态")
    requires_restart: bool = Field(False, description="是否需要重启")
    
    # 缓存
    cacheable: bool = Field(True, description="是否可缓存")
    cache_ttl: Optional[int] = Field(None, ge=0, description="缓存TTL（秒）")
    
    # 标签和元数据
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="自定义字段")
    
    @validator('key')
    def validate_key(cls, v):
        if not v or not v.strip():
            raise ValueError('配置键不能为空')
        # 配置键只能包含字母、数字、下划线和点
        import re
        if not re.match(r'^[a-zA-Z0-9_.]+$', v.strip()):
            raise ValueError('配置键只能包含字母、数字、下划线和点')
        return v.strip().lower()
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('配置名称不能为空')
        return v.strip()
    
    @validator('display_name')
    def validate_display_name(cls, v):
        if not v or not v.strip():
            raise ValueError('显示名称不能为空')
        return v.strip()
    
    @validator('pattern')
    def validate_pattern(cls, v):
        if v is not None:
            try:
                import re
                re.compile(v)
            except re.error:
                raise ValueError('正则表达式格式无效')
        return v
    
    @validator('allowed_values')
    def validate_allowed_values(cls, v):
        if v is not None and not isinstance(v, list):
            raise ValueError('允许的值必须是列表格式')
        return v
    
    @validator('dependencies')
    def validate_dependencies(cls, v):
        if v is not None and not isinstance(v, list):
            raise ValueError('依赖配置必须是列表格式')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None and not isinstance(v, list):
            raise ValueError('标签必须是列表格式')
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError('元数据必须是字典格式')
        return v
    
    @validator('custom_fields')
    def validate_custom_fields(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError('自定义字段必须是字典格式')
        return v


class SystemConfigCreate(SystemConfigBase):
    """系统配置创建模式"""
    
    # 创建者信息
    created_by: Optional[str] = Field(None, max_length=100, description="创建者")
    
    @validator('value')
    def validate_value_on_create(cls, v, values):
        # 如果是必需配置且没有默认值，则值不能为空
        if values.get('required') and not values.get('default_value') and not v:
            raise ValueError('必需配置必须提供值')
        return v


class SystemConfigUpdate(BaseModel):
    """系统配置更新模式"""
    
    name: Optional[str] = Field(None, max_length=200, description="配置名称")
    display_name: Optional[str] = Field(None, max_length=200, description="显示名称")
    description: Optional[str] = Field(None, max_length=1000, description="配置描述")
    
    # 配置值
    value: Optional[str] = Field(None, description="配置值")
    default_value: Optional[str] = Field(None, description="默认值")
    
    # 配置类型和分类
    config_type: Optional[ConfigType] = Field(None, description="配置类型")
    category: Optional[ConfigCategory] = Field(None, description="配置分类")
    
    # 配置属性
    required: Optional[bool] = Field(None, description="是否必需")
    sensitive: Optional[bool] = Field(None, description="是否敏感")
    encrypted: Optional[bool] = Field(None, description="是否加密")
    readonly: Optional[bool] = Field(None, description="是否只读")
    system: Optional[bool] = Field(None, description="是否系统配置")
    public: Optional[bool] = Field(None, description="是否公开")
    
    # 验证规则
    min_value: Optional[float] = Field(None, description="最小值")
    max_value: Optional[float] = Field(None, description="最大值")
    pattern: Optional[str] = Field(None, max_length=500, description="正则表达式")
    allowed_values: Optional[List[str]] = Field(None, description="允许的值")
    
    # 分组和依赖
    group: Optional[str] = Field(None, max_length=100, description="配置组")
    dependencies: Optional[List[str]] = Field(None, description="依赖配置")
    
    # 环境和版本
    environment: Optional[str] = Field(None, max_length=50, description="环境")
    version: Optional[str] = Field(None, max_length=50, description="版本")
    
    # 状态和重启
    status: Optional[ConfigStatus] = Field(None, description="配置状态")
    requires_restart: Optional[bool] = Field(None, description="是否需要重启")
    
    # 缓存
    cacheable: Optional[bool] = Field(None, description="是否可缓存")
    cache_ttl: Optional[int] = Field(None, ge=0, description="缓存TTL（秒）")
    
    # 标签和元数据
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="自定义字段")
    
    # 更新者信息
    updated_by: Optional[str] = Field(None, max_length=100, description="更新者")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('配置名称不能为空')
        return v.strip() if v else None
    
    @validator('display_name')
    def validate_display_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('显示名称不能为空')
        return v.strip() if v else None


class SystemConfigResponse(SystemConfigBase):
    """系统配置响应模式"""
    
    id: int = Field(..., description="配置ID")
    
    # 审计信息
    created_by: Optional[str] = Field(None, description="创建者")
    updated_by: Optional[str] = Field(None, description="更新者")
    last_accessed_at: Optional[datetime] = Field(None, description="最后访问时间")
    access_count: int = Field(0, description="访问次数")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemConfigPublicResponse(BaseModel):
    """系统配置公开响应模式（不包含敏感信息）"""
    
    key: str = Field(..., description="配置键")
    name: str = Field(..., description="配置名称")
    display_name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="配置描述")
    
    # 只返回非敏感的配置值
    value: Optional[str] = Field(None, description="配置值")
    
    config_type: ConfigType = Field(..., description="配置类型")
    category: ConfigCategory = Field(..., description="配置分类")
    
    # 验证规则（用于前端验证）
    required: bool = Field(False, description="是否必需")
    min_value: Optional[float] = Field(None, description="最小值")
    max_value: Optional[float] = Field(None, description="最大值")
    pattern: Optional[str] = Field(None, description="正则表达式")
    allowed_values: Optional[List[str]] = Field(None, description="允许的值")
    
    group: Optional[str] = Field(None, description="配置组")
    status: ConfigStatus = Field(..., description="配置状态")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemConfigValue(BaseModel):
    """系统配置值模式"""
    
    key: str = Field(..., description="配置键")
    value: Union[str, int, float, bool, List, Dict] = Field(..., description="配置值")
    config_type: ConfigType = Field(..., description="配置类型")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemConfigValidation(BaseModel):
    """系统配置验证模式"""
    
    key: str = Field(..., description="配置键")
    value: str = Field(..., description="配置值")
    

class SystemConfigValidationResponse(BaseModel):
    """系统配置验证响应模式"""
    
    key: str = Field(..., description="配置键")
    valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field([], description="验证错误")
    warnings: List[str] = Field([], description="验证警告")
    parsed_value: Optional[Union[str, int, float, bool, List, Dict]] = Field(None, description="解析后的值")
    

class SystemConfigReset(BaseModel):
    """系统配置重置模式"""
    
    keys: List[str] = Field(..., min_items=1, description="配置键列表")
    reset_to_default: bool = Field(True, description="重置为默认值")
    reason: Optional[str] = Field(None, max_length=500, description="重置原因")
    
    @validator('keys')
    def validate_keys(cls, v):
        if not v:
            raise ValueError('配置键列表不能为空')
        if len(set(v)) != len(v):
            raise ValueError('配置键列表不能包含重复项')
        return v


class SystemConfigResetResponse(BaseModel):
    """系统配置重置响应模式"""
    
    total_configs: int = Field(..., description="配置总数")
    reset_configs: int = Field(..., description="重置配置数")
    failed_configs: int = Field(..., description="重置失败配置数")
    results: List[Dict[str, Any]] = Field(..., description="重置结果")
    reset_at: datetime = Field(..., description="重置时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemConfigExport(BaseModel):
    """系统配置导出模式"""
    
    categories: Optional[List[ConfigCategory]] = Field(None, description="导出分类")
    groups: Optional[List[str]] = Field(None, description="导出组")
    keys: Optional[List[str]] = Field(None, description="导出键")
    include_sensitive: bool = Field(False, description="包含敏感配置")
    include_system: bool = Field(False, description="包含系统配置")
    format: str = Field("json", description="导出格式")
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['json', 'yaml', 'env', 'ini']
        if v not in allowed_formats:
            raise ValueError(f'导出格式必须是以下之一: {", ".join(allowed_formats)}')
        return v


class SystemConfigImport(BaseModel):
    """系统配置导入模式"""
    
    data: str = Field(..., description="导入数据")
    format: str = Field("json", description="导入格式")
    overwrite: bool = Field(False, description="覆盖现有配置")
    validate_only: bool = Field(False, description="仅验证不导入")
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['json', 'yaml', 'env', 'ini']
        if v not in allowed_formats:
            raise ValueError(f'导入格式必须是以下之一: {", ".join(allowed_formats)}')
        return v
    
    @validator('data')
    def validate_data(cls, v):
        if not v or not v.strip():
            raise ValueError('导入数据不能为空')
        return v.strip()


class SystemConfigImportResponse(BaseModel):
    """系统配置导入响应模式"""
    
    total_configs: int = Field(..., description="配置总数")
    imported_configs: int = Field(..., description="导入配置数")
    updated_configs: int = Field(..., description="更新配置数")
    failed_configs: int = Field(..., description="导入失败配置数")
    results: List[Dict[str, Any]] = Field(..., description="导入结果")
    imported_at: datetime = Field(..., description="导入时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemConfigStats(BaseModel):
    """系统配置统计模式"""
    
    total_configs: int = Field(0, description="配置总数")
    active_configs: int = Field(0, description="活跃配置数")
    deprecated_configs: int = Field(0, description="废弃配置数")
    disabled_configs: int = Field(0, description="禁用配置数")
    
    # 按分类统计
    configs_by_category: Dict[str, int] = Field({}, description="按分类统计")
    
    # 按类型统计
    configs_by_type: Dict[str, int] = Field({}, description="按类型统计")
    
    # 属性统计
    required_configs: int = Field(0, description="必需配置数")
    sensitive_configs: int = Field(0, description="敏感配置数")
    encrypted_configs: int = Field(0, description="加密配置数")
    readonly_configs: int = Field(0, description="只读配置数")
    system_configs: int = Field(0, description="系统配置数")
    public_configs: int = Field(0, description="公开配置数")
    
    # 访问统计
    total_accesses: int = Field(0, description="总访问次数")
    most_accessed_configs: List[Dict[str, Any]] = Field([], description="最常访问配置")
    
    # 更新统计
    recently_updated_configs: int = Field(0, description="最近更新配置数")
    never_accessed_configs: int = Field(0, description="从未访问配置数")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemConfigHealth(BaseModel):
    """系统配置健康检查模式"""
    
    healthy: bool = Field(..., description="是否健康")
    total_configs: int = Field(..., description="配置总数")
    
    # 问题统计
    missing_required_configs: int = Field(0, description="缺失必需配置数")
    invalid_configs: int = Field(0, description="无效配置数")
    deprecated_configs: int = Field(0, description="废弃配置数")
    
    # 详细问题
    issues: List[Dict[str, Any]] = Field([], description="配置问题")
    warnings: List[Dict[str, Any]] = Field([], description="配置警告")
    
    # 建议
    recommendations: List[str] = Field([], description="改进建议")
    
    checked_at: datetime = Field(..., description="检查时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemConfigFilter(BaseModel):
    """系统配置过滤器模式"""
    
    category: Optional[ConfigCategory] = Field(None, description="分类过滤")
    config_type: Optional[ConfigType] = Field(None, description="类型过滤")
    status: Optional[ConfigStatus] = Field(None, description="状态过滤")
    group: Optional[str] = Field(None, description="组过滤")
    environment: Optional[str] = Field(None, description="环境过滤")
    
    # 属性过滤
    required: Optional[bool] = Field(None, description="必需过滤")
    sensitive: Optional[bool] = Field(None, description="敏感过滤")
    encrypted: Optional[bool] = Field(None, description="加密过滤")
    readonly: Optional[bool] = Field(None, description="只读过滤")
    system: Optional[bool] = Field(None, description="系统过滤")
    public: Optional[bool] = Field(None, description="公开过滤")
    requires_restart: Optional[bool] = Field(None, description="需要重启过滤")
    
    # 搜索
    search: Optional[str] = Field(None, description="搜索关键词")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    
    # 时间过滤
    created_after: Optional[datetime] = Field(None, description="创建时间之后")
    created_before: Optional[datetime] = Field(None, description="创建时间之前")
    updated_after: Optional[datetime] = Field(None, description="更新时间之后")
    updated_before: Optional[datetime] = Field(None, description="更新时间之前")
    accessed_after: Optional[datetime] = Field(None, description="访问时间之后")
    accessed_before: Optional[datetime] = Field(None, description="访问时间之前")
    
    # 访问统计过滤
    min_access_count: Optional[int] = Field(None, ge=0, description="最小访问次数")
    max_access_count: Optional[int] = Field(None, ge=0, description="最大访问次数")
    never_accessed: Optional[bool] = Field(None, description="从未访问过滤")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemConfigSort(BaseModel):
    """系统配置排序模式"""
    
    field: str = Field("created_at", description="排序字段")
    order: str = Field("desc", description="排序顺序")
    
    @validator('field')
    def validate_field(cls, v):
        allowed_fields = [
            'id', 'key', 'name', 'display_name', 'category', 'config_type',
            'created_at', 'updated_at', 'last_accessed_at', 'access_count',
            'group', 'status', 'required', 'sensitive'
        ]
        if v not in allowed_fields:
            raise ValueError(f'排序字段必须是以下之一: {", ".join(allowed_fields)}')
        return v
    
    @validator('order')
    def validate_order(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('排序顺序必须是asc或desc')
        return v.lower()