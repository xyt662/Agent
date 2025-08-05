#!/usr/bin/env python3
"""
长期记忆模块

该模块提供统一的记忆管理功能，包括：
- 统一的记忆管理器
- 记忆事件处理器
- 记忆工具类
"""

from .memory_manager import MemoryManager, MemoryUtils
from .memory_event_handler import MemoryEventHandler, create_memory_event_handler

# 向后兼容性别名
EnhancedMemoryManager = MemoryManager

__all__ = [
    'MemoryManager',
    'MemoryUtils',
    'MemoryEventHandler',
    'create_memory_event_handler',
    'EnhancedMemoryManager'  # 向后兼容
]

__version__ = '3.0.0'
__author__ = 'xyt'
__description__ = 'Unified memory management system for SynapseAgent with ChromaDB integration'