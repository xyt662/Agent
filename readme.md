
# RAG-Agent: 一个基于 LangGraph 的高级检索增强生成代理

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![LangChain](https://img.shields.io/badge/LangChain-LangGraph-orange)
![License](https://img.shields.io/badge/License-MIT-green)

RAG-Agent 是一个基于 LangChain 和 LangGraph 构建的、高度模块化和可扩展的检索增强生成 (Retrieval-Augmented Generation, RAG) 代理项目。它旨在作为一个健壮的框架，用于开发能够利用私有知识库和外部工具来智能回答问题的复杂代理。

项目已成功实现**Cursor模式的MCP（Model Context Protocol）集成**，通过本地MCP服务器提供强大的工具调用能力，支持百度地图、Tavily搜索等多种工具包。

这个项目的核心设计哲学是**关注点分离**和**依赖注入**，使得每个组件（如LLM、工具、图结构）都高度解耦，易于测试、替换和扩展。

## ✨ 项目特性

- **模块化架构**: 清晰的目录结构，将图的定义、节点逻辑、工具、核心服务和工厂组装完全分离
- **ReAct 代理**: 实现了一个基础的 "Reason-Act" (ReAct) 工作流，使代理能够思考、调用工具并根据结果进行下一步行动
- **Cursor模式MCP集成**: 基于MCP官方Python SDK，通过stdio与本地MCP服务器进程通信
- **丰富的工具生态**: 支持百度地图、Tavily搜索等多种MCP工具包，可通过npm、Python等方式安装
- **异步优先设计**: 完全异步的工具调用和生命周期管理，提供高性能的并发处理能力
- **智能资源管理**: 自动管理MCP服务器子进程的启动、通信和清理
- **可配置的工作流**: `graphs` 目录下的蓝图设计允许开发者轻松定义或修改代理的工作流程
- **工程化实践**:
    - 使用工厂模式进行依赖注入和应用组装
    - 通过 `.env` 文件管理敏感信息和配置
    - 使用 `lru_cache` 缓存编译好的代理实例，提高性能
    - 完善的测试覆盖和错误处理机制

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
  打开 `.env` 文件，并填入您的大语言模型和MCP工具的 API 密钥。
  ```
  # .env
  DEEPSEEK_API_KEY="sk-your-api-key-here"
  
  # MCP工具API密钥
  BAIDU_MAP_API_KEY="your-baidu-map-api-key"
  TAVILY_API_KEY="your-tavily-api-key"
  ```

### 3. 构建知识库 (可选)

如果需要使用私有知识库检索功能，请将您的原始文档（如 `internal_docs.txt`）放入 `data/raw/` 目录。然后，运行知识库构建脚本（您可能需要自行创建此脚本，例如 `build_vectorstore.py`）来生成向量数据库。

### 4. 运行代理

本项目提供了一个简单的命令行运行脚本，用于快速测试代理的MCP工具功能。

```bash
# 在项目根目录下运行
python run.py
```

您应该能看到类似以下的日志输出，展示了代理加载MCP工具并执行路线规划的完整流程：

```
INFO:rag_agent.tools.tool_manager:正在加载MCP工具包: tavily_mcp
INFO:rag_agent.tools.tool_manager:正在加载MCP工具包: baidu_map
INFO:rag_agent.tools.tool_manager:成功注册了 14 个MCP工具
INFO:__main__:成功创建Agent
INFO:__main__:开始执行Agent流程
--- 流输出 ---
{'messages': [HumanMessage(content="请你使用百度mcp工具搜索规划一下从上海去北京的路线")]}
----------------------------------------
---思考节点(agent_node)---
决策:调用工具 map_geocode
--- 流输出 ---
...
---行动节点(action)---
调用工具: map_geocode
--- 流输出 ---
...
---思考节点(agent_node)---
决策:调用工具 map_driving_route
--- 流输出 ---
...
INFO:__main__:Agent流程执行完成
```

## 项目结构详解

```
RAG-Agent/
├── src/rag_agent/        # 源代码
│   ├── core/             # 核心共享服务 (LLM提供商, 配置, 状态定义)
│   ├── tools/            # 所有可调用的工具 (知识库, MCP工具)
│   │   ├── local_command_adapter.py  # 本地命令MCP适配器
│   │   ├── tool_manager.py           # MCP工具包管理器
│   │   └── tool_registry.py          # 工具注册表
│   ├── graphs/           # Agent工作流的"蓝图"定义
│   ├── nodes/            # 图中每个节点的具体业务逻辑
│   ├── factories/        # "总装车间"，负责组装所有组件并编译成可运行应用
│   └── main.py           # (未来) FastAPI 服务入口，用于API部署
├── tests/                # 测试代码
│   ├── test_*.py         # MCP工具功能测试
│   ├── unit/             # 单元测试
│   └── integration/      # 集成测试
├── tools/scripts/        # 工具脚本
├── docs/                 # 文档
├── data/                 # 数据文件
├── tools.config.json     # MCP工具配置文件
├── run.py                # 命令行启动脚本
├── run_tests.py          # 测试运行器
└── PROJECT_STRUCTURE.md  # 项目结构说明
```

## 🛠️ 如何扩展

- **添加新的MCP工具包**:
  1.  在 `tools.config.json` 中添加新的MCP服务器配置：
      ```json
      {
        "mcpServers": {
          "my_tool": {
            "command": "npx",
            "args": ["-y", "my-mcp-package@latest"],
            "env": {
              "API_KEY": "${MY_API_KEY}"
            },
            "disabled": false
          }
        }
      }
      ```
  2.  在 `.env` 文件中添加相应的环境变量。
  3.  工具会自动加载并集成到代理中。

- **添加传统工具**:
  1.  在 `tools/` 目录下创建一个新工具函数，并用 `@tool` 装饰器标记。
  2.  在 `tools/tool_registry.py` 的 `get_all_tools()` 函数中注册你的新工具。
  3.  工厂会自动将新工具注入代理，无需修改其他代码。

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