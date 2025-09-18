from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import secrets
import hashlib
import hmac
import base64
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 数据加密器（用于敏感信息加密）
cipher_suite = Fernet(base64.urlsafe_b64encode(settings.ENCRYPTION_KEY.encode()[:32]))


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """创建访问令牌"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    
    logger.debug(f"创建访问令牌，用户: {subject}, 过期时间: {expire}")
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """创建刷新令牌"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    
    logger.debug(f"创建刷新令牌，用户: {subject}, 过期时间: {expire}")
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """验证令牌并返回用户ID"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_type_in_token: str = payload.get("type")
        
        if user_id is None or token_type_in_token != token_type:
            logger.warning(f"令牌验证失败：用户ID或令牌类型不匹配")
            return None
            
        logger.debug(f"令牌验证成功，用户: {user_id}, 类型: {token_type}")
        return user_id
    except JWTError as e:
        logger.warning(f"令牌验证失败: {e}")
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        logger.debug(f"密码验证结果: {result}")
        return result
    except Exception as e:
        logger.error(f"密码验证异常: {e}")
        return False


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    try:
        hashed = pwd_context.hash(password)
        logger.debug("密码哈希生成成功")
        return hashed
    except Exception as e:
        logger.error(f"密码哈希生成失败: {e}")
        raise


def encrypt_sensitive_data(data: str) -> str:
    """加密敏感数据"""
    try:
        encrypted_data = cipher_suite.encrypt(data.encode())
        result = base64.urlsafe_b64encode(encrypted_data).decode()
        logger.debug("敏感数据加密成功")
        return result
    except Exception as e:
        logger.error(f"敏感数据加密失败: {e}")
        raise


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """解密敏感数据"""
    try:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = cipher_suite.decrypt(encrypted_bytes)
        result = decrypted_data.decode()
        logger.debug("敏感数据解密成功")
        return result
    except Exception as e:
        logger.error(f"敏感数据解密失败: {e}")
        raise


def generate_webhook_secret() -> str:
    """生成Webhook密钥"""
    secret = secrets.token_urlsafe(settings.WEBHOOK_SECRET_LENGTH)
    logger.debug("Webhook密钥生成成功")
    return secret


def verify_webhook_signature(
    payload: bytes, signature: str, secret: str
) -> bool:
    """验证Webhook签名"""
    try:
        # 计算期望的签名
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # 比较签名（防止时序攻击）
        result = hmac.compare_digest(
            f"sha256={expected_signature}",
            signature
        )
        
        if result:
            logger.debug("Webhook签名验证成功")
        else:
            logger.warning("Webhook签名验证失败")
            
        return result
    except Exception as e:
        logger.error(f"Webhook签名验证异常: {e}")
        return False


def generate_api_key() -> str:
    """生成API密钥"""
    api_key = secrets.token_urlsafe(32)
    logger.debug("API密钥生成成功")
    return api_key


def hash_api_key(api_key: str) -> str:
    """对API密钥进行哈希"""
    try:
        # 使用SHA-256哈希API密钥
        hashed = hashlib.sha256(api_key.encode()).hexdigest()
        logger.debug("API密钥哈希成功")
        return hashed
    except Exception as e:
        logger.error(f"API密钥哈希失败: {e}")
        raise


def verify_api_key(api_key: str, hashed_api_key: str) -> bool:
    """验证API密钥"""
    try:
        expected_hash = hashlib.sha256(api_key.encode()).hexdigest()
        result = hmac.compare_digest(expected_hash, hashed_api_key)
        
        if result:
            logger.debug("API密钥验证成功")
        else:
            logger.warning("API密钥验证失败")
            
        return result
    except Exception as e:
        logger.error(f"API密钥验证异常: {e}")
        return False


def generate_secure_filename(original_filename: str) -> str:
    """生成安全的文件名"""
    try:
        # 获取文件扩展名
        if "." in original_filename:
            name, ext = original_filename.rsplit(".", 1)
            ext = f".{ext.lower()}"
        else:
            name = original_filename
            ext = ""
        
        # 生成随机文件名
        random_name = secrets.token_urlsafe(16)
        secure_filename = f"{random_name}{ext}"
        
        logger.debug(f"生成安全文件名: {original_filename} -> {secure_filename}")
        return secure_filename
    except Exception as e:
        logger.error(f"生成安全文件名失败: {e}")
        raise


def sanitize_input(input_string: str, max_length: int = 1000) -> str:
    """清理用户输入"""
    try:
        # 移除危险字符
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
        sanitized = input_string
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # 限制长度
        sanitized = sanitized[:max_length]
        
        # 移除首尾空白
        sanitized = sanitized.strip()
        
        logger.debug(f"输入清理完成，原长度: {len(input_string)}, 新长度: {len(sanitized)}")
        return sanitized
    except Exception as e:
        logger.error(f"输入清理失败: {e}")
        return ""


class SecurityManager:
    """安全管理器"""
    
    def __init__(self):
        self.failed_attempts = {}  # 存储失败的登录尝试
    
    def is_rate_limited(self, identifier: str) -> bool:
        """检查是否被限流"""
        try:
            current_time = datetime.utcnow()
            
            if identifier not in self.failed_attempts:
                return False
            
            attempts = self.failed_attempts[identifier]
            
            # 清理过期的尝试记录
            attempts = [
                attempt for attempt in attempts
                if (current_time - attempt).seconds < settings.LOGIN_ATTEMPT_TIMEOUT
            ]
            
            self.failed_attempts[identifier] = attempts
            
            # 检查是否超过最大尝试次数
            if len(attempts) >= settings.MAX_LOGIN_ATTEMPTS:
                logger.warning(f"用户 {identifier} 被限流，尝试次数: {len(attempts)}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"限流检查异常: {e}")
            return False
    
    def record_failed_attempt(self, identifier: str):
        """记录失败的尝试"""
        try:
            current_time = datetime.utcnow()
            
            if identifier not in self.failed_attempts:
                self.failed_attempts[identifier] = []
            
            self.failed_attempts[identifier].append(current_time)
            
            logger.warning(f"记录失败尝试，用户: {identifier}, 总次数: {len(self.failed_attempts[identifier])}")
        except Exception as e:
            logger.error(f"记录失败尝试异常: {e}")
    
    def clear_failed_attempts(self, identifier: str):
        """清除失败的尝试记录"""
        try:
            if identifier in self.failed_attempts:
                del self.failed_attempts[identifier]
                logger.debug(f"清除失败尝试记录，用户: {identifier}")
        except Exception as e:
            logger.error(f"清除失败尝试记录异常: {e}")
    
    def get_security_headers(self) -> dict:
        """获取安全响应头"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }


# 创建全局安全管理器实例
security_manager = SecurityManager()