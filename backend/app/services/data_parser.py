#!/usr/bin/env python3
"""
数据解析服务
支持JSONPath表达式提取和数据验证
"""

import json
import re
from typing import Dict, Any, Optional, List, Union
from jsonpath_ng import parse, DatumInContext
from jsonpath_ng.ext import parse as parse_ext
import logging

logger = logging.getLogger(__name__)


class DataParserError(Exception):
    """数据解析异常"""
    pass


class JSONPathParser:
    """JSONPath解析器"""
    
    def __init__(self):
        self._compiled_expressions = {}
    
    def _get_compiled_expression(self, jsonpath_expr: str):
        """获取编译后的JSONPath表达式（缓存）"""
        if jsonpath_expr not in self._compiled_expressions:
            try:
                # 尝试使用扩展解析器（支持更多功能）
                self._compiled_expressions[jsonpath_expr] = parse_ext(jsonpath_expr)
            except Exception:
                try:
                    # 回退到基础解析器
                    self._compiled_expressions[jsonpath_expr] = parse(jsonpath_expr)
                except Exception as e:
                    raise DataParserError(f"无效的JSONPath表达式: {jsonpath_expr} - {e}")
        
        return self._compiled_expressions[jsonpath_expr]
    
    def extract_value(self, data: Dict[str, Any], jsonpath_expr: str) -> Optional[Any]:
        """从数据中提取单个值"""
        try:
            compiled_expr = self._get_compiled_expression(jsonpath_expr)
            matches = compiled_expr.find(data)
            
            if matches:
                return matches[0].value
            return None
            
        except Exception as e:
            logger.error(f"JSONPath提取失败 {jsonpath_expr}: {e}")
            raise DataParserError(f"JSONPath提取失败: {e}")
    
    def extract_values(self, data: Dict[str, Any], jsonpath_expr: str) -> List[Any]:
        """从数据中提取多个值"""
        try:
            compiled_expr = self._get_compiled_expression(jsonpath_expr)
            matches = compiled_expr.find(data)
            
            return [match.value for match in matches]
            
        except Exception as e:
            logger.error(f"JSONPath提取失败 {jsonpath_expr}: {e}")
            raise DataParserError(f"JSONPath提取失败: {e}")
    
    def extract_with_rules(self, data: Dict[str, Any], rules: Dict[str, str]) -> Dict[str, Any]:
        """使用规则批量提取数据"""
        extracted = {}
        errors = []
        
        for variable_name, jsonpath_expr in rules.items():
            try:
                value = self.extract_value(data, jsonpath_expr)
                extracted[variable_name] = value
                
                if value is None:
                    logger.warning(f"JSONPath '{jsonpath_expr}' 未匹配到数据: {variable_name}")
                
            except Exception as e:
                error_msg = f"变量 {variable_name} 提取失败: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        if errors:
            raise DataParserError(f"数据提取失败: {'; '.join(errors)}")
        
        return extracted


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """验证必填字段"""
        missing_fields = []
        
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        return missing_fields
    
    @staticmethod
    def validate_field_types(data: Dict[str, Any], type_rules: Dict[str, type]) -> List[str]:
        """验证字段类型"""
        type_errors = []
        
        for field, expected_type in type_rules.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    type_errors.append(f"{field}: 期望 {expected_type.__name__}, 实际 {type(data[field]).__name__}")
        
        return type_errors
    
    @staticmethod
    def validate_field_patterns(data: Dict[str, Any], pattern_rules: Dict[str, str]) -> List[str]:
        """验证字段格式（正则表达式）"""
        pattern_errors = []
        
        for field, pattern in pattern_rules.items():
            if field in data and data[field] is not None:
                try:
                    if not re.match(pattern, str(data[field])):
                        pattern_errors.append(f"{field}: 不匹配模式 {pattern}")
                except Exception as e:
                    pattern_errors.append(f"{field}: 模式验证失败 - {e}")
        
        return pattern_errors
    
    @staticmethod
    def validate_field_ranges(data: Dict[str, Any], range_rules: Dict[str, Dict[str, Union[int, float]]]) -> List[str]:
        """验证字段范围"""
        range_errors = []
        
        for field, range_rule in range_rules.items():
            if field in data and data[field] is not None:
                try:
                    value = float(data[field])
                    
                    if 'min' in range_rule and value < range_rule['min']:
                        range_errors.append(f"{field}: 值 {value} 小于最小值 {range_rule['min']}")
                    
                    if 'max' in range_rule and value > range_rule['max']:
                        range_errors.append(f"{field}: 值 {value} 大于最大值 {range_rule['max']}")
                        
                except (ValueError, TypeError):
                    range_errors.append(f"{field}: 无法转换为数字进行范围验证")
        
        return range_errors


