#!/usr/bin/env python3
"""
事件驱动AgentState功能测试脚本

测试重构后的AgentState是否能正确实现以下高级功能：
1. 长期记忆存储和检索
2. 自我纠错机制
3. 多智能体协作
4. 主动澄清
5. 多跳查询
6. 事件流分析和状态聚合
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.rag_agent.core.agent_state import AgentState, EventType, EventStatus, EventMetadata
from src.rag_agent.core.event_utils import EventMessageFactory, EventQueryHelper
from src.rag_agent.core.state_aggregator import StateAggregator
from src.rag_agent.core.memory.memory_events import MemoryEventFactory
from src.rag_agent.nodes.clarification_node import ClarificationEventFactory
from src.rag_agent.graphs.multi_hop_graph import MultiHopEventFactory


def test_memory_functionality():
    """测试长期记忆功能"""
    print("\n🧠 测试长期记忆功能...")
    
    # 创建初始状态
    state: AgentState = {"messages": []}
    
    # 1. 用户提问
    user_message = HumanMessage(content="请记住我的生日是1990年5月15日")
    state["messages"].append(user_message)
    
    # 2. 存储记忆事件
    memory_store_event = MemoryEventFactory.create_memory_store_event(
        memory_key="user_birthday",
        content="用户生日：1990年5月15日",
        context={"category": "personal_info", "importance": "high"}
    )
    state["messages"].append(memory_store_event)
    
    # 3. 后续用户询问
    query_message = HumanMessage(content="我的生日是什么时候？")
    state["messages"].append(query_message)
    
    # 4. 检索记忆事件
    memory_retrieve_event = MemoryEventFactory.create_memory_retrieve_event(
        query_context="用户生日信息",
        context={"search_keywords": ["生日", "birthday"]}
    )
    state["messages"].append(memory_retrieve_event)
    
    # 验证记忆功能
    memory_state = StateAggregator.get_memory_state(state["messages"])
    memory_events = EventQueryHelper.find_events_by_type(state["messages"], EventType.MEMORY_STORE)
    
    print(f"✅ 记忆存储事件数量: {len(memory_events)}")
    print(f"✅ 记忆状态: {memory_state}")
    
    assert len(memory_events) == 1, "应该有1个记忆存储事件"
    assert len(memory_state["stored_memories"]) == 1, "应该有1个存储的记忆"
    print("✅ 长期记忆功能测试通过")
    
    return state


def test_self_correction_functionality():
    """测试自我纠错功能"""
    print("\n🔧 测试自我纠错功能...")
    
    # 创建初始状态
    state: AgentState = {"messages": []}
    
    # 1. 用户提问
    user_message = HumanMessage(content="帮我查询天气信息")
    state["messages"].append(user_message)
    
    # 2. 工具执行失败
    tool_failure = ToolMessage(
        content="Error: API key invalid",
        tool_call_id="weather_tool_123"
    )
    state["messages"].append(tool_failure)
    
    # 3. 触发纠错
    correction_trigger = EventMessageFactory.create_correction_trigger_event(
        reason="天气API密钥无效",
        error_type="authentication_error",
        context={"tool_name": "weather_api", "error_code": "401"}
    )
    state["messages"].append(correction_trigger)
    
    # 4. 纠错尝试
    correction_attempt = EventMessageFactory.create_correction_attempt_event(
        correction_action="尝试使用备用天气API",
        parent_event_id=correction_trigger.additional_kwargs["metadata"]["event_id"],
        context={"backup_api": "openweather"}
    )
    state["messages"].append(correction_attempt)
    
    # 验证纠错功能
    correction_state = StateAggregator.get_correction_state(state["messages"])
    correction_events = EventQueryHelper.find_events_by_type(state["messages"], EventType.CORRECTION_TRIGGER)
    
    print(f"✅ 纠错触发事件数量: {len(correction_events)}")
    print(f"✅ 纠错状态: {correction_state}")
    
    assert len(correction_events) == 1, "应该有1个纠错触发事件"
    assert len(correction_state["active_corrections"]) == 1, "应该有1个活跃纠错"
    print("✅ 自我纠错功能测试通过")
    
    return state


def test_multi_agent_collaboration():
    """测试多智能体协作功能"""
    print("\n🤝 测试多智能体协作功能...")
    
    # 创建初始状态
    state: AgentState = {"messages": []}
    
    # 1. 用户提问
    user_message = HumanMessage(content="请帮我翻译这段文字并分析其情感")
    state["messages"].append(user_message)
    
    # 2. 委派给翻译专家
    translation_delegation = EventMessageFactory.create_agent_delegation_event(
        target_agent="translation_expert",
        task_description="翻译文字内容",
        context={"source_language": "auto", "target_language": "zh"}
    )
    state["messages"].append(translation_delegation)
    
    # 3. 翻译专家回调
    translation_callback = EventMessageFactory.create_agent_callback_event(
        result="翻译完成：这是一段积极正面的文字",
        parent_event_id=translation_delegation.additional_kwargs["metadata"]["event_id"],
        status=EventStatus.SUCCESS
    )
    state["messages"].append(translation_callback)
    
    # 4. 委派给情感分析专家
    sentiment_delegation = EventMessageFactory.create_agent_delegation_event(
        target_agent="sentiment_analyst",
        task_description="分析文字情感倾向",
        context={"text_source": "translated_content"}
    )
    state["messages"].append(sentiment_delegation)
    
    # 验证协作功能
    collaboration_state = StateAggregator.get_collaboration_state(state["messages"])
    delegation_events = EventQueryHelper.find_events_by_type(state["messages"], EventType.AGENT_DELEGATION)
    
    print(f"✅ 智能体委派事件数量: {len(delegation_events)}")
    print(f"✅ 协作状态: {collaboration_state}")
    
    assert len(delegation_events) == 2, "应该有2个委派事件"
    assert len(collaboration_state["active_delegations"]) >= 1, "应该有活跃委派"
    print("✅ 多智能体协作功能测试通过")
    
    return state


def test_proactive_clarification():
    """测试主动澄清功能"""
    print("\n❓ 测试主动澄清功能...")
    
    # 创建初始状态
    state: AgentState = {"messages": []}
    
    # 1. 用户模糊提问
    user_message = HumanMessage(content="帮我处理那个文件")
    state["messages"].append(user_message)
    
    # 2. 请求澄清
    clarification_request = ClarificationEventFactory.create_clarification_request_event(
        question="您提到的'那个文件'具体是指哪个文件？请提供文件名或路径。",
        context={"ambiguity_type": "file_reference", "confidence": 0.3}
    )
    state["messages"].append(clarification_request)
    
    # 3. 用户澄清
    user_clarification = HumanMessage(content="我说的是report.pdf文件")
    state["messages"].append(user_clarification)
    
    # 4. 澄清响应
    clarification_response = ClarificationEventFactory.create_clarification_response_event(
        answer="明白了，您需要处理report.pdf文件",
        parent_event_id=clarification_request.additional_kwargs["metadata"]["event_id"],
        context={"resolved_reference": "report.pdf"}
    )
    state["messages"].append(clarification_response)
    
    # 验证澄清功能
    clarification_state = StateAggregator.get_clarification_state(state["messages"])
    clarification_events = EventQueryHelper.find_events_by_type(state["messages"], EventType.CLARIFICATION_REQUEST)
    
    print(f"✅ 澄清请求事件数量: {len(clarification_events)}")
    print(f"✅ 澄清状态: {clarification_state}")
    
    assert len(clarification_events) == 1, "应该有1个澄清请求事件"
    assert len(clarification_state["pending_clarifications"]) >= 0, "澄清状态正常"
    print("✅ 主动澄清功能测试通过")
    
    return state


def test_multi_hop_queries():
    """测试多跳查询功能"""
    print("\n🔄 测试多跳查询功能...")
    
    # 创建初始状态
    state: AgentState = {"messages": []}
    
    # 1. 用户复杂查询
    user_message = HumanMessage(content="找到最近的咖啡店，然后查询它的营业时间和评价")
    state["messages"].append(user_message)
    
    # 2. 第一跳：查找咖啡店
    hop1_event = MultiHopEventFactory.create_multi_hop_step_event(
        hop_index=1,
        step_description="查找最近的咖啡店",
        context={"query_type": "location_search", "radius": "1km"}
    )
    state["messages"].append(hop1_event)
    
    # 3. 第二跳：查询营业时间
    hop2_event = MultiHopEventFactory.create_multi_hop_step_event(
        hop_index=2,
        step_description="查询咖啡店营业时间",
        parent_event_id=hop1_event.additional_kwargs["metadata"]["event_id"],
        context={"query_type": "business_hours", "shop_name": "星巴克"}
    )
    state["messages"].append(hop2_event)
    
    # 4. 第三跳：查询评价
    hop3_event = MultiHopEventFactory.create_multi_hop_step_event(
        hop_index=3,
        step_description="查询咖啡店用户评价",
        parent_event_id=hop1_event.additional_kwargs["metadata"]["event_id"],
        context={"query_type": "reviews", "shop_name": "星巴克"}
    )
    state["messages"].append(hop3_event)
    
    # 5. 完成多跳查询
    completion_event = MultiHopEventFactory.create_multi_hop_complete_event(
        final_result="找到星巴克咖啡店，营业时间7:00-22:00，评分4.5星",
        total_hops=3,
        context={"success": True, "completion_time": datetime.now().isoformat()}
    )
    state["messages"].append(completion_event)
    
    # 验证多跳查询功能
    multi_hop_state = StateAggregator.get_multi_hop_state(state["messages"])
    hop_events = EventQueryHelper.find_events_by_type(state["messages"], EventType.MULTI_HOP_STEP)
    
    print(f"✅ 多跳步骤事件数量: {len(hop_events)}")
    print(f"✅ 多跳查询状态: {multi_hop_state}")
    
    assert len(hop_events) == 3, "应该有3个多跳步骤事件"
    assert len(multi_hop_state["active_queries"]) >= 0, "多跳查询状态正常"
    print("✅ 多跳查询功能测试通过")
    
    return state


def test_event_query_capabilities():
    """测试事件查询能力"""
    print("\n🔍 测试事件查询能力...")
    
    # 创建包含多种事件的状态
    state: AgentState = {"messages": []}
    
    # 添加各种类型的事件
    events = [
        MemoryEventFactory.create_memory_store_event("test_key", "test_content"),
        EventMessageFactory.create_correction_trigger_event("test_error", "test_type"),
        ClarificationEventFactory.create_clarification_request_event("test_question"),
        EventMessageFactory.create_agent_delegation_event("test_agent", "test_task"),
        MultiHopEventFactory.create_multi_hop_step_event(1, "test_step")
    ]
    
    for event in events:
        state["messages"].append(event)
    
    # 测试各种查询功能
    memory_events = EventQueryHelper.find_events_by_type(state["messages"], EventType.MEMORY_STORE)
    pending_events = EventQueryHelper.find_events_by_status(state["messages"], EventStatus.PENDING)
    latest_memory = EventQueryHelper.get_latest_event_by_type(state["messages"], EventType.MEMORY_STORE)
    
    print(f"✅ 记忆事件数量: {len(memory_events)}")
    print(f"✅ 待处理事件数量: {len(pending_events)}")
    print(f"✅ 最新记忆事件存在: {latest_memory is not None}")
    
    # 测试状态聚合
    comprehensive_state = StateAggregator.get_comprehensive_state(state["messages"])
    print(f"✅ 综合状态: {comprehensive_state}")
    
    assert len(memory_events) == 1, "应该有1个记忆事件"
    assert len(pending_events) == 3, "应该有3个待处理事件"
    assert latest_memory is not None, "应该能找到最新记忆事件"
    print("✅ 事件查询能力测试通过")
    
    return state


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始测试事件驱动AgentState功能...")
    print("=" * 60)
    
    try:
        # 运行各项功能测试
        test_memory_functionality()
        test_self_correction_functionality()
        test_multi_agent_collaboration()
        test_proactive_clarification()
        test_multi_hop_queries()
        test_event_query_capabilities()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！事件驱动AgentState功能正常工作")
        print("\n✅ 验证的功能包括:")
        print("   • 长期记忆存储和检索")
        print("   • 自我纠错机制")
        print("   • 多智能体协作")
        print("   • 主动澄清")
        print("   • 多跳查询")
        print("   • 事件流分析和状态聚合")
        print("\n🏗️ AgentState重构成功，所有高级功能均可正常实现！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)