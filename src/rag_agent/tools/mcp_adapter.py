#!/usr/bin/env python3
"""
MCP工具适配器
负责将YAML格式的工具清单转换为LangChain工具
"""

import os
import yaml
import requests
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from pydantic import BaseModel, create_model
from langchain_core.tools import BaseTool
from ..core.config import get_mcp_allowed_domains
from .authentication_strategies import authentication_registry

logger = logging.getLogger(__name__)


class MCPToolAdapter:
    """MCP工具适配器类
    
    负责解析YAML清单文件并创建对应的LangChain工具
    """
    
    def __init__(self, manifest_path: str):
        """初始化适配器
        
        Args:
            manifest_path: YAML清单文件路径
        """
        self.manifest_path = Path(manifest_path)
        self.manifest_data = self._load_manifest()
        
    def _load_manifest(self) -> Dict[str, Any]:
        """加载并解析YAML清单文件"""
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            logger.debug(f"成功加载清单文件: {self.manifest_path}")
            return data
        except Exception as e:
            logger.error(f"加载清单文件失败 {self.manifest_path}: {e}")
            raise
    
    def _create_args_schema(self) -> BaseModel:
        """根据input_schema动态创建Pydantic模型"""
        input_schema = self.manifest_data.get('input_schema', {})
        properties = input_schema.get('properties', {})
        
        # 如果没有属性，创建一个空模型
        if not properties:
            return create_model('EmptyModel')
        
        # 类型映射表
        type_mapping = {
            'string': str,
            'integer': int,
            'number': float,
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        # 动态创建字段
        fields = {}
        required_fields = set(input_schema.get('required', []))
        
        for field_name, field_def in properties.items():
            # 获取字段类型，默认为字符串
            json_type = field_def.get('type', 'string')
            field_type = type_mapping.get(json_type, str)
            
            # 设置字段（必需或可选）
            if field_name in required_fields:
                fields[field_name] = (field_type, ...)
            else:
                fields[field_name] = (Optional[field_type], None)
        
        return create_model('DynamicModel', **fields)
    
    def _validate_url_security(self, url: str) -> None:
        """验证URL是否在允许的域名白名单中
        
        Args:
            url: 要验证的URL
            
        Raises:
            ValueError: 如果URL不在白名单中
        """
        try:
            parsed_url = urlparse(url)
            request_origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # 获取允许的域名白名单
            allowed_domains = get_mcp_allowed_domains()
            
            # 检查是否在白名单中
            if request_origin not in allowed_domains:
                logger.error(f"SSRF防护: 拒绝访问未授权域名 {request_origin}")
                logger.info(f"允许的域名白名单: {allowed_domains}")
                raise ValueError(
                    f"安全错误: 域名 '{request_origin}' 不在允许的白名单中。"
                    f"允许的域名: {', '.join(allowed_domains)}"
                )
            
            logger.debug(f"URL安全验证通过: {request_origin}")
            
        except Exception as e:
            if isinstance(e, ValueError):
                raise  # 重新抛出我们的安全错误
            else:
                logger.error(f"URL解析失败: {e}")
                raise ValueError(f"无效的URL格式: {url}")
    
    def _prepare_authentication_headers(self) -> Dict[str, str]:
        """准备认证头部（使用策略模式）"""
        headers = {}
        auth_config = self.manifest_data.get('execution', {}).get('authentication')
        
        if not auth_config:
            return headers
        
        auth_type = auth_config.get('type')
        if not auth_type:
            logger.warning("认证配置缺少type字段")
            return headers
        
        # 从注册表获取认证策略
        strategy = authentication_registry.get_strategy(auth_type)
        if not strategy:
            available_strategies = authentication_registry.list_strategies()
            logger.warning(f"不支持的认证类型: {auth_type}. 可用类型: {available_strategies}")
            return headers
        
        # 应用认证策略
        try:
            headers = strategy.apply(auth_config, headers)
        except Exception as e:
            logger.error(f"应用认证策略 {auth_type} 时发生错误: {e}")
        
        return headers
    
    def _execute_http_request(self, **kwargs) -> str:
        """执行HTTP请求"""
        execution = self.manifest_data.get('execution', {})
        url = execution.get('url')
        method = execution.get('method', 'GET')
        parameter_mapping = execution.get('parameter_mapping', {})
        
        # SSRF安全检查 - 验证URL是否在白名单中
        if url:
            self._validate_url_security(url)
        else:
            raise ValueError("清单文件中缺少URL配置")
        
        # 映射参数
        mapped_params = {}
        for param_name, value in kwargs.items():
            mapped_name = parameter_mapping.get(param_name, param_name)
            mapped_params[mapped_name] = value
        
        # 准备认证头部
        auth_headers = self._prepare_authentication_headers()
        
        try:
            logger.info(f"执行HTTP请求: {method} {url}")
            if method.upper() == 'GET':
                response = requests.get(url, params=mapped_params, headers=auth_headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=mapped_params, headers=auth_headers, timeout=10)
            else:
                response = requests.request(method, url, json=mapped_params, headers=auth_headers, timeout=10)
            
            response.raise_for_status()
            
            # 尝试返回JSON，如果失败则返回文本
            try:
                result = response.json()
                return str(result)
            except:
                return response.text
                
        except requests.RequestException as e:
            if e.response is not None:
                status_code = e.response.status_code
                error_message = f"请求失败: HTTP {status_code} - {e.response.reason}."
                
                if status_code == 401 or status_code == 403:
                    error_message += " 请检查您的认证密钥(API Key/Token)是否正确或已过期。"
                elif status_code == 404:
                    error_message += " 请检查清单文件中的URL配置是否正确。"
                elif status_code == 429:
                    error_message += " API调用频率超限，请稍后重试。"
                elif status_code >= 500:
                    error_message += " 服务器内部错误，请稍后重试或联系API提供商。"
                
                logger.error(f"HTTP请求失败: {status_code}, 响应: {e.response.text[:200]}")
                return error_message
            else:
                # 处理连接错误等没有 response 的情况
                logger.error(f"HTTP请求失败，无响应: {e}")
                return f"请求失败: 无法连接到服务器 - {str(e)}"
    
    def to_langchain_tool(self) -> BaseTool:
        """将MCP清单转换为LangChain工具"""
        tool_name = self.manifest_data.get('name_for_model')
        tool_description = self.manifest_data.get('description_for_model')
        tool_args_schema = self._create_args_schema()
        
        # 保存执行方法的引用
        execute_method = self._execute_http_request
        
        # 创建动态工具类
        class DynamicMCPTool(BaseTool):
            name: str = tool_name
            description: str = tool_description
            args_schema: type = tool_args_schema
            
            def _run(self, **kwargs) -> str:
                return execute_method(**kwargs)
        
        return DynamicMCPTool()