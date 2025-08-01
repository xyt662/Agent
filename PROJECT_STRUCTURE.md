# RAG-Agent 项目结构说明

本项目已成功实现Cursor模式的MCP（Model Context Protocol）工具集成，通过本地MCP服务器提供强大的工具调用能力。

## 功能特性

- ✅ **Cursor模式**：通过stdio与本地MCP服务器进程通信
- ✅ **官方SDK集成**：基于MCP官方Python客户端实现
- ✅ **异步支持**：完全异步的工具调用和生命周期管理
- ✅ **多工具包支持**：支持npm、Python等多种MCP服务器
- ✅ **环境变量注入**：自动从环境变量加载API密钥
- ✅ **资源管理**：自动管理子进程生命周期和资源清理
- ✅ **错误处理**：完善的异常处理和日志记录
- 🔧 **配置简单**：通过tools.config.json统一配置所有MCP服务器

## 📁 完整目录结构

```
RAG-Agent-Project/
├── .env                     # 存储环境变量 (API密钥, 配置等)，不纳入版本控制
├── .env.example             # 环境变量配置示例文件
├── .gitignore               # 指定 Git 应忽略的文件和目录
├── readme.md                # 项目高级概述、安装指南和使用示例
├── requirements.txt         # 项目Python依赖包列表
├── setup.py                 # 项目安装配置文件
├── run.py                   # 项目启动入口文件
├── run_tests.py             # 测试运行脚本
├── tools.config.json        # MCP工具配置文件 (Cursor模式本地MCP服务器)
├── PROJECT_STRUCTURE.md     # 项目结构详细说明
├── agent_graph.png          # Agent工作流程图
│
│
├── data/                    # 存放用于构建知识库的原始静态数据源
│   └── raw/
│       └── internal_docs.txt
│
├── vector_store/            # 存放生成的向量数据库文件 (ChromaDB)，被 .gitignore 忽略
│   ├── chroma.sqlite3
│   └── [uuid]/              # 向量数据存储目录
│
├── docs/                    # 项目文档目录
│   ├── MCP For Client Developers.html # MCP客户端开发者文档
│   ├── 实现cursor模式mcp.md           # Cursor模式MCP实现指南
│   ├── RAG_OPTIMIZATION_GUIDE.md      # RAG优化指南
│   └── 多跳查询.md                    # 多跳查询设计文档
│
├── tests/                   # 测试代码目录
│   ├── __init__.py
│   ├── test_api_client.py              # API客户端测试
│   ├── test_both_endpoints.py          # 双端点测试
│   ├── test_baidu_api_key.py           # 百度API密钥测试
│   ├── test_baidu_map_tools.py         # 百度地图工具测试
│   ├── test_mcp_direct.py              # MCP直接调用测试
│   ├── test_mcp_tools_simple.py        # MCP工具简单测试
│   ├── integration/                    # 集成测试
│   │   ├── __init__.py
│   │   └── test_tool_manager_integration.py
│   └── unit/                           # 单元测试
│       ├── __init__.py
│       └── test_tool_manager.py
│
├── scripts/                 # 开发和构建脚本目录
│   ├── __init__.py
│   ├── build_vectorstore.py           # 向量数据库构建脚本
│   └── visualize_graph.py             # 图结构可视化脚本
│
└── src/                     # 所有应用源代码的主目录
    └── rag_agent/
        ├── __init__.py
        ├── main.py          # API 服务入口 (FastAPI)，负责对外暴露Agent服务
        │
        ├── core/            # 存放应用的核心、共享和基础组件
        │   ├── __init__.py
        │   ├── agent_state.py       # 定义全局状态对象 (AgentState)，作为图的数据总线
        │   ├── config.py            # 封装环境变量的加载和访问逻辑
        │   ├── embedding_provider.py # 嵌入模型提供者
        │   ├── graph_compiler.py    # 定义图编译器，负责将图蓝图编译为可执行的应用实例
        │   └── llm_provider.py      # 集中管理和提供LLM实例，实现模型层的解耦
        │
        ├── tools/           # 存放所有可供Agent调用的工具 (Tool) 和MCP框架
        │   ├── __init__.py
        │   ├── knowledge_base.py    # 实现基于向量数据库的知识库检索工具
        │   ├── tool_registry.py     # 负责发现、注册并提供所有可用工具的列表
        │   ├── tool_manager.py      # MCP工具包管理器 (Cursor模式本地MCP服务器)
        │   ├── local_command_adapter.py  # 本地命令MCP适配器，通过stdio与本地MCP服务器通信
        │   └── mcp_manifests/       # 本地MCP工具清单目录 (已废弃，保留用于兼容性)
        │       └── __init__.py
        │
        ├── graphs/          # 存放图(Graph)的定义蓝图，描述Agent的工作流程和状态转换
        │   ├── __init__.py
        │   ├── base_agent_graph.py      # 定义基础的 ReAct (Reason-Act) Agent 的图结构
        │   ├── multi_hop_graph.py       # 【未来】定义支持多跳查询分解的复杂图结构
        │   └── self_correct_graph.py    # 【未来】定义具备反思和自我纠错能力的图结构
        │
        ├── nodes/           # 存放图中具体节点(Node)的业务逻辑实现
        │   ├── __init__.py
        │   ├── agent_node.py            # 实现核心"思考"节点：调用LLM进行决策，决定下一步行动
        │   ├── clarification_node.py    # 【未来】实现"主动澄清"节点：当输入模糊时向用户提问
        │   └── error_handling_node.py   # 【未来】实现"错误处理"节点：捕获并处理工具执行失败等异常
        │
        ├── retrieval/       # RAG检索系统
        │   ├── __init__.py
        │   ├── base_retriever.py        # 提供最基础的向量数据库检索功能
        │   ├── pipeline.py              # 定义检索流水线，负责将查询转换为文档列表
        │   ├── reranker.py              # 定义重排序模型，负责优化检索结果的相关性
        │   └── query_transformer.py     # 定义查询转换模型，负责查询优化
        │
        └── factories/       # 存放"工厂"模块，负责组装所有组件并生成最终可运行的应用实例
            ├── __init__.py
            └── agent_factory.py         # 实现具体的组装逻辑，将LLM、工具注入图蓝图并编译
```