class DataTransformer:
    """数据转换器"""
    
    @staticmethod
    def transform_field_types(data: Dict[str, Any], transform_rules: Dict[str, str]) -> Dict[str, Any]:
        """转换字段类型"""
        transformed = data.copy()
        
        for field, target_type in transform_rules.items():
            if field in transformed and transformed[field] is not None:
                try:
                    if target_type == 'int':
                        transformed[field] = int(transformed[field])
                    elif target_type == 'float':
                        transformed[field] = float(transformed[field])
                    elif target_type == 'str':
                        transformed[field] = str(transformed[field])
                    elif target_type == 'bool':
                        if isinstance(transformed[field], str):
                            transformed[field] = transformed[field].lower() in ('true', '1', 'yes', 'on')
                        else:
                            transformed[field] = bool(transformed[field])
                    elif target_type == 'json':
                        if isinstance(transformed[field], str):
                            transformed[field] = json.loads(transformed[field])
                    else:
                        logger.warning(f"不支持的转换类型: {target_type}")
                        
                except Exception as e:
                    logger.error(f"字段 {field} 类型转换失败 ({target_type}): {e}")
                    raise DataParserError(f"字段 {field} 转换失败: {e}")
        
        return transformed
    
    @staticmethod
    def apply_field_mappings(data: Dict[str, Any], field_mappings: Dict[str, str]) -> Dict[str, Any]:
        """应用字段映射（重命名）"""
        mapped = {}
        
        for new_field, old_field in field_mappings.items():
            if old_field in data:
                mapped[new_field] = data[old_field]
            else:
                logger.warning(f"映射源字段不存在: {old_field} -> {new_field}")
        
        # 保留未映射的字段
        for field, value in data.items():
            if field not in field_mappings.values():
                mapped[field] = value
        
        return mapped


