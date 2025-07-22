#!/usr/bin/env python3
"""
RAG知识库检索工具

该工具提供从ChromaDB向量数据库检索相关文档的功能
现在使用模块化的检索管道架构
"""

from typing import Optional, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from ..retrieval.pipeline import RetrievalPipeline


class KnowledgeBaseSearchInput(BaseModel):
    """知识库搜索工具的输入参数"""
    query: str = Field(
        description="要搜索的查询内容，应该是一个清晰的问题或关键词"
    )


class KnowledgeBaseTool(BaseTool):
    """知识库检索工具
    
    该工具从ChromaDB向量数据库中检索与查询相关的文档片段
    并将其作为上下文信息返回。现在使用模块化的检索管道架构。
    """
    
    name: str = "knowledge_base_search"
    description: str = (
        "用于查询内部知识库以获取有关特定主题的信息。"
        "当用户询问关于LangGraph、Agent架构、工具开发、"
        "最佳实践或其他技术相关问题时，应使用此工具。"
        "输入应该是一个清晰的查询问题。"
    )
    args_schema: Type[BaseModel] = KnowledgeBaseSearchInput
    
    # 检索管道
    retrieval_pipeline: Optional[RetrievalPipeline] = None
    
    def __init__(self, **kwargs):
        """初始化知识库工具"""
        super().__init__(**kwargs)
        # 初始化检索管道
        self.retrieval_pipeline = RetrievalPipeline()
    
    def _run(self, query: str) -> str:
        """执行知识库检索
        
        Args:
            query: 搜索查询
            
        Returns:
            格式化的检索结果字符串
        """
        try:
            # 直接调用检索管道
            documents = self.retrieval_pipeline.invoke(query)
            
            if not documents:
                return "未找到相关信息。建议尝试使用不同的关键词或更具体的问题。"
            
            # 格式化输出
            return self._format_results(documents)
        
        except Exception as e:
            return f"检索知识库时发生错误: {e}"
    
    def _format_results(self, documents) -> str:
        """格式化检索结果
        
        Args:
            documents: 检索到的文档列表
            
        Returns:
            格式化的结果字符串
        """
        result_parts = []
        result_parts.append(f"检索到 {len(documents)} 条相关信息：\n")
        
        for i, doc in enumerate(documents, 1):
            content = doc.page_content.strip()
            # 限制每个文档片段的长度
            if len(content) > 500:
                content = content[:500] + "..."
            
            result_parts.append(f"[信息片段 {i}]")
            result_parts.append(content)
            result_parts.append("")  # 空行分隔
        
        return "\n".join(result_parts)
    
    async def _arun(self, query: str) -> str:
        """异步执行知识库检索"""
        # 对于这个简单的实现，我们直接调用同步版本
        return self._run(query)
    
    def get_pipeline_stats(self) -> dict:
        """获取检索管道统计信息
        
        Returns:
            管道统计信息字典
        """
        if self.retrieval_pipeline:
            return self.retrieval_pipeline.get_stats()
        return {}
    
    def clear_cache(self):
        """清空检索缓存"""
        if self.retrieval_pipeline:
            self.retrieval_pipeline.clear_cache()


def create_knowledge_base_tool() -> KnowledgeBaseTool:
    """创建知识库工具实例
    
    Returns:
        配置好的知识库工具实例
    """
    return KnowledgeBaseTool()