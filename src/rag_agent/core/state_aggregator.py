"""状态聚合器 - 从事件流中计算当前状态快照"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage
from .agent_state import EventType, EventStatus, EventMetadata


class StateAggregator:
    """
    状态聚合器 - 负责从事件流(messages)中计算各种状态快照
    
    这个类实现了"状态聚合"的核心逻辑，将事件流转换为结构化的状态视图。
    每个聚合方法都是无状态的，完全基于输入的messages计算结果。
    """
    
    @staticmethod
    def extract_event_metadata(message: BaseMessage) -> Optional[EventMetadata]:
        """从消息中提取事件元数据"""
        if not hasattr(message, 'additional_kwargs') or not message.additional_kwargs:
            return None
            
        metadata_dict = message.additional_kwargs.get('metadata')
        if not metadata_dict or 'event_type' not in metadata_dict:
            return None
            
        try:
            return EventMetadata.from_dict(metadata_dict)
        except (KeyError, ValueError):
            return None
    
    @staticmethod
    def get_memory_state(messages: List[BaseMessage]) -> Dict[str, Any]:
        """
        聚合长期记忆状态
        
        从事件流中提取所有记忆相关的事件，计算当前的记忆状态。
        
        Returns:
            Dict包含:
            - stored_memories: 已存储的记忆键列表
            - recent_retrievals: 最近的记忆检索记录
            - memory_operations: 记忆操作统计
        """
        stored_memories = set()
        recent_retrievals = []
        memory_operations = defaultdict(int)
        
        for message in messages:
            event_meta = StateAggregator.extract_event_metadata(message)
            if not event_meta:
                continue
                
            if event_meta.event_type == EventType.MEMORY_STORE:
                if event_meta.status == EventStatus.SUCCESS and event_meta.memory_key:
                    stored_memories.add(event_meta.memory_key)
                memory_operations['store'] += 1
                
            elif event_meta.event_type == EventType.MEMORY_RETRIEVE:
                if event_meta.memory_key:
                    recent_retrievals.append({
                        'key': event_meta.memory_key,
                        'timestamp': event_meta.timestamp,
                        'status': event_meta.status.value
                    })
                memory_operations['retrieve'] += 1
        
        # 只保留最近的检索记录（最近10条）
        recent_retrievals = sorted(recent_retrievals, 
                                 key=lambda x: x['timestamp'], 
                                 reverse=True)[:10]
        
        return {
            'stored_memories': list(stored_memories),
            'recent_retrievals': recent_retrievals,
            'memory_operations': dict(memory_operations)
        }
    
    @staticmethod
    def get_correction_state(messages: List[BaseMessage]) -> Dict[str, Any]:
        """
        聚合自我纠错状态
        
        分析错误事件和纠错尝试，提供当前的纠错状态视图。
        
        Returns:
            Dict包含:
            - active_corrections: 正在进行的纠错
            - correction_history: 纠错历史
            - error_patterns: 错误模式分析
        """
        active_corrections = []
        correction_history = []
        error_patterns = defaultdict(int)
        
        for message in messages:
            event_meta = StateAggregator.extract_event_metadata(message)
            if not event_meta:
                continue
                
            if event_meta.event_type == EventType.CORRECTION_TRIGGER:
                correction_record = {
                    'event_id': event_meta.event_id,
                    'reason': event_meta.correction_reason,
                    'timestamp': event_meta.timestamp,
                    'status': event_meta.status.value
                }
                
                if event_meta.status in [EventStatus.PENDING, EventStatus.IN_PROGRESS]:
                    active_corrections.append(correction_record)
                else:
                    correction_history.append(correction_record)
                    
                # 统计错误模式
                if event_meta.correction_reason:
                    error_patterns[event_meta.correction_reason] += 1
        
        return {
            'active_corrections': active_corrections,
            'correction_history': correction_history[-20:],  # 最近20条
            'error_patterns': dict(error_patterns)
        }
    
    @staticmethod
    def get_collaboration_state(messages: List[BaseMessage]) -> Dict[str, Any]:
        """
        聚合多智能体协作状态
        
        跟踪智能体间的委派和回调关系。
        
        Returns:
            Dict包含:
            - active_delegations: 活跃的委派任务
            - agent_interactions: 智能体交互历史
            - collaboration_metrics: 协作指标
        """
        active_delegations = []
        agent_interactions = []
        collaboration_metrics = defaultdict(int)
        
        for message in messages:
            event_meta = StateAggregator.extract_event_metadata(message)
            if not event_meta:
                continue
                
            if event_meta.event_type == EventType.AGENT_DELEGATION:
                delegation = {
                    'event_id': event_meta.event_id,
                    'target_agent': event_meta.target_agent,
                    'timestamp': event_meta.timestamp,
                    'status': event_meta.status.value
                }
                
                if event_meta.status in [EventStatus.PENDING, EventStatus.IN_PROGRESS]:
                    active_delegations.append(delegation)
                    
                agent_interactions.append(delegation)
                collaboration_metrics['delegations'] += 1
                
            elif event_meta.event_type == EventType.AGENT_CALLBACK:
                callback = {
                    'event_id': event_meta.event_id,
                    'parent_event_id': event_meta.parent_event_id,
                    'timestamp': event_meta.timestamp,
                    'status': event_meta.status.value
                }
                agent_interactions.append(callback)
                collaboration_metrics['callbacks'] += 1
        
        return {
            'active_delegations': active_delegations,
            'agent_interactions': agent_interactions[-15:],  # 最近15条
            'collaboration_metrics': dict(collaboration_metrics)
        }
    
    @staticmethod
    def get_clarification_state(messages: List[BaseMessage]) -> Dict[str, Any]:
        """
        聚合主动澄清状态
        
        跟踪澄清请求和响应的状态。
        
        Returns:
            Dict包含:
            - pending_clarifications: 待处理的澄清请求
            - clarification_history: 澄清历史
            - clarification_patterns: 澄清模式分析
        """
        pending_clarifications = []
        clarification_history = []
        clarification_patterns = defaultdict(int)
        
        for message in messages:
            event_meta = StateAggregator.extract_event_metadata(message)
            if not event_meta:
                continue
                
            if event_meta.event_type == EventType.CLARIFICATION_REQUEST:
                clarification = {
                    'event_id': event_meta.event_id,
                    'question': event_meta.clarification_question,
                    'timestamp': event_meta.timestamp,
                    'status': event_meta.status.value
                }
                
                if event_meta.status == EventStatus.PENDING:
                    pending_clarifications.append(clarification)
                else:
                    clarification_history.append(clarification)
                    
                clarification_patterns['requests'] += 1
                
            elif event_meta.event_type == EventType.CLARIFICATION_RESPONSE:
                clarification_patterns['responses'] += 1
        
        return {
            'pending_clarifications': pending_clarifications,
            'clarification_history': clarification_history[-10:],  # 最近10条
            'clarification_patterns': dict(clarification_patterns)
        }
    
    @staticmethod
    def get_multi_hop_state(messages: List[BaseMessage]) -> Dict[str, Any]:
        """
        聚合多跳查询状态
        
        跟踪复杂查询的执行进度和步骤。
        
        Returns:
            Dict包含:
            - active_queries: 活跃的多跳查询
            - completed_queries: 已完成的查询
            - hop_statistics: 跳数统计
        """
        active_queries = defaultdict(list)
        completed_queries = []
        hop_statistics = defaultdict(int)
        
        for message in messages:
            event_meta = StateAggregator.extract_event_metadata(message)
            if not event_meta:
                continue
                
            if event_meta.event_type == EventType.MULTI_HOP_STEP:
                step = {
                    'event_id': event_meta.event_id,
                    'hop_index': event_meta.hop_index,
                    'timestamp': event_meta.timestamp,
                    'status': event_meta.status.value
                }
                
                # 使用parent_event_id作为查询ID分组
                query_id = event_meta.parent_event_id or event_meta.event_id
                active_queries[query_id].append(step)
                
                hop_statistics[f'hop_{event_meta.hop_index}'] += 1
                
            elif event_meta.event_type == EventType.MULTI_HOP_COMPLETE:
                query_id = event_meta.parent_event_id or event_meta.event_id
                if query_id in active_queries:
                    completed_queries.append({
                        'query_id': query_id,
                        'steps': active_queries[query_id],
                        'completion_time': event_meta.timestamp,
                        'total_hops': len(active_queries[query_id])
                    })
                    del active_queries[query_id]
        
        return {
            'active_queries': dict(active_queries),
            'completed_queries': completed_queries[-5:],  # 最近5个完成的查询
            'hop_statistics': dict(hop_statistics)
        }
    
    @staticmethod
    def get_comprehensive_state(messages: List[BaseMessage], memory_manager=None) -> Dict[str, Any]:
        """
        获取综合状态快照
        
        聚合所有功能模块的状态，提供完整的Agent状态视图。
        
        Args:
            messages: 消息列表
            memory_manager: 记忆管理器实例（可选）
        
        Returns:
            包含所有子状态的综合字典
        """
        # 获取记忆状态
        memory_state = {}
        if memory_manager:
            try:
                memory_state = memory_manager.get_memory_stats()
                memory_state["backend_type"] = "enhanced" if memory_manager.is_enhanced_backend() else "file"
            except Exception as e:
                memory_state = {"error": f"Failed to get memory stats: {str(e)}"}
        else:
            # 向后兼容：从事件流推断记忆状态
            memory_state = StateAggregator.get_memory_state(messages)
        
        return {
            'memory': memory_state,
            'correction': StateAggregator.get_correction_state(messages),
            'collaboration': StateAggregator.get_collaboration_state(messages),
            'clarification': StateAggregator.get_clarification_state(messages),
            'multi_hop': StateAggregator.get_multi_hop_state(messages),
            'timestamp': datetime.now().isoformat(),
            'total_messages': len(messages)
        }