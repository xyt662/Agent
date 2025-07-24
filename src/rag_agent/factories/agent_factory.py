# 文件: src/rag_agent/factories/agent_factory.py

import logging
from functools import lru_cache
from typing import Callable

from langgraph.prebuilt import ToolNode

# 导入"零件"提供商
from rag_agent.core.llm_provider import get_llm
from rag_agent.tools.tool_registry import get_all_tools
from rag_agent.tools.tool_manager import get_tool_manager

# 导入图的"蓝图"
from rag_agent.graphs.base_agent_graph import BaseAgentGraphBuilder

logger = logging.getLogger(__name__)

# 全局变量持有 ToolManager
_tool_manager_instance = None

async def get_main_agent_runnable() -> Callable:
    """
    工厂函数,负责组装和编译主Agent
    职责:
    1. 获取所有必要的组件(LLM, 工具)
    2. 配置组件(绑定工具,创建ToolNode)
    3. 获取图的蓝图
    4. 将配置好的组件注入蓝图并编译成可运行的应用
    5. 返回缓存的应用实例
    """
    global _tool_manager_instance
    
    logger.info("Assembling and compiling the main agent...")
    
    # 1. 初始化全局ToolManager（如果尚未初始化）
    if _tool_manager_instance is None:
        _tool_manager_instance = await get_tool_manager()
        logger.info("Global ToolManager initialized")
    
    # 2. 获取所有"零件"
    llm = get_llm()
    tools = await get_all_tools(_tool_manager_instance)

    # 3. 获取图的"蓝图"
    graph_builder = BaseAgentGraphBuilder()

    # 4. 注入依赖并编译出最终产品
    app = graph_builder.build(llm=llm, tools=tools)
    
    logger.info("Main agent compiled and cached successfully.")
    return app


async def shutdown_agent_services():
    """
    提供一个全局的关闭函数，用于清理ToolManager资源
    """
    global _tool_manager_instance
    
    if _tool_manager_instance:
        logger.info("Shutting down ToolManager...")
        try:
            await _tool_manager_instance.cleanup()
            logger.info("ToolManager cleanup completed")
        except Exception as e:
            logger.error(f"Error during ToolManager cleanup: {e}")
        finally:
            _tool_manager_instance = None
    else:
        logger.info("No ToolManager instance to cleanup")