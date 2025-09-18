"""存储凭证相关Pydantic模式

定义存储凭证的创建、更新、响应等数据验证模式。
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class StorageProtocol(str, Enum):
    """存储协议枚举"""
    SMB = "smb"
    NFS = "nfs"
    FTP = "ftp"
    SFTP = "sftp"
    HTTP = "http"
    HTTPS = "https"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"
    LOCAL = "local"
    WEBDAV = "webdav"


class StorageCredentialBase(BaseModel):
    """存储凭证基础模式"""
    
    name: str = Field(..., min_length=1, max_length=100, description="凭证名称")
    protocol_type: StorageProtocol = Field(..., description="存储协议")
    server_address: Optional[str] = Field(None, description="服务器地址")
    port: Optional[int] = Field(None, ge=1, le=65535, description="端口")
    base_path: Optional[str] = Field("/", description="基础路径")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    
    # 连接设置
    connection_timeout: int = Field(30, ge=1, le=300, description="连接超时（秒）")
    read_timeout: int = Field(60, ge=1, le=600, description="读取超时（秒）")
    max_retries: int = Field(3, ge=0, le=10, description="最大重试次数")
    
    # SSL/TLS设置
    use_ssl: bool = Field(False, description="使用SSL")
    verify_ssl: bool = Field(True, description="验证SSL证书")
    ssl_cert_path: Optional[str] = Field(None, description="SSL证书路径")
    ssl_key_path: Optional[str] = Field(None, description="SSL密钥路径")
    
    # 权限设置
    allowed_extensions: Optional[List[str]] = Field(None, description="允许的文件扩展名")
    max_file_size: Optional[int] = Field(None, ge=1, description="最大文件大小（字节）")
    is_readonly: bool = Field(False, description="只读模式")
    
    # 高级配置
    advanced_config: Optional[Dict[str, Any]] = Field(None, description="高级配置")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('凭证名称不能为空')
        return v.strip()
    
    @validator('base_path')
    def validate_base_path(cls, v):
        if v and not v.startswith('/'):
            return '/' + v
        return v or '/'
    
    @validator('allowed_extensions')
    def validate_allowed_extensions(cls, v):
        if v:
            # 确保扩展名以点开头
            return [ext if ext.startswith('.') else '.' + ext for ext in v]
        return v


class StorageCredentialCreate(StorageCredentialBase):
    """存储凭证创建模式"""
    
    # 认证信息
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    access_key: Optional[str] = Field(None, description="访问密钥")
    secret_key: Optional[str] = Field(None, description="秘密密钥")
    token: Optional[str] = Field(None, description="访问令牌")
    
    is_active: bool = Field(True, description="是否激活")
    is_default: bool = Field(False, description="是否默认")
    
    @validator('username')
    def validate_username(cls, v, values):
        protocol = values.get('protocol_type')
        if protocol in [StorageProtocol.SMB, StorageProtocol.FTP, StorageProtocol.SFTP] and not v:
            raise ValueError(f'{protocol.value}协议需要用户名')
        return v
    
    @validator('password')
    def validate_password(cls, v, values):
        protocol = values.get('protocol_type')
        username = values.get('username')
        if protocol in [StorageProtocol.SMB, StorageProtocol.FTP] and username and not v:
            raise ValueError(f'{protocol.value}协议需要密码')
        return v
    
    @validator('access_key')
    def validate_access_key(cls, v, values):
        protocol = values.get('protocol_type')
        if protocol in [StorageProtocol.S3, StorageProtocol.AZURE_BLOB, StorageProtocol.GCS] and not v:
            raise ValueError(f'{protocol.value}协议需要访问密钥')
        return v
    
    @validator('secret_key')
    def validate_secret_key(cls, v, values):
        protocol = values.get('protocol_type')
        access_key = values.get('access_key')
        if protocol == StorageProtocol.S3 and access_key and not v:
            raise ValueError('S3协议需要秘密密钥')
        return v


class StorageCredentialUpdate(BaseModel):
    """存储凭证更新模式"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="凭证名称")
    server_address: Optional[str] = Field(None, description="服务器地址")
    port: Optional[int] = Field(None, ge=1, le=65535, description="端口")
    base_path: Optional[str] = Field(None, description="基础路径")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    
    # 认证信息
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    access_key: Optional[str] = Field(None, description="访问密钥")
    secret_key: Optional[str] = Field(None, description="秘密密钥")
    token: Optional[str] = Field(None, description="访问令牌")
    
    # 连接设置
    connection_timeout: Optional[int] = Field(None, ge=1, le=300, description="连接超时（秒）")
    read_timeout: Optional[int] = Field(None, ge=1, le=600, description="读取超时（秒）")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="最大重试次数")
    
    # SSL/TLS设置
    use_ssl: Optional[bool] = Field(None, description="使用SSL")
    verify_ssl: Optional[bool] = Field(None, description="验证SSL证书")
    ssl_cert_path: Optional[str] = Field(None, description="SSL证书路径")
    ssl_key_path: Optional[str] = Field(None, description="SSL密钥路径")
    
    # 权限设置
    allowed_extensions: Optional[List[str]] = Field(None, description="允许的文件扩展名")
    max_file_size: Optional[int] = Field(None, ge=1, description="最大文件大小（字节）")
    is_readonly: Optional[bool] = Field(None, description="只读模式")
    
    # 状态
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_default: Optional[bool] = Field(None, description="是否默认")
    
    # 高级配置
    advanced_config: Optional[Dict[str, Any]] = Field(None, description="高级配置")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('凭证名称不能为空')
        return v.strip() if v else v
    
    @validator('base_path')
    def validate_base_path(cls, v):
        if v and not v.startswith('/'):
            return '/' + v
        return v
    
    @validator('allowed_extensions')
    def validate_allowed_extensions(cls, v):
        if v:
            # 确保扩展名以点开头
            return [ext if ext.startswith('.') else '.' + ext for ext in v]
        return v


