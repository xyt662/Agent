#!/usr/bin/env python3
"""
RAG 检索模块

该模块提供模块化的检索功能，包括：
- 基础向量数据库检索
- 查询转换和扩展
- 文档重排序
- 检索管道编排
"""

from .base_retriever import VectorDBRetriever
from .query_transformer import QueryTransformer, query_expansion
from .reranker import DocumentReranker, rerank_documents
from .pipeline import RetrievalPipeline

__all__ = [
    'VectorDBRetriever',
    'QueryTransformer',
    'query_expansion',
    'DocumentReranker', 
    'rerank_documents',
    'RetrievalPipeline'
]

__version__ = '1.0.0'
__author__ = 'xyt'
__description__ = 'Modular RAG retrieval system with advanced optimization techniques'