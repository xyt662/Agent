#!/usr/bin/env python3
"""
多跳查询图模块

实现复杂查询的多步骤处理，支持查询分解、步骤执行和结果聚合。
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END

from langchain_core.messages import AIMessage, BaseMessage
from ..core.agent_state import AgentState, EventType, EventStatus, EventMetadata
from ..core.event_utils import EventQueryHelper


class MultiHopEventFactory:
    """
    多跳查询事件工厂类
    
    负责创建多跳查询相关的事件消息
    """
    
    @staticmethod
    def create_multi_hop_step_event(hop_index: int, step_description: str,
                                  parent_event_id: Optional[str] = None,
                                  status: EventStatus = EventStatus.IN_PROGRESS,
                                  context: Optional[Dict[str, Any]] = None) -> AIMessage:
        """
        创建多跳查询步骤事件
        
        Args:
            hop_index: 跳数索引
            step_description: 步骤描述
            parent_event_id: 父查询事件ID
            status: 事件状态
            context: 额外的上下文信息
        
        Returns:
            包含多跳查询步骤事件元数据的AIMessage
        """
        event_metadata = EventMetadata(
            event_type=EventType.MULTI_HOP_STEP,
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            status=status,
            hop_index=hop_index,
            parent_event_id=parent_event_id,
            context=context or {"step": step_description}
        )
        
        message_content = f"🔗 多跳查询步骤 {hop_index}: {step_description}"
        
        return AIMessage(
            content=message_content,
            additional_kwargs={"metadata": event_metadata.to_dict()}
        )
    
    @staticmethod
    def create_multi_hop_complete_event(total_hops: int, final_result: str,
                                      parent_event_id: Optional[str] = None,
                                      status: EventStatus = EventStatus.SUCCESS,
                                      context: Optional[Dict[str, Any]] = None) -> AIMessage:
        """
        创建多跳查询完成事件
        
        Args:
            total_hops: 总跳数
            final_result: 最终结果
            parent_event_id: 父查询事件ID
            status: 事件状态
            context: 额外的上下文信息
        
        Returns:
            包含多跳查询完成事件元数据的AIMessage
        """
        event_metadata = EventMetadata(
            event_type=EventType.MULTI_HOP_COMPLETE,
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            status=status,
            parent_event_id=parent_event_id,
            context=context or {"total_hops": total_hops, "result": final_result}
        )
        
        message_content = f"🎯 多跳查询完成 (共{total_hops}跳): {final_result}"
        if status == EventStatus.FAILED:
            message_content = f"❌ 多跳查询失败 (共{total_hops}跳): {final_result}"
        
        return AIMessage(
            content=message_content,
            additional_kwargs={"metadata": event_metadata.to_dict()}
        )


class MultiHopQueryProcessor:
    """
    多跳查询处理器
    
    负责处理复杂查询的分解、执行和结果聚合。
    """
    
    def __init__(self):
        self.max_hops = 5  # 最大跳数限制
    
    def decompose_query(self, query: str) -> List[str]:
        """
        将复杂查询分解为多个子查询步骤
        
        Args:
            query: 原始查询
        
        Returns:
            分解后的子查询列表
        """
        # 这里可以使用LLM来智能分解查询
        # 暂时使用简单的规则分解
        if "然后" in query or "接着" in query:
            return query.split("然后")
        elif "和" in query:
            return query.split("和")
        else:
            return [query]
    
    def execute_hop_step(self, state: AgentState, hop_index: int, 
                        step_query: str, parent_event_id: str) -> AgentState:
        """
        执行单个跳步
        
        Args:
            state: 当前状态
            hop_index: 跳数索引
            step_query: 步骤查询
            parent_event_id: 父事件ID
        
        Returns:
            更新后的状态
        """
        # 创建步骤事件
        step_event = MultiHopEventFactory.create_multi_hop_step_event(
            hop_index=hop_index,
            step_description=step_query,
            parent_event_id=parent_event_id,
            status=EventStatus.IN_PROGRESS
        )
        
        # 添加到消息流
        state["messages"].append(step_event)
        
        # 这里可以调用具体的查询执行逻辑
        # 例如调用检索器、LLM等
        
        # 模拟执行结果
        result = f"步骤{hop_index}的执行结果: {step_query}"
        
        # 更新事件状态为成功
        step_event.additional_kwargs["metadata"]["status"] = EventStatus.SUCCESS.value
        step_event.additional_kwargs["metadata"]["context"]["result"] = result
        
        return state
    
    def aggregate_results(self, state: AgentState, parent_event_id: str) -> AgentState:
        """
        聚合多跳查询的结果
        
        Args:
            state: 当前状态
            parent_event_id: 父事件ID
        
        Returns:
            更新后的状态
        """
        # 查找所有相关的步骤事件
        step_events = EventQueryHelper.find_event_chain(state["messages"], parent_event_id)
        
        # 聚合结果
        results = []
        for event in step_events:
            if event.additional_kwargs.get("metadata", {}).get("event_type") == EventType.MULTI_HOP_STEP.value:
                context = event.additional_kwargs["metadata"].get("context", {})
                if "result" in context:
                    results.append(context["result"])
        
        # 创建完成事件
        final_result = "\n".join(results)
        complete_event = MultiHopEventFactory.create_multi_hop_complete_event(
            total_hops=len(results),
            final_result=final_result,
            parent_event_id=parent_event_id,
            status=EventStatus.SUCCESS
        )
        
        state["messages"].append(complete_event)
        return state


def create_multi_hop_graph() -> StateGraph:
    """
    创建多跳查询处理图
    
    Returns:
        配置好的多跳查询图
    """
    processor = MultiHopQueryProcessor()
    
    def query_decomposition_node(state: AgentState) -> AgentState:
        """
        查询分解节点
        """
        # 获取最新的用户查询
        user_query = None
        for message in reversed(state["messages"]):
            if hasattr(message, 'content') and message.content:
                user_query = message.content
                break
        
        if not user_query:
            return state
        
        # 分解查询
        sub_queries = processor.decompose_query(user_query)
        
        # 如果只有一个子查询，不需要多跳处理
        if len(sub_queries) <= 1:
            state["multi_hop_required"] = False
            return state
        
        state["multi_hop_required"] = True
        state["sub_queries"] = sub_queries
        state["current_hop"] = 0
        state["parent_event_id"] = str(uuid.uuid4())
        
        return state
    
    def hop_execution_node(state: AgentState) -> AgentState:
        """
        跳步执行节点
        """
        if not state.get("multi_hop_required", False):
            return state
        
        current_hop = state.get("current_hop", 0)
        sub_queries = state.get("sub_queries", [])
        parent_event_id = state.get("parent_event_id")
        
        if current_hop < len(sub_queries):
            # 执行当前跳步
            state = processor.execute_hop_step(
                state, current_hop + 1, sub_queries[current_hop], parent_event_id
            )
            state["current_hop"] = current_hop + 1
        
        return state
    
    def result_aggregation_node(state: AgentState) -> AgentState:
        """
        结果聚合节点
        """
        if not state.get("multi_hop_required", False):
            return state
        
        parent_event_id = state.get("parent_event_id")
        if parent_event_id:
            state = processor.aggregate_results(state, parent_event_id)
        
        # 清理临时状态
        state.pop("multi_hop_required", None)
        state.pop("sub_queries", None)
        state.pop("current_hop", None)
        state.pop("parent_event_id", None)
        
        return state
    
    def should_continue_hops(state: AgentState) -> str:
        """
        判断是否继续执行跳步
        """
        if not state.get("multi_hop_required", False):
            return "aggregate"
        
        current_hop = state.get("current_hop", 0)
        sub_queries = state.get("sub_queries", [])
        
        if current_hop < len(sub_queries):
            return "continue"
        else:
            return "aggregate"
    
    # 构建图
    graph = StateGraph(AgentState)
    
    # 添加节点
    graph.add_node("decompose", query_decomposition_node)
    graph.add_node("execute_hop", hop_execution_node)
    graph.add_node("aggregate", result_aggregation_node)
    
    # 添加边
    graph.set_entry_point("decompose")
    graph.add_edge("decompose", "execute_hop")
    graph.add_conditional_edges(
        "execute_hop",
        should_continue_hops,
        {
            "continue": "execute_hop",
            "aggregate": "aggregate"
        }
    )
    graph.add_edge("aggregate", END)
    
    return graph