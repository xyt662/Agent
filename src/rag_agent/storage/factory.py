#!/usr/bin/env python3
"""
存储工厂

提供存储实例的创建和管理，支持依赖注入模式
"""

from typing import Optional, Union, Dict, Any
from pathlib import Path
from enum import Enum

from langchain_core.embeddings import Embeddings

from .base import BaseStore
from .chroma_store import ChromaStore
try:
    from ..core.embedding_provider import get_embedding_model
except ImportError:
    get_embedding_model = None


class StorageType(Enum):
    """存储类型枚举"""
    CHROMA = "chroma"
    # 未来可以扩展其他存储类型
    # PINECONE = "pinecone"
    # WEAVIATE = "weaviate"


class StorageFactory:
    """
    存储工厂类
    
    负责创建和管理不同类型的存储实例，
    支持依赖注入和配置管理。
    """
    
    _instances: Dict[str, BaseStore] = {}
    
    @classmethod
    def create_store(
        cls,
        storage_type: StorageType = StorageType.CHROMA,
        storage_dir: Optional[Union[str, Path]] = None,
        collection_name: str = "synapseagent_storage",
        embedding_model: Optional[Embeddings] = None,
        enable_cache: bool = True,
        **kwargs
    ) -> BaseStore:
        """
        创建存储实例（统一的存储后端初始化方式）
        
        Args:
            storage_type: 存储类型
            storage_dir: 存储目录
            collection_name: 集合名称
            embedding_model: 嵌入模型
            enable_cache: 是否启用实例缓存
            **kwargs: 其他配置参数
            
        Returns:
            存储实例
        """
        # 生成实例键
        instance_key = f"{storage_type.value}_{collection_name}"
        
        # 检查是否已存在实例（如果启用缓存）
        if enable_cache and instance_key in cls._instances:
            return cls._instances[instance_key]
        
        # 创建新实例
        if storage_type == StorageType.CHROMA:
            store = cls._create_chroma_store(
                storage_dir=storage_dir,
                collection_name=collection_name,
                embedding_model=embedding_model,
                **kwargs
            )
        else:
            raise ValueError(f"不支持的存储类型: {storage_type}")
        
        # 缓存实例（如果启用缓存）
        if enable_cache:
            cls._instances[instance_key] = store
        
        return store
    
    @classmethod
    def _create_chroma_store(
        cls,
        storage_dir: Optional[Union[str, Path]] = None,
        collection_name: str = "synapseagent_storage",
        embedding_model: Optional[Embeddings] = None,
        **kwargs
    ) -> ChromaStore:
        """
        创建 ChromaDB 存储实例
        """
        if embedding_model is None:
            if get_embedding_model:
                embedding_model = get_embedding_model()
            else:
                raise ValueError("No embedding model provided and get_embedding_model is not available")
        
        return ChromaStore(
            storage_dir=storage_dir,
            collection_name=collection_name,
            embedding_model=embedding_model
        )
    
    @classmethod
    def get_default_store(
        cls,
        collection_name: str = "synapseagent_storage",
        **kwargs
    ) -> BaseStore:
        """
        获取默认存储实例（ChromaDB）
        
        Args:
            collection_name: 集合名称
            **kwargs: 其他配置参数
            
        Returns:
            默认存储实例
        """
        return cls.create_store(
            storage_type=StorageType.CHROMA,
            collection_name=collection_name,
            **kwargs
        )
    
    @classmethod
    def get_memory_store(cls, **kwargs) -> BaseStore:
        """
        获取专用于长期记忆的存储实例
        
        Args:
            **kwargs: 其他配置参数
            
        Returns:
            记忆存储实例
        """
        return cls.create_store(
            storage_type=StorageType.CHROMA,
            collection_name="synapseagent_memory",
            **kwargs
        )
    
    @classmethod
    def get_session_store(cls, **kwargs) -> BaseStore:
        """
        获取专用于会话历史的存储实例
        
        Args:
            **kwargs: 其他配置参数
            
        Returns:
            会话存储实例
        """
        return cls.create_store(
            storage_type=StorageType.CHROMA,
            collection_name="synapseagent_sessions",
            **kwargs
        )
    
    @classmethod
    def clear_instances(cls):
        """
        清空所有缓存的实例
        """
        cls._instances.clear()
    
    @classmethod
    def get_instance_info(cls) -> Dict[str, Any]:
        """
        获取当前实例信息
        
        Returns:
            实例信息字典
        """
        return {
            'total_instances': len(cls._instances),
            'instance_keys': list(cls._instances.keys()),
            'storage_types': [StorageType.CHROMA.value]  # 当前支持的存储类型
        }


# 便捷函数
def get_default_store(**kwargs) -> BaseStore:
    """获取默认存储实例"""
    return StorageFactory.get_default_store(**kwargs)


def get_memory_store(**kwargs) -> BaseStore:
    """获取记忆存储实例"""
    return StorageFactory.get_memory_store(**kwargs)


def get_session_store(**kwargs) -> BaseStore:
    """获取会话存储实例"""
    return StorageFactory.get_session_store(**kwargs)


def create_storage_backend(
    storage_type: str = "chroma",
    collection_name: str = "synapseagent_storage",
    **kwargs
) -> BaseStore:
    """
    统一的存储后端创建函数
    
    这是一个便捷函数，用于简化存储后端的创建过程。
    支持字符串类型参数，自动转换为相应的枚举类型。
    
    Args:
        storage_type: 存储类型（"chroma"）
        collection_name: 集合名称
        **kwargs: 其他配置参数
        
    Returns:
        存储实例
        
    Examples:
        >>> # 创建默认存储
        >>> store = create_storage_backend()
        >>> 
        >>> # 创建记忆存储
        >>> memory_store = create_storage_backend(collection_name="memory")
        >>> 
        >>> # 创建会话存储
        >>> session_store = create_storage_backend(collection_name="sessions")
    """
    # 转换字符串类型为枚举
    if isinstance(storage_type, str):
        storage_type_map = {
            "chroma": StorageType.CHROMA,
            "chromadb": StorageType.CHROMA,
        }
        storage_type_enum = storage_type_map.get(storage_type.lower())
        if storage_type_enum is None:
            raise ValueError(f"不支持的存储类型: {storage_type}")
    else:
        storage_type_enum = storage_type
    
    return StorageFactory.create_store(
        storage_type=storage_type_enum,
        collection_name=collection_name,
        **kwargs
    )