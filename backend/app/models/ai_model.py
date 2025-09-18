from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ModelType(str, enum.Enum):
    """AI模型类型枚举"""
    OPENAI_COMPATIBLE = "OpenAI-Compatible"
    GEMINI = "Gemini"
    CLAUDE = "Claude" 
    OTHER = "Other"


class AIModel(Base):
    """AI模型配置模型"""
    
    __tablename__ = "ai_models"
    
    id = Column(Integer, primary_key=True, index=True, comment="模型ID")
    name = Column(String(100), nullable=False, comment="模型名称")
    display_name = Column(String(200), comment="显示名称")
    model_type = Column(
        SQLEnum(ModelType, values_callable=lambda obj: [e.value for e in obj]), 
        nullable=False, 
        comment="模型类型"
    )
    
    # API配置
    api_endpoint = Column(String(500), nullable=False, comment="API端点")
    api_key = Column(Text, comment="API密钥")
    model_name = Column(String(100), comment="具体模型名称（如gpt-4）")
    
    # 模型参数（移除max_tokens，统一使用任务级别配置）
    temperature = Column(String(10), default="0.7", comment="温度参数")
    top_p = Column(String(10), default="1.0", comment="top_p参数")
    frequency_penalty = Column(String(10), default="0.0", comment="频率惩罚")
    presence_penalty = Column(String(10), default="0.0", comment="存在惩罚")
    
    # 默认参数（JSON格式）
    default_params = Column(JSON, comment="默认参数配置")
    
    # 功能支持
    supports_streaming = Column(Boolean, default=True, comment="是否支持流式输出")
    supports_function_calling = Column(Boolean, default=False, comment="是否支持函数调用")
    supports_vision = Column(Boolean, default=False, comment="是否支持视觉理解")
    supports_multimodal = Column(Boolean, default=False, comment="是否支持多模态")
    
    # 限制配置
    rate_limit_per_minute = Column(Integer, default=60, comment="每分钟请求限制")
    rate_limit_per_day = Column(Integer, default=1000, comment="每天请求限制")
    max_concurrent_requests = Column(Integer, default=5, comment="最大并发请求数")
    
    # 成本配置
    cost_per_1k_input_tokens = Column(String(20), comment="每1K输入token成本")
    cost_per_1k_output_tokens = Column(String(20), comment="每1K输出token成本")
    currency = Column(String(10), default="USD", comment="货币单位")
    
    # 网络代理配置
    use_proxy = Column(Boolean, default=False, comment="是否使用网络代理")
    proxy_url = Column(String(500), comment="代理服务器地址")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认模型")
    
    # 描述信息
    description = Column(Text, comment="模型描述")
    usage_notes = Column(Text, comment="使用说明")
    
    # 统计信息
    total_requests = Column(Integer, default=0, comment="总请求次数")
    total_tokens_used = Column(Integer, default=0, comment="总使用token数")
    total_cost = Column(String(20), default="0.00", comment="总成本")
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
        return f"<AIModel(id={self.id}, name='{self.name}', type='{self.model_type}')>"
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "model_type": self.model_type.value if self.model_type else None,
            "api_endpoint": self.api_endpoint,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "default_params": self.default_params,
            "supports_streaming": self.supports_streaming,
            "supports_function_calling": self.supports_function_calling,
            "supports_vision": self.supports_vision,
            "supports_multimodal": self.supports_multimodal,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "rate_limit_per_day": self.rate_limit_per_day,
            "max_concurrent_requests": self.max_concurrent_requests,
            "cost_per_1k_input_tokens": self.cost_per_1k_input_tokens,
            "cost_per_1k_output_tokens": self.cost_per_1k_output_tokens,
            "currency": self.currency,
            "use_proxy": self.use_proxy,
            "proxy_url": self.proxy_url,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "description": self.description,
            "usage_notes": self.usage_notes,
            "total_requests": self.total_requests,
            "total_tokens_used": self.total_tokens_used,
            "total_cost": self.total_cost,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_status": self.health_status,
            "health_message": self.health_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # 敏感信息只在需要时包含
        if include_sensitive:
            data["api_key"] = self.api_key
        else:
            data["has_api_key"] = bool(self.api_key)
        
        return data
    
    def get_request_params(self, custom_params=None):
        """获取请求参数"""
        params = {
            "model": self.model_name or self.name,
            "max_tokens": self.max_tokens,
            "temperature": float(self.temperature) if self.temperature else 0.7,
            "top_p": float(self.top_p) if self.top_p else 1.0,
            "frequency_penalty": float(self.frequency_penalty) if self.frequency_penalty else 0.0,
            "presence_penalty": float(self.presence_penalty) if self.presence_penalty else 0.0,
        }
        
        # 合并默认参数
        if self.default_params:
            params.update(self.default_params)
        
        # 合并自定义参数
        if custom_params:
            params.update(custom_params)
        
        return params
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算成本"""
        try:
            input_cost = 0.0
            output_cost = 0.0
            
            if self.cost_per_1k_input_tokens:
                input_cost = (input_tokens / 1000) * float(self.cost_per_1k_input_tokens)
            
            if self.cost_per_1k_output_tokens:
                output_cost = (output_tokens / 1000) * float(self.cost_per_1k_output_tokens)
            
            return input_cost + output_cost
        except (ValueError, TypeError):
            return 0.0
    
    def update_usage_stats(self, tokens_used: int, cost: float = 0.0):
        """更新使用统计"""
        self.total_requests += 1
        self.total_tokens_used += tokens_used
        
        try:
            current_cost = float(self.total_cost) if self.total_cost else 0.0
            self.total_cost = str(current_cost + cost)
        except (ValueError, TypeError):
            self.total_cost = str(cost)
        
        from datetime import datetime
        self.last_used_at = datetime.utcnow()
    
    def is_healthy(self) -> bool:
        """检查模型是否健康"""
        return self.health_status == "healthy"
    
    def can_make_request(self) -> bool:
        """检查是否可以发起请求"""
        return self.is_active and self.is_healthy() and bool(self.api_key)