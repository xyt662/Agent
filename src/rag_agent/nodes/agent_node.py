from rag_agent.core.agent_state import AgentState


async def agent_node(state: AgentState, llm_with_tools):
    """
    异步思考节点
    
    现代 LangGraph 的最佳实践：
    - 不再需要手动格式化 intermediate_steps
    - ToolNode 和新的状态管理方式会自动处理工具调用历史
    - 只需要把 LLM 的响应返回即可
    - 使用异步调用以支持异步工具
    
    Args:
        state(AgentState): 当前Agent的状态，只包含messages
        llm_with_tools: 绑定了工具的LLM实例
    Returns:
        dict: 包含更新后的messages的字典
    """
    print("---思考节点(agent_node)---")

    # 使用异步调用LLM，它能看到包含ToolMessage在内的完整历史
    response = await llm_with_tools.ainvoke(state["messages"])
    
    # 简单的调试信息
    if response.tool_calls:
        print(f"决策:调用工具{response.tool_calls[0]['name']}")
    else:
        print("决策:直接回答")

    # 不再需要复杂的判断，直接返回包含AIMessage的更新
    return {"messages": [response]}
