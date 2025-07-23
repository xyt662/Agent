#!/usr/bin/env python3
"""
认证策略模块

实现了策略模式来处理不同的认证方式，符合开闭原则
新的认证方式只需要创建新的策略类并注册，无需修改核心代码
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AuthenticationStrategy(ABC):
    """认证策略基类"""
    
    @abstractmethod
    def apply(self, auth_config: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, str]:
        """
        应用认证策略到HTTP头部
        
        Args:
            auth_config: 认证配置字典
            headers: 现有的HTTP头部字典
            
        Returns:
            更新后的HTTP头部字典
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        pass


class BearerTokenStrategy(AuthenticationStrategy):
    """Bearer Token认证策略"""
    
    def apply(self, auth_config: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, str]:
        secret_env_var = auth_config.get('secret_env_variable')
        if not secret_env_var:
            logger.warning("Bearer token认证配置缺少secret_env_variable字段")
            return headers
        
        token = os.getenv(secret_env_var)
        if not token:
            logger.warning(f"环境变量 {secret_env_var} 未设置或为空")
            return headers
        
        headers['Authorization'] = f'Bearer {token}'
        logger.debug(f"添加Bearer token认证头部(来源: {secret_env_var})")
        return headers
    
    def get_strategy_name(self) -> str:
        return "bearer_token"


class ApiKeyInHeaderStrategy(AuthenticationStrategy):
    """API Key in Header认证策略"""
    
    def apply(self, auth_config: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, str]:
        secret_env_var = auth_config.get('secret_env_variable')
        header_name = auth_config.get('header_name', 'X-API-Key')
        
        if not secret_env_var:
            logger.warning("API Key认证配置缺少secret_env_variable字段")
            return headers
        
        api_key = os.getenv(secret_env_var)
        if not api_key:
            logger.warning(f"环境变量 {secret_env_var} 未设置或为空")
            return headers
        
        headers[header_name] = api_key
        logger.debug(f"添加API Key认证头部 {header_name}（来源: {secret_env_var})")
        return headers
    
    def get_strategy_name(self) -> str:
        return "api_key_in_header"


class BasicAuthStrategy(AuthenticationStrategy):
    """Basic Auth认证策略(示例扩展)"""
    
    def apply(self, auth_config: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, str]:
        username_env_var = auth_config.get('username_env_variable')
        password_env_var = auth_config.get('password_env_variable')
        
        if not username_env_var or not password_env_var:
            logger.warning("Basic Auth认证配置缺少username_env_variable或password_env_variable字段")
            return headers
        
        username = os.getenv(username_env_var)
        password = os.getenv(password_env_var)
        
        if not username or not password:
            logger.warning(f"环境变量 {username_env_var} 或 {password_env_var} 未设置或为空")
            return headers
        
        import base64
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        headers['Authorization'] = f'Basic {credentials}'
        logger.debug(f"添加Basic Auth认证头部（用户名来源: {username_env_var}）")
        return headers
    
    def get_strategy_name(self) -> str:
        return "basic_auth"


class AuthenticationRegistry:
    """认证策略注册表"""
    
    def __init__(self):
        self._strategies: Dict[str, AuthenticationStrategy] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """注册默认的认证策略"""
        self.register(BearerTokenStrategy())
        self.register(ApiKeyInHeaderStrategy())
        self.register(BasicAuthStrategy())
    
    def register(self, strategy: AuthenticationStrategy):
        """注册认证策略"""
        strategy_name = strategy.get_strategy_name()
        self._strategies[strategy_name] = strategy
        logger.debug(f"注册认证策略: {strategy_name}")
    
    def get_strategy(self, auth_type: str) -> Optional[AuthenticationStrategy]:
        """获取认证策略"""
        return self._strategies.get(auth_type)
    
    def list_strategies(self) -> list[str]:
        """列出所有可用的认证策略"""
        return list(self._strategies.keys())


# 全局注册表实例
authentication_registry = AuthenticationRegistry()