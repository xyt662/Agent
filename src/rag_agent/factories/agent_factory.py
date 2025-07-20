"""
构建和编译图的核心
"""

# src/rag_agent/factories/agent_factory.py

import logging
from functools import partial, lru_cache
from typing import List, Callable

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.rag_agent.core.agent_state import AgentState
from src.rag_agent.nodes.agent_node import agent_node
from src.rag_agent.nodes.tool_node import tool_node
from src.rag_agent.core.llm_provider import get_llm
from src.rag_agent.tools.tool_registry import get_all_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- 路由逻辑应该和图的构建逻辑放在一起 ---
def should_continue(state: AgentState) -> str:
    """决定流程走向的条件边"""
    if "agent_outcome" not in state or state["agent_outcome"] is None:
        # 这是一个初始状态或错误状态，应该结束
        logger.warning("Agent outcome not in state, ending.")
        return "end"

    if (
        hasattr(state["agent_outcome"], "tool_calls")
        and state["agent_outcome"].tool_calls
    ):
        logger.info("Decision: Continue to action.")
        return "continue"
    else:
        logger.info("Decision: End.")
        return "end"


class AgentBuilder:
    """
    一个负责构建和编译 Agent 图的构建器
    它接受模型、工具和节点作为参数，而不是硬编码它们
    """

    def __init__(self, llm: BaseChatModel, tools: List[BaseTool]):
        self.llm = llm
        self.tools = tools
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.tool_executor = ToolNode(self.tools)

    def build(self) -> Callable:
        """构建、编译并返回一个可执行的 Agent 图"""
        logger.info("Building Agent graph...")

        graph = StateGraph(AgentState)

        # 绑定节点函数，使其符合 LangGraph 签名
        agent_node_partial = partial(agent_node, llm_with_tools=self.llm_with_tools)
        tool_node_partial = partial(tool_node, tool_executor=self.tool_executor)

        # 添加节点
        graph.add_node("agent", agent_node_partial)
        graph.add_node("action", tool_node_partial)

        # 设置图的流程
        graph.set_entry_point("agent")
        graph.add_conditional_edges(
            "agent", should_continue, {"continue": "action", "end": END}
        )
        graph.add_edge("action", "agent")

        # 编译
        app = graph.compile()
        logger.info("Agent graph compiled successfully.")
        return app


@lru_cache(maxsize=1)
def get_main_agent_runnable() -> Callable:
    """
    一个全局可用的函数，用于获取单例的、编译好的 Agent
    这是应用的实际入口点
    """
    logger.info("Creating main agent runnable (cached)...")
    try:
        # 1. 获取模型
        llm = get_llm()  # 这个函数封装了模型初始化逻辑
        # 2. 获取工具
        tools = get_all_tools()  # 这个函数封装了工具注册逻辑
        # 3. 使用构建器创建 Agent
        builder = AgentBuilder(llm=llm, tools=tools)
        return builder.build()
    except Exception as e:
        logger.error(f"Failed to create main agent runnable: {e}", exc_info=True)
        raise


# 示例：如何使用
if __name__ == "__main__":
    # 第一次调用会创建并编译
    main_agent = get_main_agent_runnable()
    print(f"Agent 1: {main_agent}")

    # 第二次调用会直接从缓存返回
    main_agent_cached = get_main_agent_runnable()
    print(f"Agent 2 (from cache): {main_agent_cached}")
    print(f"Is same object? {main_agent is main_agent_cached}")
