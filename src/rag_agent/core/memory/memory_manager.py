#!/usr/bin/env python3
"""
统一记忆管理器

整合基础和增强功能的统一记忆管理器，提供：
- 向量相似性搜索
- 元数据过滤
- 混合查询能力
- 事件驱动机制
- 会话管理
- 向后兼容性
"""

from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
import hashlib
import json

from langchain_core.messages import BaseMessage
from ..agent_state import AgentState, EventType, EventStatus
from ...storage import BaseStore, StorageDocument, SearchResult, get_memory_store


class MemoryUtils:
    """记忆管理工具类 - 提取公共功能"""
    
    @staticmethod
    def calculate_auto_importance(content: str, context: Dict[str, Any]) -> int:
        """
        自动计算记忆重要性
        
        Args:
            content: 记忆内容
            context: 上下文信息
            
        Returns:
            重要性评分 (1-10)
        """
        importance = 5  # 基础重要性
        
        # 基于内容长度
        if len(content) > 200:
            importance += 1
        elif len(content) < 50:
            importance -= 1
        
        # 基于关键词
        high_importance_keywords = [
            '重要', '关键', '核心', '必须', '紧急', 
            'important', 'critical', 'urgent', 'key',
            'decision', 'plan', 'strategy', 'goal'
        ]
        low_importance_keywords = [
            '可能', '也许', '或许', 
            'maybe', 'perhaps', 'possibly'
        ]
        
        content_lower = content.lower()
        for keyword in high_importance_keywords:
            if keyword in content_lower:
                importance += 1
                break
        
        for keyword in low_importance_keywords:
            if keyword in content_lower:
                importance -= 1
                break
        
        # 基于上下文
        if context:
            if context.get('importance_level') == 'high':
                importance += 2
            elif context.get('importance_level') == 'low':
                importance -= 1
            
            if context.get('user_marked_important'):
                importance += 2
                
            # 如果包含用户信息，提高重要性
            if any(key in context for key in ['user_id', 'user_name', 'user_preference']):
                importance += 1
            
            # 如果是错误或问题相关，提高重要性
            if any(keyword in str(context).lower() for keyword in ['error', 'problem', 'issue', 'bug']):
                importance += 2
        
        # 确保在有效范围内
        return max(1, min(10, importance))
    
    @staticmethod
    def generate_memory_key(content: str, context: Dict[str, Any]) -> str:
        """
        生成记忆键
        
        Args:
            content: 记忆内容
            context: 上下文信息
            
        Returns:
            记忆键
        """
        # 基于内容和时间戳生成唯一键
        timestamp = datetime.now().isoformat()
        key_source = f"{content}_{timestamp}"
        
        # 如果上下文中有用户ID，加入键生成
        if context and 'user_id' in context:
            key_source = f"{context['user_id']}_{key_source}"
        
        return hashlib.md5(key_source.encode()).hexdigest()[:16]


