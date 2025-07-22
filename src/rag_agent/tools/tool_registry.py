"""
提供一个get_all_tools()函数,它会自动导入并收集所有定义在tools/目录下的工具
"""

import os
import logging
from typing import List, Dict, Callable
from functools import lru_cache
from langchain_core.tools import BaseTool
from langchain_core.tools import tool

from .knowledge_base import create_knowledge_base_tool

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
    
    if not tools:
        logger.warning("所有工具都加载失败，使用备用工具")
        tools.append(fake_tool)
    
    return tools


def clear_tools_cache():
    """清除工具缓存（主要用于测试）"""
    get_all_tools.cache_clear()