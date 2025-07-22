#!/usr/bin/env python3
"""
检索管道

该模块是新架构的核心，使用管道模式组织检索流程，
将查询转换、基础检索、去重、重排序等步骤串联成一个可配置的检索管道
"""

from typing import List, Optional, Dict, Any, Set
from langchain_core.documents import Document

from .base_retriever import VectorDBRetriever
from .query_transformer import QueryTransformer
from .reranker import DocumentReranker
from ..core.config import get_retrieval_config


class RetrievalPipeline:
    """检索管道
    
    职责：
    - 编排完整的检索流程
    - 管理各个检索组件
    - 提供可配置的检索策略
    - 处理异常和回退机制
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化检索管道
        
        Args:
            config: 管道配置，如果为 None 则使用默认配置
        """
        # 加载配置
        self.config = config or get_retrieval_config()
        
        # 初始化组件
        self.base_retriever = VectorDBRetriever(self.config)
        self.query_transformer = QueryTransformer(self.config)
        self.reranker = DocumentReranker(self.config)
        
        # 缓存，用于避免重复检索
        self._cache: Dict[str, List[Document]] = {}
        self._enable_cache = self.config.get('enable_cache', False)
    
    def invoke(self, query: str, **kwargs) -> List[Document]:
        """执行完整的检索管道
        
        Args:
            query: 原始查询字符串
            **kwargs: 运行时参数，可以覆盖配置中的参数
            
        Returns:
            最终的检索结果文档列表
        """
        try:
            # 合并运行时参数和配置
            runtime_config = {**self.config, **kwargs}
            
            # 检查缓存
            if self._enable_cache and query in self._cache:
                print(f"从缓存中获取查询结果: {query[:50]}...")
                return self._cache[query]
            
            # 1. 查询预处理和标准化
            normalized_query = self._preprocess_query(query, runtime_config)
            
            # 2. 查询转换（可选）
            queries = self._transform_query(normalized_query, runtime_config)
            
            # 3. 基础检索
            all_documents = self._retrieve_documents(queries, runtime_config)
            
            # 4. 后处理：去重、过滤
            processed_documents = self._postprocess_documents(
                all_documents, normalized_query, runtime_config
            )
            
            # 5. 重排序（可选）
            final_documents = self._rerank_documents(
                normalized_query, processed_documents, runtime_config
            )
            
            # 6. 最终过滤和限制数量
            result = self._finalize_results(final_documents, runtime_config)
            
            # 缓存结果
            if self._enable_cache:
                self._cache[query] = result
            
            return result
            
        except Exception as e:
            print(f"检索管道执行失败: {e}")
            # 回退到基础检索
            return self._fallback_retrieve(query, kwargs.get('k', self.config.get('k', 5)))
    
    def _preprocess_query(self, query: str, config: Dict[str, Any]) -> str:
        """查询预处理
        
        Args:
            query: 原始查询
            config: 配置参数
            
        Returns:
            预处理后的查询
        """
        # 标准化查询
        if config.get('normalize_query', True):
            return self.query_transformer.normalize_query(query)
        return query
    
    def _transform_query(self, query: str, config: Dict[str, Any]) -> List[str]:
        """查询转换
        
        Args:
            query: 标准化后的查询
            config: 配置参数
            
        Returns:
            转换后的查询列表
        """
        if config.get('use_query_expansion', False):
            expanded_queries = self.query_transformer.expand_query(query)
            print(f"查询扩展: {len(expanded_queries)} 个查询")
            return expanded_queries
        else:
            return [query]
    
    def _retrieve_documents(self, queries: List[str], config: Dict[str, Any]) -> List[Document]:
        """基础文档检索
        
        Args:
            queries: 查询列表
            config: 配置参数
            
        Returns:
            检索到的文档列表
        """
        all_documents = []
        
        # 检索参数
        k = config.get('k', 5)
        search_type = "similarity"
        search_kwargs = {"k": k}
        
        # 配置 MMR 检索
        if config.get('use_mmr', False):
            search_type = "mmr"
            search_kwargs.update({
                "fetch_k": config.get('mmr_fetch_k', k * 2),
                "lambda_mult": config.get('mmr_lambda', 0.5)
            })
        
        # 配置阈值过滤
        elif config.get('score_threshold') is not None:
            search_type = "similarity_score_threshold"
            search_kwargs.update({
                "score_threshold": config.get('score_threshold')
            })
        
        # 对每个查询执行检索
        for query in queries:
            try:
                documents = self.base_retriever.retrieve(
                    query=query,
                    k=k,
                    search_type=search_type,
                    search_kwargs=search_kwargs
                )
                all_documents.extend(documents)
                print(f"查询 '{query[:30]}...' 检索到 {len(documents)} 个文档")
                
            except Exception as e:
                print(f"查询 '{query[:30]}...' 检索失败: {e}")
                # 回退到基础检索
                try:
                    documents = self.base_retriever.retrieve(query, k, "similarity")
                    all_documents.extend(documents)
                except Exception as fallback_e:
                    print(f"回退检索也失败: {fallback_e}")
        
        return all_documents
    
    def _postprocess_documents(
        self, 
        documents: List[Document], 
        query: str, 
        config: Dict[str, Any]
    ) -> List[Document]:
        """文档后处理
        
        Args:
            documents: 原始检索文档
            query: 查询字符串
            config: 配置参数
            
        Returns:
            后处理后的文档列表
        """
        if not documents:
            return []
        
        # 去重
        unique_documents = self._deduplicate_documents(documents)
        print(f"去重后文档数量: {len(unique_documents)}")
        
        # 内容过滤
        filtered_documents = self._filter_documents(unique_documents, query, config)
        print(f"过滤后文档数量: {len(filtered_documents)}")
        
        return filtered_documents
    
    def _deduplicate_documents(self, documents: List[Document]) -> List[Document]:
        """文档去重
        
        基于文档内容进行去重
        
        Args:
            documents: 文档列表
            
        Returns:
            去重后的文档列表
        """
        seen_content: Set[str] = set()
        unique_documents = []
        
        for doc in documents:
            # 使用文档内容的哈希作为去重标识
            content_hash = hash(doc.page_content.strip())
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_documents.append(doc)
        
        return unique_documents
    
    def _filter_documents(
        self, 
        documents: List[Document], 
        query: str, 
        config: Dict[str, Any]
    ) -> List[Document]:
        """文档过滤
        
        根据配置过滤文档
        
        Args:
            documents: 文档列表
            query: 查询字符串
            config: 配置参数
            
        Returns:
            过滤后的文档列表
        """
        filtered = documents
        
        # 最小内容长度过滤
        min_content_length = config.get('min_content_length', 10)
        if min_content_length > 0:
            filtered = [
                doc for doc in filtered 
                if len(doc.page_content.strip()) >= min_content_length
            ]
        
        # 最大文档数量限制（预过滤，为重排序准备）
        max_docs_before_rerank = config.get('max_docs_before_rerank', 20)
        if len(filtered) > max_docs_before_rerank:
            # 简单截取前N个文档
            filtered = filtered[:max_docs_before_rerank]
        
        return filtered
    
    def _rerank_documents(
        self, 
        query: str, 
        documents: List[Document], 
        config: Dict[str, Any]
    ) -> List[Document]:
        """文档重排序
        
        Args:
            query: 查询字符串
            documents: 文档列表
            config: 配置参数
            
        Returns:
            重排序后的文档列表
        """
        if not config.get('use_reranking', False) or not documents:
            return documents
        
        try:
            # 重排序策略
            rerank_strategy = config.get('rerank_strategy', 'relevance')
            rerank_top_k = config.get('rerank_top_k', len(documents))
            
            reranked_documents = self.reranker.rerank(
                query=query,
                documents=documents,
                strategy=rerank_strategy,
                top_k=rerank_top_k
            )
            
            print(f"重排序完成: {len(reranked_documents)} 个文档")
            return reranked_documents
            
        except Exception as e:
            print(f"重排序失败: {e}")
            return documents
    
    def _finalize_results(self, documents: List[Document], config: Dict[str, Any]) -> List[Document]:
        """最终结果处理
        
        Args:
            documents: 文档列表
            config: 配置参数
            
        Returns:
            最终的文档列表
        """
        # 最终数量限制
        final_k = config.get('final_k') or config.get('k', 5)
        
        if len(documents) > final_k:
            documents = documents[:final_k]
        
        print(f"最终返回 {len(documents)} 个文档")
        return documents
    
    def _fallback_retrieve(self, query: str, k: int = 5) -> List[Document]:
        """回退检索策略
        
        当主要检索流程失败时使用的简单检索
        
        Args:
            query: 查询字符串
            k: 返回文档数量
            
        Returns:
            检索到的文档列表
        """
        try:
            print(f"使用回退检索策略")
            return self.base_retriever.retrieve(query, k, "similarity")
        except Exception as e:
            print(f"回退检索也失败: {e}")
            return []
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        print("检索缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取管道统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "cache_size": len(self._cache),
            "cache_enabled": self._enable_cache,
            "base_retriever_initialized": self.base_retriever.is_initialized(),
            "config": self.config
        }