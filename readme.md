
# RAG-Agent: 一个基于 LangGraph 的高级检索增强生成代理

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![LangChain](https://img.shields.io/badge/LangChain-LangGraph-orange)
![License](https://img.shields.io/badge/License-MIT-green)

RAG-Agent 是一个基于 LangChain 和 LangGraph 构建的、高度模块化和可扩展的检索增强生成 (Retrieval-Augmented Generation, RAG) 代理项目。它旨在作为一个健壮的框架，用于开发能够利用私有知识库和外部工具来智能回答问题的复杂代理。

这个项目的核心设计哲学是**关注点分离**和**依赖注入**，使得每个组件（如LLM、工具、图结构）都高度解耦，易于测试、替换和扩展。

## ✨ 项目特性

- **模块化架构**: 清晰的目录结构，将图的定义、节点逻辑、工具、核心服务和工厂组装完全分离
- **ReAct 代理**: 实现了一个基础的 "Reason-Act" (ReAct) 工作流，使代理能够思考、调用工具并根据结果进行下一步行动
- **可扩展的工具集**: 轻松集成自定义工具，如私有知识库检索、网络搜索等。
- **MCP工具集成**: 支持通过YAML清单文件定义和加载外部HTTP API工具，具备完整的认证和错误处理机制。
- **可配置的工作流**: `graphs` 目录下的蓝图设计允许开发者轻松定义或修改代理的工作流程，例如实现多跳查询或自我纠错循环。
- **工程化实践**:
    - 使用工厂模式进行依赖注入和应用组装。
    - 通过 `.env` 文件管理敏感信息和配置。
    - 使用 `lru_cache` 缓存编译好的代理实例，提高性能。

## 🚀 快速开始

### 1. 环境准备

- **克隆项目**:
  ```bash
  git clone https://github.com/xyt662/Agent.git
  cd Agent
  ```

- **安装依赖**:
  建议使用虚拟环境（如 venv 或 conda）。
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
  pip install -r requirements.txt
  ```

### 2. 配置 API 密钥

- **创建 `.env` 文件**:
  项目根目录下有一个 `.env.example` 文件（如果还没有，请创建一个）。请将其复制并重命名为 `.env`。
  ```bash
  cp .env.example .env
  ```

- **编辑 `.env` 文件**:
  打开 `.env` 文件，并填入您的大语言模型（例如 DeepSeek）的 API 密钥。
  ```
  # .env
  DEEPSEEK_API_KEY="sk-your-api-key-here"
  ```

### 3. 构建知识库 (可选)

如果需要使用私有知识库检索功能，请将您的原始文档（如 `internal_docs.txt`）放入 `data/raw/` 目录。然后，运行知识库构建脚本（您可能需要自行创建此脚本，例如 `build_vectorstore.py`）来生成向量数据库。

### 4. 运行代理

本项目提供了一个简单的命令行运行脚本，用于快速测试代理的功能。

```bash
# 在项目根目录下运行
python src/rag_agent/run.py
```

您应该能看到类似以下的日志输出，展示了代理的完整思考和行动流程：

```
INFO:rag_agent.factories.agent_factory:Assembling and compiling the main agent...
INFO:__main__:成功创建Agent
INFO:__main__:开始执行Agent流程
--- 流输出 ---
{'messages': [HumanMessage(content="你好,请介绍一下LangGraph")], 'intermediate_steps': []}
----------------------------------------
---思考节点(agent_node)---
决策:调用工具 knowledge_base
--- 流输出 ---
...
---行动节点(action)---
...
---思考节点(agent_node)---
决策:直接回答
--- 流输出 ---
...
INFO:__main__:Agent流程执行完成
```

## 项目结构详解

```
RAG-Agent/
├── src/rag_agent/        # 源代码
│   ├── core/             # 核心共享服务 (LLM提供商, 配置, 状态定义)
│   ├── tools/            # 所有可调用的工具 (知识库, 网络搜索, MCP工具)
│   ├── graphs/           # Agent工作流的"蓝图"定义
│   ├── nodes/            # 图中每个节点的具体业务逻辑
│   ├── factories/        # "总装车间"，负责组装所有组件并编译成可运行应用
│   ├── main.py           # (未来) FastAPI 服务入口，用于API部署
│   └── run.py            # 用于开发和调试的命令行启动脚本
├── tests/                # 测试代码
│   ├── unit/             # 单元测试
│   └── integration/      # 集成测试
├── tools/scripts/        # 工具脚本
├── docs/                 # 文档
├── data/                 # 数据文件
├── run_tests.py          # 测试运行器
└── PROJECT_STRUCTURE.md  # 项目结构说明
```

## 🛠️ 如何扩展

- **添加新工具**:
  1.  在 `tools/` 目录下创建一个新工具函数，并用 `@tool` 装饰器标记。
  2.  在 `tools/tool_registry.py` 的 `get_all_tools()` 函数中注册你的新工具。
  3.  工厂会自动将新工具注入代理，无需修改其他代码。

- **添加MCP工具**:
  1.  在 `tools/mcp_manifests/` 目录下创建YAML清单文件，定义API工具的参数、认证和执行方式。
  2.  支持多种认证方式：Bearer Token、API Key、Basic Auth等。
  3.  工具会自动加载并集成到代理中，支持完整的错误处理和SSRF防护。

- **修改工作流**:
  1.  打开 `graphs/base_agent_graph.py`。
  2.  您可以添加新的节点（`add_node`）或修改现有的边（`add_conditional_edges`）来改变代理的行为。

- **运行测试**:
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

## 许可

本项目采用 [MIT 许可](LICENSE)。
```