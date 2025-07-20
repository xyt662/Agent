# RAG Agent 项目

基于 LangGraph 的智能问答 Agent，支持多跳查询、主动澄清和外部 API 集成。

## 项目结构

````


## 开发计划

### 第一周：基础框架搭建与核心工具集成
- **任务 1.1**: Agent框架选型与环境搭建 (2天)
- **任务 1.2**: 封装核心工具 — "知识库检索" (1天)

### 第二周：增强Agent的推理与交互能力
- **任务 2.1**: 实现多跳查询（Multi-hop）能力验证 (3天)
- **任务 2.2**: 实现主动澄清式交互 (2天)

### 第三周：集成外部能力与健壮性提升
- **任务 3.1**: 集成真实外部API工具 — "网络搜索" (2天)
- **任务 3.2**: Agent自我纠错能力与错误处理 (3天)

## 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
````

2. 配置环境变量：

```bash
cp config/settings.py.example config/settings.py
# 编辑 settings.py 添加必要的API密钥
```

3. 运行 Hello World 示例：

```bash
python week1_foundation/hello_world_agent.py
```

## 技术栈

- **框架**: LangChain
- **监控**: LangSmith
- **搜索**: Tavily Search API
- **向量数据库**: (根据现有 RAG 系统)
- **语言模型**: (根据现有配置)
