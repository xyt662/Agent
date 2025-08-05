"""事件驱动AgentState使用示例

这个文件演示了如何在LangGraph节点中使用新的事件驱动架构，
包括自我纠错、长期记忆、多智能体协作等高级功能的实现
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.rag_agent.core.agent_state import AgentState, EventType, EventStatus
from src.rag_agent.core.state_aggregator import StateAggregator
from src.rag_agent.core.event_utils import EventMessageFactory, EventQueryHelper


def example_self_correction_node(state: AgentState) -> AgentState:
    """
    示例：自我纠错节点
    
    演示如何检测错误并触发自我纠错机制
    """
    messages = state["messages"]
    new_messages = []
    
    # 1. 检查最近的工具执行是否失败
    recent_tool_messages = [msg for msg in messages[-5:] if isinstance(msg, ToolMessage)]
    
    for tool_msg in recent_tool_messages:
        if "error" in tool_msg.content.lower() or "failed" in tool_msg.content.lower():
            # 触发纠错事件
            correction_event = EventMessageFactory.create_correction_trigger_event(
                reason=f"工具执行失败: {getattr(tool_msg, 'name', 'unknown')}",
                error_type="tool_failure",
                context={"tool_content": tool_msg.content}
            )
            new_messages.append(correction_event)
            
            # 创建纠错尝试
            correction_attempt = EventMessageFactory.create_correction_attempt_event(
                correction_action="重新分析问题并选择合适的工具",
                parent_event_id=correction_event.additional_kwargs["metadata"]["event_id"]
            )
            new_messages.append(correction_attempt)
    
    return {"messages": messages + new_messages}


def example_memory_management_node(state: AgentState) -> AgentState:
    """
    示例：记忆管理节点
    
    演示如何存储和检索长期记忆
    """
    messages = state["messages"]
    new_messages = []
    
    # 1. 检查是否有重要信息需要存储
    if messages:
        last_message = messages[-1]
        if isinstance(last_message, AIMessage) and "重要" in last_message.content:
            # 存储重要信息到长期记忆
            memory_key = f"insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            memory_event = EventMessageFactory.create_memory_store_event(
                memory_key=memory_key,
                content=last_message.content,
                context={"importance_level": "high"}
            )
            new_messages.append(memory_event)
    
    # 2. 检查是否需要检索记忆
    if messages and isinstance(messages[-1], HumanMessage):
        user_message = messages[-1].content
        if any(keyword in user_message for keyword in ["之前", "历史", "记得"]):
            # 检索相关记忆
            retrieval_event = EventMessageFactory.create_memory_retrieve_event(
                query_context=user_message[:100],
                context={"retrieval_trigger": "user_reference"}
            )
            new_messages.append(retrieval_event)
    
    return {"messages": messages + new_messages}


def example_multi_agent_collaboration_node(state: AgentState) -> AgentState:
    """
    示例：多智能体协作节点
    
    演示如何委派任务给其他智能体
    """
    messages = state["messages"]
    new_messages = []
    
    # 检查是否需要委派任务
    if messages and isinstance(messages[-1], HumanMessage):
        user_message = messages[-1].content
        
        # 简单的任务分类逻辑
        if "翻译" in user_message:
            # 委派给翻译专家
            delegation_event = EventMessageFactory.create_agent_delegation_event(
                target_agent="translation_expert",
                task_description=f"翻译任务: {user_message}",
                context={"task_type": "translation", "priority": "normal"}
            )
            new_messages.append(delegation_event)
            
        elif "数据分析" in user_message:
            # 委派给数据分析专家
            delegation_event = EventMessageFactory.create_agent_delegation_event(
                target_agent="data_analyst",
                task_description=f"数据分析任务: {user_message}",
                context={"task_type": "analysis", "priority": "high"}
            )
            new_messages.append(delegation_event)
    
    return {"messages": messages + new_messages}


def example_clarification_node(state: AgentState) -> AgentState:
    """
    示例：主动澄清节点
    
    演示如何检测歧义并请求澄清
    """
    messages = state["messages"]
    new_messages = []
    
    if messages and isinstance(messages[-1], HumanMessage):
        user_message = messages[-1].content
        
        # 检测歧义的简单规则
        ambiguous_keywords = ["这个", "那个", "它", "他们"]
        if any(keyword in user_message for keyword in ambiguous_keywords):
            # 请求澄清
            clarification_event = EventMessageFactory.create_clarification_request_event(
                question="您提到的'这个'具体指的是什么？能否提供更多细节？",
                context={"ambiguous_terms": ambiguous_keywords, "original_message": user_message}
            )
            new_messages.append(clarification_event)
    
    return {"messages": messages + new_messages}


def example_multi_hop_query_node(state: AgentState) -> AgentState:
    """
    示例：多跳查询节点
    
    演示如何处理复杂的多步骤查询
    """
    messages = state["messages"]
    new_messages = []
    
    # 检查是否是复杂查询
    if messages and isinstance(messages[-1], HumanMessage):
        user_message = messages[-1].content
        
        # 检测复杂查询的关键词
        complex_indicators = ["首先", "然后", "接下来", "最后", "步骤"]
        if any(indicator in user_message for indicator in complex_indicators):
            # 开始多跳查询
            query_id = str(uuid.uuid4())
            
            # 第一步
            step1_event = EventMessageFactory.create_multi_hop_step_event(
                hop_index=1,
                step_description="分析用户需求，识别查询步骤",
                parent_event_id=query_id,
                context={"original_query": user_message}
            )
            new_messages.append(step1_event)
            
            # 第二步
            step2_event = EventMessageFactory.create_multi_hop_step_event(
                hop_index=2,
                step_description="执行第一个子查询",
                parent_event_id=query_id,
                context={"sub_query": "提取关键信息"}
            )
            new_messages.append(step2_event)
    
    return {"messages": messages + new_messages}


def example_state_analysis_node(state: AgentState) -> AgentState:
    """
    示例：状态分析节点
    
    演示如何使用StateAggregator分析当前状态
    """
    messages = state["messages"]
    new_messages = []
    
    # 获取综合状态
    comprehensive_state = StateAggregator.get_comprehensive_state(messages)
    
    # 分析状态并生成报告
    analysis_parts = []
    
    # 记忆状态分析
    memory_state = comprehensive_state['memory']
    if memory_state['stored_memories']:
        analysis_parts.append(f"长期记忆: {len(memory_state['stored_memories'])}条记录")
    
    # 纠错状态分析
    correction_state = comprehensive_state['correction']
    if correction_state['active_corrections']:
        analysis_parts.append(f"活跃纠错: {len(correction_state['active_corrections'])}个任务")
    
    # 协作状态分析
    collaboration_state = comprehensive_state['collaboration']
    if collaboration_state['active_delegations']:
        analysis_parts.append(f"协作任务: {len(collaboration_state['active_delegations'])}个委派")
    
    if analysis_parts:
        # 生成状态报告
        report_content = f"📊 当前状态: {'; '.join(analysis_parts)}"
        system_event = EventMessageFactory.create_system_event(
            content=report_content,
            context={"state_analysis": comprehensive_state}
        )
        new_messages.append(system_event)
    
    return {"messages": messages + new_messages}


def example_event_query_usage(messages: List):
    """
    示例：事件查询功能的使用
    
    演示如何使用EventQueryHelper查询特定事件
    """
    # 查找所有记忆相关事件
    memory_events = EventQueryHelper.find_events_by_type(messages, EventType.MEMORY_STORE)
    print(f"找到 {len(memory_events)} 个记忆存储事件")
    
    # 查找所有待处理的事件
    pending_events = EventQueryHelper.find_events_by_status(messages, EventStatus.PENDING)
    print(f"找到 {len(pending_events)} 个待处理事件")
    
    # 查找最新的纠错事件
    latest_correction = EventQueryHelper.get_latest_event_by_type(messages, EventType.CORRECTION_TRIGGER)
    if latest_correction:
        print(f"最新纠错事件: {latest_correction.content}")
    
    # 查找事件链
    if memory_events:
        first_memory_event = memory_events[0]
        event_id = first_memory_event.additional_kwargs["metadata"]["event_id"]
        related_events = EventQueryHelper.find_event_chain(messages, event_id)
        print(f"找到 {len(related_events)} 个相关事件")


def create_sample_conversation() -> List:
    """
    创建一个示例对话，展示事件驱动架构的完整流程
    """
    messages = []
    
    # 1. 用户提问
    messages.append(HumanMessage(content="请帮我分析这个数据，然后记住重要的发现"))
    
    # 2. AI响应并存储记忆
    messages.append(AIMessage(content="我将分析数据并记录重要发现"))
    
    # 3. 记忆存储事件
    memory_event = EventMessageFactory.create_memory_store_event(
        memory_key="data_analysis_20241201",
        content="用户请求数据分析并要求记录重要发现"
    )
    messages.append(memory_event)
    
    # 4. 工具执行失败
    messages.append(ToolMessage(
        content="Error: 数据文件无法访问",
        tool_call_id="tool_123"
    ))
    
    # 5. 触发纠错
    correction_event = EventMessageFactory.create_correction_trigger_event(
        reason="数据文件访问失败",
        error_type="file_access_error"
    )
    messages.append(correction_event)
    
    # 6. 纠错尝试
    correction_attempt = EventMessageFactory.create_correction_attempt_event(
        correction_action="尝试使用备用数据源",
        parent_event_id=correction_event.additional_kwargs["metadata"]["event_id"]
    )
    messages.append(correction_attempt)
    
    # 7. 用户澄清
    messages.append(HumanMessage(content="我之前提到的那个数据是什么意思？"))
    
    # 8. 请求澄清
    clarification_event = EventMessageFactory.create_clarification_request_event(
        question="您提到的'那个数据'具体指哪个数据集？"
    )
    messages.append(clarification_event)
    
    return messages


if __name__ == "__main__":
    # 创建示例对话
    sample_messages = create_sample_conversation()
    
    # 演示状态聚合
    print("=== 状态聚合示例 ===")
    comprehensive_state = StateAggregator.get_comprehensive_state(sample_messages)
    print(f"总消息数: {comprehensive_state['total_messages']}")
    print(f"记忆状态: {comprehensive_state['memory']}")
    print(f"纠错状态: {comprehensive_state['correction']}")
    print(f"澄清状态: {comprehensive_state['clarification']}")
    
    # 演示事件查询
    print("\n=== 事件查询示例 ===")
    example_event_query_usage(sample_messages)
    
    # 演示节点处理
    print("\n=== 节点处理示例 ===")
    initial_state = {"messages": sample_messages}
    
    # 通过各个示例节点处理
    state_after_correction = example_self_correction_node(initial_state)
    state_after_memory = example_memory_management_node(state_after_correction)
    state_after_analysis = example_state_analysis_node(state_after_memory)
    
    print(f"处理后总消息数: {len(state_after_analysis['messages'])}")
    print("最新消息:")
    for msg in state_after_analysis['messages'][-3:]:
        print(f"  - {type(msg).__name__}: {msg.content}")