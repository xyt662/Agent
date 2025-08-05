#!/usr/bin/env python3
"""
记忆事件处理器

统一处理记忆相关的事件逻辑，避免在多个节点中重复实现
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from ..agent_state import AgentState, EventType, EventStatus, EventMetadata
from .memory_manager import MemoryManager


class MemoryEventHandler:
    """
    记忆事件处理器
    
    统一处理记忆相关的事件，包括：
    - 自动识别重要信息
    - 处理显式记忆请求
    - 管理记忆检索
    - 创建记忆事件消息
    """
    
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        """
        初始化记忆事件处理器
        
        Args:
            memory_manager: 记忆管理器实例
        """
        self.memory_manager = memory_manager or MemoryManager()
        self._auto_store_enabled = True
        self._importance_threshold = 6
        self._retrieval_triggers = ["之前", "历史", "记得", "以前", "曾经", "remember", "recall", "previous"]
        self._store_keywords = ['记住', '保存', '存储', '记录', 'remember', 'save', 'store', 'record']
    
    def handle_memory_events(self, state: AgentState) -> AgentState:
        """
        处理记忆相关事件
        
        Args:
            state: 当前Agent状态
            
        Returns:
            更新后的Agent状态
        """
        # 1. 处理显式的记忆存储请求
        state = self._handle_explicit_memory_requests(state)
        
        # 2. 自动存储重要信息
        if self._auto_store_enabled:
            state = self._auto_store_important_info(state)
        
        # 3. 处理记忆检索请求
        state = self._handle_memory_retrieval_requests(state)
        
        return state
    
    def _handle_explicit_memory_requests(self, state: AgentState) -> AgentState:
        """
        处理显式的记忆存储请求
        
        检查用户消息中是否包含明确的记忆存储指令
        """
        messages = state["messages"]
        
        # 查找最新的用户消息
        latest_human_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                latest_human_message = msg
                break
        
        if not latest_human_message:
            return state
        
        content = latest_human_message.content.lower()
        
        # 检查是否包含记忆存储关键词
        if any(keyword in content for keyword in self._store_keywords):
            # 提取要存储的内容
            memory_content = self._extract_memory_content(latest_human_message.content)
            if memory_content:
                context = {
                    'source': 'explicit_user_request',
                    'importance': 8,  # 用户明确要求存储的信息重要性较高
                    'category': 'user_instruction',
                    'timestamp': datetime.now().isoformat()
                }
                state = self.memory_manager.store_memory_from_event(
                    state, memory_content, context
                )
        
        return state
    
    def _extract_memory_content(self, user_input: str) -> Optional[str]:
        """
        从用户输入中提取要存储的记忆内容
        
        Args:
            user_input: 用户输入
            
        Returns:
            提取的记忆内容
        """
        # 简单的启发式规则：去除存储指令，保留实际内容
        content = user_input
        
        # 移除常见的存储指令
        for keyword in self._store_keywords:
            content = content.replace(keyword, "").strip()
        
        # 移除常见的连接词
        content = content.replace("这个", "").replace("这些", "").replace("that", "").replace("this", "").strip()
        
        # 如果内容太短，可能不是有效的记忆内容
        if len(content) < 10:
            return None
        
        return content
    
    def _auto_store_important_info(self, state: AgentState) -> AgentState:
        """
        自动存储重要信息
        
        分析最近的消息，识别并存储重要信息
        """
        messages = state["messages"]
        
        # 检查最近的几条消息
        recent_messages = messages[-3:] if len(messages) > 3 else messages
        
        for message in recent_messages:
            if not hasattr(message, 'content'):
                continue
            
            # 计算消息重要性
            importance = self._calculate_message_importance(message)
            
            if importance >= self._importance_threshold:
                # 存储重要信息
                context = {
                    'source': 'auto_detection',
                    'importance': importance,
                    'category': 'important_info',
                    'message_type': type(message).__name__,
                    'timestamp': datetime.now().isoformat()
                }
                
                state = self.memory_manager.store_memory_from_event(
                    state, message.content, context
                )
        
        return state
    
    def _calculate_message_importance(self, message: BaseMessage) -> int:
        """
        计算消息重要性
        
        Args:
            message: 消息对象
            
        Returns:
            重要性评分 (1-10)
        """
        if not hasattr(message, 'content'):
            return 1
        
        content = message.content.lower()
        importance = 5  # 基础重要性
        
        # 基于关键词提升重要性
        high_importance_keywords = [
            '重要', '关键', '核心', '必须', '紧急', '错误', '问题',
            'important', 'critical', 'urgent', 'key', 'error', 'problem',
            'decision', 'plan', 'strategy', 'goal', 'learn', 'discover'
        ]
        
        for keyword in high_importance_keywords:
            if keyword in content:
                importance += 2
                break
        
        # 基于消息类型
        if isinstance(message, AIMessage):
            # AI消息中的解决方案或建议通常重要
            if any(word in content for word in ['解决', '建议', 'solution', 'recommend']):
                importance += 1
        elif isinstance(message, HumanMessage):
            # 用户的问题或需求通常重要
            if '?' in content or '？' in content:
                importance += 1
        
        # 基于消息长度
        if len(content) > 200:
            importance += 1
        elif len(content) < 50:
            importance -= 1
        
        return max(1, min(10, importance))
    
    def _handle_memory_retrieval_requests(self, state: AgentState) -> AgentState:
        """
        处理记忆检索请求
        
        检查是否需要检索相关的历史记忆
        """
        messages = state["messages"]
        
        if not self._should_retrieve_memory(messages):
            return state
        
        # 提取查询上下文
        query_context = self._extract_current_context(messages)
        
        if query_context:
            # 执行记忆搜索
            state = self.memory_manager.search_memories_from_event(
                state=state,
                query=query_context,
                limit=5,
                similarity_threshold=0.3
            )
        
        return state
    
    def _should_retrieve_memory(self, messages: List[BaseMessage]) -> bool:
        """
        判断是否需要检索记忆
        
        基于当前对话上下文判断是否需要检索相关的历史记忆
        """
        if not messages:
            return False
        
        # 检查最近的消息是否包含需要记忆检索的信号
        recent_message = messages[-1]
        if hasattr(recent_message, 'content'):
            return any(trigger in recent_message.content for trigger in self._retrieval_triggers)
        
        return False
    
    def _extract_current_context(self, messages: List[BaseMessage]) -> str:
        """
        提取当前对话上下文
        
        用于记忆检索的查询上下文
        """
        if not messages:
            return "general_context"
        
        # 获取最近几条消息的内容作为上下文
        recent_contents = []
        for msg in messages[-3:]:
            if hasattr(msg, 'content') and msg.content:
                recent_contents.append(msg.content[:100])  # 限制长度
        
        return " ".join(recent_contents) if recent_contents else "general_context"
    
    def create_memory_store_event(
        self, 
        memory_key: str, 
        content: str,
        status: EventStatus = EventStatus.SUCCESS,
        context: Optional[Dict[str, Any]] = None
    ) -> AIMessage:
        """
        创建记忆存储事件消息
        
        Args:
            memory_key: 记忆键
            content: 记忆内容
            status: 事件状态
            context: 上下文信息
            
        Returns:
            事件消息
        """
        event_metadata = EventMetadata(
            event_id=f"memory_store_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            event_type=EventType.MEMORY_STORE,
            status=status,
            context=context or {}
        )
        
        if status == EventStatus.SUCCESS:
            message_content = f"💾 存储长期记忆: {memory_key}\n内容: {content[:100]}..."
        else:
            message_content = f"❌ 记忆存储失败: {memory_key}"
        
        return AIMessage(
            content=message_content,
            additional_kwargs={
                "metadata": event_metadata.to_dict()
            }
        )
    
    def create_memory_retrieve_event(
        self, 
        query_context: str,
        results_count: int = 0,
        status: EventStatus = EventStatus.SUCCESS,
        context: Optional[Dict[str, Any]] = None
    ) -> AIMessage:
        """
        创建记忆检索事件消息
        
        Args:
            query_context: 查询上下文
            results_count: 结果数量
            status: 事件状态
            context: 上下文信息
            
        Returns:
            事件消息
        """
        event_metadata = EventMetadata(
            event_id=f"memory_retrieve_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            event_type=EventType.MEMORY_RETRIEVE,
            status=status,
            context=context or {}
        )
        
        if status == EventStatus.SUCCESS:
            message_content = f"🔍 检索相关长期记忆: {query_context}\n找到 {results_count} 条相关记忆"
        else:
            message_content = f"❌ 记忆检索失败: {query_context}"
        
        return AIMessage(
            content=message_content,
            additional_kwargs={
                "metadata": event_metadata.to_dict()
            }
        )
    
    def configure(
        self, 
        auto_store_enabled: bool = True, 
        importance_threshold: int = 6,
        retrieval_triggers: Optional[List[str]] = None,
        store_keywords: Optional[List[str]] = None
    ):
        """
        配置事件处理器
        
        Args:
            auto_store_enabled: 是否启用自动存储
            importance_threshold: 重要性阈值
            retrieval_triggers: 检索触发词
            store_keywords: 存储关键词
        """
        self._auto_store_enabled = auto_store_enabled
        self._importance_threshold = importance_threshold
        
        if retrieval_triggers:
            self._retrieval_triggers = retrieval_triggers
        
        if store_keywords:
            self._store_keywords = store_keywords


def create_memory_event_handler(memory_manager: Optional[MemoryManager] = None) -> MemoryEventHandler:
    """
    创建记忆事件处理器实例
    
    Args:
        memory_manager: 记忆管理器实例
        
    Returns:
        记忆事件处理器实例
    """
    return MemoryEventHandler(memory_manager)