## 🎯 核心设计哲学

### 依赖注入与关注点分离

- **Graphs (graphs/)**: 只负责定义图的"蓝图"或"模板"。它应该导出一个可以被配置的类或函数，而不是一个已经编译好的、包含了具体模型和工具的实例。它定义了"结构"，但不关心"零件"

- **Factories (factories/)**: 这才是真正的"总装车间"。它的核心职责是：
  - 获取零件：调用 llm_provider 获取LLM，调用 tool_registry 获取工具
  - 选择蓝图：从 graphs 目录中导入图的"模板"（比如 BaseAgentGraphBuilder 类）
  - 组装和编译：将具体的LLM和工具"注入"到图的模板中，然后调用编译方法，生成一个最终可运行的 app 实例
  - 提供产品：通过带缓存的函数（如 get_main_agent_runnable）将这个最终产品提供给外部调用者（如 main.py 或 run.py）

这个模型完美地体现了依赖注入 (Dependency Injection) 和关注点分离 (Separation of Concerns) 的思想，这是非常高级和易于理解的工程实践

## 🧪 测试结构

### MCP工具测试 (`tests/`)
- `test_baidu_api_key.py` - 百度地图API KEY验证测试
- `test_mcp_direct.py` - 直接MCP工具调用测试
- `test_baidu_map_tools.py` - 百度地图MCP工具集成测试
- `test_mcp_tools_simple.py` - 简单MCP工具功能测试

### 单元测试 (`tests/unit/`)
- `test_tool_manager.py` - 工具管理器单元测试

### 集成测试 (`tests/integration/`)
- `test_tool_manager_integration.py` - 工具管理器集成测试

## 🛠️ 工具脚本 (`tools/scripts/`)
- `build_vectorstore.py` - 构建向量存储
- `visualize_graph.py` - 可视化图结构

## 🚀 使用方法

### 运行测试
```bash
# 运行所有测试
python run_tests.py all

# 只运行单元测试
python run_tests.py unit

# 只运行集成测试
python run_tests.py integration

# 查看可用工具脚本
python run_tests.py scripts
```

### 运行工具脚本
```bash
# 构建向量存储
python tools/scripts/build_vectorstore.py

# 可视化图结构
python tools/scripts/visualize_graph.py
```

## 📋 重构改进

### 🔄 从HTTP模式到Cursor模式的演进

**旧HTTP模式问题:**
- 需要维护复杂的YAML清单文件
- HTTP请求的网络延迟和稳定性问题
- 认证和安全配置复杂
- 无法充分利用本地计算资源

**新Cursor模式优势:**
- **原生集成**: 基于MCP官方Python SDK实现
- **高性能**: 通过stdio直接与本地进程通信，无网络开销
- **简化配置**: 只需配置命令和参数，无需维护清单文件
- **资源高效**: 自动管理子进程生命周期
- **异步优先**: 完全异步的工具调用和错误处理
- **生态丰富**: 支持npm、Python等多种MCP服务器生态

### 🎯 设计原则

1. **单一职责**: 每个目录有明确的职责
2. **可测试性**: 测试代码与业务代码分离
3. **可维护性**: 相关功能集中管理
4. **可扩展性**: 便于添加新的测试和工具
5. **标准化**: 遵循Python社区最佳实践
6. **模块化**: 支持依赖注入和工厂模式

## 📝 开发指南

### 添加新测试
1. **单元测试**: 在 `tests/unit/` 下创建 `test_*.py` 文件
2. **集成测试**: 在 `tests/integration/` 下创建 `test_*.py` 文件
3. 确保测试文件包含适当的路径设置以导入项目模块
4. 在 `run_tests.py` 中注册新的测试文件

### 添加新MCP工具
1. 在 `tools.config.json` 中添加新的MCP服务器配置：
   ```json
   {
     "mcpServers": {
       "my_tool": {
         "command": "npx",
         "args": ["-y", "my-mcp-package"],
         "env": {
           "API_KEY": "${MY_API_KEY}"
         },
         "disabled": false
       }
     }
   }
   ```
2. 工具会自动加载并集成到Agent中

### 添加新工具脚本
1. 在 `tools/scripts/` 下创建脚本文件
2. 添加适当的文档字符串说明功能
3. 在 `run_tests.py` 的 `run_utility_scripts()` 函数中注册新脚本

### 最佳实践
- 保持测试文件的独立性
- 使用描述性的测试函数名
- 为每个测试添加适当的清理逻辑
- 在测试中使用临时文件，避免污染项目目录
- 优先使用官方MCP服务器包，确保兼容性
- 合理配置环境变量，避免硬编码敏感信息

## 🚀 Agent 功能进阶路线图

### 第一阶段：基础功能
- **ReAct 循环**: 思考-行动的基础模式
- **单工具使用**: 能调用知识库进行问答

### 第二阶段：增强推理与交互
- **多跳查询**: `A->B`, `B->C` 的链式推理
- **主动澄清**: 当指令模糊时，会反问用户
- **多工具使用**: 能在知识库和网络搜索之间做选择
- **自我纠错**: 工具失败时，会尝试其他方法或参数

### 第三阶段：高级功能 - 成为"Pro"级 Agent

1. **动态工具规划与生成 (Dynamic Tool Planning)**
   - Agent 能根据任务即时生成"微工具"（小的 Python 函数）来解决特定问题
   - 极大地提升了 Agent 的灵活性和解决未知问题的能力

2. **长期记忆与个性化 (Long-term Memory & Personalization)**
   - Agent 能记住与特定用户的历史交互摘要
   - 提供更具个性化的服务，从无状态工具变成有记忆的"私人助理"

3. **多 Agent 协作 (Multi-Agent Collaboration)**
   - 构建 Agent 系统：规划者、研究员、代码、报告者等专业化 Agent
   - 解决单个 Agent 难以处理的极其复杂的、跨领域的任务

4. **自主学习与工具优化 (Self-Learning & Tool Optimization)**
   - Agent 能够根据成功和失败的经验，自我优化其工具使用策略
   - 让 Agent 具备自我进化的能力，越用越聪明

## 📊 ChromaDB 向量数据库文件结构详解

`vector_store/` 文件夹包含了我们RAG系统的ChromaDB向量数据库：

### 核心数据库文件

**`chroma.sqlite3`**
- ChromaDB的主数据库文件，使用SQLite格式
- 存储集合元数据、文档原始文本、元数据和索引配置信息

### 向量索引文件夹

**`[uuid]/`** (如 `fcdf3f22-adb3-45b8-af1c-7f77293ea50a/`)
- 存储向量索引的二进制文件夹，每个集合对应一个唯一的UUID文件夹

**索引文件详解:**
- `data_level0.bin` - 存储文档的嵌入向量（embeddings）
- `header.bin` - 存储索引的头部信息（向量维度、索引类型等）
- `length.bin` - 存储向量长度和大小信息
- `link_lists.bin` - 存储HNSW算法的链接列表，用于高效的近似最近邻搜索

### 技术原理

**HNSW算法**: ChromaDB使用HNSW（Hierarchical Navigable Small World）算法进行向量检索：
- 多层图结构，上层稀疏，下层密集
- O(log n)的搜索复杂度
- 在速度和精度之间取得良好平衡

这种文件结构设计确保了我们的知识库检索既快速又准确，为Agent提供了强大的背景知识支持！

## 🎯 下一步行动计划

1. **采纳项目结构**: 将现有代码迁移到设计的新结构中
2. **实现基础功能**: 构建一个能使用知识库工具的基础 Agent
3. **逐步进阶**: 按照功能路线图，一步一个脚印地为 Agent 添加新能力
4. **生产化部署**: 使用 FastAPI 部署为API服务，集成可观测性工具

这个蓝图为项目提供了一个清晰的、从现在到未来的发展路径！