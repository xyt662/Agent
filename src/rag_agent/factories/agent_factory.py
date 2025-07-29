# 文件: src/rag_agent/factories/agent_factory.py

import logging
import functools
from typing import Callable

from langgraph.prebuilt import ToolNode

# 导入"零件"提供商
from ..core.llm_provider import get_llm
from ..tools.tool_registry import get_all_tools
from ..tools.tool_manager import get_tool_manager

# 导入图的"蓝图"
from ..graphs.base_agent_graph import BaseAgentGraphBuilder

logger = logging.getLogger(__name__)

# 全局变量持有 ToolManager
_tool_manager_instance = None

# Agent实例缓存
_agent_cache = {}

def _get_cache_key(tools_signature: str, llm_model: str) -> str:
    """生成缓存key"""
    return f"{tools_signature}_{llm_model}"

def _clear_agent_cache():
    """清除Agent缓存"""
    global _agent_cache
    _agent_cache.clear()
    logger.info("Agent缓存已清除")

async def get_main_agent_runnable() -> Callable:
    """
    工厂函数,负责组装和编译主Agent
    职责:
    1. 获取工具签名用于缓存key
    2. 检查缓存是否命中
    3. 如果缓存未命中，则构建新的Agent实例
    4. 返回Agent实例
    """
    global _tool_manager_instance, _agent_cache
    
    # 1. 初始化全局ToolManager（如果尚未初始化）
    if _tool_manager_instance is None:
        _tool_manager_instance = await get_tool_manager()
        logger.info("Global ToolManager initialized")
    
    # 2. 获取工具签名用于缓存
    tools_signature = _tool_manager_instance.get_tools_signature()
    llm_model = "deepseek-v3"  # 从配置获取模型名称
    cache_key = _get_cache_key(tools_signature, llm_model)
    
    # 3. 检查缓存
    if cache_key in _agent_cache:
        logger.info(f"✅ Agent缓存命中 - 签名: {tools_signature[:8]}...")
        return _agent_cache[cache_key]
    
    # 4. 缓存未命中，构建新的Agent
    logger.info(f"❌ Agent缓存未命中 - 开始编译新实例")
    logger.info(f"工具签名: {tools_signature}")
    
    # 获取所有"零件"
    llm = get_llm()
    tools = await get_all_tools(_tool_manager_instance)

    # 获取图的"蓝图"
    graph_builder = BaseAgentGraphBuilder()

    # 注入依赖并编译出最终产品
    app = graph_builder.build(llm=llm, tools=tools)
    
    # 将结果存入缓存
    _agent_cache[cache_key] = app
    
    logger.info(f"✅ Agent编译完成并已缓存 - 缓存大小: {len(_agent_cache)}")
    return app


async def reset_agent_cache():
    """
    重置 Agent 缓存，强制下次调用时重新初始化
    用于工具配置热重载后刷新 Agent 实例
    """
    global _tool_manager_instance
    
    logger.info("重置 Agent 缓存...")
    
    # 清理Agent实例缓存
    _clear_agent_cache()
    
    # 清理旧的 ToolManager 实例
    if _tool_manager_instance:
        try:
            await _tool_manager_instance.cleanup()
        except Exception as e:
            logger.error(f"清理旧 ToolManager 时出错: {e}")
    
    # 重置全局实例，下次调用时会重新创建
    _tool_manager_instance = None
    
    logger.info("Agent 缓存重置完成")


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