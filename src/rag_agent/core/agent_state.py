"""
LangGraph的核心,AgentState是一个贯穿始终的数据容器,记录了Agent的所有状态
"""

import operator

# TypedDict确保状态字典的类型安全，Annotated为状态字段添加LangGraph特定的元数据
from typing import TypedDict, Annotated, List, Union, Tuple

# BaseMessage是LangChain消息系统的基础类型
from langchain_core.messages import BaseMessage

# AgentAction/AgentFinish是Agent决策结果的类型定义
from langchain_core.agents import AgentAction, AgentFinish


class AgentState(TypedDict):
    """
    Agent的中心状态,所有节点都会读取和修改这个状态
    Attributes:
        messages:对话历史记录
        agent_outcome:Agent上一步的决策结果,可能是调用工具或结束
        intermediate_steps:包含(工具调用、工具输出)的历史记录元组
    """

    messages: Annotated[List[BaseMessage], operator.add]
    agent_outcome: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[Tuple[AgentAction, str]], operator.add]
