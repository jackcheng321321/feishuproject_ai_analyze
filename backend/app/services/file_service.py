"""文件服务模块 - 处理文件上传、下载和网络文件获取"""

import os
import shutil
import aiofiles
import asyncio
import logging
from typing import Dict, Any, Optional, List, BinaryIO
from pathlib import Path, PurePath, PureWindowsPath
from urllib.parse import urlparse
import tempfile
import mimetypes
import hashlib
from datetime import datetime

# 用于网络文件访问
import subprocess
import platform

logger = logging.getLogger(__name__)


class FileService:
    """文件服务类"""
    
    def __init__(self, temp_dir: str = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_extensions = {
            '.txt', '.md', '.doc', '.docx', '.pdf', '.rtf',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
            '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv',
            '.mp3', '.wav', '.flac', '.aac',
            '.zip', '.rar', '.7z', '.tar', '.gz',
            '.py', '.js', '.html', '.css', '.json', '.xml',
            '.csv', '.xlsx', '.xls', '.pptx', '.ppt'
        }
        
        # 确保临时目录存在
        os.makedirs(self.temp_dir, exist_ok=True)
        logger.info(f"文件服务初始化，临时目录: {self.temp_dir}")
    
    def generate_file_hash(self, file_content: bytes) -> str:
        """生成文件哈希"""
        return hashlib.sha256(file_content).hexdigest()
    
    def is_allowed_file(self, filename: str) -> bool:
        """检查文件是否被允许"""
        ext = Path(filename).suffix.lower()
        return ext in self.allowed_extensions
    
    def get_file_type(self, filename: str) -> str:
        """获取文件类型"""
        ext = Path(filename).suffix.lower()
        
        # 文档类型
        if ext in {'.txt', '.md', '.rtf'}:
            return 'text'
        elif ext in {'.doc', '.docx', '.pdf'}:
            return 'document'
        elif ext in {'.csv', '.xlsx', '.xls'}:
            return 'spreadsheet'
        elif ext in {'.pptx', '.ppt'}:
            return 'presentation'
        
        # 媒体类型
        elif ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'}:
            return 'image'
        elif ext in {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'}:
            return 'video'
        elif ext in {'.mp3', '.wav', '.flac', '.aac'}:
            return 'audio'
        
        # 代码类型
        elif ext in {'.py', '.js', '.html', '.css', '.json', '.xml'}:
            return 'code'
        
        # 压缩文件
        elif ext in {'.zip', '.rar', '.7z', '.tar', '.gz'}:
            return 'archive'
        
        else:
            return 'other'
    
    async def save_uploaded_file(
        self, 
        file_content: bytes, 
        filename: str,
        subfolder: str = None
    ) -> Dict[str, Any]:
        """保存上传的文件"""
        try:
            logger.info(f"保存上传文件: {filename}")
            
            # 检查文件大小
            if len(file_content) > self.max_file_size:
                raise Exception(f"文件过大，超过 {self.max_file_size / 1024 / 1024}MB 限制")
            
            # 检查文件类型
            if not self.is_allowed_file(filename):
                raise Exception(f"不支持的文件类型: {Path(filename).suffix}")
            
            # 生成安全的文件名
            file_hash = self.generate_file_hash(file_content)
            ext = Path(filename).suffix
            safe_filename = f"{file_hash}{ext}"
            
            # 确定保存路径
            if subfolder:
                save_dir = os.path.join(self.temp_dir, subfolder)
                os.makedirs(save_dir, exist_ok=True)
            else:
                save_dir = self.temp_dir
            
            file_path = os.path.join(save_dir, safe_filename)
            
            # 异步写入文件
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # 获取文件信息
            file_info = {
                "original_filename": filename,
                "safe_filename": safe_filename,
                "file_path": file_path,
                "file_size": len(file_content),
                "file_hash": file_hash,
                "file_type": self.get_file_type(filename),
                "mime_type": mimetypes.guess_type(filename)[0],
                "uploaded_at": datetime.utcnow().isoformat(),
                "relative_path": os.path.relpath(file_path, self.temp_dir)
            }
            
            logger.info(f"文件保存成功: {file_path}")
            return file_info
            
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            raise
    
    async def read_file_content(self, file_path: str) -> Dict[str, Any]:
        """读取文件内容"""
        try:
            logger.info(f"读取文件内容: {file_path}")
            
            if not os.path.exists(file_path):
                raise Exception(f"文件不存在: {file_path}")
            
            file_info = {
                "file_path": file_path,
                "file_size": os.path.getsize(file_path),
                "file_type": self.get_file_type(file_path),
                "read_at": datetime.utcnow().isoformat()
            }
            
            # 根据文件类型决定读取方式
            file_type = self.get_file_type(file_path)
            
            if file_type in ['text', 'code']:
                # 文本文件，直接读取内容
                async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = await f.read()
                file_info["content"] = content
                file_info["content_type"] = "text"
                
            elif file_type == 'image':
                # 图像文件，返回base64编码
                async with aiofiles.open(file_path, 'rb') as f:
                    content = await f.read()
                import base64
                file_info["content"] = base64.b64encode(content).decode()
                file_info["content_type"] = "base64"
                
            else:
                # 其他文件类型，只返回文件信息，不读取内容
                file_info["content"] = None
                file_info["content_type"] = "binary"
                file_info["message"] = f"文件类型 {file_type} 不支持内容读取，仅返回文件信息"
            
            logger.info(f"文件读取成功: {file_path}")
            file_info["success"] = True
            file_info["file_name"] = os.path.basename(file_path)
            return file_info
            
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path,
                "message": f"读取文件失败: {str(e)}"
            }
    
    async def get_network_file(self, network_path: str) -> Dict[str, Any]:
        """获取网络文件（支持Windows SMB路径）"""
        try:
            logger.info(f"获取网络文件: {network_path}")
            
            # 解析网络路径
            if network_path.startswith('\\\\'):
                # Windows UNC路径 (\\server\share\path)
                return await self._get_smb_file(network_path)
            elif network_path.startswith('smb://'):
                # SMB URL格式
                return await self._get_smb_url_file(network_path)
            elif network_path.startswith(('http://', 'https://')):
                # HTTP URL
                return await self._get_http_file(network_path)
            elif network_path.startswith('ftp://'):
                # FTP URL
                return await self._get_ftp_file(network_path)
            else:
                # 尝试作为本地路径处理
                if os.path.exists(network_path):
                    return await self.read_file_content(network_path)
                else:
                    raise Exception(f"不支持的网络路径格式或路径不存在: {network_path}")
                    
        except Exception as e:
            logger.error(f"获取网络文件失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": network_path,
                "message": f"获取网络文件失败: {str(e)}"
            }
    
    async def _get_smb_file(self, smb_path: str) -> Dict[str, Any]:
        """获取SMB文件（Windows UNC路径）"""
        try:
            logger.info(f"获取SMB文件: {smb_path}")
            
            # 在Windows系统上，可以直接访问UNC路径
            if platform.system() == 'Windows':
                if os.path.exists(smb_path):
                    # 如果路径存在，直接读取
                    return await self.read_file_content(smb_path)
                else:
                    raise Exception(f"SMB路径不存在或无法访问: {smb_path}")
            else:
                # 在Linux/Mac上，需要使用smbclient或mount
                raise Exception("Linux/Mac系统需要配置SMB客户端支持")
                
        except Exception as e:
            logger.error(f"获取SMB文件失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": smb_path,
                "message": f"获取SMB文件失败: {str(e)}"
            }
    
    async def _get_smb_url_file(self, smb_url: str) -> Dict[str, Any]:
        """获取SMB URL文件"""
        try:
            logger.info(f"获取SMB URL文件: {smb_url}")
            
            # 解析SMB URL: smb://server/share/path
            parsed = urlparse(smb_url)
            server = parsed.hostname
            share_path = parsed.path.lstrip('/')
            
            # 转换为Windows UNC路径
            if platform.system() == 'Windows':
                backslash = '\\'
                unc_path = f"{backslash}{backslash}{server}{backslash}{share_path.replace('/', backslash)}"
                return await self._get_smb_file(unc_path)
            else:
                raise Exception("SMB URL访问需要在Windows系统或配置smbclient")
                
        except Exception as e:
            logger.error(f"获取SMB URL文件失败: {e}")
            raise
    
    async def _get_http_file(self, http_url: str) -> Dict[str, Any]:
        """获取HTTP文件"""
        try:
            logger.info(f"获取HTTP文件: {http_url}")
            
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(http_url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP请求失败: {response.status}")
                    
                    content = await response.read()
                    
                    # 从URL获取文件名
                    filename = os.path.basename(urlparse(http_url).path) or "downloaded_file"
                    
                    # 保存到临时文件
                    file_info = await self.save_uploaded_file(
                        content, filename, subfolder="downloads"
                    )
                    
                    file_info["source_url"] = http_url
                    file_info["download_method"] = "http"
                    
                    return file_info
                    
        except Exception as e:
            logger.error(f"获取HTTP文件失败: {e}")
            raise
    
    async def _get_ftp_file(self, ftp_url: str) -> Dict[str, Any]:
        """获取FTP文件"""
        try:
            logger.info(f"获取FTP文件: {ftp_url}")
            
            # 这里可以实现FTP文件获取
            # 现在先抛出异常，表示功能未实现
            raise Exception("FTP文件获取功能暂未实现")
            
        except Exception as e:
            logger.error(f"获取FTP文件失败: {e}")
            raise
    
    async def list_network_directory(self, network_path: str) -> List[Dict[str, Any]]:
        """列出网络目录内容"""
        try:
            logger.info(f"列出网络目录: {network_path}")
            
            if network_path.startswith('\\\\'):
                # Windows UNC路径
                if platform.system() == 'Windows':
                    return await self._list_smb_directory(network_path)
                else:
                    raise Exception("需要在Windows系统上访问UNC路径")
            elif os.path.isdir(network_path):
                # 本地目录
                return await self._list_local_directory(network_path)
            else:
                raise Exception(f"不支持的目录路径: {network_path}")
                
        except Exception as e:
            logger.error(f"列出目录失败: {e}")
            return []
    
    async def _list_smb_directory(self, smb_path: str) -> List[Dict[str, Any]]:
        """列出SMB目录内容"""
        try:
            if not os.path.exists(smb_path):
                raise Exception(f"SMB目录不存在或无法访问: {smb_path}")
            
            items = []
            for item_name in os.listdir(smb_path):
                item_path = os.path.join(smb_path, item_name)
                
                try:
                    stat = os.stat(item_path)
                    item_info = {
                        "name": item_name,
                        "path": item_path,
                        "is_file": os.path.isfile(item_path),
                        "is_directory": os.path.isdir(item_path),
                        "size": stat.st_size if os.path.isfile(item_path) else None,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "file_type": self.get_file_type(item_name) if os.path.isfile(item_path) else None,
                        "allowed": self.is_allowed_file(item_name) if os.path.isfile(item_path) else True
                    }
                    items.append(item_info)
                except Exception as item_error:
                    logger.warning(f"无法获取项目信息 {item_path}: {item_error}")
                    continue
            
            # 按类型和名称排序（目录在前）
            items.sort(key=lambda x: (not x["is_directory"], x["name"].lower()))
            
            logger.info(f"列出SMB目录成功，项目数量: {len(items)}")
            return items
            
        except Exception as e:
            logger.error(f"列出SMB目录失败: {e}")
            return []
    
    async def _list_local_directory(self, local_path: str) -> List[Dict[str, Any]]:
        """列出本地目录内容"""
        try:
            items = []
            for item_name in os.listdir(local_path):
                item_path = os.path.join(local_path, item_name)
                
                try:
                    stat = os.stat(item_path)
                    item_info = {
                        "name": item_name,
                        "path": item_path,
                        "is_file": os.path.isfile(item_path),
                        "is_directory": os.path.isdir(item_path),
                        "size": stat.st_size if os.path.isfile(item_path) else None,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "file_type": self.get_file_type(item_name) if os.path.isfile(item_path) else None,
                        "allowed": self.is_allowed_file(item_name) if os.path.isfile(item_path) else True
                    }
                    items.append(item_info)
                except Exception as item_error:
                    logger.warning(f"无法获取项目信息 {item_path}: {item_error}")
                    continue
            
            # 按类型和名称排序（目录在前）
            items.sort(key=lambda x: (not x["is_directory"], x["name"].lower()))
            
            logger.info(f"列出本地目录成功，项目数量: {len(items)}")
            return items
            
        except Exception as e:
            logger.error(f"列出本地目录失败: {e}")
            return []
    
    async def cleanup_temp_files(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """清理临时文件"""
        try:
            logger.info(f"开始清理临时文件，最大保留时间: {max_age_hours}小时")
            
            current_time = datetime.utcnow()
            max_age_seconds = max_age_hours * 3600
            
            cleaned_files = 0
            cleaned_size = 0
            
            for root, dirs, files in os.walk(self.temp_dir):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    
                    try:
                        # 检查文件年龄
                        file_stat = os.stat(file_path)
                        file_age = (current_time - datetime.fromtimestamp(file_stat.st_mtime)).total_seconds()
                        
                        if file_age > max_age_seconds:
                            file_size = file_stat.st_size
                            os.remove(file_path)
                            cleaned_files += 1
                            cleaned_size += file_size
                            logger.debug(f"删除过期文件: {file_path}")
                            
                    except Exception as cleanup_error:
                        logger.warning(f"清理文件失败 {file_path}: {cleanup_error}")
                        continue
            
            result = {
                "cleaned_files": cleaned_files,
                "cleaned_size": cleaned_size,
                "cleaned_size_mb": round(cleaned_size / 1024 / 1024, 2),
                "max_age_hours": max_age_hours,
                "cleaned_at": current_time.isoformat()
            }
            
            logger.info(f"临时文件清理完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
            raise


# 创建全局文件服务实例
file_service = FileService()