class StorageCredentialResponse(StorageCredentialBase):
    """存储凭证响应模式"""
    
    id: int = Field(..., description="凭证ID")
    is_active: bool = Field(..., description="是否激活")
    is_default: bool = Field(..., description="是否默认")
    
    # 统计信息
    total_connections: int = Field(0, description="总连接数")
    successful_connections: int = Field(0, description="成功连接数")
    failed_connections: int = Field(0, description="失败连接数")
    total_files_accessed: int = Field(0, description="访问文件总数")
    total_bytes_transferred: int = Field(0, description="传输字节总数")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    
    # 健康检查
    health_status: Optional[str] = Field(None, description="健康状态")
    last_health_check_at: Optional[datetime] = Field(None, description="最后健康检查时间")
    health_check_error: Optional[str] = Field(None, description="健康检查错误")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StorageCredentialTest(BaseModel):
    """存储凭证测试模式"""
    
    test_path: Optional[str] = Field("/", description="测试路径")
    test_operation: str = Field("list", description="测试操作")
    
    @validator('test_operation')
    def validate_test_operation(cls, v):
        allowed_operations = ['list', 'read', 'write', 'delete']
        if v not in allowed_operations:
            raise ValueError(f'测试操作必须是以下之一: {", ".join(allowed_operations)}')
        return v


