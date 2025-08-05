"""事件工具函数 - 提供便捷的事件消息创建方法"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from .agent_state import EventType, EventStatus, EventMetadata


class EventMessageFactory:
    """
    事件消息工厂 - 提供标准化的事件消息创建方法
    
    这个工厂类简化了在LangGraph节点中创建事件驱动消息的过程，
    确保所有事件消息都遵循统一的格式和元数据结构。
    """
    
    # 记忆相关事件已迁移到 core.memory.memory_events 模块
    # 请使用 MemoryEventFactory 类
    
    # 记忆检索事件已迁移到 core.memory.memory_events 模块
    # 请使用 MemoryEventFactory.create_memory_retrieve_event()
    
    @staticmethod
    def create_correction_trigger_event(reason: str, error_type: Optional[str] = None,
                                      status: EventStatus = EventStatus.PENDING,
                                      context: Optional[Dict[str, Any]] = None) -> AIMessage:
        """
        创建自我纠错触发事件
        
        Args:
            reason: 纠错原因
            error_type: 错误类型
            status: 事件状态
            context: 额外的上下文信息
        
        Returns:
            包含纠错触发事件元数据的AIMessage
        """
        event_context = context or {}
        if error_type:
            event_context["error_type"] = error_type
        
        event_metadata = EventMetadata(
            event_type=EventType.CORRECTION_TRIGGER,
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            status=status,
            correction_reason=reason,
            context=event_context
        )
        
        message_content = f"🔍 触发自我纠错: {reason}"
        
        return AIMessage(
            content=message_content,
            additional_kwargs={"metadata": event_metadata.to_dict()}
        )
    
    @staticmethod
    def create_correction_attempt_event(correction_action: str, 
                                      parent_event_id: str,
                                      status: EventStatus = EventStatus.IN_PROGRESS,
                                      context: Optional[Dict[str, Any]] = None) -> AIMessage:
        """
        创建自我纠错尝试事件
        
        Args:
            correction_action: 纠错行动描述
            parent_event_id: 父事件ID（对应的触发事件）
            status: 事件状态
            context: 额外的上下文信息
        
        Returns:
            包含纠错尝试事件元数据的AIMessage
        """
        event_metadata = EventMetadata(
            event_type=EventType.CORRECTION_ATTEMPT,
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            status=status,
            parent_event_id=parent_event_id,
            context=context or {"action": correction_action}
        )
        
        message_content = f"🔧 执行纠错行动: {correction_action}"
        if status == EventStatus.SUCCESS:
            message_content = f"✅ 纠错成功: {correction_action}"
        elif status == EventStatus.FAILED:
            message_content = f"❌ 纠错失败: {correction_action}"
        
        return AIMessage(
            content=message_content,
            additional_kwargs={"metadata": event_metadata.to_dict()}
        )
    
    # 澄清相关事件已迁移到 nodes/clarification_node.py
    
    @staticmethod
    def create_agent_delegation_event(target_agent: str, task_description: str,
                                    status: EventStatus = EventStatus.PENDING,
                                    context: Optional[Dict[str, Any]] = None) -> AIMessage:
        """
        创建智能体委派事件
        
        Args:
            target_agent: 目标智能体标识
            task_description: 任务描述
            status: 事件状态
            context: 额外的上下文信息
        
        Returns:
            包含智能体委派事件元数据的AIMessage
        """
        event_metadata = EventMetadata(
            event_type=EventType.AGENT_DELEGATION,
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            status=status,
            target_agent=target_agent,
            context=context or {"task": task_description}
        )
        
        message_content = f"🤝 委派任务给 {target_agent}: {task_description}"
        
        return AIMessage(
            content=message_content,
            additional_kwargs={"metadata": event_metadata.to_dict()}
        )
    
    @staticmethod
    def create_agent_callback_event(result: str, parent_event_id: str,
                                  status: EventStatus = EventStatus.SUCCESS,
                                  context: Optional[Dict[str, Any]] = None) -> AIMessage:
        """
        创建智能体回调事件
        
        Args:
            result: 任务执行结果
            parent_event_id: 对应的委派事件ID
            status: 事件状态
            context: 额外的上下文信息
        
        Returns:
            包含智能体回调事件元数据的AIMessage
        """
        event_metadata = EventMetadata(
            event_type=EventType.AGENT_CALLBACK,
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            status=status,
            parent_event_id=parent_event_id,
            context=context or {"result": result}
        )
        
        message_content = f"📋 任务完成回调: {result}"
        if status == EventStatus.FAILED:
            message_content = f"❌ 任务执行失败: {result}"
        
        return AIMessage(
            content=message_content,
            additional_kwargs={"metadata": event_metadata.to_dict()}
        )
    
    # 多跳查询相关事件已迁移到 graphs/multi_hop_graph.py
    
    @staticmethod
    def create_system_event(content: str, 
                          status: EventStatus = EventStatus.SUCCESS,
                          context: Optional[Dict[str, Any]] = None) -> SystemMessage:
        """
        创建系统事件
        
        Args:
            content: 系统消息内容
            status: 事件状态
            context: 额外的上下文信息
        
        Returns:
            包含系统事件元数据的SystemMessage
        """
        event_metadata = EventMetadata(
            event_type=EventType.SYSTEM,
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            status=status,
            context=context or {}
        )
        
        return SystemMessage(
            content=content,
            additional_kwargs={"metadata": event_metadata.to_dict()}
        )


class EventQueryHelper:
    """
    事件查询助手 - 提供便捷的事件查询和过滤方法
    """
    
    @staticmethod
    def find_events_by_type(messages: List[BaseMessage], 
                          event_type: EventType) -> List[BaseMessage]:
        """
        根据事件类型查找消息
        
        Args:
            messages: 消息列表
            event_type: 要查找的事件类型
        
        Returns:
            匹配的消息列表
        """
        matching_messages = []
        
        for message in messages:
            if hasattr(message, 'additional_kwargs') and message.additional_kwargs:
                metadata_dict = message.additional_kwargs.get('metadata')
                if metadata_dict and metadata_dict.get('event_type') == event_type.value:
                    matching_messages.append(message)
        
        return matching_messages
    
    @staticmethod
    def find_events_by_status(messages: List[BaseMessage], 
                            status: EventStatus) -> List[BaseMessage]:
        """
        根据事件状态查找消息
        
        Args:
            messages: 消息列表
            status: 要查找的事件状态
        
        Returns:
            匹配的消息列表
        """
        matching_messages = []
        
        for message in messages:
            if hasattr(message, 'additional_kwargs') and message.additional_kwargs:
                metadata_dict = message.additional_kwargs.get('metadata')
                if metadata_dict and metadata_dict.get('status') == status.value:
                    matching_messages.append(message)
        
        return matching_messages
    
    @staticmethod
    def find_event_chain(messages: List[BaseMessage], 
                       parent_event_id: str) -> List[BaseMessage]:
        """
        查找事件链（根据parent_event_id）
        
        Args:
            messages: 消息列表
            parent_event_id: 父事件ID
        
        Returns:
            事件链中的所有消息
        """
        chain_messages = []
        
        for message in messages:
            if hasattr(message, 'additional_kwargs') and message.additional_kwargs:
                metadata_dict = message.additional_kwargs.get('metadata')
                if metadata_dict and metadata_dict.get('parent_event_id') == parent_event_id:
                    chain_messages.append(message)
        
        return chain_messages
    
    @staticmethod
    def get_latest_event_by_type(messages: List[BaseMessage], 
                               event_type: EventType) -> Optional[BaseMessage]:
        """
        获取指定类型的最新事件
        
        Args:
            messages: 消息列表
            event_type: 事件类型
        
        Returns:
            最新的匹配消息，如果没有则返回None
        """
        matching_messages = EventQueryHelper.find_events_by_type(messages, event_type)
        
        if not matching_messages:
            return None
        
        # 返回最后一个（最新的）
        return matching_messages[-1]