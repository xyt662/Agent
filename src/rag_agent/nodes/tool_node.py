from langgraph.prebuilt import ToolNode
from rag_agent.core.agent_state import AgentState


def tool_node(state: AgentState, tool_executor: ToolNode):
    """
    负责执行工具的行动节点
    """
    # 直接使用ToolNode执行工具调用
    result = tool_executor.invoke(state)

    # 返回更新后的状态
    return result
