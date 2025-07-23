# 项目结构说明

## 📁 目录结构

```
RAG-Agent/
├── src/                    # 源代码
│   └── rag_agent/
│       ├── core/           # 核心服务
│       ├── tools/          # 工具模块
│       ├── graphs/         # 图结构定义
│       ├── nodes/          # 节点逻辑
│       ├── factories/      # 工厂模式组装
│       └── retrieval/      # 检索模块
├── tests/                  # 测试代码
│   ├── unit/              # 单元测试
│   └── integration/       # 集成测试
├── tools/                  # 工具和脚本
│   └── scripts/           # 实用脚本
├── docs/                   # 文档
├── data/                   # 数据文件
├── vector_store/          # 向量存储
└── run_tests.py           # 测试运行器
```

## 🧪 测试结构

### 单元测试 (`tests/unit/`)
- `test_authentication.py` - 认证功能测试
- `test_authentication_strategies.py` - 认证策略模式测试
- `test_pydantic_schema.py` - Pydantic模型创建测试
- `test_ssrf_protection.py` - SSRF防护测试
- `test_http_error_handling.py` - HTTP错误处理综合测试

### 集成测试 (`tests/integration/`)
- `test_auth_integration.py` - 认证集成测试

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

### 🔄 从旧结构迁移

**旧结构问题:**
- `scripts/` 目录混合了功能脚本和测试脚本
- 测试文件分散，难以管理
- 存在冗余的测试文件（如 `test_403_error.py` 和 `test_http_error_handling.py`）

**新结构优势:**
- **关注点分离**: 测试、工具、源码完全分离
- **功能分类**: 单元测试和集成测试分开管理
- **消除冗余**: 合并相关测试文件，减少维护成本
- **标准化**: 遵循Python项目标准结构
- **易于扩展**: 清晰的目录结构便于添加新测试和工具

### 🎯 设计原则

1. **单一职责**: 每个目录有明确的职责
2. **可测试性**: 测试代码与业务代码分离
3. **可维护性**: 相关功能集中管理
4. **可扩展性**: 便于添加新的测试和工具
5. **标准化**: 遵循Python社区最佳实践

## 📝 开发指南

### 添加新测试
1. **单元测试**: 在 `tests/unit/` 下创建 `test_*.py` 文件
2. **集成测试**: 在 `tests/integration/` 下创建 `test_*.py` 文件
3. 确保测试文件包含适当的路径设置以导入项目模块

### 添加新工具
1. 在 `tools/scripts/` 下创建脚本文件
2. 添加适当的文档字符串说明功能
3. 在 `run_tests.py` 的 `run_utility_scripts()` 函数中注册新脚本

### 最佳实践
- 保持测试文件的独立性
- 使用描述性的测试函数名
- 为每个测试添加适当的清理逻辑
- 在测试中使用临时文件，避免污染项目目录