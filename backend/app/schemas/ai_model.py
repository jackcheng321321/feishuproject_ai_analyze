"""AI模型相关Pydantic模式

定义AI模型的创建、更新、响应等数据验证模式。
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class ModelType(str, Enum):
    """模型类型枚举"""
    OPENAI_COMPATIBLE = "OpenAI-Compatible"
    GEMINI = "Gemini" 
    CLAUDE = "Claude"
    OTHER = "Other"


class AIModelBase(BaseModel):
    """AI模型基础模式"""
    
    name: str = Field(..., min_length=1, max_length=100, description="模型名称")
    model_type: ModelType = Field(..., description="模型类型")
    api_endpoint: str = Field(..., description="API端点")
    model_name: str = Field(..., description="模型名称")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    usage_notes: Optional[str] = Field(None, max_length=1000, description="使用说明")
    
    # 模型参数（移除max_tokens，统一使用任务级别配置）
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="温度")
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Top-p")
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="存在惩罚")
    
    # 功能支持
    supports_streaming: bool = Field(True, description="支持流式输出")
    supports_function_calling: bool = Field(False, description="支持函数调用")
    supports_vision: bool = Field(False, description="支持视觉")
    supports_multimodal: bool = Field(False, description="支持多模态")
    
    # 速率限制
    rate_limit_rpm: Optional[int] = Field(None, ge=1, description="每分钟请求限制")
    rate_limit_tpm: Optional[int] = Field(None, ge=1, description="每分钟令牌限制")
    rate_limit_rpd: Optional[int] = Field(None, ge=1, description="每日请求限制")
    
    # 成本设置
    cost_per_input_token: Optional[float] = Field(None, ge=0, description="输入令牌成本")
    cost_per_output_token: Optional[float] = Field(None, ge=0, description="输出令牌成本")
    
    # 网络代理设置
    use_proxy: bool = Field(False, description="是否使用网络代理")
    proxy_url: Optional[str] = Field(None, description="代理服务器地址")
    
    @validator('api_endpoint')
    def validate_api_endpoint(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('API端点必须以http://或https://开头')
        return v
    
    @validator('proxy_url')
    def validate_proxy_url(cls, v, values):
        if values.get('use_proxy') and not v:
            raise ValueError('启用代理时必须设置代理地址')
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('代理地址必须以http://或https://开头')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('模型名称不能为空')
        return v.strip()


class AIModelCreate(AIModelBase):
    """AI模型创建模式"""
    
    api_key: str = Field(..., min_length=1, description="API密钥")
    is_active: bool = Field(True, description="是否激活")
    is_default: bool = Field(False, description="是否默认")
    default_params: Optional[Dict[str, Any]] = Field(None, description="默认参数")
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v.strip():
            raise ValueError('API密钥不能为空')
        return v.strip()


class AIModelUpdate(BaseModel):
    """AI模型更新模式"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模型名称")
    api_endpoint: Optional[str] = Field(None, description="API端点")
    api_key: Optional[str] = Field(None, description="API密钥")
    model_name: Optional[str] = Field(None, description="模型名称")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    usage_notes: Optional[str] = Field(None, max_length=1000, description="使用说明")
    
    # 模型参数（移除max_tokens，统一使用任务级别配置）
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="温度")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top-p")
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="存在惩罚")
    
    # 功能支持
    supports_streaming: Optional[bool] = Field(None, description="支持流式输出")
    supports_function_calling: Optional[bool] = Field(None, description="支持函数调用")
    supports_vision: Optional[bool] = Field(None, description="支持视觉")
    supports_multimodal: Optional[bool] = Field(None, description="支持多模态")
    
    # 速率限制
    rate_limit_rpm: Optional[int] = Field(None, ge=1, description="每分钟请求限制")
    rate_limit_tpm: Optional[int] = Field(None, ge=1, description="每分钟令牌限制")
    rate_limit_rpd: Optional[int] = Field(None, ge=1, description="每日请求限制")
    
    # 成本设置
    cost_per_input_token: Optional[float] = Field(None, ge=0, description="输入令牌成本")
    cost_per_output_token: Optional[float] = Field(None, ge=0, description="输出令牌成本")
    
    # 网络代理设置
    use_proxy: Optional[bool] = Field(None, description="是否使用网络代理")
    proxy_url: Optional[str] = Field(None, description="代理服务器地址")
    
    # 状态
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_default: Optional[bool] = Field(None, description="是否默认")
    
    # 参数
    default_params: Optional[Dict[str, Any]] = Field(None, description="默认参数")
    
    @validator('api_endpoint')
    def validate_api_endpoint(cls, v):
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('API端点必须以http://或https://开头')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('模型名称不能为空')
        return v.strip() if v else v


class AIModelResponse(AIModelBase):
    """AI模型响应模式"""
    
    id: int = Field(..., description="模型ID")
    is_active: bool = Field(..., description="是否激活")
    is_default: bool = Field(..., description="是否默认")
    default_params: Optional[Dict[str, Any]] = Field(None, description="默认参数")
    
    # 统计信息
    total_requests: int = Field(0, description="总请求数")
    total_tokens: int = Field(0, description="总令牌数")
    total_cost: float = Field(0.0, description="总成本")
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