class MemoryManager:
    """
    统一记忆管理器
    
    整合基础和增强功能，提供：
    - ChromaDB 存储后端
    - 事件驱动机制
    - 智能记忆策略
    - 向量相似性搜索
    - 混合查询能力
    - 会话管理
    """
    
    def __init__(
        self, 
        storage_backend: Optional[BaseStore] = None,
        auto_importance_enabled: bool = True,
        max_memories_per_session: int = 100,
        enable_session_management: bool = True,
        enable_hybrid_search: bool = True
    ):
        """
        初始化记忆管理器
        
        Args:
            storage_backend: 存储后端实例（可选，默认使用ChromaDB）
            auto_importance_enabled: 是否启用自动重要性计算
            max_memories_per_session: 每个会话最大记忆数量
            enable_session_management: 是否启用会话管理
            enable_hybrid_search: 是否启用混合搜索
        """
        # 统一存储后端初始化
        if storage_backend is None:
            self.memory_store = get_memory_store()
            self.storage = self.memory_store  # 向后兼容
        else:
            self.memory_store = storage_backend
            self.storage = storage_backend
        
        self._auto_importance_enabled = auto_importance_enabled
        self._max_memories_per_session = max_memories_per_session
        self._enable_session_management = enable_session_management
        self._enable_hybrid_search = enable_hybrid_search
    
    def _calculate_auto_importance(self, content: str, context: Dict[str, Any]) -> int:
        """向后兼容的重要性计算方法"""
        return MemoryUtils.calculate_auto_importance(content, context)
    
    def _generate_memory_key(self, content: str, context: Dict[str, Any]) -> str:
        """向后兼容的记忆键生成方法"""
        return MemoryUtils.generate_memory_key(content, context)
    
    def store_memory(
        self, 
        content: str, 
        context: Optional[Dict[str, Any]] = None, 
        tags: Optional[List[str]] = None, 
        importance: Optional[int] = None
    ) -> bool:
        """
        存储记忆
        
        Args:
            content: 记忆内容
            context: 上下文信息
            tags: 标签列表
            importance: 重要性评分
            
        Returns:
            是否存储成功
        """
        try:
            # 生成记忆键
            memory_key = self._generate_memory_key(content, context or {})
            
            # 计算重要性
            if importance is None and self._auto_importance_enabled:
                importance = self._calculate_auto_importance(content, context or {})
            importance = importance or 5
            
            # 存储到后端
            return self.memory_store.store_memory(
                memory_key=memory_key,
                content=content,
                context=context,
                tags=tags,
                importance=importance
            )
        except Exception as e:
            print(f"存储记忆失败: {e}")
            return False
    
    def store_memory_from_event(
        self, 
        state: AgentState, 
        content: str,
        context: Optional[Dict[str, Any]] = None,
        memory_key: Optional[str] = None,
        tags: Optional[List[str]] = None,
        importance: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> AgentState:
        """
        从事件存储记忆
        
        Args:
            state: Agent 状态
            content: 记忆内容
            context: 上下文信息
            memory_key: 记忆键（可选）
            tags: 标签列表
            importance: 重要性评分
            user_id: 用户 ID
            
        Returns:
            更新后的 Agent 状态
        """
        try:
            # 生成记忆键
            if not memory_key:
                memory_key = self._generate_memory_key(content, context or {})
            
            # 计算重要性
            if importance is None and self._auto_importance_enabled:
                importance = self._calculate_auto_importance(content, context or {})
            importance = importance or 5
            
            # 存储到后端
            success = self.memory_store.store_memory(
                memory_key=memory_key,
                content=content,
                context=context,
                tags=tags,
                importance=importance,
                user_id=user_id
            )
            
            if success:
                print(f"记忆存储成功: {memory_key}")
            else:
                print(f"记忆存储失败: {memory_key}")
            
            # 返回原始状态的副本（不修改消息列表）
            return state.copy()
            
        except Exception as e:
            print(f"存储记忆时发生错误: {e}")
            return state.copy()
    
    def search_memories_from_event(
        self,
        state: AgentState,
        query: str,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        importance_threshold: Optional[int] = None,
        limit: int = 10,
        similarity_threshold: float = 0.3
    ) -> AgentState:
        """
        从事件搜索记忆
        
        Args:
            state: Agent 状态
            query: 搜索查询
            user_id: 用户 ID
            tags: 标签过滤
            importance_threshold: 重要性阈值
            limit: 结果数量限制
            similarity_threshold: 相似度阈值
            
        Returns:
            更新后的 Agent 状态
        """
        try:
            # 构建元数据过滤器
            metadata_filter = {}
            if user_id:
                metadata_filter['user_id'] = user_id
            if tags:
                metadata_filter['tags'] = tags
            if importance_threshold:
                metadata_filter['importance'] = {'$gte': importance_threshold}
            
            # 执行搜索
            if self._enable_hybrid_search and hasattr(self.memory_store, 'hybrid_search'):
                results = self.memory_store.hybrid_search(
                    query=query,
                    metadata_filter=metadata_filter,
                    k=limit,
                    similarity_threshold=similarity_threshold
                )
            else:
                results = self.memory_store.search_memories(
                    query=query,
                    limit=limit
                )
            
            print(f"搜索到 {len(results)} 条相关记忆")
            return state.copy()
            
        except Exception as e:
            print(f"搜索记忆时发生错误: {e}")
            return state.copy()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        获取记忆统计信息
        
        Returns:
            统计信息字典
        """
        try:
            return self.memory_store.get_stats()
        except Exception as e:
            print(f"获取记忆统计失败: {e}")
            return {"error": str(e)}
    
    def hybrid_search(
        self,
        query: str,
        metadata_filter: Optional[Dict[str, Any]] = None,
        k: int = 10,
        similarity_threshold: float = 0.3
    ) -> List[SearchResult]:
        """
        混合搜索（语义 + 元数据）
        
        Args:
            query: 搜索查询
            metadata_filter: 元数据过滤器
            k: 返回结果数量
            similarity_threshold: 相似度阈值
            
        Returns:
            搜索结果列表
        """
        if not self._enable_hybrid_search:
            # 回退到基础搜索
            return self.memory_store.search_memories(query=query, limit=k)
        
        try:
            if hasattr(self.memory_store, 'hybrid_search'):
                return self.memory_store.hybrid_search(
                    query=query,
                    metadata_filter=metadata_filter,
                    k=k,
                    similarity_threshold=similarity_threshold
                )
            else:
                return self.memory_store.search_memories(query=query, limit=k)
        except Exception as e:
            print(f"混合搜索失败: {e}")
            return []
    
    def store_session_message(
        self,
        session_id: str,
        message: BaseMessage,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        存储会话消息
        
        Args:
            session_id: 会话 ID
            message: 消息对象
            metadata: 元数据
            
        Returns:
            是否存储成功
        """
        if not self._enable_session_management:
            return False
        
        try:
            if hasattr(self.memory_store, 'store_session_message'):
                return self.memory_store.store_session_message(
                    session_id=session_id,
                    message=message,
                    metadata=metadata
                )
            else:
                # 回退到基础存储
                return self.store_memory(
                    content=message.content,
                    context={'session_id': session_id, 'message_type': type(message).__name__},
                    tags=['session_message']
                )
        except Exception as e:
            print(f"存储会话消息失败: {e}")
            return False
    
    def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[BaseMessage]:
        """
        获取会话历史
        
        Args:
            session_id: 会话 ID
            limit: 数量限制
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            消息列表
        """
        if not self._enable_session_management:
            return []
        
        try:
            if hasattr(self.memory_store, 'get_session_history'):
                return self.memory_store.get_session_history(
                    session_id=session_id,
                    limit=limit,
                    start_time=start_time,
                    end_time=end_time
                )
            else:
                return []
        except Exception as e:
            print(f"获取会话历史失败: {e}")
            return []
    
    def clear_memories(self) -> bool:
        """
        清空所有记忆
        
        Returns:
            是否清空成功
        """
        try:
            if hasattr(self.memory_store, 'clear_collection'):
                return self.memory_store.clear_collection()
            else:
                return False
        except Exception as e:
            print(f"清空记忆失败: {e}")
            return False
    
    # 向后兼容方法
    def is_enhanced_backend(self) -> bool:
        """检查是否为增强后端"""
        return hasattr(self.memory_store, 'hybrid_search')
    
    def get_storage_backend(self) -> BaseStore:
        """获取存储后端"""
        return self.memory_store
    
    def list_recent_memories(self, limit: int = 10) -> List:
        """列出最近的记忆"""
        try:
            if hasattr(self.memory_store, 'list_recent_memories'):
                return self.memory_store.list_recent_memories(limit)
            else:
                return []
        except Exception as e:
            print(f"获取最近记忆失败: {e}")
            return []
    
    def list_important_memories(self, limit: int = 10) -> List:
        """列出重要记忆"""
        try:
            if hasattr(self.memory_store, 'list_important_memories'):
                return self.memory_store.list_important_memories(limit)
            else:
                return []
        except Exception as e:
            print(f"获取重要记忆失败: {e}")
            return []
    
    def search_memories(self, query: str, limit: int = 10) -> List:
        """搜索记忆"""
        try:
            return self.memory_store.search_memories(query=query, limit=limit)
        except Exception as e:
            print(f"搜索记忆失败: {e}")
            return []
    
    def cleanup_old_memories(self, max_memories: int = 1000) -> int:
        """清理旧记忆"""
        try:
            if hasattr(self.memory_store, 'cleanup_old_memories'):
                return self.memory_store.cleanup_old_memories(max_memories)
            else:
                return 0
        except Exception as e:
            print(f"清理旧记忆失败: {e}")
            return 0
    
    def export_memories(self, export_path: Union[str, Path]) -> bool:
        """导出记忆"""
        try:
            if hasattr(self.memory_store, 'export_memories'):
                return self.memory_store.export_memories(export_path)
            else:
                return False
        except Exception as e:
            print(f"导出记忆失败: {e}")
            return False
    
    def import_memories(self, import_path: Union[str, Path]) -> int:
        """导入记忆"""
        try:
            if hasattr(self.memory_store, 'import_memories'):
                return self.memory_store.import_memories(import_path)
            else:
                return 0
        except Exception as e:
            print(f"导入记忆失败: {e}")
            return 0


# 向后兼容的别名
EnhancedMemoryManager = MemoryManager