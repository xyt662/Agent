#!/usr/bin/env python3
"""
基础向量数据库检索器

该模块提供最基础的向量数据库检索功能，不包含复杂的优化逻辑
"""

import os
from typing import Optional, List, Dict, Any
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from ..core.config import (
    get_vector_db_path,
    get_collection_name,
    get_embedding_model_name,
    get_project_root,
    DEFAULT_RETRIEVAL_K
)
from ..core.embedding_provider import get_embedding_model


class VectorDBRetriever:
    """基础向量数据库检索器
    
    职责：
    - 初始化和管理 ChromaDB 连接
    - 提供基础的相似性检索功能
    - 支持不同的检索策略（similarity, mmr, threshold）
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化向量数据库检索器
        
        Args:
            config: 检索配置字典，如果为 None 则使用默认配置
        """
        self.config = config or {}
        self.vectorstore: Optional[Chroma] = None
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """初始化向量存储"""
        try:
            # 加载配置
            vector_store_path = get_vector_db_path()
            collection_name = get_collection_name()
            embedding_model_name = get_embedding_model_name()
            
            # 构建向量存储路径
            project_root = get_project_root()
            vector_store_dir = project_root / vector_store_path
            
            if not vector_store_dir.exists():
                raise FileNotFoundError(
                    f"向量数据库目录不存在: {vector_store_dir}\n"
                    "请先运行 scripts/build_vectorstore.py 构建向量数据库"
                )
            
            # 获取嵌入模型
            embeddings = get_embedding_model()
            
            # 连接到现有的ChromaDB
            self.vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=str(vector_store_dir)
            )
            
        except Exception as e:
            raise RuntimeError(f"初始化向量数据库检索器失败: {e}")
    
    def retrieve(
        self,
        query: str,
        k: int = DEFAULT_RETRIEVAL_K,
        search_type: str = "similarity",
        search_kwargs: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """执行基础检索
        
        Args:
            query: 查询字符串
            k: 返回的文档数量
            search_type: 检索类型 ("similarity", "mmr", "similarity_score_threshold")
            search_kwargs: 检索参数
            
        Returns:
            检索到的文档列表
        """
        if not self.vectorstore:
            raise RuntimeError("向量存储未初始化")
        
        # 设置默认检索参数
        if search_kwargs is None:
            search_kwargs = {"k": k}
        else:
            search_kwargs = {"k": k, **search_kwargs}
        
        try:
            # 创建检索器
            retriever = self.vectorstore.as_retriever(
                search_type=search_type,
                search_kwargs=search_kwargs
            )
            
            # 执行检索
            documents = retriever.invoke(query)
            return documents
            
        except Exception as e:
            # 如果特定检索类型失败，回退到基础相似性搜索
            if search_type != "similarity":
                print(f"检索类型 {search_type} 失败，回退到基础相似性搜索: {e}")
                return self.retrieve(query, k, "similarity", {"k": k})
            else:
                raise RuntimeError(f"基础检索失败: {e}")
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = DEFAULT_RETRIEVAL_K
    ) -> List[tuple]:
        """执行带分数的相似性搜索
        
        Args:
            query: 查询字符串
            k: 返回的文档数量
            
        Returns:
            (文档, 分数) 元组列表
        """
        if not self.vectorstore:
            raise RuntimeError("向量存储未初始化")
        
        try:
            return self.vectorstore.similarity_search_with_score(query, k=k)
        except Exception as e:
            raise RuntimeError(f"带分数的相似性搜索失败: {e}")
    
    def get_vectorstore(self) -> Chroma:
        """获取向量存储实例
        
        Returns:
            ChromaDB 向量存储实例
        """
        if not self.vectorstore:
            raise RuntimeError("向量存储未初始化")
        return self.vectorstore
    
    def is_initialized(self) -> bool:
        """检查向量存储是否已初始化
        
        Returns:
            是否已初始化
        """
        return self.vectorstore is not None