#!/usr/bin/env python3
"""
本地命令MCP适配器
负责通过stdio与本地MCP服务器进程通信
基于官方MCP Python客户端教程实现
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, create_model

logger = logging.getLogger(__name__)


class LocalCommandToolAdapter:
    """本地命令MCP适配器类
    
    负责启动本地MCP服务器子进程并与其通信
    将MCP工具转换为LangChain工具
    """
    
    def __init__(self, command: str, args: List[str], env: Optional[Dict[str, str]] = None, name: str = "mcp_adapter"):
        """初始化适配器
        
        Args:
            command: 执行命令 (如 'python', 'node')
            args: 命令参数列表 (如 ['server.py'])
            env: 环境变量字典
            name: 适配器名称
        """
        self.command = command
        self.args = args
        self.env = env
        self.name = name
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.write = None
        self._tools: List[BaseTool] = []
        self._connected = False
        
    async def connect(self) -> None:
        """连接到MCP服务器
        
        基于官方教程的connect_to_server方法实现
        """
        try:
            logger.info(f"🚀 启动MCP服务器 | 命令: {self.command} | 参数: {' '.join(self.args)} | 通信协议: stdio")
            
            # 过滤掉None值的环境变量
            filtered_env = {k: v for k, v in (self.env or {}).items() if v is not None}
            
            # 创建服务器参数
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=filtered_env if filtered_env else None
            )
            
            # 建立stdio传输连接
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport
            
            # 创建客户端会话
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )
            
            # 初始化会话
            await self.session.initialize()
            
            self._connected = True
            logger.info("Successfully connected to MCP server")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            # 简单重置状态，避免调用可能有问题的cleanup
            self._connected = False
            self.session = None
            self.stdio = None
            self.write = None
            raise
    
    async def get_tools(self) -> List[BaseTool]:
        """获取MCP服务器提供的工具列表
        
        Returns:
            List[BaseTool]: LangChain工具列表
        """
        # 如果还未连接，先连接
        if not self._connected:
            await self.connect()
        
        if not self.session:
            raise RuntimeError("Failed to establish MCP server connection.")
        
        try:
            # 获取工具列表
            response = await self.session.list_tools()
            tools = response.tools
            
            logger.info(f"Found {len(tools)} tools: {[tool.name for tool in tools]}")
            
            # 转换为LangChain工具
            langchain_tools = []
            for tool in tools:
                langchain_tool = self._create_langchain_tool(tool)
                langchain_tools.append(langchain_tool)
            
            self._tools = langchain_tools
            return langchain_tools
            
        except Exception as e:
            logger.error(f"Failed to get tools from MCP server: {e}")
            raise
    
    def _create_langchain_tool(self, mcp_tool) -> BaseTool:
        """将MCP工具转换为LangChain工具
        
        Args:
            mcp_tool: MCP工具定义
            
        Returns:
            BaseTool: LangChain工具实例
        """
        tool_name = mcp_tool.name
        tool_description = mcp_tool.description or f"MCP tool: {tool_name}"
        input_schema = mcp_tool.inputSchema or {}
        
        # 创建动态的Pydantic模型作为输入模式
        if input_schema.get('properties'):
            # 从JSON Schema创建Pydantic字段
            fields = {}
            properties = input_schema.get('properties', {})
            required_fields = input_schema.get('required', [])
            
            for field_name, field_def in properties.items():
                field_type = self._json_type_to_python_type(field_def.get('type', 'string'))
                field_description = field_def.get('description', '')
                
                if field_name in required_fields:
                    fields[field_name] = (field_type, Field(description=field_description))
                else:
                    fields[field_name] = (Optional[field_type], Field(default=None, description=field_description))
            
            # 创建动态模型
            InputModel = create_model(f"{tool_name}Input", **fields)
        else:
            # 如果没有输入模式，创建一个空模型
            class InputModel(BaseModel):
                pass
        
        # 创建动态的LangChain工具类
        class DynamicMCPTool(BaseTool):
            name: str = tool_name
            description: str = tool_description
            args_schema: type[BaseModel] = InputModel
            adapter_session: Any = None
            
            def __init__(self, adapter_session):
                super().__init__()
                self.adapter_session = adapter_session
            
            async def _arun(self, **kwargs) -> str:
                """异步执行工具"""
                try:
                    # 过滤掉None值
                    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
                    
                    logger.info(f"🔧 MCP工具调用 | 工具: {tool_name} | 参数: {filtered_kwargs} | 通信方式: stdio")
                    
                    # 调用MCP工具
                    result = await self.adapter_session.call_tool(tool_name, filtered_kwargs)
                    logger.info(f"✅ MCP工具执行完成 | 工具: {tool_name} | 结果长度: {len(str(result)) if result else 0} 字符")
                    
                    # 处理结果
                    if hasattr(result, 'content'):
                        if isinstance(result.content, list):
                            # 如果content是列表，提取文本内容
                            content_parts = []
                            for item in result.content:
                                if hasattr(item, 'text'):
                                    content_parts.append(item.text)
                                elif isinstance(item, str):
                                    content_parts.append(item)
                                else:
                                    content_parts.append(str(item))
                            return '\n'.join(content_parts)
                        else:
                            return str(result.content)
                    else:
                        return str(result)
                        
                except Exception as e:
                    logger.error(f"Error calling MCP tool {tool_name}: {e}")
                    return f"Error: {str(e)}"
            
            def _run(self, **kwargs) -> str:
                """同步执行工具 - MCP工具不支持同步执行，请使用异步方法"""
                return "Error: MCP tools only support asynchronous execution. Please use the async version of this tool."
        
        return DynamicMCPTool(self.session)
    
    def _json_type_to_python_type(self, json_type: str):
        """将JSON Schema类型转换为Python类型
        
        Args:
            json_type: JSON Schema类型字符串
            
        Returns:
            Python类型
        """
        type_mapping = {
            'string': str,
            'integer': int,
            'number': float,
            'boolean': bool,
            'array': list,
            'object': dict
        }
        return type_mapping.get(json_type, str)
    
    async def cleanup(self) -> None:
        """清理资源
        
        关闭会话和子进程
        """
        if not self._connected and self.session is None:
            logger.debug("Adapter already cleaned up, skipping")
            return
            
        logger.info("Cleaning up MCP adapter resources")
        
        # 首先标记为未连接，避免重复清理
        self._connected = False
        
        # 尝试优雅关闭exit_stack，使用多层异常处理
        exit_stack_closed = False
        try:
            # 使用更短的超时时间，快速失败
            await asyncio.wait_for(self.exit_stack.aclose(), timeout=2.0)
            exit_stack_closed = True
            logger.debug("Exit stack closed successfully")
        except asyncio.TimeoutError:
            logger.warning("Exit stack cleanup timed out, will force cleanup")
        except asyncio.CancelledError:
            logger.warning("Exit stack cleanup was cancelled, will force cleanup")
        except Exception as e:
            logger.warning(f"Exit stack cleanup failed: {type(e).__name__}: {e}")
        
        # 如果exit_stack没有正常关闭，尝试强制清理
        if not exit_stack_closed:
            try:
                # 创建新的exit_stack来替换可能损坏的旧实例
                self.exit_stack = AsyncExitStack()
                logger.debug("Created new exit stack after cleanup failure")
            except Exception as e:
                logger.warning(f"Failed to create new exit stack: {e}")
        
        # 清理其他资源
        try:
            self.session = None
            self.stdio = None
            self.write = None
            self._tools = []
            logger.debug("MCP adapter cleanup completed")
        except Exception as e:
            logger.error(f"Error during final cleanup: {e}")
    
    def __del__(self):
        """析构函数，确保资源被清理"""
        if self.session is not None:
            logger.warning("LocalCommandToolAdapter was not properly cleaned up")