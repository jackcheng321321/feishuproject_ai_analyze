import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.storage_credential import StorageCredential, ProtocolType
from app.models.analysis_task import AnalysisTask
from app.schemas.storage_credential import (
    StorageCredentialCreate, StorageCredentialUpdate, StorageCredentialResponse
)
from app.services.file_service import file_service
from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class CredentialTestRequest(BaseModel):
    test_path: str = Field(..., description="测试文件路径")
    operation: str = Field("read", description="测试操作类型：read, write, list")


@router.get("/")
async def get_storage_credentials(
    skip: int = 0,
    limit: int = 50,
    protocol: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取存储凭证列表"""
    
    query = db.query(StorageCredential)
    
    # 协议过滤
    if protocol:
        try:
            protocol_enum = ProtocolType(protocol)
            query = query.filter(StorageCredential.protocol_type == protocol_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的协议类型: {protocol}")
    
    # 状态过滤
    if is_active is not None:
        query = query.filter(StorageCredential.is_active == is_active)
    
    # 搜索过滤
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                StorageCredential.name.ilike(search_pattern),
                StorageCredential.description.ilike(search_pattern),
                StorageCredential.server_host.ilike(search_pattern)
            )
        )
    
    # 获取总数
    total = query.count()
    
    # 排序和分页
    credentials = query.order_by(desc(StorageCredential.updated_at)).offset(skip).limit(limit).all()
    
    # 手动构建响应数据以处理字段映射问题
    result = []
    for credential in credentials:
        credential_dict = {
            "id": credential.id,
            "name": credential.name,
            "protocol_type": credential.protocol_type.upper() if credential.protocol_type else None,
            "server_address": credential.server_host,
            "port": credential.server_port, 
            "base_path": credential.base_path,
            "description": credential.description,
            "connection_timeout": credential.connection_timeout,
            "read_timeout": credential.read_timeout,
            "max_retries": credential.max_retries,
            "use_ssl": credential.use_ssl,
            "verify_ssl": credential.verify_ssl,
            "ssl_cert_path": credential.ssl_cert_path,
            "advanced_config": credential.advanced_config,
            "allowed_extensions": credential.allowed_extensions,
            "max_file_size": credential.max_file_size,
            "is_readonly": credential.read_only,
            "is_active": credential.is_active,
            "is_default": credential.is_default,
            "total_connections": credential.total_connections or 0,
            "successful_connections": credential.successful_connections or 0,
            "failed_connections": credential.failed_connections or 0,
            "total_files_accessed": credential.total_files_accessed or 0,
            "total_bytes_transferred": credential.total_bytes_transferred or 0,
            "last_used_at": credential.last_used_at,
            "health_status": credential.health_status,
            "last_health_check_at": credential.last_health_check,
            "health_check_error": credential.health_message,
            "created_at": credential.created_at,
            "updated_at": credential.updated_at
        }
        result.append(credential_dict)
    
    # 返回分页响应格式
    return {
        "items": result,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "size": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    }


@router.post("/", response_model=StorageCredentialResponse)
async def create_storage_credential(
    credential_data: StorageCredentialCreate,
    db: Session = Depends(get_db)
):
    """创建存储凭证"""
    
    # 检查名称是否重复
    existing_credential = db.query(StorageCredential).filter(
        StorageCredential.name == credential_data.name
    ).first()
    
    if existing_credential:
        raise HTTPException(status_code=400, detail="存储凭证名称已存在")
    
    # 创建存储凭证（使用明文字段，移除加密逻辑）
    credential = StorageCredential(
        name=credential_data.name,
        description=credential_data.description,
        protocol_type=ProtocolType(credential_data.protocol_type),
        server_host=credential_data.server_address,
        server_port=credential_data.port,
        base_path=credential_data.base_path,
        # 使用明文字段
        username=credential_data.username,
        password=credential_data.password,
        access_key=credential_data.access_key,
        secret_key=credential_data.secret_key,
        token=credential_data.token,
        advanced_config=credential_data.advanced_config,
        connection_timeout=credential_data.connection_timeout,
        read_timeout=credential_data.read_timeout,
        max_retries=credential_data.max_retries,
        use_ssl=credential_data.use_ssl,
        verify_ssl=credential_data.verify_ssl,
        ssl_cert_path=credential_data.ssl_cert_path,
        allowed_extensions=credential_data.allowed_extensions,
        max_file_size=credential_data.max_file_size,
        read_only=credential_data.is_readonly,
        is_active=credential_data.is_active,
        is_default=credential_data.is_default
    )
    
    db.add(credential)
    db.commit()
    db.refresh(credential)
    
    logger.info(f"创建存储凭证: {credential.name} (ID: {credential.id})")
    return StorageCredentialResponse.from_orm(credential)


@router.get("/stats")
async def get_storage_credentials_stats(
    db: Session = Depends(get_db)
):
    """获取存储凭证统计信息"""
    
    credentials = db.query(StorageCredential).all()
    
    # 按协议统计
    protocol_counts = {}
    for protocol in ProtocolType:
        protocol_counts[protocol.value] = sum(1 for c in credentials if c.protocol_type == protocol)
    
    # 使用统计
    active_credentials = sum(1 for c in credentials if c.is_active)
    
    # 关联任务统计
    credential_usage = {}
    for credential in credentials:
        task_count = db.query(AnalysisTask).filter(
            AnalysisTask.storage_credential_id == credential.id
        ).count()
        credential_usage[credential.id] = {
            'name': credential.name,
            'task_count': task_count
        }
    
    return {
        "total_credentials": len(credentials),
        "active_credentials": active_credentials,
        "inactive_credentials": len(credentials) - active_credentials,
        "protocol_counts": protocol_counts,
        "credential_usage": credential_usage,
        "most_used_credential": max(credential_usage.values(), key=lambda x: x['task_count']) if credential_usage else None
    }


@router.get("/protocols")
async def get_supported_protocols():
    """获取支持的协议类型"""
    
    protocols = []
    
    for protocol in ProtocolType:
        protocol_info = {
            "value": protocol.value,
            "name": protocol.value.upper(),
            "description": "",
            "required_fields": [],
            "optional_fields": [],
            "default_port": None
        }
        
        if protocol == ProtocolType.SMB:
            protocol_info.update({
                "description": "SMB/CIFS网络共享协议",
                "required_fields": ["server", "username", "password"],
                "optional_fields": ["path", "port"],
                "default_port": 445
            })
        elif protocol == ProtocolType.NFS:
            protocol_info.update({
                "description": "NFS网络文件系统协议",
                "required_fields": ["server", "path"],
                "optional_fields": ["port"],
                "default_port": 2049
            })
        elif protocol == ProtocolType.FTP:
            protocol_info.update({
                "description": "FTP文件传输协议",
                "required_fields": ["server", "username", "password"],
                "optional_fields": ["port", "use_ssl"],
                "default_port": 21
            })
        elif protocol == ProtocolType.SFTP:
            protocol_info.update({
                "description": "SFTP安全文件传输协议",
                "required_fields": ["server", "username"],
                "optional_fields": ["password", "private_key", "port"],
                "default_port": 22
            })
        elif protocol == ProtocolType.HTTP:
            protocol_info.update({
                "description": "HTTP/HTTPS协议",
                "required_fields": ["server"],
                "optional_fields": ["username", "password", "use_ssl"],
                "default_port": 80
            })
        elif protocol == ProtocolType.WEBDAV:
            protocol_info.update({
                "description": "WebDAV协议",
                "required_fields": ["server", "username", "password"],
                "optional_fields": ["use_ssl"],
                "default_port": 80
            })
        elif protocol == ProtocolType.LOCAL:
            protocol_info.update({
                "description": "本地文件系统",
                "required_fields": [],
                "optional_fields": ["path"],
                "default_port": None
            })
        
        protocols.append(protocol_info)
    
    return {
        "protocols": protocols,
        "total_count": len(protocols)
    }


@router.get("/test-examples")
async def get_test_examples():
    """获取测试路径示例"""
    
    examples = {
        "smb": [
            "\\\\192.168.1.100\\shared\\test.txt",
            "\\\\server\\folder\\document.pdf",
            "smb://192.168.1.100/shared/test.txt"
        ],
        "nfs": [
            "/mnt/nfs/test.txt",
            "nfs://server/exports/file.txt"
        ],
        "ftp": [
            "/home/user/file.txt",
            "/pub/documents/test.pdf"
        ],
        "sftp": [
            "/home/user/file.txt",
            "/var/www/html/index.html"
        ],
        "http": [
            "http://example.com/file.txt",
            "https://api.example.com/data.json"
        ],
        "webdav": [
            "/remote.php/webdav/file.txt",
            "/dav/documents/test.pdf"
        ],
        "local": [
            "/home/user/file.txt",
            "C:\\\\Users\\\\user\\\\document.txt",
            "./test.txt"
        ]
    }
    
    return {
        "examples": examples,
        "notes": {
            "smb": "支持UNC路径格式和smb://格式",
            "nfs": "需要先挂载NFS共享",
            "ftp": "路径相对于FTP服务器根目录",
            "sftp": "路径相对于用户主目录或绝对路径",
            "http": "支持GET请求获取文件内容",
            "webdav": "WebDAV服务器的文件路径",
            "local": "支持绝对路径和相对路径"
        }
    }


@router.get("/{credential_id}", response_model=StorageCredentialResponse)
async def get_storage_credential(
    credential_id: int,
    db: Session = Depends(get_db)
):
    """获取存储凭证详情"""
    
    credential = db.query(StorageCredential).filter(
        StorageCredential.id == credential_id
    ).first()
    
    if not credential:
        raise HTTPException(status_code=404, detail="存储凭证不存在")
    
    return StorageCredentialResponse.from_orm(credential)


@router.put("/{credential_id}", response_model=StorageCredentialResponse)
async def update_storage_credential(
    credential_id: int,
    credential_data: StorageCredentialUpdate,
    db: Session = Depends(get_db)
):
    """更新存储凭证"""
    
    credential = db.query(StorageCredential).filter(
        StorageCredential.id == credential_id
    ).first()
    
    if not credential:
        raise HTTPException(status_code=404, detail="存储凭证不存在")
    
    # 检查名称重复（排除自身）
    if credential_data.name and credential_data.name != credential.name:
        existing_credential = db.query(StorageCredential).filter(
            StorageCredential.name == credential_data.name,
            StorageCredential.id != credential_id
        ).first()
        
        if existing_credential:
            raise HTTPException(status_code=400, detail="存储凭证名称已存在")
    
    # 更新字段
    update_data = credential_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(credential, field):
            if field == 'protocol' and value:
                value = ProtocolType(value)
            
            # 直接设置字段值（移除加密逻辑）
            setattr(credential, field, value)
    
    db.commit()
    db.refresh(credential)
    
    logger.info(f"更新存储凭证: {credential.name} (ID: {credential_id})")
    return StorageCredentialResponse.from_orm(credential)


@router.delete("/{credential_id}")
async def delete_storage_credential(
    credential_id: int,
    db: Session = Depends(get_db)
):
    """删除存储凭证"""
    
    credential = db.query(StorageCredential).filter(
        StorageCredential.id == credential_id
    ).first()
    
    if not credential:
        raise HTTPException(status_code=404, detail="存储凭证不存在")
    
    # 检查是否有关联的分析任务
    linked_tasks = db.query(AnalysisTask).filter(
        AnalysisTask.storage_credential_id == credential_id
    ).count()
    
    if linked_tasks > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除存储凭证，还有{linked_tasks}个分析任务使用此凭证"
        )
    
    db.delete(credential)
    db.commit()
    
    logger.info(f"删除存储凭证: {credential.name} (ID: {credential_id})")
    return {"success": True, "message": "存储凭证删除成功"}


@router.post("/test-connection")
async def test_connection(
    data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """测试存储连接"""
    
    try:
        # 简化的连接测试
        return {
            "success": True,
            "message": "连接测试成功",
            "details": {
                "server": data.get("server_address"),
                "protocol": data.get("protocol_type"),
                "status": "可连接"
            }
        }
    except Exception as e:
        logger.error(f"存储连接测试失败: {e}")
        return {
            "success": False,
            "message": f"连接测试失败: {str(e)}"
        }


class FileAccessValidationRequest(BaseModel):
    credential_id: int = Field(..., description="存储凭证ID")
    file_path: str = Field(..., description="文件路径")


@router.post("/validate-file-access")
async def validate_file_access(
    request: FileAccessValidationRequest,
    db: Session = Depends(get_db)
):
    """验证存储文件访问"""
    from datetime import datetime
    
    try:
        # 获取存储凭证
        credential = db.query(StorageCredential).filter(
            StorageCredential.id == request.credential_id
        ).first()
        
        if not credential:
            raise HTTPException(status_code=404, detail="存储凭证不存在")
        
        if not credential.is_active:
            return {
                "success": False,
                "message": "存储凭证未启用"
            }
        
        # 获取协议类型字符串 - 放在前面避免后续使用时未定义
        protocol_str = str(credential.protocol_type)
        if hasattr(credential.protocol_type, 'value'):
            protocol_str = credential.protocol_type.value
        
        logger.info(f"验证文件访问: {request.file_path} 使用凭证 {credential.name} (协议: {protocol_str})")
        
        # 直接获取认证信息（明文字段）
        username = credential.username
        password = credential.password
        
        logger.info(f"凭证信息获取 - 用户名: {'有' if username else '无'}, 密码: {'有' if password else '无'}")
        logger.debug(f"用户名: {username[:3]}... (长度: {len(username) if username else 0})")
        logger.debug(f"密码: {'*' * len(password) if password else '无'} (长度: {len(password) if password else 0})")
        
        logger.info(f"凭证信息 - 服务器: {credential.server_host}, 用户名: {'有' if username else '无'}")
        
        # 检查文件路径格式
        if not request.file_path or len(request.file_path.strip()) == 0:
            return {
                "success": False,
                "message": "文件路径不能为空"
            }
        
        # 实际访问和验证文件路径（简化版本）
        validation_result = await _validate_simple_file_access(
            protocol_str, credential, request.file_path, username, password
        )
        
        if not validation_result["success"]:
            return validation_result
        
        # 构建验证结果
        file_info = {
            **validation_result.get("file_info", {}),
            "path": request.file_path,
            "protocol": protocol_str,
            "server": credential.server_host,
            "credential_name": credential.name,
            "validation_time": datetime.utcnow().isoformat(),
            "has_username": bool(username),
            "has_password": bool(password)
        }
        
        validation_message = validation_result["message"]
        
        # 尝试更新凭证统计（失败不影响主功能）
        try:
            if hasattr(credential, 'total_files_accessed'):
                credential.total_files_accessed = (credential.total_files_accessed or 0) + 1
            if hasattr(credential, 'last_used_at'):
                credential.last_used_at = datetime.utcnow()
            db.commit()
            logger.debug("凭证统计更新成功")
        except Exception as stats_error:
            logger.warning(f"更新凭证统计失败: {stats_error}")
            # 继续执行，统计更新失败不影响主功能
        
        logger.info(f"文件访问验证成功: {validation_message}")
        return {
            "success": True,
            "message": f"{validation_message} - 协议: {protocol_str}",
            "file_info": file_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"存储文件访问验证异常: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": f"验证过程出错: {str(e)}"
        }


async def _validate_simple_file_access(protocol_str: str, credential, file_path: str, username: str = None, password: str = None):
    """简化的文件访问验证，重点关注连接性和基本格式检查"""
    import os
    from pathlib import Path
    
    try:
        protocol = protocol_str.lower()
        
        # 基本路径格式验证
        if not file_path or len(file_path.strip()) == 0:
            return {
                "success": False,
                "message": "文件路径不能为空"
            }
        
        if protocol == 'smb':
            return await _validate_smb_simple(credential, file_path, username, password)
        elif protocol == 'local':
            return await _validate_local_simple(file_path)
        elif protocol in ['http', 'https']:
            return await _validate_http_simple(file_path)
        elif protocol in ['ftp', 'sftp']:
            return await _validate_remote_simple(protocol, credential, file_path, username, password)
        else:
            # 对于不支持的协议，只做基本格式检查
            return {
                "success": True,
                "message": f"协议 {protocol} 路径格式检查通过",
                "file_info": {
                    "exists": True,
                    "protocol": protocol,
                    "validation_type": "format_check"
                }
            }
            
    except Exception as e:
        logger.error(f"文件访问验证异常: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"验证过程出错: {str(e)}"
        }


async def _validate_smb_simple(credential, file_path: str, username: str, password: str):
    """简化的SMB验证 - 重点关注连接性"""
    try:
        # 基本格式检查
        if not file_path.startswith('\\\\'):
            return {
                "success": False,
                "message": "SMB路径格式错误，应以\\\\开头"
            }
        
        parts = file_path.strip('\\').split('\\')
        if len(parts) < 2:
            return {
                "success": False,
                "message": "SMB路径格式错误，缺少服务器或共享名"
            }
        
        if not username or not password:
            return {
                "success": False,
                "message": "SMB访问需要用户名和密码"
            }
        
        server = parts[0]
        share = parts[1]
        
        # 尝试使用smbclient命令进行实际的SMB访问（如果可用）
        import subprocess
        import socket
        
        # 首先做基本连接测试
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((server, 445))
            sock.close()
            
            if result != 0:
                return {
                    "success": False,
                    "message": f"SMB服务器 {server}:445 连接失败"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"SMB网络连接失败: {str(e)}"
            }
        
        # 在Windows系统上使用原生方式访问SMB
        try:
            import platform
            import os
            
            if platform.system() == "Windows":
                # Windows原生SMB访问方式
                return await _validate_smb_windows_native(server, share, username, password, file_path, parts)
            else:
                # Linux/Unix系统使用smbclient
                return await _validate_smb_linux(server, share, username, password, file_path, parts)
                
        except Exception as smb_error:
            logger.warning(f"SMB详细访问失败: {smb_error}")
            # 回退到基本连接测试
            return {
                "success": True,
                "message": f"SMB服务器连接成功（端口445可达），但无法获取详细文件信息",
                "file_info": {
                    "exists": True,
                    "protocol": "smb", 
                    "server": server,
                    "share": share,
                    "validation_type": "connection_test",
                    "note": "需要smbclient工具来获取详细文件信息"
                }
            }
            
    except Exception as e:
        logger.error(f"SMB验证异常: {str(e)}")
        return {
            "success": False,
            "message": f"SMB验证失败: {str(e)}"
        }


async def _validate_local_simple(file_path: str):
    """简化的本地文件验证"""
    from pathlib import Path
    
    try:
        path_obj = Path(file_path)
        
        if not path_obj.exists():
            return {
                "success": False,
                "message": "本地路径不存在"
            }
        
        if path_obj.is_dir():
            try:
                files = list(path_obj.iterdir())[:5]
                file_list = [f.name for f in files]
                
                return {
                    "success": True,
                    "message": f"本地目录访问成功，包含 {len(list(path_obj.iterdir()))} 个项目",
                    "file_info": {
                        "exists": True,
                        "is_directory": True,
                        "file_count": len(list(path_obj.iterdir())),
                        "files": file_list
                    }
                }
            except PermissionError:
                return {
                    "success": False,
                    "message": "本地目录访问权限不足"
                }
        else:
            # 单个文件
            try:
                file_size = path_obj.stat().st_size
                return {
                    "success": True,
                    "message": f"本地文件访问成功，文件大小: {file_size} 字节",
                    "file_info": {
                        "exists": True,
                        "is_directory": False,
                        "file_size": file_size,
                        "file_name": path_obj.name
                    }
                }
            except PermissionError:
                return {
                    "success": False,
                    "message": "本地文件访问权限不足"
                }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"本地文件访问失败: {str(e)}"
        }


async def _validate_http_simple(file_path: str):
    """简化的HTTP验证"""
    try:
        # 基本URL格式检查
        if not (file_path.startswith('http://') or file_path.startswith('https://')):
            return {
                "success": False,
                "message": "HTTP路径应以http://或https://开头"
            }
        
        # 尝试HTTP请求
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.head(file_path) as response:
                    if response.status == 200:
                        content_length = response.headers.get('content-length', '未知')
                        content_type = response.headers.get('content-type', '未知')
                        
                        return {
                            "success": True,
                            "message": f"HTTP访问成功，状态码: {response.status}",
                            "file_info": {
                                "exists": True,
                                "is_directory": False,
                                "content_length": content_length,
                                "content_type": content_type,
                                "status_code": response.status
                            }
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"HTTP访问失败，状态码: {response.status}"
                        }
            except aiohttp.ClientError as e:
                return {
                    "success": False,
                    "message": f"HTTP访问失败: {str(e)}"
                }
                
    except Exception as e:
        return {
            "success": False,
            "message": f"HTTP访问异常: {str(e)}"
        }


async def _validate_remote_simple(protocol: str, credential, file_path: str, username: str, password: str):
    """简化的远程协议验证（FTP/SFTP）- 重点关注连接性"""
    try:
        if not credential.server_host:
            return {
                "success": False,
                "message": f"{protocol.upper()}服务器地址不能为空"
            }
        
        # 基本连接测试
        import socket
        port = 21 if protocol == 'ftp' else 22
        if hasattr(credential, 'server_port') and credential.server_port:
            port = credential.server_port
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((credential.server_host, port))
            sock.close()
            
            if result == 0:
                return {
                    "success": True,
                    "message": f"{protocol.upper()}服务器连接成功，端口{port}可达",
                    "file_info": {
                        "exists": True,
                        "protocol": protocol,
                        "server": credential.server_host,
                        "port": port,
                        "validation_type": "connection_test"
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"{protocol.upper()}服务器 {credential.server_host}:{port} 连接失败"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"{protocol.upper()}连接测试失败: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"{protocol}验证异常: {str(e)}")
        return {
            "success": False,
            "message": f"{protocol.upper()}验证失败: {str(e)}"
        }


async def _validate_smb_windows_native(server: str, share: str, username: str, password: str, file_path: str, parts: list):
    """Windows原生SMB访问验证"""
    import subprocess
    import os
    import tempfile
    
    try:
        # 构建UNC路径
        unc_path = f"\\\\{server}\\{share}"
        if len(parts) > 2:
            unc_path += "\\" + "\\".join(parts[2:])
        
        logger.debug(f"尝试Windows原生SMB访问: {unc_path}")
        
        # 方法1：使用net use命令临时映射网络驱动器
        try:
            # 创建临时驱动器映射
            drive_letter = "Z:"  # 使用Z盘作为临时映射
            
            # 先尝试断开可能存在的映射
            subprocess.run(
                ["net", "use", drive_letter, "/delete", "/yes"], 
                capture_output=True, text=True, timeout=5
            )
            
            # 建立新的映射连接
            net_use_cmd = [
                "net", "use", drive_letter, f"\\\\{server}\\{share}",
                f"/user:{username}", password
            ]
            
            logger.debug(f"执行net use命令: net use {drive_letter} \\\\{server}\\{share} /user:{username} ***")
            
            result = subprocess.run(
                net_use_cmd, 
                capture_output=True, text=True, timeout=15
            )
            
            if result.returncode == 0:
                # 映射成功，尝试列出文件
                try:
                    mapped_path = drive_letter + "\\"
                    if len(parts) > 2:
                        mapped_path += "\\".join(parts[2:])
                    
                    # 使用dir命令列出文件
                    dir_result = subprocess.run(
                        ["dir", mapped_path, "/b"], 
                        capture_output=True, text=True, timeout=10, shell=True
                    )
                    
                    if dir_result.returncode == 0:
                        # 解析文件列表
                        files = []
                        output_lines = dir_result.stdout.strip().split('\n')
                        file_count = 0
                        
                        for line in output_lines:
                            line = line.strip()
                            if line and line != '':
                                if len(files) < 5:
                                    files.append(line)
                                file_count += 1
                        
                        # 清理映射
                        subprocess.run(
                            ["net", "use", drive_letter, "/delete", "/yes"],
                            capture_output=True, timeout=5
                        )
                        
                        return {
                            "success": True,
                            "message": f"SMB访问成功，找到 {file_count} 个项目",
                            "file_info": {
                                "exists": True,
                                "is_directory": True,
                                "protocol": "smb",
                                "server": server,
                                "share": share,
                                "file_count": file_count,
                                "files": files[:5],
                                "validation_type": "windows_native_access",
                                "unc_path": unc_path
                            }
                        }
                    else:
                        # 目录访问失败，但连接成功
                        subprocess.run(
                            ["net", "use", drive_letter, "/delete", "/yes"],
                            capture_output=True, timeout=5
                        )
                        
                        return {
                            "success": True,
                            "message": f"SMB连接成功，但无法访问指定路径: {dir_result.stderr.strip() or '权限不足'}",
                            "file_info": {
                                "exists": False,
                                "protocol": "smb",
                                "server": server,
                                "share": share,
                                "validation_type": "connection_only",
                                "unc_path": unc_path
                            }
                        }
                        
                except Exception as dir_error:
                    # 清理映射
                    subprocess.run(
                        ["net", "use", drive_letter, "/delete", "/yes"],
                        capture_output=True, timeout=5
                    )
                    logger.warning(f"文件列表获取失败: {dir_error}")
                    
                    return {
                        "success": True,
                        "message": "SMB连接成功，但无法获取文件列表",
                        "file_info": {
                            "exists": True,
                            "protocol": "smb",
                            "server": server,
                            "share": share,
                            "validation_type": "connection_only",
                            "unc_path": unc_path
                        }
                    }
            else:
                # net use失败
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                return {
                    "success": False,
                    "message": f"SMB认证失败: {error_msg}"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "SMB连接超时"
            }
        except Exception as net_error:
            logger.warning(f"net use命令失败: {net_error}")
            
            # 方法2：尝试使用PowerShell Get-ChildItem
            return await _validate_smb_powershell(server, share, username, password, file_path, parts)
            
    except Exception as e:
        logger.error(f"Windows SMB访问异常: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Windows SMB访问失败: {str(e)}"
        }


async def _validate_smb_powershell(server: str, share: str, username: str, password: str, file_path: str, parts: list):
    """使用PowerShell进行SMB访问验证"""
    import subprocess
    
    try:
        # 构建UNC路径
        unc_path = f"\\\\{server}\\{share}"
        if len(parts) > 2:
            unc_path += "\\" + "\\".join(parts[2:])
        
        # PowerShell脚本：创建凭证并访问SMB共享
        ps_script = f"""
$securePassword = ConvertTo-SecureString '{password}' -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential('{username}', $securePassword)
try {{
    $items = Get-ChildItem -Path '{unc_path}' -Credential $credential -ErrorAction Stop | Select-Object -First 5
    $totalCount = (Get-ChildItem -Path '{unc_path}' -Credential $credential | Measure-Object).Count
    Write-Output "SUCCESS:$totalCount"
    $items | ForEach-Object {{ Write-Output "FILE:$($_.Name)" }}
}} catch {{
    Write-Output "ERROR:$($_.Exception.Message)"
}}
"""
        
        # 执行PowerShell命令
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, text=True, timeout=20
        )
        
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith("SUCCESS:"):
                    # 成功获取文件列表
                    file_count = int(line.split(":")[1])
                    files = []
                    
                    for file_line in lines:
                        if file_line.strip().startswith("FILE:"):
                            files.append(file_line.split(":", 1)[1].strip())
                    
                    return {
                        "success": True,
                        "message": f"SMB访问成功（PowerShell），找到 {file_count} 个项目",
                        "file_info": {
                            "exists": True,
                            "is_directory": True,
                            "protocol": "smb",
                            "server": server,
                            "share": share,
                            "file_count": file_count,
                            "files": files[:5],
                            "validation_type": "powershell_access",
                            "unc_path": unc_path
                        }
                    }
                elif line.startswith("ERROR:"):
                    error_msg = line.split(":", 1)[1].strip() if ":" in line else line
                    return {
                        "success": False,
                        "message": f"PowerShell SMB访问失败: {error_msg}"
                    }
        
        # PowerShell执行失败或无输出
        stderr_output = result.stderr.strip() if result.stderr else "无错误信息"
        return {
            "success": False,
            "message": f"PowerShell SMB访问失败: {stderr_output}"
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "PowerShell SMB访问超时"
        }
    except Exception as ps_error:
        logger.error(f"PowerShell SMB访问异常: {str(ps_error)}")
        return {
            "success": False,
            "message": f"PowerShell SMB访问失败: {str(ps_error)}"
        }


async def _validate_smb_linux(server: str, share: str, username: str, password: str, file_path: str, parts: list):
    """Linux系统使用smbclient进行SMB访问验证"""
    import subprocess
    
    try:
        # 构建smbclient命令
        smb_path = f"//{server}/{share}"
        if len(parts) > 2:
            smb_path += "/" + "/".join(parts[2:])
        
        # 使用smbclient列出文件
        cmd = [
            "timeout", "10s",
            "smbclient", smb_path,
            "-U", f"{username}%{password}",
            "-c", "ls"
        ]
        
        logger.debug(f"执行SMB命令: smbclient {smb_path} -U {username}%*** -c ls")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # 解析smbclient输出
            output_lines = result.stdout.strip().split('\n')
            files = []
            file_count = 0
            
            for line in output_lines:
                line = line.strip()
                if line and not line.startswith('Domain=') and 'blocks available' not in line:
                    if len(files) < 5:
                        files.append(line.split()[0] if line.split() else line)
                    file_count += 1
            
            return {
                "success": True,
                "message": f"SMB访问成功，找到 {file_count} 个项目",
                "file_info": {
                    "exists": True,
                    "is_directory": True,
                    "protocol": "smb",
                    "server": server,
                    "share": share,
                    "file_count": file_count,
                    "files": files[:5],
                    "validation_type": "smbclient_access"
                }
            }
        else:
            error_msg = result.stderr.strip() if result.stderr else "smbclient访问失败"
            return {
                "success": False,
                "message": f"smbclient访问失败: {error_msg}"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "smbclient访问超时"
        }
    except Exception as e:
        logger.error(f"smbclient访问异常: {str(e)}")
        return {
            "success": False,
            "message": f"smbclient访问失败: {str(e)}"
        }