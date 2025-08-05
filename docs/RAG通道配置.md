# RAG 检索优化指南

本文档详细介绍了项目中实现的 RAG（检索增强生成）优化技术，以及如何配置和使用这些功能来提升检索质量

## 🎯 优化技术概览

### 1. 相似度阈值过滤 (Similarity Score Threshold)

**原理**：设置最低相似度阈值，过滤掉质量较低的检索结果

**优势**：
- 提高检索结果的相关性
- 减少噪音信息
- 避免返回不相关的文档片段

**配置**：
```bash
# 在 .env 文件中设置
RAG_SCORE_THRESHOLD=0.7  # 0-1之间，越高越严格
```

### 2. MMR 算法 (Maximal Marginal Relevance)

**原理**：在保证相关性的同时，最大化结果的多样性，减少重复内容

**优势**：
- 减少检索结果的重复性
- 提供更全面的信息覆盖
- 平衡相关性和多样性

**配置**：
```bash
# 在 .env 文件中设置
RAG_USE_MMR=true
RAG_MMR_FETCH_K=20      # 初始获取的文档数量
RAG_MMR_LAMBDA=0.5      # 多样性参数 (0-1，越小越多样)
```

### 3. 查询扩展 (Query Expansion)

**原理**：通过添加同义词和相关术语来扩展原始查询，提高检索召回率

**优势**：
- 提高检索召回率
- 处理术语变体和同义词
- 增强对技术术语的理解

**支持的术语映射**：
- `agent` → `智能体`, `代理`, `AI agent`
- `langgraph` → `LangGraph`, `图`, `工作流`
- `rag` → `RAG`, `检索增强生成`, `retrieval augmented generation`
- `tool` → `工具`, `函数`, `function`
- `embedding` → `嵌入`, `向量`, `vector`
- `llm` → `大语言模型`, `language model`, `AI模型`

**配置**：
```bash
RAG_USE_QUERY_EXPANSION=true
```

### 4. 文档重排序 (Document Reranking)

**原理**：基于查询与文档的语义相似度对检索结果进行重新排序

**排序因子**：
- 查询词匹配分数
- 文档长度适中性
- 技术关键词密度

**配置**：
```bash
RAG_USE_RERANKING=true
```

## 🔧 配置参数详解

### 环境变量配置

在项目根目录的 `.env` 文件中添加以下配置：

```bash
# RAG 检索优化配置
RAG_SCORE_THRESHOLD=0.6        # 相似度阈值 (默认: 0.6)
RAG_USE_MMR=false              # 是否使用MMR算法 (默认: false)
RAG_USE_QUERY_EXPANSION=true   # 是否使用查询扩展 (默认: true)
RAG_USE_RERANKING=true         # 是否使用重排序 (默认: true)
RAG_MMR_FETCH_K=20             # MMR初始获取文档数 (默认: 20)
RAG_MMR_LAMBDA=0.5             # MMR多样性参数 (默认: 0.5)
```

### 参数调优建议

#### 相似度阈值 (SCORE_THRESHOLD)
- **0.8-1.0**：高精度，低召回率，适合对准确性要求极高的场景
- **0.6-0.8**：平衡精度和召回率，推荐用于大多数场景
- **0.4-0.6**：高召回率，低精度，适合探索性查询

#### MMR 参数调优
- **LAMBDA = 0.0**：最大多样性，最小相关性
- **LAMBDA = 0.5**：平衡多样性和相关性（推荐）
- **LAMBDA = 1.0**：最大相关性，最小多样性

## 📊 性能对比

### 基础检索 vs 增强检索

| 检索方式 | 相关性 | 多样性 | 召回率 | 处理时间 |
|---------|--------|--------|--------|----------|
| 基础检索 | 中等 | 低 | 中等 | 快 |
| 增强检索 | 高 | 高 | 高 | 稍慢 |

### 适用场景

**基础检索适用于**：
- 对响应时间要求极高的场景
- 简单的事实性查询
- 资源受限的环境

**增强检索适用于**：
- 复杂的技术查询
- 需要全面信息的场景
- 对准确性要求较高的应用


## 🔍 故障排除

### 常见问题

**Q: 检索结果太少或为空**
A: 降低 `RAG_SCORE_THRESHOLD` 值，或启用查询扩展

**Q: 检索结果重复性高**
A: 启用 MMR 算法：`RAG_USE_MMR=true`

**Q: 检索速度较慢**
A: 禁用部分优化功能，或减少 `RAG_MMR_FETCH_K` 值

**Q: 检索结果不够相关**
A: 提高 `RAG_SCORE_THRESHOLD` 值，启用重排序功能



## 📈 未来优化方向

### 1. 混合检索 (Hybrid Search)
- 结合语义检索和关键词检索
- 提供更全面的检索覆盖

### 2. 学习型重排序
- 基于用户反馈的重排序模型
- 持续优化检索质量

### 3. 动态阈值调整
- 根据查询复杂度自动调整阈值
- 智能化参数优化

### 4. 上下文感知检索
- 考虑对话历史的检索策略
- 多轮对话优化

## 📚 参考资源

- [ChromaDB 官方文档](https://docs.trychroma.com/)
- [LangChain 检索器文档](https://python.langchain.com/docs/modules/data_connection/retrievers/)
- [MMR 算法论文](https://www.cs.cmu.edu/~jgc/publication/The_Use_MMR_Diversity_Based_LTMIR_1998.pdf)
- [RAG 优化最佳实践](https://arxiv.org/abs/2312.10997)

---
