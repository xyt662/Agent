from langchain_core.agents import AgentFinish
from langchain_core.messages import AIMessage
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from rag_agent.core.agent_state import AgentState


def agent_node(state: AgentState, llm_with_tools):
    """
    负责决策的思考节点
    Args:
        state(AgentState):当前Agent的状态
        llm_with_tools:绑定了工具的LLM实例
    Returns:
        dict:包含Agent决策结果的字典
    """
    print("---思考节点(agent_node)---")

    # 1.格式化历史工具调用记录,作为agent_scratchpad
    # 输入:intermediate_steps = [(AgentAction, tool_output), ...]
    # 输出:格式化的消息列表,包含 AIMessage 和 FunctionMessage
    agent_scratchpad = format_to_openai_tool_messages(state["intermediate_steps"])

    # 2.调用LLM进行决策
    # 将消息和agent_scratchpad合并为完整的消息列表
    all_messages = state["messages"] + agent_scratchpad
    response = llm_with_tools.invoke(all_messages)

    # 3.判断LLM的输出类型
    # 工具调用的决策权完全在LLM,而不是开发者的硬编码逻辑
    if response.tool_calls:
        # 如果LLM决定调用工具
        print(f"决策:调用工具{response.tool_calls[0]['name']}")
        return {
            "messages": [response],  # 将AIMessage添加到消息列表中
            "agent_outcome": {
                "name": response.tool_calls[0]["name"],
                "args": response.tool_calls[0]["args"],
                "id": response.tool_calls[0]["id"],
                "type": "tool_call",
            }
        }
    else:
        # 如果LLM决定直接回答
        print("决策:直接回答")
        return {
            "messages": [response],  # 将AIMessage添加到消息列表中
            "agent_outcome": AgentFinish(
                return_values={"output": response.content}, log=response.content
            )
        }
