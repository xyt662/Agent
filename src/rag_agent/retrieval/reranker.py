#!/usr/bin/env python3
"""
文档重排序器

该模块负责对检索到的文档进行后处理和重排序，提高检索结果的相关性
"""

import math
from typing import List, Optional, Dict, Any, Tuple
from collections import Counter

from langchain_core.documents import Document


class DocumentReranker:
    """文档重排序器
    
    职责：
    - 基于相关性分数的重排序
    - 基于多样性的重排序
    - 基于语义相似度的重排序
    - 未来可集成更高级的重排序模型（如 Cohere Rerank）
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化文档重排序器
        
        Args:
            config: 重排序器配置
        """
        self.config = config or {}
    
    def rerank_by_relevance(
        self,
        query: str,
        documents: List[Document],
        top_k: Optional[int] = None
    ) -> List[Document]:
        """基于相关性分数的重排序
        
        Args:
            query: 原始查询
            documents: 待重排序的文档列表
            top_k: 返回的文档数量，None 表示返回所有文档
            
        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []
        
        try:
            # 计算每个文档的相关性分数
            scored_docs = []
            for doc in documents:
                score = self._calculate_relevance_score(query, doc)
                scored_docs.append((doc, score))
            
            # 按分数降序排序
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            # 返回指定数量的文档
            if top_k is not None:
                scored_docs = scored_docs[:top_k]
            
            return [doc for doc, _ in scored_docs]
            
        except Exception as e:
            print(f"基于相关性的重排序失败: {e}")
            return documents[:top_k] if top_k else documents
    
    def rerank_by_diversity(
        self,
        query: str,
        documents: List[Document],
        top_k: Optional[int] = None,
        diversity_threshold: float = 0.7
    ) -> List[Document]:
        """基于多样性的重排序
        
        使用 MMR (Maximal Marginal Relevance) 算法平衡相关性和多样性
        
        Args:
            query: 原始查询
            documents: 待重排序的文档列表
            top_k: 返回的文档数量
            diversity_threshold: 多样性阈值 (0-1)，越高越注重多样性
            
        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []
        
        if len(documents) <= 1:
            return documents
        
        try:
            # 计算所有文档的相关性分数
            relevance_scores = {}
            for i, doc in enumerate(documents):
                relevance_scores[i] = self._calculate_relevance_score(query, doc)
            
            # MMR 算法
            selected = []
            remaining = list(range(len(documents)))
            
            # 选择第一个最相关的文档
            first_idx = max(remaining, key=lambda i: relevance_scores[i])
            selected.append(first_idx)
            remaining.remove(first_idx)
            
            # 迭代选择剩余文档
            while remaining and (top_k is None or len(selected) < top_k):
                best_idx = None
                best_score = float('-inf')
                
                for idx in remaining:
                    # 计算与查询的相关性
                    relevance = relevance_scores[idx]
                    
                    # 计算与已选文档的最大相似度
                    max_similarity = 0
                    for selected_idx in selected:
                        similarity = self._calculate_document_similarity(
                            documents[idx], documents[selected_idx]
                        )
                        max_similarity = max(max_similarity, similarity)
                    
                    # MMR 分数：平衡相关性和多样性
                    mmr_score = (
                        diversity_threshold * relevance - 
                        (1 - diversity_threshold) * max_similarity
                    )
                    
                    if mmr_score > best_score:
                        best_score = mmr_score
                        best_idx = idx
                
                if best_idx is not None:
                    selected.append(best_idx)
                    remaining.remove(best_idx)
                else:
                    break
            
            return [documents[i] for i in selected]
            
        except Exception as e:
            print(f"基于多样性的重排序失败: {e}")
            return documents[:top_k] if top_k else documents
    
    def rerank_hybrid(
        self,
        query: str,
        documents: List[Document],
        top_k: Optional[int] = None,
        relevance_weight: float = 0.7,
        diversity_weight: float = 0.3
    ) -> List[Document]:
        """混合重排序策略
        
        结合相关性和多样性进行重排序
        
        Args:
            query: 原始查询
            documents: 待重排序的文档列表
            top_k: 返回的文档数量
            relevance_weight: 相关性权重
            diversity_weight: 多样性权重
            
        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []
        
        try:
            # 确保权重和为1
            total_weight = relevance_weight + diversity_weight
            if total_weight > 0:
                relevance_weight /= total_weight
                diversity_weight /= total_weight
            
            # 基于相关性的排序
            relevance_ranked = self.rerank_by_relevance(query, documents)
            
            # 基于多样性的排序
            diversity_ranked = self.rerank_by_diversity(query, documents)
            
            # 计算混合分数
            doc_scores = {}
            
            # 相关性分数（基于排名）
            for i, doc in enumerate(relevance_ranked):
                doc_id = id(doc)
                relevance_score = (len(relevance_ranked) - i) / len(relevance_ranked)
                doc_scores[doc_id] = relevance_weight * relevance_score
            
            # 多样性分数（基于排名）
            for i, doc in enumerate(diversity_ranked):
                doc_id = id(doc)
                diversity_score = (len(diversity_ranked) - i) / len(diversity_ranked)
                if doc_id in doc_scores:
                    doc_scores[doc_id] += diversity_weight * diversity_score
                else:
                    doc_scores[doc_id] = diversity_weight * diversity_score
            
            # 按混合分数排序
            sorted_docs = sorted(
                documents,
                key=lambda doc: doc_scores.get(id(doc), 0),
                reverse=True
            )
            
            return sorted_docs[:top_k] if top_k else sorted_docs
            
        except Exception as e:
            print(f"混合重排序失败: {e}")
            return documents[:top_k] if top_k else documents
    
    def _calculate_relevance_score(self, query: str, document: Document) -> float:
        """计算文档与查询的相关性分数
        
        使用简单的 TF-IDF 和关键词匹配算法
        
        Args:
            query: 查询字符串
            document: 文档对象
            
        Returns:
            相关性分数 (0-1)
        """
        try:
            doc_content = document.page_content.lower()
            query_lower = query.lower()
            
            # 1. 精确匹配分数
            exact_match_score = 1.0 if query_lower in doc_content else 0.0
            
            # 2. 关键词匹配分数
            query_words = set(query_lower.split())
            doc_words = set(doc_content.split())
            
            if not query_words:
                keyword_score = 0.0
            else:
                matched_words = query_words.intersection(doc_words)
                keyword_score = len(matched_words) / len(query_words)
            
            # 3. 词频分数
            word_freq_score = 0.0
            for word in query_words:
                if word in doc_content:
                    freq = doc_content.count(word)
                    word_freq_score += math.log(1 + freq)
            
            # 标准化词频分数
            if query_words:
                word_freq_score /= len(query_words)
                word_freq_score = min(word_freq_score, 1.0)
            
            # 4. 文档长度惩罚（较短的文档可能更相关）
            doc_length = len(doc_content.split())
            length_penalty = 1.0 / (1.0 + math.log(1 + doc_length / 100))
            
            # 综合分数
            final_score = (
                0.4 * exact_match_score +
                0.3 * keyword_score +
                0.2 * word_freq_score +
                0.1 * length_penalty
            )
            
            return min(final_score, 1.0)
            
        except Exception as e:
            print(f"计算相关性分数失败: {e}")
            return 0.0
    
    def _calculate_document_similarity(self, doc1: Document, doc2: Document) -> float:
        """计算两个文档之间的相似度
        
        使用简单的词汇重叠算法
        
        Args:
            doc1: 第一个文档
            doc2: 第二个文档
            
        Returns:
            相似度分数 (0-1)
        """
        try:
            content1 = set(doc1.page_content.lower().split())
            content2 = set(doc2.page_content.lower().split())
            
            if not content1 or not content2:
                return 0.0
            
            # Jaccard 相似度
            intersection = content1.intersection(content2)
            union = content1.union(content2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception as e:
            print(f"计算文档相似度失败: {e}")
            return 0.0
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        strategy: str = "relevance",
        top_k: Optional[int] = None,
        **kwargs
    ) -> List[Document]:
        """执行文档重排序
        
        Args:
            query: 原始查询
            documents: 待重排序的文档列表
            strategy: 重排序策略 ("relevance", "diversity", "hybrid")
            top_k: 返回的文档数量
            **kwargs: 策略特定的参数
            
        Returns:
            重排序后的文档列表
        """
        if strategy == "relevance":
            return self.rerank_by_relevance(query, documents, top_k)
        elif strategy == "diversity":
            return self.rerank_by_diversity(query, documents, top_k, **kwargs)
        elif strategy == "hybrid":
            return self.rerank_hybrid(query, documents, top_k, **kwargs)
        else:
            print(f"未知的重排序策略: {strategy}，使用默认相关性排序")
            return self.rerank_by_relevance(query, documents, top_k)


# 便捷函数，保持向后兼容
def rerank_documents(
    query: str,
    documents: List[Document],
    top_k: Optional[int] = None,
    strategy: str = "relevance"
) -> List[Document]:
    """文档重排序便捷函数
    
    Args:
        query: 原始查询
        documents: 待重排序的文档列表
        top_k: 返回的文档数量
        strategy: 重排序策略
        
    Returns:
        重排序后的文档列表
    """
    reranker = DocumentReranker()
    return reranker.rerank(query, documents, strategy, top_k)