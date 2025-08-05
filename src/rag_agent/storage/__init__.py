#!/usr/bin/env python3
"""
存储层模块

提供可插拔的持久化存储接口和实现：
- BaseStore: 抽象存储接口
- ChromaStore: 基于 ChromaDB 的向量存储实现
- StorageFactory: 存储工厂，支持依赖注入
- 支持向量相似性搜索和元数据过滤
"""

from .base import BaseStore, StorageDocument, SearchResult
from .chroma_store import ChromaStore
from .factory import (
    StorageFactory, 
    StorageType, 
    get_default_store, 
    get_memory_store, 
    get_session_store,
    create_storage_backend
)

__all__ = [
    'BaseStore',
    'StorageDocument', 
    'SearchResult',
    'ChromaStore',
    'StorageFactory',
    'StorageType',
    'get_default_store',
    'get_memory_store',
    'get_session_store',
    'create_storage_backend'
]

__version__ = '1.0.0'
__author__ = 'Claude & xyt'
__description__ = 'Pluggable storage layer for SynapseAgent with ChromaDB integration'