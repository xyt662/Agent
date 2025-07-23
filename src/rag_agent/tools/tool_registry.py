"""
提供一个get_all_tools()函数,它会自动导入并收集所有定义在tools/目录下的工具
"""

import os
import logging
from typing import List, Dict, Callable
from functools import lru_cache
from pathlib import Path
from langchain_core.tools import BaseTool
from langchain_core.tools import tool

from .knowledge_base import create_knowledge_base_tool
from .mcp_adapter import MCPToolAdapter
from ..core.config import get_mcp_enabled, get_mcp_manifests_dir

logger = logging.getLogger(__name__)

# 可通过环境变量控制的工具配置
CONDITIONAL_TOOL_CONFIGS: Dict[str, Dict[str, any]] = {
    "knowledge_base": {
        "creator": create_knowledge_base_tool,
        "enabled": True  # 核心工具，始终启用
    },
    # 未来可以添加更多工具，例如：
    # "web_search": {
    #     "creator": create_web_search_tool,
    #     "enabled": os.getenv("ENABLE_WEB_SEARCH", "false").lower() == "true"
    # }
}


# 定义默认工具
@tool
def fake_tool(query: str) -> str:
    """这是一个用于测试的伪工具，它总是返回一个固定的字符串。"""
    logger.info(f"伪工具被调用，查询: {query}")
    return "这是一个来自伪工具的回答。"


def load_mcp_tools() -> List[BaseTool]:
    """加载MCP工具
    
    Returns:
        List[BaseTool]: MCP工具列表
    """
    mcp_tools = []
    
    if not get_mcp_enabled():
        logger.info("MCP工具已禁用")
        return mcp_tools
    
    manifests_dir = get_mcp_manifests_dir()
    if not manifests_dir.exists():
        logger.warning(f"MCP清单目录不存在: {manifests_dir}")
        return mcp_tools
    
    logger.info(f"开始加载MCP工具，清单目录: {manifests_dir}")
    
    # 遍历清单目录中的所有YAML文件
    for manifest_file in manifests_dir.glob("*.yaml"):
        try:
            logger.info(f"正在加载MCP工具清单: {manifest_file.name}")
            adapter = MCPToolAdapter(str(manifest_file))
            tool = adapter.to_langchain_tool()
            mcp_tools.append(tool)
            logger.info(f"✓ 成功注册MCP工具: {tool.name}")
        except Exception as e:
            logger.error(f"✗ MCP工具 {manifest_file.name} 加载失败: {e}")
    
    logger.info(f"MCP工具加载完成，共加载 {len(mcp_tools)} 个工具")
    return mcp_tools


@lru_cache(maxsize=1)
def get_all_tools() -> List[BaseTool]:
    """获取所有可用工具
    
    该函数使用lru_cache装饰器确保工具只被实例化一次。
    会尝试加载所有配置的工具，失败的工具会被跳过。
    如果所有工具都失败，将返回备用工具。
    """
    tools = []
    
    for tool_name, config in CONDITIONAL_TOOL_CONFIGS.items():
        if not config["enabled"]:
            logger.info(f"{tool_name}工具已禁用，跳过")
            continue
            
        try:
            tool = config["creator"]()
            tools.append(tool)
            logger.info(f"{tool_name}工具注册成功")
        except Exception as e:
            logger.warning(f"{tool_name}工具注册失败: {e}，跳过该工具")
    
    # 加载MCP工具
    mcp_tools = load_mcp_tools()
    tools.extend(mcp_tools)
    
    if not tools:
        logger.warning("所有工具都加载失败，使用备用工具")
        tools.append(fake_tool)
    
    return tools


def clear_tools_cache():
    """清除工具缓存（主要用于测试）"""
    get_all_tools.cache_clear()