class AIModelHealthCheck(BaseModel):
    """AI模型健康检查模式"""
    
    model_id: int = Field(..., description="模型ID")
    status: str = Field(..., description="状态")
    response_time: Optional[float] = Field(None, description="响应时间（毫秒）")
    error_message: Optional[str] = Field(None, description="错误信息")
    checked_at: datetime = Field(..., description="检查时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AIModelUsage(BaseModel):
    """AI模型使用情况模式"""
    
    model_id: int = Field(..., description="模型ID")
    model_name: str = Field(..., description="模型名称")
    requests_count: int = Field(0, description="请求数量")
    input_tokens: int = Field(0, description="输入令牌数")
    output_tokens: int = Field(0, description="输出令牌数")
    total_tokens: int = Field(0, description="总令牌数")
    total_cost: float = Field(0.0, description="总成本")
    average_response_time: Optional[float] = Field(None, description="平均响应时间")
    success_rate: float = Field(0.0, description="成功率")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AIModelTest(BaseModel):
    """AI模型测试模式"""
    
    prompt: str = Field(..., min_length=1, description="测试提示")
    max_tokens: Optional[int] = Field(None, ge=1, le=4096, description="最大令牌数")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="温度")
    stream: bool = Field(False, description="是否流式输出")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError('测试提示不能为空')
        return v.strip()


class AIModelTestResponse(BaseModel):
    """AI模型测试响应模式"""
    
    success: bool = Field(..., description="是否成功")
    response: Optional[str] = Field(None, description="响应内容")
    input_tokens: Optional[int] = Field(None, description="输入令牌数")
    output_tokens: Optional[int] = Field(None, description="输出令牌数")
    total_tokens: Optional[int] = Field(None, description="总令牌数")
    cost: Optional[float] = Field(None, description="成本")
    response_time: Optional[float] = Field(None, description="响应时间（毫秒）")
    error_message: Optional[str] = Field(None, description="错误信息")
    tested_at: datetime = Field(..., description="测试时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AIModelStats(BaseModel):
    """AI模型统计模式"""
    
    total_models: int = Field(0, description="总模型数")
    active_models: int = Field(0, description="活跃模型数")
    total_requests: int = Field(0, description="总请求数")
    total_tokens: int = Field(0, description="总令牌数")
    total_cost: float = Field(0.0, description="总成本")
    average_response_time: Optional[float] = Field(None, description="平均响应时间")
    success_rate: float = Field(0.0, description="成功率")
    most_used_model: Optional[str] = Field(None, description="最常用模型")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AIModelBatchTest(BaseModel):
    """AI模型批量测试模式"""
    
    model_ids: List[int] = Field(..., min_items=1, description="模型ID列表")
    prompt: str = Field(..., min_length=1, description="测试提示")
    max_tokens: Optional[int] = Field(100, ge=1, le=4096, description="最大令牌数")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="温度")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError('测试提示不能为空')
        return v.strip()


class AIModelBatchTestResponse(BaseModel):
    """AI模型批量测试响应模式"""
    
    results: List[AIModelTestResponse] = Field(..., description="测试结果列表")
    total_tested: int = Field(..., description="测试总数")
    successful_tests: int = Field(..., description="成功测试数")
    failed_tests: int = Field(..., description="失败测试数")
    total_cost: float = Field(0.0, description="总成本")
    average_response_time: Optional[float] = Field(None, description="平均响应时间")
    tested_at: datetime = Field(..., description="测试时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AIModelConfig(BaseModel):
    """AI模型配置模式"""
    
    model_id: int = Field(..., description="模型ID")
    config: Dict[str, Any] = Field(..., description="配置参数")
    
    @validator('config')
    def validate_config(cls, v):
        if not isinstance(v, dict):
            raise ValueError('配置必须是字典格式')
        return v


class AIModelMetrics(BaseModel):
    """AI模型指标模式"""
    
    model_id: int = Field(..., description="模型ID")
    date: datetime = Field(..., description="日期")
    requests_count: int = Field(0, description="请求数量")
    input_tokens: int = Field(0, description="输入令牌数")
    output_tokens: int = Field(0, description="输出令牌数")
    total_cost: float = Field(0.0, description="总成本")
    average_response_time: float = Field(0.0, description="平均响应时间")
    success_rate: float = Field(0.0, description="成功率")
    error_count: int = Field(0, description="错误数量")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AIModelComparison(BaseModel):
    """AI模型比较模式"""
    
    model_ids: List[int] = Field(..., min_items=2, max_items=5, description="模型ID列表")
    metrics: List[str] = Field(
        ["cost", "response_time", "success_rate"], 
        description="比较指标"
    )
    time_range: Optional[str] = Field("7d", description="时间范围")
    
    @validator('metrics')
    def validate_metrics(cls, v):
        allowed_metrics = [
            "cost", "response_time", "success_rate", 
            "tokens", "requests", "errors"
        ]
        for metric in v:
            if metric not in allowed_metrics:
                raise ValueError(f'不支持的指标: {metric}')
        return v


class AIModelComparisonResponse(BaseModel):
    """AI模型比较响应模式"""
    
    models: List[AIModelResponse] = Field(..., description="模型列表")
    comparison_data: Dict[str, Any] = Field(..., description="比较数据")
    recommendations: List[str] = Field([], description="推荐建议")
    generated_at: datetime = Field(..., description="生成时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }