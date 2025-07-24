#!/usr/bin/env python3
"""
工具包管理器 (Tool Package Manager)

负责处理MCP工具包的安装、配置和管理，实现"即插即用"的用户体验

核心功能：
1. 读取 tools.config.json 配置文件
2. 处理本地命令模式的MCP工具（local_command）
3. 动态注入环境变量配置
4. 通过LocalCommandToolAdapter与本地MCP服务器通信
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from langchain_core.tools import BaseTool

from .local_command_adapter import LocalCommandToolAdapter

logger = logging.getLogger(__name__)


@dataclass
class ToolPackage:
    """工具包信息"""
    name: str
    enabled: bool
    tool_type: str  # 'local_command'
    command: str
    args: List[str]
    env: Optional[Dict[str, str]]
    description: str


class ToolPackageManager:
    """工具包管理器"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """初始化工具包管理器
        
        Args:
            project_root: 项目根目录，默认为当前工作目录
        """
        self.project_root = project_root or Path.cwd()
        self.config_file = self.project_root / "tools.config.json"
        
        # 加载配置
        self.config = self._load_config()
        self.packages = self._parse_packages()
        
        # 存储适配器实例
        self.adapters: Dict[str, LocalCommandToolAdapter] = {}
        self.tools_cache: Dict[str, List[BaseTool]] = {}
    
    def _load_config(self) -> Dict[str, Any]:
        """加载 tools.config.json 配置文件"""
        if not self.config_file.exists():
            logger.warning(f"配置文件不存在: {self.config_file}")
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"成功加载配置文件: {self.config_file}")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败 {self.config_file}: {e}")
            return {}
    
    def _parse_packages(self) -> List[ToolPackage]:
        """解析配置中的工具包信息，支持官方mcpServers格式和自定义格式"""
        packages = []
        
        # 检查是否为官方mcpServers格式
        if "mcpServers" in self.config:
            logger.info("检测到官方mcpServers配置格式")
            mcp_servers = self.config["mcpServers"]
            
            for name, server_config in mcp_servers.items():
                try:
                    # 解析环境变量
                    env = server_config.get("env", {})
                    resolved_env = self._resolve_env_variables(env) if env else None
                    
                    # 官方格式中disabled字段转换为enabled
                    enabled = not server_config.get("disabled", False)
                    
                    package = ToolPackage(
                        name=name,
                        enabled=enabled,
                        tool_type="local_command",
                        command=server_config["command"],
                        args=server_config["args"],
                        env=resolved_env,
                        description=f"MCP Server: {name}"
                    )
                    packages.append(package)
                    logger.debug(f"解析MCP服务器: {name} ({package.command} {' '.join(package.args)})")
                except KeyError as e:
                    logger.error(f"MCP服务器 {name} 缺少必要配置字段: {e}")
                except Exception as e:
                    logger.error(f"解析MCP服务器 {name} 失败: {e}")
        else:
            # 自定义格式（向后兼容）
            logger.info("使用自定义配置格式")
            for name, tool_config in self.config.items():
                try:
                    # 检查是否为local_command类型
                    if tool_config.get("type") != "local_command":
                        logger.warning(f"工具包 {name} 不是local_command类型，跳过")
                        continue
                    
                    # 解析环境变量
                    env = tool_config.get("env", {})
                    resolved_env = self._resolve_env_variables(env) if env else None
                    
                    package = ToolPackage(
                        name=name,
                        enabled=tool_config.get("enabled", True),
                        tool_type="local_command",
                        command=tool_config["command"],
                        args=tool_config["args"],
                        env=resolved_env,
                        description=tool_config.get("description", f"Local MCP tool: {name}")
                    )
                    packages.append(package)
                    logger.debug(f"解析工具包: {name} ({package.command} {' '.join(package.args)})")
                except KeyError as e:
                    logger.error(f"工具包 {name} 缺少必要配置字段: {e}")
                except Exception as e:
                    logger.error(f"解析工具包 {name} 失败: {e}")
        
        return packages
    
    async def get_enabled_tools(self) -> List[BaseTool]:
        """获取所有已启用的工具实例
        
        Returns:
            List[BaseTool]: 已启用的工具列表
        """
        all_tools = []
        
        for package in self.packages:
            if not package.enabled:
                logger.debug(f"跳过已禁用的工具: {package.name}")
                continue
            
            try:
                tools = await self._load_package_tools(package)
                all_tools.extend(tools)
                logger.info(f"成功加载工具包 {package.name}，包含 {len(tools)} 个工具")
            except Exception as e:
                logger.error(f"加载工具包 {package.name} 失败: {e}")
        
        return all_tools
    
    async def _load_package_tools(self, package: ToolPackage) -> List[BaseTool]:
        """加载单个工具包的工具
        
        Args:
            package: 工具包信息
            
        Returns:
            List[BaseTool]: 工具列表
        """
        # 检查缓存
        if package.name in self.tools_cache:
            logger.debug(f"从缓存加载工具: {package.name}")
            return self.tools_cache[package.name]
        
        # 创建适配器
        if package.name not in self.adapters:
            adapter = LocalCommandToolAdapter(
                command=package.command,
                args=package.args,
                env=package.env,
                name=package.name
            )
            self.adapters[package.name] = adapter
        
        adapter = self.adapters[package.name]
        
        try:
            # 启动MCP服务器并获取工具
            tools = await adapter.get_tools()
            
            # 缓存工具
            self.tools_cache[package.name] = tools
            
            return tools
        except Exception as e:
            logger.error(f"从适配器获取工具失败 {package.name}: {e}")
            return []
    
    def _resolve_env_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析配置中的环境变量引用
        
        支持 ${ENV_VAR} 语法从环境变量读取值
        """
        resolved_config = {}
        
        for key, value in config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]  # 移除 ${ 和 }
                env_value = os.getenv(env_var)
                if env_value is not None:
                    resolved_config[key] = env_value
                    logger.debug(f"解析环境变量 {env_var}: ✓")
                else:
                    logger.warning(f"环境变量 {env_var} 未设置")
                    resolved_config[key] = None
            else:
                resolved_config[key] = value
        
        return resolved_config
    
    def inject_authentication(self, manifest_content: Dict[str, Any], authentication: Dict[str, Any]) -> Dict[str, Any]:
        """将认证信息注入到清单内容中
        
        Args:
            manifest_content: 清单内容字典
            authentication: 认证配置字典
            
        Returns:
            Dict[str, Any]: 注入认证信息后的清单内容
        """
        # 深拷贝清单内容，避免修改原始数据
        import copy
        final_manifest = copy.deepcopy(manifest_content)
        
        # 解析环境变量
        resolved_auth = self._resolve_env_variables(authentication)
        
        # 将认证信息设置为环境变量
        for key, value in resolved_auth.items():
            if value is not None:
                os.environ[key] = str(value)
                logger.debug(f"注入环境变量 {key}")
        
        return final_manifest
    

    
    async def get_tool_by_name(self, tool_name: str, package_name: str) -> Optional[BaseTool]:
        """根据工具名称和包名获取特定工具
        
        Args:
            tool_name: 工具名称
            package_name: 包名称
            
        Returns:
            Optional[BaseTool]: 工具实例，如果未找到则返回None
        """
        package = self.get_package_info(package_name)
        if not package or not package.enabled:
            return None
        
        try:
            tools = await self._load_package_tools(package)
            for tool in tools:
                if tool.name == tool_name:
                    return tool
        except Exception as e:
            logger.error(f"获取工具 {tool_name} 失败: {e}")
        
        return None
    
    async def cleanup(self) -> None:
        """清理资源，关闭所有适配器"""
        logger.info("清理工具包管理器资源...")
        
        for name, adapter in self.adapters.items():
            try:
                await adapter.cleanup()
                logger.debug(f"已清理适配器: {name}")
            except Exception as e:
                logger.error(f"清理适配器 {name} 失败: {e}")
        
        self.adapters.clear()
        self.tools_cache.clear()
        logger.info("工具包管理器资源清理完成")
    
    def get_package_info(self, tool_name: str) -> Optional[ToolPackage]:
        """获取指定工具的包信息"""
        for package in self.packages:
            if package.name == tool_name:
                return package
        return None
    
    def is_tool_enabled(self, tool_name: str) -> bool:
        """检查工具是否已启用"""
        package = self.get_package_info(tool_name)
        return package.enabled if package else False
    
    def list_available_tools(self) -> List[str]:
        """列出所有可用工具名称"""
        return [package.name for package in self.packages]
    
    def list_enabled_tools(self) -> List[str]:
        """列出所有已启用工具名称"""
        return [package.name for package in self.packages if package.enabled]
    
    def reload_config(self) -> None:
        """重新加载配置文件"""
        logger.info("重新加载工具包配置...")
        self.config = self._load_config()
        self.packages = self._parse_packages()
        # 清理缓存
        self.tools_cache.clear()
        logger.info(f"已加载 {len(self.packages)} 个工具包")


# 全局工具包管理器实例
_tool_manager_instance: Optional[ToolPackageManager] = None


async def get_tool_manager(project_root: Optional[Path] = None) -> ToolPackageManager:
    """获取全局工具包管理器实例"""
    global _tool_manager_instance
    
    if _tool_manager_instance is None:
        _tool_manager_instance = ToolPackageManager(project_root)
    
    return _tool_manager_instance


async def reset_tool_manager() -> None:
    """重置全局工具包管理器实例（主要用于测试）"""
    global _tool_manager_instance
    
    if _tool_manager_instance is not None:
        await _tool_manager_instance.cleanup()
    
    _tool_manager_instance = None