class StorageCredentialTestResponse(BaseModel):
    """存储凭证测试响应模式"""
    
    success: bool = Field(..., description="是否成功")
    operation: str = Field(..., description="测试操作")
    path: str = Field(..., description="测试路径")
    response_time: Optional[float] = Field(None, description="响应时间（毫秒）")
    file_count: Optional[int] = Field(None, description="文件数量")
    total_size: Optional[int] = Field(None, description="总大小（字节）")
    error_message: Optional[str] = Field(None, description="错误信息")
    tested_at: datetime = Field(..., description="测试时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StorageCredentialHealthCheck(BaseModel):
    """存储凭证健康检查模式"""
    
    credential_id: int = Field(..., description="凭证ID")
    status: str = Field(..., description="状态")
    response_time: Optional[float] = Field(None, description="响应时间（毫秒）")
    error_message: Optional[str] = Field(None, description="错误信息")
    checked_at: datetime = Field(..., description="检查时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StorageCredentialUsage(BaseModel):
    """存储凭证使用情况模式"""
    
    credential_id: int = Field(..., description="凭证ID")
    credential_name: str = Field(..., description="凭证名称")
    connections_count: int = Field(0, description="连接数量")
    files_accessed: int = Field(0, description="访问文件数")
    bytes_transferred: int = Field(0, description="传输字节数")
    success_rate: float = Field(0.0, description="成功率")
    average_response_time: Optional[float] = Field(None, description="平均响应时间")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StorageCredentialStats(BaseModel):
    """存储凭证统计模式"""
    
    total_credentials: int = Field(0, description="总凭证数")
    active_credentials: int = Field(0, description="活跃凭证数")
    total_connections: int = Field(0, description="总连接数")
    successful_connections: int = Field(0, description="成功连接数")
    total_files_accessed: int = Field(0, description="访问文件总数")
    total_bytes_transferred: int = Field(0, description="传输字节总数")
    average_success_rate: float = Field(0.0, description="平均成功率")
    most_used_protocol: Optional[str] = Field(None, description="最常用协议")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StorageFileInfo(BaseModel):
    """存储文件信息模式"""
    
    name: str = Field(..., description="文件名")
    path: str = Field(..., description="文件路径")
    size: int = Field(..., description="文件大小（字节）")
    is_directory: bool = Field(..., description="是否为目录")
    modified_at: Optional[datetime] = Field(None, description="修改时间")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    permissions: Optional[str] = Field(None, description="权限")
    mime_type: Optional[str] = Field(None, description="MIME类型")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StorageListRequest(BaseModel):
    """存储列表请求模式"""
    
    path: str = Field("/", description="路径")
    recursive: bool = Field(False, description="递归列出")
    include_hidden: bool = Field(False, description="包含隐藏文件")
    file_pattern: Optional[str] = Field(None, description="文件模式")
    max_depth: Optional[int] = Field(None, ge=1, le=10, description="最大深度")


class StorageListResponse(BaseModel):
    """存储列表响应模式"""
    
    path: str = Field(..., description="路径")
    files: List[StorageFileInfo] = Field(..., description="文件列表")
    total_files: int = Field(..., description="文件总数")
    total_directories: int = Field(..., description="目录总数")
    total_size: int = Field(..., description="总大小（字节）")
    listed_at: datetime = Field(..., description="列出时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StorageUploadRequest(BaseModel):
    """存储上传请求模式"""
    
    path: str = Field(..., description="上传路径")
    filename: str = Field(..., description="文件名")
    overwrite: bool = Field(False, description="是否覆盖")
    create_directories: bool = Field(True, description="创建目录")
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v.strip():
            raise ValueError('文件名不能为空')
        # 检查文件名中的非法字符
        illegal_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in illegal_chars:
            if char in v:
                raise ValueError(f'文件名不能包含字符: {char}')
        return v.strip()


class StorageUploadResponse(BaseModel):
    """存储上传响应模式"""
    
    success: bool = Field(..., description="是否成功")
    path: str = Field(..., description="上传路径")
    filename: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小（字节）")
    upload_time: float = Field(..., description="上传时间（秒）")
    upload_speed: float = Field(..., description="上传速度（字节/秒）")
    error_message: Optional[str] = Field(None, description="错误信息")
    uploaded_at: datetime = Field(..., description="上传时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StorageDownloadRequest(BaseModel):
    """存储下载请求模式"""
    
    path: str = Field(..., description="下载路径")
    range_start: Optional[int] = Field(None, ge=0, description="范围开始")
    range_end: Optional[int] = Field(None, ge=0, description="范围结束")
    
    @validator('range_end')
    def validate_range_end(cls, v, values):
        range_start = values.get('range_start')
        if v is not None and range_start is not None and v <= range_start:
            raise ValueError('范围结束必须大于范围开始')
        return v


class StorageDownloadResponse(BaseModel):
    """存储下载响应模式"""
    
    success: bool = Field(..., description="是否成功")
    path: str = Field(..., description="下载路径")
    filename: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小（字节）")
    download_time: float = Field(..., description="下载时间（秒）")
    download_speed: float = Field(..., description="下载速度（字节/秒）")
    content_type: Optional[str] = Field(None, description="内容类型")
    error_message: Optional[str] = Field(None, description="错误信息")
    downloaded_at: datetime = Field(..., description="下载时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StorageDeleteRequest(BaseModel):
    """存储删除请求模式"""
    
    paths: List[str] = Field(..., min_items=1, description="删除路径列表")
    recursive: bool = Field(False, description="递归删除")
    force: bool = Field(False, description="强制删除")


class StorageDeleteResponse(BaseModel):
    """存储删除响应模式"""
    
    success: bool = Field(..., description="是否成功")
    deleted_paths: List[str] = Field(..., description="已删除路径列表")
    failed_paths: List[str] = Field([], description="删除失败路径列表")
    total_deleted: int = Field(..., description="删除总数")
    error_messages: List[str] = Field([], description="错误信息列表")
    deleted_at: datetime = Field(..., description="删除时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StorageBatchOperation(BaseModel):
    """存储批量操作模式"""
    
    credential_ids: List[int] = Field(..., min_items=1, description="凭证ID列表")
    operation: str = Field(..., description="操作类型")
    parameters: Dict[str, Any] = Field({}, description="操作参数")
    
    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ['test', 'health_check', 'list', 'cleanup']
        if v not in allowed_operations:
            raise ValueError(f'操作类型必须是以下之一: {", ".join(allowed_operations)}')
        return v


class StorageBatchOperationResponse(BaseModel):
    """存储批量操作响应模式"""
    
    operation: str = Field(..., description="操作类型")
    total_processed: int = Field(..., description="处理总数")
    successful_operations: int = Field(..., description="成功操作数")
    failed_operations: int = Field(..., description="失败操作数")
    results: List[Dict[str, Any]] = Field(..., description="结果列表")
    executed_at: datetime = Field(..., description="执行时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }