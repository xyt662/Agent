# 文件: src/rag_agent/graphs/base_agent_graph.py

import logging
from typing import List
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from rag_agent.core.agent_state import AgentState
from rag_agent.nodes.agent_node import agent_node

logger = logging.getLogger(__name__)

def should_continue(state: AgentState) -> str:
    """路由逻辑：检查最新的消息是否包含工具调用"""
    if state['messages'][-1].tool_calls:
        return "action"
    return "end"

class BaseAgentGraphBuilder:
    """
    一个负责定义基础 ReAct Agent 图“结构”的构建器
    它不关心具体的LLM和工具,只定义流程
    """
    def __init__(self):
        self.graph = StateGraph(AgentState)
        self._setup_nodes()
        self._setup_edges()

    def _setup_nodes(self):
        """定义图中的所有节点，但不绑定具体实现"""
        # 节点定义是占位符，等待被注入具体逻辑
        # 这里先不添加节点，在build方法中添加
        pass

    def _setup_edges(self):
        """定义图的流程和边"""
        self.graph.set_entry_point("agent")
        self.graph.add_conditional_edges("agent", should_continue, {"action": "action", "end": END})
        self.graph.add_edge("action", "agent")

    def build(self, llm: BaseChatModel, tools: List[BaseTool]):
        """
        接收具体的“零件”(LLM和工具),完成图的最终组装和编译。
        """
        # 1. 绑定LLM和工具
        llm_with_tools = llm.bind_tools(tools)
        tool_node_executor = ToolNode(tools)

        # 2. 定义节点运行时的具体逻辑（异步版本）
        async def agent_node_wrapper(state):
            # 将外部注入的 llm_with_tools 传递给异步节点函数
            return await agent_node(state, llm_with_tools)

        async def tool_node_wrapper(state):
            # ToolNode 使用异步调用来支持异步工具
            return await tool_node_executor.ainvoke(state)

        # 3. 将具体逻辑绑定到图中
        self.graph.add_node("agent", agent_node_wrapper)
        self.graph.add_node("action", tool_node_wrapper)

        # 4. 编译并返回最终产品
        return self.graph.compile()