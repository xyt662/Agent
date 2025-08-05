#!/usr/bin/env python3
"""
记忆处理节点

在 LangGraph 工作流中处理长期记忆的存储和检索
"""

from typing import Dict, Any, Optional, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from ..core.agent_state import AgentState, EventType, EventStatus
from ..core.memory.memory_manager import MemoryManager
from ..core.memory.memory_event_handler import MemoryEventHandler, create_memory_event_handler


class MemoryNode:
    """
    记忆处理节点
    
    负责在 LangGraph 工作流中处理记忆相关的操作：
    - 自动识别需要存储的重要信息
    - 响应记忆检索请求
    - 管理记忆的生命周期
    
    使用统一的事件处理器，避免重复实现
    """
    
    def __init__(self, storage_backend: Optional[Any] = None):
        """
        初始化记忆节点
        
        Args:
            storage_backend: 存储后端（可选）
        """
        self.memory_manager = MemoryManager(storage_backend=storage_backend)
        self.event_handler = create_memory_event_handler(self.memory_manager)
    
    def __call__(self, state: AgentState) -> AgentState:
        """
        处理记忆相关操作
        
        Args:
            state: 当前Agent状态
            
        Returns:
            更新后的Agent状态
        """
        # 使用统一的事件处理器处理所有记忆事件
        return self.event_handler.handle_memory_events(state)
    
    # 向后兼容的方法，委托给事件处理器或记忆管理器
    def configure(self, auto_store_enabled: bool = True, importance_threshold: int = 6):
        """
        配置记忆节点
        
        Args:
            auto_store_enabled: 是否启用自动存储
            importance_threshold: 重要性阈值
        """
        self.event_handler.configure(
            auto_store_enabled=auto_store_enabled,
            importance_threshold=importance_threshold
        )
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        获取记忆统计信息
        
        Returns:
            统计信息字典
        """
        return self.memory_manager.get_memory_stats()
    
    def search_memories(self, query: str, limit: int = 10):
        """
        搜索记忆
        
        Args:
            query: 搜索查询
            limit: 返回数量限制
            
        Returns:
            搜索结果列表
        """
        return self.memory_manager.search_memories(query, limit)
    
    def list_recent_memories(self, limit: int = 10):
        """
        列出最近的记忆
        
        Args:
            limit: 返回数量限制
            
        Returns:
            最近的记忆记录列表
        """
        return self.memory_manager.list_recent_memories(limit)


def create_memory_node(storage_backend: Optional[Any] = None) -> MemoryNode:
    """
    创建记忆节点实例
    
    Args:
        storage_backend: 存储后端（可选）
        
    Returns:
        记忆节点实例
    """
    return MemoryNode(storage_backend)