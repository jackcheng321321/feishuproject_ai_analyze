"""用户相关Pydantic模式

定义用户的创建、更新、响应等数据验证模式。
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模式"""
    
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    avatar: Optional[str] = Field(None, description="头像URL")
    timezone: Optional[str] = Field("UTC", description="时区")
    language: Optional[str] = Field("zh-CN", description="语言")
    theme: Optional[str] = Field("light", description="主题")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v.lower()
    
    @validator('timezone')
    def validate_timezone(cls, v):
        # 这里可以添加时区验证逻辑
        return v
    
    @validator('language')
    def validate_language(cls, v):
        allowed_languages = ['zh-CN', 'en-US', 'ja-JP']
        if v not in allowed_languages:
            raise ValueError(f'语言必须是以下之一: {", ".join(allowed_languages)}')
        return v
    
    @validator('theme')
    def validate_theme(cls, v):
        allowed_themes = ['light', 'dark', 'auto']
        if v not in allowed_themes:
            raise ValueError(f'主题必须是以下之一: {", ".join(allowed_themes)}')
        return v


class UserCreate(UserBase):
    """用户创建模式"""
    
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    confirm_password: str = Field(..., description="确认密码")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        
        # 检查密码复杂度
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('密码必须包含大写字母、小写字母和数字')
        
        return v
    
    @validator('confirm_password')
    def validate_confirm_password(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不一致')
        return v


class UserUpdate(BaseModel):
    """用户更新模式"""
    
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    avatar: Optional[str] = Field(None, description="头像URL")
    timezone: Optional[str] = Field(None, description="时区")
    language: Optional[str] = Field(None, description="语言")
    theme: Optional[str] = Field(None, description="主题")
    is_active: Optional[bool] = Field(None, description="是否激活")
    
    @validator('language')
    def validate_language(cls, v):
        if v is not None:
            allowed_languages = ['zh-CN', 'en-US', 'ja-JP']
            if v not in allowed_languages:
                raise ValueError(f'语言必须是以下之一: {", ".join(allowed_languages)}')
        return v
    
    @validator('theme')
    def validate_theme(cls, v):
        if v is not None:
            allowed_themes = ['light', 'dark', 'auto']
            if v not in allowed_themes:
                raise ValueError(f'主题必须是以下之一: {", ".join(allowed_themes)}')
        return v


class UserResponse(UserBase):
    """用户响应模式"""
    
    id: int = Field(..., description="用户ID")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级用户")
    is_verified: bool = Field(..., description="是否已验证")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserLogin(BaseModel):
    """用户登录模式"""
    
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="记住我")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()


class UserProfile(BaseModel):
    """用户资料模式"""
    
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, description="全名")
    avatar: Optional[str] = Field(None, description="头像URL")
    timezone: str = Field(..., description="时区")
    language: str = Field(..., description="语言")
    theme: str = Field(..., description="主题")
    is_active: bool = Field(..., description="是否激活")
    is_verified: bool = Field(..., description="是否已验证")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserPermissions(BaseModel):
    """用户权限模式"""
    
    can_manage_config: bool = Field(False, description="可以管理配置")
    can_manage_webhooks: bool = Field(False, description="可以管理Webhook")
    can_manage_tasks: bool = Field(False, description="可以管理任务")
    can_view_logs: bool = Field(False, description="可以查看日志")
    can_manage_users: bool = Field(False, description="可以管理用户")
    can_manage_ai_models: bool = Field(False, description="可以管理AI模型")
    can_manage_storage: bool = Field(False, description="可以管理存储")
    
    class Config:
        from_attributes = True


class UserPreferences(BaseModel):
    """用户偏好设置模式"""
    
    email_notifications: bool = Field(True, description="邮件通知")
    webhook_notifications: bool = Field(True, description="Webhook通知")
    task_notifications: bool = Field(True, description="任务通知")
    security_notifications: bool = Field(True, description="安全通知")
    notification_frequency: str = Field("immediate", description="通知频率")
    dashboard_layout: Optional[Dict[str, Any]] = Field(None, description="仪表板布局")
    default_page_size: int = Field(20, ge=10, le=100, description="默认页面大小")
    
    @validator('notification_frequency')
    def validate_notification_frequency(cls, v):
        allowed_frequencies = ['immediate', 'hourly', 'daily', 'weekly', 'never']
        if v not in allowed_frequencies:
            raise ValueError(f'通知频率必须是以下之一: {", ".join(allowed_frequencies)}')
        return v
    
    class Config:
        from_attributes = True


class UserPasswordChange(BaseModel):
    """用户密码修改模式"""
    
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        
        # 检查密码复杂度
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('密码必须包含大写字母、小写字母和数字')
        
        return v
    
    @validator('confirm_password')
    def validate_confirm_password(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v


class UserPasswordReset(BaseModel):
    """用户密码重置模式"""
    
    email: EmailStr = Field(..., description="邮箱地址")


class UserPasswordResetConfirm(BaseModel):
    """用户密码重置确认模式"""
    
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        
        # 检查密码复杂度
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('密码必须包含大写字母、小写字母和数字')
        
        return v
    
    @validator('confirm_password')
    def validate_confirm_password(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v


class UserEmailVerification(BaseModel):
    """用户邮箱验证模式"""
    
    token: str = Field(..., description="验证令牌")


class UserStats(BaseModel):
    """用户统计模式"""
    
    total_tasks: int = Field(0, description="总任务数")
    active_tasks: int = Field(0, description="活跃任务数")
    successful_executions: int = Field(0, description="成功执行数")
    failed_executions: int = Field(0, description="失败执行数")
    total_webhooks: int = Field(0, description="总Webhook数")
    total_ai_models: int = Field(0, description="总AI模型数")
    total_storage_credentials: int = Field(0, description="总存储凭证数")
    last_activity_at: Optional[datetime] = Field(None, description="最后活动时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserActivity(BaseModel):
    """用户活动模式"""
    
    id: int = Field(..., description="活动ID")
    user_id: int = Field(..., description="用户ID")
    action: str = Field(..., description="操作")
    resource_type: str = Field(..., description="资源类型")
    resource_id: Optional[int] = Field(None, description="资源ID")
    details: Optional[Dict[str, Any]] = Field(None, description="详情")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserSession(BaseModel):
    """用户会话模式"""
    
    id: str = Field(..., description="会话ID")
    user_id: int = Field(..., description="用户ID")
    ip_address: str = Field(..., description="IP地址")
    user_agent: str = Field(..., description="用户代理")
    created_at: datetime = Field(..., description="创建时间")
    last_activity_at: datetime = Field(..., description="最后活动时间")
    expires_at: datetime = Field(..., description="过期时间")
    is_active: bool = Field(True, description="是否活跃")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TokenResponse(BaseModel):
    """令牌响应模式"""
    
    access_token: str = Field(..., description="访问令牌")
    refresh_token: Optional[str] = Field(None, description="刷新令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: UserProfile = Field(..., description="用户信息")
    permissions: UserPermissions = Field(..., description="用户权限")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模式"""
    
    refresh_token: str = Field(..., description="刷新令牌")