class WebhookDataParser:
    """Webhook数据解析器（主类）"""
    
    def __init__(self):
        self.jsonpath_parser = JSONPathParser()
        self.validator = DataValidator()
        self.transformer = DataTransformer()
    
    def parse_webhook_data(
        self,
        payload_data: Dict[str, Any],
        parsing_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析Webhook数据
        
        Args:
            payload_data: 原始webhook数据
            parsing_config: 解析配置，包含：
                - jsonpath_rules: JSONPath提取规则
                - validation_rules: 数据验证规则
                - transform_rules: 数据转换规则
                - field_mappings: 字段映射规则
        
        Returns:
            解析后的数据
        """
        try:
            logger.info(f"开始解析Webhook数据，配置: {parsing_config}")
            
            # 1. JSONPath数据提取
            extracted_data = {}
            if 'jsonpath_rules' in parsing_config and parsing_config['jsonpath_rules']:
                extracted_data = self.jsonpath_parser.extract_with_rules(
                    payload_data, 
                    parsing_config['jsonpath_rules']
                )
                logger.info(f"JSONPath提取结果: {extracted_data}")
            else:
                # 如果没有JSONPath规则，直接使用原始数据
                extracted_data = payload_data.copy()
            
            # 2. 数据验证
            validation_errors = []
            
            if 'validation_rules' in parsing_config and parsing_config['validation_rules']:
                validation_rules = parsing_config['validation_rules']
                
                # 必填字段验证
                if 'required_fields' in validation_rules:
                    missing_fields = self.validator.validate_required_fields(
                        extracted_data, 
                        validation_rules['required_fields']
                    )
                    if missing_fields:
                        validation_errors.extend([f"缺少必填字段: {field}" for field in missing_fields])
                
                # 字段类型验证
                if 'field_types' in validation_rules:
                    type_errors = self.validator.validate_field_types(
                        extracted_data,
                        validation_rules['field_types']
                    )
                    validation_errors.extend(type_errors)
                
                # 字段格式验证
                if 'field_patterns' in validation_rules:
                    pattern_errors = self.validator.validate_field_patterns(
                        extracted_data,
                        validation_rules['field_patterns']
                    )
                    validation_errors.extend(pattern_errors)
                
                # 字段范围验证
                if 'field_ranges' in validation_rules:
                    range_errors = self.validator.validate_field_ranges(
                        extracted_data,
                        validation_rules['field_ranges']
                    )
                    validation_errors.extend(range_errors)
            
            if validation_errors:
                raise DataParserError(f"数据验证失败: {'; '.join(validation_errors)}")
            
            # 3. 数据转换
            transformed_data = extracted_data.copy()
            
            if 'transform_rules' in parsing_config and parsing_config['transform_rules']:
                if 'field_types' in parsing_config['transform_rules']:
                    transformed_data = self.transformer.transform_field_types(
                        transformed_data,
                        parsing_config['transform_rules']['field_types']
                    )
                    logger.info(f"类型转换后数据: {transformed_data}")
            
            # 4. 字段映射
            if 'field_mappings' in parsing_config and parsing_config['field_mappings']:
                transformed_data = self.transformer.apply_field_mappings(
                    transformed_data,
                    parsing_config['field_mappings']
                )
                logger.info(f"字段映射后数据: {transformed_data}")
            
            logger.info(f"数据解析成功，最终结果: {transformed_data}")
            return transformed_data
            
        except Exception as e:
            logger.error(f"Webhook数据解析失败: {e}")
            raise DataParserError(f"数据解析失败: {e}")
    
    def test_parsing_config(
        self, 
        sample_data: Dict[str, Any], 
        parsing_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        测试解析配置
        
        Args:
            sample_data: 示例数据
            parsing_config: 解析配置
            
        Returns:
            测试结果，包含解析结果或错误信息
        """
        try:
            result = self.parse_webhook_data(sample_data, parsing_config)
            
            return {
                "success": True,
                "message": "解析配置测试成功",
                "parsed_data": result,
                "original_data": sample_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "error_type": type(e).__name__,
                "original_data": sample_data
            }
    
    def validate_config(self, parsing_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证解析配置格式
        
        Args:
            parsing_config: 解析配置
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        # 验证JSONPath规则
        if 'jsonpath_rules' in parsing_config:
            if not isinstance(parsing_config['jsonpath_rules'], dict):
                errors.append("jsonpath_rules 必须是字典格式")
            else:
                for var_name, jsonpath_expr in parsing_config['jsonpath_rules'].items():
                    if not isinstance(jsonpath_expr, str):
                        errors.append(f"JSONPath表达式必须是字符串: {var_name}")
                    else:
                        try:
                            self.jsonpath_parser._get_compiled_expression(jsonpath_expr)
                        except Exception as e:
                            errors.append(f"无效的JSONPath表达式 {var_name}: {e}")
        
        # 验证验证规则
        if 'validation_rules' in parsing_config:
            validation_rules = parsing_config['validation_rules']
            
            if 'required_fields' in validation_rules:
                if not isinstance(validation_rules['required_fields'], list):
                    errors.append("required_fields 必须是数组")
            
            if 'field_types' in validation_rules:
                if not isinstance(validation_rules['field_types'], dict):
                    errors.append("field_types 必须是字典")
            
            if 'field_patterns' in validation_rules:
                if not isinstance(validation_rules['field_patterns'], dict):
                    errors.append("field_patterns 必须是字典")
                else:
                    for field, pattern in validation_rules['field_patterns'].items():
                        try:
                            re.compile(pattern)
                        except Exception as e:
                            errors.append(f"无效的正则表达式 {field}: {e}")
        
        # 验证转换规则
        if 'transform_rules' in parsing_config:
            transform_rules = parsing_config['transform_rules']
            
            if 'field_types' in transform_rules:
                if not isinstance(transform_rules['field_types'], dict):
                    errors.append("transform_rules.field_types 必须是字典")
                else:
                    valid_types = {'int', 'float', 'str', 'bool', 'json'}
                    for field, target_type in transform_rules['field_types'].items():
                        if target_type not in valid_types:
                            errors.append(f"不支持的转换类型 {field}: {target_type}")
        
        # 验证字段映射
        if 'field_mappings' in parsing_config:
            if not isinstance(parsing_config['field_mappings'], dict):
                errors.append("field_mappings 必须是字典")
        
        if not parsing_config.get('jsonpath_rules') and not parsing_config.get('field_mappings'):
            warnings.append("建议设置 jsonpath_rules 或 field_mappings 来提取所需数据")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


# 全局解析器实例
webhook_data_parser = WebhookDataParser()