# 文件: src/rag_agent/factories/agent_factory.py

import logging
from functools import lru_cache
from typing import Callable

from langgraph.prebuilt import ToolNode

# 导入“零件”提供商
from rag_agent.core.llm_provider import get_llm
from rag_agent.tools.tool_registry import get_all_tools

# 导入图的“蓝图”
from rag_agent.graphs.base_agent_graph import BaseAgentGraph

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_main_agent_runnable() -> Callable:
    """
    工厂函数,负责组装和编译主Agent。
    职责:
    1. 获取所有必要的组件(LLM, 工具)
    2. 配置组件(绑定工具,创建ToolNode)
    3. 获取图的蓝图
    4. 将配置好的组件注入蓝图并编译成可运行的应用
    5. 返回缓存的应用实例
    """
    logger.info("Assembling and compiling the main agent...")
    
    # 1. 获取所有“零件”
    llm = get_llm()
    tools = get_all_tools()

    # 2. 配置和准备“零件”
    llm_with_tools = llm.bind_tools(tools)
    tool_node = ToolNode(tools) # ToolNode 本身就是配置好的节点

    # 3. 获取图的“蓝图”
    graph_blueprint = BaseAgentGraph()

    # 4. 注入依赖并编译出最终产品
    app = graph_blueprint.compile_app(
        llm_with_tools=llm_with_tools,
        tool_node=tool_node
    )
    
    logger.info("Main agent compiled and cached successfully.")
    return app