#!/usr/bin/env python3
"""
RAG知识库检索工具

该工具提供从ChromaDB向量数据库检索相关文档的功能
"""

import os
from typing import Optional, Type
from pathlib import Path

from langchain_core.tools import BaseTool
from langchain_chroma import Chroma
from pydantic import BaseModel, Field

from ..core.config import (
    get_vector_db_path,
    get_collection_name,
    get_embedding_model_name,
    get_project_root,
    DEFAULT_RETRIEVAL_K
)
from ..core.embedding_provider import get_embedding_model

class KnowledgeBaseSearchInput(BaseModel):
    """知识库搜索工具的输入参数"""
    query: str = Field(
        description="要搜索的查询内容，应该是一个清晰的问题或关键词"
    )

class KnowledgeBaseTool(BaseTool):
    """知识库检索工具
    
    该工具从ChromaDB向量数据库中检索与查询相关的文档片段
    并将其作为上下文信息返回
    """
    
    name: str = "knowledge_base_search"
    description: str = (
        "用于查询内部知识库以获取有关特定主题的信息"
        "当用户询问关于LangGraph、Agent架构、工具开发"
        "最佳实践或其他技术相关问题时，应使用此工具"
        "输入应该是一个清晰的查询问题"
    )
    args_schema: Type[BaseModel] = KnowledgeBaseSearchInput
    
    # 定义类属性
    vectorstore: Optional[object] = None
    retriever: Optional[object] = None
    
    def __init__(self, **kwargs):
        """初始化知识库工具"""
        super().__init__(**kwargs)
        self._initialize_retriever()
    
    def _initialize_retriever(self):
        """初始化检索器"""
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
            
            # 创建检索器
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": DEFAULT_RETRIEVAL_K}
            )
            
        except Exception as e:
            raise RuntimeError(f"初始化知识库检索器失败: {e}")
    
    def _run(self, query: str) -> str:
        """执行知识库检索
        
        Args:
            query: 搜索查询
            
        Returns:
            格式化的检索结果字符串
        """
        try:
            # 执行检索
            documents = self.retriever.invoke(query)
            
            if not documents:
                return "未找到相关信息"
            
            # 格式化检索结果
            result_parts = []
            result_parts.append(f"基于知识库检索到 {len(documents)} 条相关信息：\n")
            
            for i, doc in enumerate(documents, 1):
                content = doc.page_content.strip()
                # 限制每个文档片段的长度
                if len(content) > 500:
                    content = content[:500] + "..."
                
                result_parts.append(f"[信息片段 {i}]")
                result_parts.append(content)
                result_parts.append("")  # 空行分隔
            
            return "\n".join(result_parts)
            
        except Exception as e:
            return f"检索知识库时发生错误: {e}"
    
    async def _arun(self, query: str) -> str:
        """异步执行知识库检索"""
        # 对于这个简单的实现，我们直接调用同步版本
        return self._run(query)

def create_knowledge_base_tool() -> KnowledgeBaseTool:
    """创建知识库工具实例
    
    Returns:
        配置好的知识库工具实例
    """
    return KnowledgeBaseTool()