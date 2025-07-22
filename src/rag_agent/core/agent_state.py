"""LangGraph的核心,AgentState是一个贯穿始终的数据容器,记录了Agent的所有状态"""

import operator

# TypedDict确保状态字典的类型安全，Annotated为状态字段添加LangGraph特定的元数据
from typing import TypedDict, Annotated, List

# BaseMessage是LangChain消息系统的基础类型
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    现代化的Agent状态,只通过messages驱动一切
    
    现代 LangGraph 的最佳实践是只使用 messages 列表来管理状态：
    - ToolNode 会自动将 ToolMessage 追加到 messages
    - 不再需要手动管理 agent_outcome 和 intermediate_steps
    - 更简单、更健壮的状态管理
    
    Attributes:
        messages: 完整的对话历史，包含 HumanMessage、AIMessage、ToolMessage 等
    """

    messages: Annotated[List[BaseMessage], operator.add]
