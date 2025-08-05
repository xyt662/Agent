#!/usr/bin/env python3
"""
抽象存储接口

定义面向 AI 应用的存储抽象，支持：
- 向量存储与检索
- 元数据过滤
- 混合搜索（语义 + 元数据）
- 会话历史管理
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from langchain_core.messages import BaseMessage


@dataclass
class StorageDocument:
    """
    存储文档数据结构
    
    统一的文档表示，支持向量存储和元数据过滤
    """
    id: str  # 文档唯一标识
    content: str  # 文档内容
    metadata: Dict[str, Any]  # 元数据
    timestamp: datetime  # 创建时间
    embedding: Optional[List[float]] = None  # 向量嵌入（可选）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'embedding': self.embedding
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StorageDocument':
        """从字典创建文档"""
        return cls(
            id=data['id'],
            content=data['content'],
            metadata=data['metadata'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            embedding=data.get('embedding')
        )


@dataclass
class SearchResult:
    """
    搜索结果数据结构
    """
    document: StorageDocument
    score: float  # 相似度评分
    distance: Optional[float] = None  # 向量距离（可选）


class BaseStore(ABC):
    """
    抽象存储接口
    
    定义了 AI 应用所需的核心存储操作：
    - 文档存储与检索
    - 向量相似性搜索
    - 元数据过滤
    - 混合查询
    """
    
    @abstractmethod
    def store_document(self, document: StorageDocument) -> bool:
        """
        存储文档
        
        Args:
            document: 要存储的文档
            
        Returns:
            是否存储成功
        """
        pass
    
    @abstractmethod
    def store_documents(self, documents: List[StorageDocument]) -> bool:
        """
        批量存储文档
        
        Args:
            documents: 要存储的文档列表
            
        Returns:
            是否存储成功
        """
        pass
    
    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[StorageDocument]:
        """
        根据 ID 获取文档
        
        Args:
            doc_id: 文档 ID
            
        Returns:
            文档对象，如果不存在则返回 None
        """
        pass
    
    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档 ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def similarity_search(
        self, 
        query: str, 
        k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        向量相似性搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            metadata_filter: 元数据过滤条件
            
        Returns:
            搜索结果列表
        """
        pass
    
    @abstractmethod
    def metadata_search(
        self,
        metadata_filter: Dict[str, Any],
        limit: int = 10
    ) -> List[StorageDocument]:
        """
        基于元数据的精确搜索
        
        Args:
            metadata_filter: 元数据过滤条件
            limit: 返回结果数量限制
            
        Returns:
            匹配的文档列表
        """
        pass
    
    @abstractmethod
    def hybrid_search(
        self,
        query: str,
        metadata_filter: Optional[Dict[str, Any]] = None,
        k: int = 10,
        similarity_threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        混合搜索（语义相似性 + 元数据过滤）
        
        Args:
            query: 查询文本
            metadata_filter: 元数据过滤条件
            k: 返回结果数量
            similarity_threshold: 相似度阈值
            
        Returns:
            搜索结果列表
        """
        pass
    
    @abstractmethod
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
            metadata: 额外的元数据
            
        Returns:
            是否存储成功
        """
        pass
    
    @abstractmethod
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
            limit: 返回消息数量限制
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            消息列表
        """
        pass
    
    @abstractmethod
    def store_memory(
        self,
        memory_key: str,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        importance: int = 5,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> bool:
        """
        存储长期记忆
        
        Args:
            memory_key: 记忆唯一标识
            content: 记忆内容
            context: 上下文信息
            tags: 标签列表
            importance: 重要性评分 (1-10)
            user_id: 用户 ID
            event_type: 事件类型
            
        Returns:
            是否存储成功
        """
        pass
    
    @abstractmethod
    def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        importance_threshold: Optional[int] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        搜索长期记忆
        
        Args:
            query: 查询文本
            user_id: 用户 ID 过滤
            tags: 标签过滤
            importance_threshold: 重要性阈值
            limit: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    def clear_collection(self, collection_name: Optional[str] = None) -> bool:
        """
        清空集合
        
        Args:
            collection_name: 集合名称，如果为 None 则清空默认集合
            
        Returns:
            是否清空成功
        """
        pass