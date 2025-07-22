#!/usr/bin/env python3
"""
查询转换器

该模块负责对原始查询进行各种转换和优化，包括查询扩展等技术
"""

import re
from typing import List, Optional, Dict, Any


class QueryTransformer:
    """查询转换器
    
    职责：
    - 查询扩展 (Query Expansion)
    - 查询重写 (Query Rewriting)
    - 查询标准化 (Query Normalization)
    - 未来可扩展其他查询转换技术
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化查询转换器
        
        Args:
            config: 转换器配置
        """
        self.config = config or {}
    
    def expand_query(self, query: str) -> List[str]:
        """查询扩展
        
        通过添加同义词、相关术语等方式扩展原始查询，提高检索召回率
        
        Args:
            query: 原始查询字符串
            
        Returns:
            扩展后的查询列表，包含原始查询
        """
        queries = [query]  # 始终包含原始查询
        
        try:
            # 1. 基于关键词的扩展
            keyword_expanded = self._expand_by_keywords(query)
            queries.extend(keyword_expanded)
            
            # 2. 基于同义词的扩展
            synonym_expanded = self._expand_by_synonyms(query)
            queries.extend(synonym_expanded)
            
            # 3. 基于上下文的扩展
            context_expanded = self._expand_by_context(query)
            queries.extend(context_expanded)
            
            # 去重并保持顺序
            unique_queries = []
            seen = set()
            for q in queries:
                if q not in seen and q.strip():
                    unique_queries.append(q)
                    seen.add(q)
            
            return unique_queries
            
        except Exception as e:
            print(f"查询扩展失败: {e}")
            return [query]  # 失败时返回原始查询
    
    def _expand_by_keywords(self, query: str) -> List[str]:
        """基于关键词的查询扩展"""
        expanded_queries = []
        
        # 技术术语映射
        tech_mappings = {
            'AI': ['人工智能', 'Artificial Intelligence', '机器学习', 'ML'],
            '人工智能': ['AI', 'Artificial Intelligence', '机器学习', 'ML'],
            'LangChain': ['langchain', 'Lang Chain', '语言链'],
            'LangGraph': ['langgraph', 'Lang Graph', '语言图'],
            'RAG': ['检索增强生成', 'Retrieval Augmented Generation', '检索增强'],
            '向量数据库': ['vector database', 'vectorstore', '向量存储'],
            'Agent': ['智能体', '代理', 'agent'],
            '智能体': ['Agent', '代理', 'agent'],
        }
        
        # 查找并扩展技术术语
        for term, expansions in tech_mappings.items():
            if term.lower() in query.lower():
                for expansion in expansions:
                    if expansion.lower() not in query.lower():
                        expanded_query = query + f" {expansion}"
                        expanded_queries.append(expanded_query)
        
        return expanded_queries
    
    def _expand_by_synonyms(self, query: str) -> List[str]:
        """基于同义词的查询扩展"""
        expanded_queries = []
        
        # 同义词映射
        synonym_mappings = {
            '优势': ['好处', '优点', '特点', '特色'],
            '特点': ['特色', '特征', '优势', '优点'],
            '使用': ['应用', '运用', '利用', '采用'],
            '方法': ['方式', '策略', '技术', '手段'],
            '实现': ['完成', '达成', '构建', '开发'],
            '配置': ['设置', '配制', '设定', '调整'],
            '问题': ['困难', '挑战', '难题', '故障'],
            '解决': ['处理', '解答', '修复', '应对'],
        }
        
        # 查找并扩展同义词
        for word, synonyms in synonym_mappings.items():
            if word in query:
                for synonym in synonyms:
                    expanded_query = query.replace(word, synonym)
                    if expanded_query != query:
                        expanded_queries.append(expanded_query)
        
        return expanded_queries
    
    def _expand_by_context(self, query: str) -> List[str]:
        """基于上下文的查询扩展"""
        expanded_queries = []
        
        # 上下文扩展规则
        context_rules = {
            # 如果查询包含某些关键词，添加相关上下文
            'LangGraph': ['工作流', '状态管理', '节点', '边'],
            'Agent': ['工具', '推理', '决策', '执行'],
            'RAG': ['检索', '生成', '知识库', '向量'],
            '配置': ['参数', '设置', '环境变量', '初始化'],
            '错误': ['调试', '日志', '异常', '故障排除'],
        }
        
        for keyword, contexts in context_rules.items():
            if keyword.lower() in query.lower():
                for context in contexts:
                    if context not in query:
                        expanded_query = f"{query} {context}"
                        expanded_queries.append(expanded_query)
        
        return expanded_queries
    
    def normalize_query(self, query: str) -> str:
        """查询标准化
        
        清理和标准化查询字符串
        
        Args:
            query: 原始查询字符串
            
        Returns:
            标准化后的查询字符串
        """
        # 移除多余的空白字符
        normalized = re.sub(r'\s+', ' ', query.strip())
        
        # 移除特殊字符（保留中文、英文、数字、基本标点）
        normalized = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()\[\]{}"\'-]', '', normalized)
        
        return normalized
    
    def transform(self, query: str, expand: bool = True, normalize: bool = True) -> List[str]:
        """执行完整的查询转换
        
        Args:
            query: 原始查询字符串
            expand: 是否执行查询扩展
            normalize: 是否执行查询标准化
            
        Returns:
            转换后的查询列表
        """
        # 标准化查询
        if normalize:
            query = self.normalize_query(query)
        
        # 扩展查询
        if expand:
            return self.expand_query(query)
        else:
            return [query]


# 便捷函数，保持向后兼容
def query_expansion(query: str) -> List[str]:
    """查询扩展便捷函数
    
    Args:
        query: 原始查询字符串
        
    Returns:
        扩展后的查询列表
    """
    transformer = QueryTransformer()
    return transformer.expand_query(query)