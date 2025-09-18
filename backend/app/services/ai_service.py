"""AI服务模块 - 统一处理各种AI模型的调用"""

import asyncio
import aiohttp
import json
import logging
import os
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class AIService:
    """AI服务类，统一处理各种AI模型的调用"""
    
    def __init__(self):
        self.session_timeout = aiohttp.ClientTimeout(total=300)  # 5分钟超时
        
        # 获取全局代理配置（作为后备）
        self.default_http_proxy = os.getenv('HTTP_PROXY')
        self.default_https_proxy = os.getenv('HTTPS_PROXY')

        logger.info(f"AI服务默认代理: HTTP={self.default_http_proxy}, HTTPS={self.default_https_proxy}")
    
    async def test_gemini_model(
        self,
        api_key: str,
        model_name: str,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stream: bool = False,
        proxy_url: str = None
    ) -> Tuple[str, Dict[str, int]]:
        """测试Gemini模型"""
        try:
            logger.info(f"=== Gemini API调用开始 ===")
            logger.info(f"模型名称: {model_name}")
            logger.info(f"API密钥前10位: {api_key[:10]}...")
            logger.info(f"最大Token: {max_tokens}")
            logger.info(f"温度: {temperature}")
            logger.info(f"是否流式: {stream}")

            # 确定代理设置 - 只有明确配置的代理才使用
            use_proxy = proxy_url if proxy_url else None
            if use_proxy:
                logger.info(f"使用代理: {use_proxy}")
            else:
                logger.info("不使用代理，直连网络")

            # Gemini API 端点
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            logger.info(f"API端点: {api_url}")
            
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            }
            
            # 构建请求体
            request_body = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "topP": 0.95,
                    "topK": 64
                }
            }
            
            logger.info(f"请求体: {json.dumps(request_body, ensure_ascii=False, indent=2)}")
            
            # 创建连接器，支持代理
            connector = aiohttp.TCPConnector(ssl=True)
            
            async with aiohttp.ClientSession(
                timeout=self.session_timeout,
                connector=connector
            ) as session:
                async with session.post(
                    api_url,
                    headers=headers,
                    json=request_body,
                    proxy=use_proxy  # 使用指定的代理
                ) as response:
                    response_data = await response.json()
                    
                    if response.status != 200:
                        error_msg = response_data.get('error', {}).get('message', '未知错误')
                        logger.error(f"Gemini API调用失败: {response.status}, {error_msg}")
                        raise Exception(f"Gemini API错误: {error_msg}")
                    
                    # 解析响应
                    candidates = response_data.get('candidates', [])
                    if not candidates:
                        raise Exception("Gemini API返回空结果")
                    
                    content = candidates[0].get('content', {})
                    parts = content.get('parts', [])
                    if not parts:
                        raise Exception("Gemini API返回格式错误")
                    
                    # 合并所有parts的文本内容（Gemini可能返回多个parts）
                    response_text = ''
                    if parts:
                        for part in parts:
                            if 'text' in part:
                                response_text += part['text']
                        logger.info(f"合并了 {len(parts)} 个parts的响应内容")
                    
                    # 解析token使用情况
                    usage_metadata = response_data.get('usageMetadata', {})
                    token_usage = {
                        "input_tokens": usage_metadata.get('promptTokenCount', 0),
                        "output_tokens": usage_metadata.get('candidatesTokenCount', 0),
                        "total_tokens": usage_metadata.get('totalTokenCount', 0)
                    }
                    
                    logger.info(f"=== Gemini API调用成功 ===")
                    logger.info(f"HTTP状态码: {response.status}")
                    logger.info(f"响应长度: {len(response_text)} 字符")
                    logger.info(f"Token使用: {token_usage}")
                    logger.info(f"响应内容前200字符: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")
                    return response_text, token_usage
                    
        except Exception as e:
            logger.error(f"Gemini模型调用失败: {e}")
            raise
    
    async def test_gemini_model_with_files(
        self,
        api_key: str,
        model_name: str,
        prompt: str,
        file_contents: List[Dict[str, Any]] = None,
        data_content: str = "",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stream: bool = False,
        proxy_url: str = None
    ) -> Tuple[str, Dict[str, int]]:
        """测试Gemini模型，支持文件内容（多模态）"""
        try:
            logger.info(f"=== Gemini多模态API调用开始 ===")
            logger.info(f"模型名称: {model_name}")
            logger.info(f"API密钥前10位: {api_key[:10]}...")
            logger.info(f"最大Token: {max_tokens}")
            logger.info(f"温度: {temperature}")
            logger.info(f"文件数量: {len(file_contents or [])}")

            # 确定代理设置 - 只有明确配置的代理才使用
            use_proxy = proxy_url if proxy_url else None
            if use_proxy:
                logger.info(f"使用代理: {use_proxy}")
            else:
                logger.info("不使用代理，直连网络")

            # Gemini API 端点
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            logger.info(f"API端点: {api_url}")
            
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            }
            
            # 构建消息内容
            parts = []
            
            # 添加文本提示
            full_prompt = prompt
            if data_content:
                full_prompt += f"\n\n{data_content}"
            parts.append({"text": full_prompt})
            
            # 添加文件内容（图片）
            if file_contents:
                for file_info in file_contents:
                    if file_info.get('file_type') == 'image' and file_info.get('content'):
                        # 获取MIME类型
                        import mimetypes
                        mime_type, _ = mimetypes.guess_type(file_info.get('file_path', ''))
                        if not mime_type or not mime_type.startswith('image/'):
                            mime_type = 'image/jpeg'  # 默认MIME类型
                        
                        parts.append({
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": file_info['content']  # 已经是base64编码
                            }
                        })
                        logger.info(f"添加图片: {file_info.get('file_name')}, MIME: {mime_type}")
                    elif file_info.get('file_type') in ['text', 'code'] and file_info.get('content'):
                        # 文本文件直接添加内容
                        parts.append({
                            "text": f"\n\n文件内容 ({file_info.get('file_name')}):\n{file_info['content']}"
                        })
                        logger.info(f"添加文本文件: {file_info.get('file_name')}")
            
            # 构建请求体
            request_body = {
                "contents": [
                    {
                        "parts": parts
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "topP": 0.95,
                    "topK": 64
                }
            }
            
            logger.info(f"请求体（不包含base64数据）: {json.dumps({**request_body, 'contents': [{'parts': f'{len(parts)} parts'}]}, ensure_ascii=False, indent=2)}")
            
            # 创建连接器，支持代理
            connector = aiohttp.TCPConnector(ssl=True)
            
            async with aiohttp.ClientSession(
                timeout=self.session_timeout,
                connector=connector
            ) as session:
                async with session.post(
                    api_url,
                    headers=headers,
                    json=request_body,
                    proxy=use_proxy  # 使用指定的代理
                ) as response:
                    response_data = await response.json()
                    
                    if response.status != 200:
                        error_msg = response_data.get('error', {}).get('message', '未知错误')
                        logger.error(f"Gemini API调用失败: {response.status}, {error_msg}")
                        raise Exception(f"Gemini API错误: {error_msg}")
                    
                    # 解析响应
                    candidates = response_data.get('candidates', [])
                    if not candidates:
                        raise Exception("Gemini API返回空响应")
                    
                    content = candidates[0].get('content', {})
                    parts = content.get('parts', [])
                    finish_reason = candidates[0].get('finishReason', 'UNKNOWN')
                    
                    # 诊断空响应的原因
                    if not parts:
                        logger.warning(f"Gemini返回空内容 - finishReason: {finish_reason}")
                        logger.warning(f"完整content结构: {content}")
                        if finish_reason == 'SAFETY':
                            logger.error("内容被安全过滤器拦截，请检查图片内容或提示词")
                        elif finish_reason == 'RECITATION':
                            logger.error("内容涉及版权问题被拦截")
                        elif finish_reason == 'OTHER':
                            logger.error("其他原因导致内容生成失败")
                    
                    # 合并所有parts的文本内容（Gemini可能返回多个parts）
                    response_text = ''
                    if parts:
                        for part in parts:
                            if 'text' in part:
                                response_text += part['text']
                        logger.info(f"合并了 {len(parts)} 个parts的响应内容")
                    
                    # 解析token使用情况
                    usage_metadata = response_data.get('usageMetadata', {})
                    token_usage = {
                        "input_tokens": usage_metadata.get('promptTokenCount', 0),
                        "output_tokens": usage_metadata.get('candidatesTokenCount', 0),
                        "total_tokens": usage_metadata.get('totalTokenCount', 0)
                    }
                    
                    logger.info(f"=== Gemini多模态API调用成功 ===")
                    logger.info(f"HTTP状态码: {response.status}")
                    logger.info(f"响应长度: {len(response_text)} 字符")
                    logger.info(f"Token使用: {token_usage}")
                    logger.info(f"响应内容前200字符: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")
                    
                    # 详细调试信息
                    logger.info(f"=== 详细响应信息（调试用）===")
                    logger.info(f"完整响应字符数: {len(response_text)}")
                    logger.info(f"完整响应字节数: {len(response_text.encode('utf-8'))}")
                    logger.info(f"Input Tokens: {token_usage.get('input_tokens', 0)}")
                    logger.info(f"Output Tokens: {token_usage.get('output_tokens', 0)}")
                    logger.info(f"Total Tokens: {token_usage.get('total_tokens', 0)}")
                    logger.info(f"原始API响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    logger.info(f"=== 完整响应内容开始 ===")
                    logger.info(response_text)
                    logger.info(f"=== 完整响应内容结束 ===")
                    
                    return response_text, token_usage
                    
        except Exception as e:
            logger.error(f"Gemini多模态模型调用失败: {e}")
            raise
    
    async def test_openai_model(
        self,
        api_endpoint: str,
        api_key: str,
        model_name: str,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stream: bool = False,
        proxy_url: str = None
    ) -> Tuple[str, Dict[str, int]]:
        """测试OpenAI兼容模型"""
        try:
            logger.info(f"=== OpenAI兼容API调用开始 ===")
            logger.info(f"API端点: {api_endpoint}")
            logger.info(f"模型名称: {model_name}")
            logger.info(f"API密钥前10位: {api_key[:10]}...")
            logger.info(f"最大Token: {max_tokens}")
            logger.info(f"温度: {temperature}")
            logger.info(f"是否流式: {stream}")

            # 确定代理设置 - 只有明确配置的代理才使用
            use_proxy = proxy_url if proxy_url else None
            if use_proxy:
                logger.info(f"使用代理: {use_proxy}")
            else:
                logger.info("不使用代理，直连网络")

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            request_body = {
                "model": model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream
            }
            
            logger.info(f"请求体: {json.dumps(request_body, ensure_ascii=False, indent=2)}")
            
            # 创建连接器，支持代理
            connector = aiohttp.TCPConnector(ssl=True)
            
            async with aiohttp.ClientSession(
                timeout=self.session_timeout,
                connector=connector
            ) as session:
                async with session.post(
                    api_endpoint,
                    headers=headers,
                    json=request_body,
                    proxy=use_proxy  # 使用指定的代理
                ) as response:
                    response_data = await response.json()
                    
                    if response.status != 200:
                        error_msg = response_data.get('error', {}).get('message', '未知错误')
                        logger.error(f"OpenAI API调用失败: {response.status}, {error_msg}")
                        raise Exception(f"OpenAI API错误: {error_msg}")
                    
                    # 解析响应
                    choices = response_data.get('choices', [])
                    if not choices:
                        raise Exception("API返回空结果")
                    
                    message = choices[0].get('message', {})
                    response_text = message.get('content', '')
                    
                    # 解析token使用情况
                    usage = response_data.get('usage', {})
                    token_usage = {
                        "input_tokens": usage.get('prompt_tokens', 0),
                        "output_tokens": usage.get('completion_tokens', 0),
                        "total_tokens": usage.get('total_tokens', 0)
                    }
                    
                    logger.info(f"=== OpenAI兼容API调用成功 ===")
                    logger.info(f"HTTP状态码: {response.status}")
                    logger.info(f"响应长度: {len(response_text)} 字符")
                    logger.info(f"Token使用: {token_usage}")
                    logger.info(f"响应内容前200字符: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")
                    
                    # 详细调试信息
                    logger.info(f"=== 详细响应信息（调试用）===")
                    logger.info(f"完整响应字符数: {len(response_text)}")
                    logger.info(f"完整响应字节数: {len(response_text.encode('utf-8'))}")
                    logger.info(f"Input Tokens: {token_usage.get('input_tokens', 0)}")
                    logger.info(f"Output Tokens: {token_usage.get('output_tokens', 0)}")
                    logger.info(f"Total Tokens: {token_usage.get('total_tokens', 0)}")
                    logger.info(f"原始API响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    logger.info(f"=== 完整响应内容开始 ===")
                    logger.info(response_text)
                    logger.info(f"=== 完整响应内容结束 ===")
                    
                    return response_text, token_usage
                    
        except Exception as e:
            logger.error(f"OpenAI模型调用失败: {e}")
            raise
    
    async def test_generic_model(
        self,
        api_endpoint: str,
        api_key: str,
        model_name: str,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        proxy_url: str = None
    ) -> Tuple[str, Dict[str, int]]:
        """测试通用模型（尝试OpenAI兼容格式）"""
        try:
            # 首先尝试OpenAI格式
            return await self.test_openai_model(
                api_endpoint=api_endpoint,
                api_key=api_key,
                model_name=model_name,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                proxy_url=proxy_url
            )
        except Exception as e:
            logger.warning(f"OpenAI格式调用失败，尝试其他格式: {e}")
            # 这里可以添加其他API格式的支持
            raise Exception(f"无法识别的API格式: {e}")
    
    async def analyze_text(
        self,
        api_key: str,
        model_name: str,
        text: str,
        analysis_prompt: str,
        model_type: str = "gemini",
        api_endpoint: str = None,
        proxy_url: str = None
    ) -> Dict[str, Any]:
        """分析文本内容"""
        try:
            logger.info(f"开始文本分析，模型: {model_name}")
            
            # 构建完整的分析提示
            full_prompt = f"{analysis_prompt}\n\n需要分析的文本:\n{text}\n\n请提供详细的分析结果："
            
            # 根据模型类型选择调用方式
            if model_type.lower() == "gemini" or "gemini" in model_name.lower():
                response_text, token_usage = await self.test_gemini_model(
                    api_key=api_key,
                    model_name=model_name,
                    prompt=full_prompt,
                    max_tokens=2000,
                    temperature=0.3  # 分析任务使用较低温度
                )
            elif api_endpoint:
                response_text, token_usage = await self.test_openai_model(
                    api_endpoint=api_endpoint,
                    api_key=api_key,
                    model_name=model_name,
                    prompt=full_prompt,
                    max_tokens=2000,
                    temperature=0.3,
                    proxy_url=proxy_url
                )
            else:
                raise Exception(f"不支持的模型类型: {model_type}")
            
            # 构建分析结果
            analysis_result = {
                "success": True,
                "analysis": response_text,
                "model_used": model_name,
                "token_usage": token_usage,
                "analyzed_at": datetime.utcnow().isoformat(),
                "text_length": len(text),
                "prompt_length": len(full_prompt)
            }
            
            logger.info(f"文本分析完成，使用token: {token_usage}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"文本分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "analyzed_at": datetime.utcnow().isoformat(),
                "text_length": len(text) if text else 0
            }
    
    async def analyze_file_content(
        self,
        api_key: str,
        model_name: str,
        file_content: str,
        file_type: str,
        analysis_type: str,
        custom_prompt: str = None,
        model_type: str = "gemini",
        api_endpoint: str = None
    ) -> Dict[str, Any]:
        """分析文件内容"""
        try:
            logger.info(f"开始文件内容分析，文件类型: {file_type}, 分析类型: {analysis_type}")
            
            # 根据分析类型和文件类型构建提示
            if custom_prompt:
                analysis_prompt = custom_prompt
            else:
                analysis_prompt = self._get_default_analysis_prompt(file_type, analysis_type)
            
            # 如果文件内容过长，进行截断
            max_content_length = 10000  # 限制文件内容长度
            if len(file_content) > max_content_length:
                file_content = file_content[:max_content_length] + "\n...[内容已截断]..."
                logger.warning(f"文件内容过长，已截断到 {max_content_length} 字符")
            
            # 调用文本分析
            result = await self.analyze_text(
                api_key=api_key,
                model_name=model_name,
                text=file_content,
                analysis_prompt=analysis_prompt,
                model_type=model_type,
                api_endpoint=api_endpoint
            )
            
            # 添加文件分析特定信息
            result.update({
                "file_type": file_type,
                "analysis_type": analysis_type,
                "file_content_length": len(file_content)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"文件内容分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_type": file_type,
                "analysis_type": analysis_type,
                "analyzed_at": datetime.utcnow().isoformat()
            }
    
    def _get_default_analysis_prompt(self, file_type: str, analysis_type: str) -> str:
        """获取默认分析提示"""
        prompts = {
            "code": {
                "quality": "请分析这段代码的质量，包括代码结构、可读性、性能、安全性等方面，并提供改进建议。",
                "bug": "请仔细检查这段代码，识别可能存在的bug、错误或潜在问题，并提供修复建议。",
                "security": "请从安全角度分析这段代码，识别可能的安全漏洞或风险点，并提供安全改进建议。",
                "performance": "请分析这段代码的性能，识别可能的性能瓶颈或优化点，并提供性能优化建议。"
            },
            "document": {
                "summary": "请总结这份文档的主要内容和关键信息，提取重点。",
                "sentiment": "请分析这份文档的情感倾向和语调，判断是正面、负面还是中性。",
                "content": "请分析这份文档的内容结构、逻辑关系和主要观点。",
                "extract": "请从这份文档中提取关键信息、重要数据和主要结论。"
            },
            "text": {
                "sentiment": "请分析这段文本的情感倾向，判断是正面、负面还是中性，并说明原因。",
                "summary": "请对这段文本进行总结，提取主要信息和关键点。",
                "analysis": "请对这段文本进行详细分析，包括主题、结构、语言特点等。",
                "extract": "请从这段文本中提取关键信息、重要概念和核心内容。"
            }
        }
        
        # 根据文件类型和分析类型获取提示
        file_prompts = prompts.get(file_type, prompts["text"])
        prompt = file_prompts.get(analysis_type, file_prompts.get("analysis", "请分析以下内容："))
        
        return prompt
    
    async def batch_analyze(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """批量分析任务"""
        try:
            logger.info(f"开始批量分析，任务数量: {len(tasks)}")
            
            # 并发执行分析任务
            analysis_tasks = []
            for task in tasks:
                if task.get("type") == "text":
                    analysis_tasks.append(
                        self.analyze_text(
                            api_key=task["api_key"],
                            model_name=task["model_name"],
                            text=task["text"],
                            analysis_prompt=task["analysis_prompt"],
                            model_type=task.get("model_type", "gemini"),
                            api_endpoint=task.get("api_endpoint")
                        )
                    )
                elif task.get("type") == "file":
                    analysis_tasks.append(
                        self.analyze_file_content(
                            api_key=task["api_key"],
                            model_name=task["model_name"],
                            file_content=task["file_content"],
                            file_type=task["file_type"],
                            analysis_type=task["analysis_type"],
                            custom_prompt=task.get("custom_prompt"),
                            model_type=task.get("model_type", "gemini"),
                            api_endpoint=task.get("api_endpoint")
                        )
                    )
            
            # 等待所有任务完成
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # 处理结果和异常
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "success": False,
                        "error": str(result),
                        "task_index": i,
                        "analyzed_at": datetime.utcnow().isoformat()
                    })
                else:
                    result["task_index"] = i
                    processed_results.append(result)
            
            logger.info(f"批量分析完成，成功: {sum(1 for r in processed_results if r.get('success', False))}")
            return processed_results
            
        except Exception as e:
            logger.error(f"批量分析失败: {e}")
            raise
    
    async def health_check_model(
        self,
        api_key: str,
        model_name: str,
        model_type: str = "gemini",
        api_endpoint: str = None,
        proxy_url: str = None
    ) -> Dict[str, Any]:
        """模型健康检查"""
        try:
            start_time = datetime.utcnow()
            
            # 使用简单的测试提示
            test_prompt = "请回复'OK'以确认模型正常工作。"
            
            if model_type.lower() == "gemini" or "gemini" in model_name.lower():
                response_text, token_usage = await self.test_gemini_model(
                    api_key=api_key,
                    model_name=model_name,
                    prompt=test_prompt,
                    max_tokens=10,
                    temperature=0.1
                )
            elif api_endpoint:
                response_text, token_usage = await self.test_openai_model(
                    api_endpoint=api_endpoint,
                    api_key=api_key,
                    model_name=model_name,
                    prompt=test_prompt,
                    max_tokens=10,
                    temperature=0.1,
                    proxy_url=proxy_url
                )
            else:
                raise Exception(f"不支持的模型类型: {model_type}")
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "model_name": model_name,
                "response_text": response_text,
                "token_usage": token_usage,
                "checked_at": end_time.isoformat()
            }
            
        except Exception as e:
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time": response_time,
                "model_name": model_name,
                "checked_at": end_time.isoformat()
            }
    
    async def analyze_content(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """分析内容的通用方法，用于AI分析测试"""
        try:
            model_config = request.get("model_config", {})
            prompt = request.get("prompt", "")
            data_content = request.get("data_content", "")
            file_contents = request.get("file_contents", [])
            rich_text_images = request.get("rich_text_images", [])
            context = request.get("context", {})
            
            # 提取模型配置
            provider = model_config.get("provider", "").lower()
            model_name = model_config.get("model_name", "")
            api_key = model_config.get("api_key", "")
            api_endpoint = model_config.get("api_endpoint", "")
            temperature = model_config.get("temperature", 1.0)
            max_tokens = model_config.get("max_tokens", 10000)
            
            if not api_key:
                raise Exception("API密钥不能为空")
            
            if not prompt:
                raise Exception("分析提示词不能为空")
            
            logger.info(f"=== AI分析测试开始 ===")
            logger.info(f"模型提供商: {provider}")
            logger.info(f"模型名称: {model_name}")
            logger.info(f"API端点: {api_endpoint}")
            logger.info(f"温度参数: {temperature}")
            logger.info(f"最大Token: {max_tokens}")
            logger.info(f"提示词长度: {len(prompt)} 字符")
            logger.info(f"数据内容长度: {len(data_content)} 字符")
            logger.info(f"文件数量: {len(file_contents)} 个")
            logger.info(f"富文本图片数量: {len(rich_text_images)} 张")
            if file_contents:
                for i, file_info in enumerate(file_contents):
                    logger.info(f"文件{i+1}: {file_info.get('file_name', '未知')}, 大小: {file_info.get('file_size', 0)} 字节, 类型: {file_info.get('mime_type', '未知')}")
            if rich_text_images:
                for i, img_info in enumerate(rich_text_images):
                    logger.info(f"图片{i+1}: {img_info.get('uuid', f'img_{i}')}, 大小: {img_info.get('size', 0)} 字节, 类型: {img_info.get('type', '未知')}")
            logger.info(f"提示词内容: {prompt[:200]}{'...' if len(prompt) > 200 else ''}")
            if data_content:
                logger.info(f"数据内容: {data_content[:200]}{'...' if len(data_content) > 200 else ''}")
            
            # 根据模型类型选择调用方法
            if provider == "google" or "gemini" in model_name.lower():
                # 合并文件内容和富文本图片
                all_media_content = []
                if file_contents:
                    all_media_content.extend(file_contents)
                if rich_text_images:
                    # 将富文本图片转换为file_contents格式
                    for img in rich_text_images:
                        all_media_content.append({
                            'file_name': img.get('uuid', 'rich_text_image'),
                            'content': img.get('base64', ''),
                            'file_type': 'image',  # 关键：添加file_type字段
                            'mime_type': img.get('type', 'image/jpeg'),
                            'file_size': img.get('size', 0),
                            'source': 'rich_text'
                        })
                
                response_text, token_usage = await self.test_gemini_model_with_files(
                    api_key=api_key,
                    model_name=model_name,
                    prompt=prompt,
                    file_contents=all_media_content,
                    data_content=data_content,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    proxy_url=model_config.get("proxy_url")
                )
            elif provider in ["openai", "anthropic", "deepseek"] or api_endpoint:
                # 对于支持视觉的模型，添加图片支持
                if rich_text_images and self._model_supports_vision(model_name):
                    # 将富文本内容和提示词组合
                    combined_prompt = prompt
                    if data_content:
                        combined_prompt = f"{prompt}\n\n需要分析的富文本内容：\n{data_content}"
                    
                    response_text, token_usage = await self.test_openai_model_with_images(
                        api_endpoint=api_endpoint,
                        api_key=api_key,
                        model_name=model_name,
                        prompt=combined_prompt,
                        images=rich_text_images,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                else:
                    response_text, token_usage = await self.test_openai_model(
                        api_endpoint=api_endpoint,
                        api_key=api_key,
                        model_name=model_name,
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        proxy_url=model_config.get("proxy_url")
                    )
            else:
                raise Exception(f"不支持的模型提供商: {provider}")
            
            logger.info(f"=== AI分析测试成功 ===")
            logger.info(f"响应内容长度: {len(response_text)} 字符")
            logger.info(f"Token使用情况: {token_usage}")
            logger.info(f"响应内容前200字符: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")
            
            # 完整分析结果调试输出
            logger.info(f"=== 完整AI分析结果（调试用）===")
            logger.info(f"分析结果字符数: {len(response_text)}")
            logger.info(f"分析结果字节数: {len(response_text.encode('utf-8'))}")
            logger.info(f"请求的Max Tokens: {max_tokens}")
            logger.info(f"实际输出 Tokens: {token_usage.get('output_tokens', 0)}")
            logger.info(f"Token利用率: {(token_usage.get('output_tokens', 0) / max_tokens * 100):.2f}%" if max_tokens > 0 else "N/A")
            logger.info(f"=== 完整分析结果内容开始 ===")
            logger.info(response_text)
            logger.info(f"=== 完整分析结果内容结束 ===")
            
            return {
                "success": True,
                "content": response_text,
                "usage": token_usage,
                "model_info": {
                    "provider": provider,
                    "model_name": model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"AI分析失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "analyzed_at": datetime.utcnow().isoformat()
            }
    
    def _model_supports_vision(self, model_name: str) -> bool:
        """检查模型是否支持视觉功能"""
        vision_models = [
            'gpt-4-vision-preview',
            'gpt-4-turbo',
            'gpt-4o',
            'gpt-4o-mini',
            'claude-3-opus',
            'claude-3-sonnet',
            'claude-3-haiku',
            'claude-3.5-sonnet',
            'claude-3-5-sonnet-20241022'
        ]
        
        model_lower = model_name.lower()
        for vision_model in vision_models:
            if vision_model.lower() in model_lower:
                return True
        
        # 检查是否包含vision关键词
        if 'vision' in model_lower or 'visual' in model_lower:
            return True
            
        return False
    
    async def test_openai_model_with_images(
        self,
        api_endpoint: str,
        api_key: str,
        model_name: str,
        prompt: str,
        images: List[Dict[str, Any]],
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Tuple[str, Dict[str, int]]:
        """测试支持图片的OpenAI兼容模型"""
        try:
            logger.info(f"=== OpenAI视觉模型API调用开始 ===")
            logger.info(f"API端点: {api_endpoint}")
            logger.info(f"模型名称: {model_name}")
            logger.info(f"API密钥前10位: {api_key[:10]}...")
            logger.info(f"图片数量: {len(images)}")
            logger.info(f"最大Token: {max_tokens}")
            logger.info(f"温度: {temperature}")
            
            # 构建消息内容
            message_content = [{"type": "text", "text": prompt}]
            
            # 添加图片
            for i, img in enumerate(images):
                base64_data = img.get('base64', '')
                if base64_data.startswith('data:'):
                    # 如果已经是完整的data URL，直接使用
                    image_url = base64_data
                else:
                    # 如果只是base64数据，添加data URL前缀
                    mime_type = img.get('type', 'image/jpeg')
                    image_url = f"data:{mime_type};base64,{base64_data}"
                
                message_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_url,
                        "detail": "high"  # 使用高质量分析
                    }
                })
                logger.info(f"添加图片 {i+1}: {img.get('uuid', f'img_{i}')}, 类型: {img.get('type', '未知')}")
            
            # 构建请求数据
            data = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": message_content
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            logger.info(f"请求数据结构: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
            
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=self.session_timeout,
                trust_env=True
            ) as session:
                logger.info(f"发送API请求到: {api_endpoint}")
                
                async with session.post(
                    api_endpoint,
                    headers=headers,
                    json=data
                ) as response:
                    response_text = await response.text()
                    logger.info(f"响应状态码: {response.status}")
                    logger.info(f"响应内容: {response_text[:1000]}{'...' if len(response_text) > 1000 else ''}")
                    
                    if response.status == 200:
                        response_data = json.loads(response_text)
                        
                        # 提取响应内容
                        content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        
                        # 提取Token使用情况
                        usage = response_data.get("usage", {})
                        token_usage = {
                            "prompt_tokens": usage.get("prompt_tokens", 0),
                            "completion_tokens": usage.get("completion_tokens", 0),
                            "total_tokens": usage.get("total_tokens", 0),
                            "output_tokens": usage.get("completion_tokens", 0)  # 别名
                        }
                        
                        logger.info(f"=== OpenAI视觉API调用成功 ===")
                        logger.info(f"响应长度: {len(content)} 字符")
                        logger.info(f"Token使用: {token_usage}")
                        
                        return content, token_usage
                    else:
                        error_msg = f"API调用失败: {response.status} - {response_text}"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                        
        except Exception as e:
            logger.error(f"OpenAI视觉模型调用失败: {str(e)}", exc_info=True)
            raise Exception(f"OpenAI视觉模型调用失败: {str(e)}")


# 创建全局AI服务实例
ai_service = AIService()