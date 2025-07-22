"""
提供一个get_all_tools()函数,它会自动导入并收集所有定义在tools/目录下的工具
"""

import logging
from typing import List
from langchain_core.tools import BaseTool
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# 全局工具注册表
_TOOL_REGISTRY: List[BaseTool] = []


def register_tool(tool_func: BaseTool):
    """注册工具到全局注册表"""
    _TOOL_REGISTRY.append(tool_func)
    logger.info(f"工具 {tool_func.name} 注册成功")


def get_all_tools() -> List[BaseTool]:
    """获取所有注册的工具"""
    return _TOOL_REGISTRY.copy()


def clear_tools():
    """清空工具注册表（主要用于测试）"""
    global _TOOL_REGISTRY
    _TOOL_REGISTRY.clear()


# 注册默认工具
@tool
def fake_tool(query: str) -> str:
    """这是一个用于测试的伪工具，它总是返回一个固定的字符串。"""
    logger.info(f"伪工具被调用，查询: {query}")
    return "这是一个来自伪工具的回答。"


# 自动注册默认工具
register_tool(fake_tool)