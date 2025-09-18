from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ProtocolType(str, enum.Enum):
    """存储协议类型枚举"""
    SMB = "smb"          # Windows共享
    NFS = "nfs"          # 网络文件系统
    FTP = "ftp"          # 文件传输协议
    SFTP = "sftp"        # 安全文件传输协议
    HTTP = "http"        # HTTP协议
    HTTPS = "https"      # HTTPS协议
    S3 = "s3"            # Amazon S3
    OSS = "oss"          # 阿里云对象存储
    COS = "cos"          # 腾讯云对象存储
    LOCAL = "local"      # 本地文件系统
    WEBDAV = "webdav"    # WebDAV协议


class StorageCredential(Base):
    """存储凭证模型"""
    
    __tablename__ = "storage_credentials"
    
    id = Column(Integer, primary_key=True, index=True, comment="凭证ID")
    name = Column(String(100), nullable=False, comment="配置名称")
    display_name = Column(String(200), comment="显示名称")
    protocol_type = Column(
        String(20), 
        nullable=False, 
        comment="协议类型"
    )
    
    # 服务器配置
    server_host = Column(String(255), nullable=False, comment="服务器地址")
    server_port = Column(Integer, comment="服务器端口")
    base_path = Column(String(500), default="/", comment="基础路径")
    
    # 认证信息（明文存储，简化处理）
    username = Column(String(255), comment="用户名")
    password = Column(String(255), comment="密码") 
    access_key = Column(String(500), comment="访问密钥")
    secret_key = Column(String(500), comment="密钥")
    token = Column(Text, comment="令牌")
    
    # 保留加密字段用于兼容性（可选）
    username_encrypted = Column(Text, comment="加密的用户名（已废弃）")
    password_encrypted = Column(Text, comment="加密的密码（已废弃）")
    access_key_encrypted = Column(Text, comment="加密的访问密钥（已废弃）")
    secret_key_encrypted = Column(Text, comment="加密的密钥（已废弃）")
    token_encrypted = Column(Text, comment="加密的令牌（已废弃）")
    
    # 连接配置
    connection_timeout = Column(Integer, default=30, comment="连接超时时间（秒）")
    read_timeout = Column(Integer, default=60, comment="读取超时时间（秒）")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    
    # SSL/TLS配置
    use_ssl = Column(Boolean, default=False, comment="是否使用SSL")
    verify_ssl = Column(Boolean, default=True, comment="是否验证SSL证书")
    ssl_cert_path = Column(String(500), comment="SSL证书路径")
    
    # 高级配置（JSON格式）
    advanced_config = Column(JSON, comment="高级配置")
    
    # 权限配置
    allowed_extensions = Column(JSON, comment="允许的文件扩展名")
    max_file_size = Column(Integer, comment="最大文件大小（字节）")
    read_only = Column(Boolean, default=False, comment="是否只读")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认凭证")
    
    # 描述信息
    description = Column(Text, comment="描述")
    usage_notes = Column(Text, comment="使用说明")
    
    # 统计信息
    total_connections = Column(Integer, default=0, comment="总连接次数")
    successful_connections = Column(Integer, default=0, comment="成功连接次数")
    failed_connections = Column(Integer, default=0, comment="失败连接次数")
    total_files_accessed = Column(Integer, default=0, comment="总访问文件数")
    total_bytes_transferred = Column(Integer, default=0, comment="总传输字节数")
    last_used_at = Column(DateTime(timezone=True), comment="最后使用时间")
    
    # 健康检查
    last_health_check = Column(DateTime(timezone=True), comment="最后健康检查时间")
    health_status = Column(String(20), default="unknown", comment="健康状态")
    health_message = Column(Text, comment="健康检查消息")
    
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
        return f"<StorageCredential(id={self.id}, name='{self.name}', protocol='{self.protocol_type}')>"
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "protocol_type": self.protocol_type.value if self.protocol_type else None,
            "server_host": self.server_host,
            "server_port": self.server_port,
            "base_path": self.base_path,
            "connection_timeout": self.connection_timeout,
            "read_timeout": self.read_timeout,
            "max_retries": self.max_retries,
            "use_ssl": self.use_ssl,
            "verify_ssl": self.verify_ssl,
            "ssl_cert_path": self.ssl_cert_path,
            "advanced_config": self.advanced_config,
            "allowed_extensions": self.allowed_extensions,
            "max_file_size": self.max_file_size,
            "read_only": self.read_only,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "description": self.description,
            "usage_notes": self.usage_notes,
            "total_connections": self.total_connections,
            "successful_connections": self.successful_connections,
            "failed_connections": self.failed_connections,
            "total_files_accessed": self.total_files_accessed,
            "total_bytes_transferred": self.total_bytes_transferred,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_status": self.health_status,
            "health_message": self.health_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # 敏感信息只在需要时包含
        if include_sensitive:
            data.update({
                "username": self.username,
                "password": self.password,
                "access_key": self.access_key,
                "secret_key": self.secret_key,
                "token": self.token,
                # 兼容性：包含加密字段
                "username_encrypted": self.username_encrypted,
                "password_encrypted": self.password_encrypted,
                "access_key_encrypted": self.access_key_encrypted,
                "secret_key_encrypted": self.secret_key_encrypted,
                "token_encrypted": self.token_encrypted,
            })
        else:
            data.update({
                "has_username": bool(self.username or self.username_encrypted),
                "has_password": bool(self.password or self.password_encrypted),
                "has_access_key": bool(self.access_key or self.access_key_encrypted),
                "has_secret_key": bool(self.secret_key or self.secret_key_encrypted),
                "has_token": bool(self.token or self.token_encrypted),
            })
        
        return data
    
    def get_connection_url(self) -> str:
        """获取连接URL（不包含敏感信息）"""
        protocol = self.protocol_type.value
        host = self.server_host
        port = self.server_port
        path = self.base_path or "/"
        
        if port:
            return f"{protocol}://{host}:{port}{path}"
        else:
            return f"{protocol}://{host}{path}"
    
    def get_default_port(self) -> int:
        """获取协议默认端口"""
        default_ports = {
            ProtocolType.SMB: 445,
            ProtocolType.NFS: 2049,
            ProtocolType.FTP: 21,
            ProtocolType.SFTP: 22,
            ProtocolType.HTTP: 80,
            ProtocolType.HTTPS: 443,
            ProtocolType.WEBDAV: 80,
        }
        return default_ports.get(self.protocol_type, 0)
    
    def requires_authentication(self) -> bool:
        """检查是否需要认证"""
        auth_required_protocols = {
            ProtocolType.SMB,
            ProtocolType.FTP,
            ProtocolType.SFTP,
            ProtocolType.S3,
            ProtocolType.OSS,
            ProtocolType.COS,
            ProtocolType.WEBDAV,
        }
        return self.protocol_type in auth_required_protocols
    
    def is_cloud_storage(self) -> bool:
        """检查是否为云存储"""
        cloud_protocols = {
            ProtocolType.S3,
            ProtocolType.OSS,
            ProtocolType.COS,
        }
        return self.protocol_type in cloud_protocols
    
    def update_connection_stats(self, success: bool, bytes_transferred: int = 0, files_accessed: int = 0):
        """更新连接统计"""
        self.total_connections += 1
        
        if success:
            self.successful_connections += 1
        else:
            self.failed_connections += 1
        
        if bytes_transferred > 0:
            self.total_bytes_transferred += bytes_transferred
        
        if files_accessed > 0:
            self.total_files_accessed += files_accessed
        
        from datetime import datetime
        self.last_used_at = datetime.utcnow()
    
    def get_success_rate(self) -> float:
        """获取连接成功率"""
        if self.total_connections == 0:
            return 0.0
        return (self.successful_connections / self.total_connections) * 100
    
    def is_healthy(self) -> bool:
        """检查存储是否健康"""
        return self.health_status == "healthy"
    
    def can_access_file(self, file_path: str) -> bool:
        """检查是否可以访问指定文件"""
        if not self.is_active or not self.is_healthy():
            return False
        
        # 检查文件扩展名
        if self.allowed_extensions:
            import os
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.allowed_extensions:
                return False
        
        return True
    
    def get_connection_config(self) -> dict:
        """获取连接配置"""
        config = {
            "protocol": self.protocol_type.value,
            "host": self.server_host,
            "port": self.server_port or self.get_default_port(),
            "base_path": self.base_path,
            "timeout": self.connection_timeout,
            "read_timeout": self.read_timeout,
            "max_retries": self.max_retries,
            "use_ssl": self.use_ssl,
            "verify_ssl": self.verify_ssl,
        }
        
        if self.ssl_cert_path:
            config["ssl_cert_path"] = self.ssl_cert_path
        
        if self.advanced_config:
            config.update(self.advanced_config)
        
        return config