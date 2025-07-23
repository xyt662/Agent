# MCP工具集成使用指南

## 概述

本项目已成功集成MCP（Model Context Protocol）工具适配器，允许通过YAML清单文件动态加载外部工具。

## 功能特性

- ✅ **声明式配置**：通过YAML文件定义工具
- ✅ **动态加载**：自动扫描并加载MCP工具
- ✅ **零侵入性**：不影响现有工具系统
- ✅ **HTTP支持**：支持GET/POST等HTTP请求
- ✅ **参数映射**：灵活的参数转换机制
- ✅ **错误处理**：完善的异常处理和日志记录
- 🔒 **SSRF防护**：域名白名单机制防止服务器端请求伪造攻击
- 🔐 **认证支持**：支持Bearer Token和API Key等多种认证方式

## 目录结构

```
src/rag_agent/tools/
├── mcp_adapter.py              # MCP适配器核心实现
├── mcp_manifests/              # MCP工具清单目录
│   └── httpbin_tool_manifest.yaml  # 示例工具清单
└── tool_registry.py            # 工具注册表（已集成MCP支持）
```

## 使用方法

### 1. 创建工具清单

在 `src/rag_agent/tools/mcp_manifests/` 目录下创建YAML文件：

```yaml
# my_tool_manifest.yaml
spec_version: 1.0
name_for_model: "my_custom_tool"
description_for_model: "工具描述"

input_schema:
  type: "object"
  properties:
    param1:
      type: "string"
      description: "参数1描述"
    param2:
      type: "integer"
      description: "参数2描述"
  required: ["param1"]

execution:
  type: "http_request"
  url: "https://api.example.com/endpoint"
  method: "POST"
  parameter_mapping:
    param1: "api_param1"
    param2: "api_param2"
```

### 2. 配置环境变量（可选）

```bash
# 启用/禁用MCP工具
export MCP_ENABLED=true

# 自定义清单目录路径
export MCP_MANIFESTS_DIR="/path/to/your/manifests"

# 配置允许访问的域名白名单（SSRF防护）
export MCP_ALLOWED_DOMAINS="https://httpbin.org,https://api.github.com,https://api.weather.com"
```

### 3. 运行测试

```bash
python run.py
```

## 示例工具

项目包含一个示例工具 `get_my_public_ip`，演示如何：
- 定义无参数工具
- 调用外部HTTP API
- 返回JSON结果

## 测试结果

✅ **RAG知识库查询测试**：成功检索LangGraph相关信息  
✅ **MCP工具测试**：成功调用httpbin API获取公网IP  
✅ **工具集成测试**：MCP工具与现有工具系统完美协作  
✅ **SSRF防护测试**：恶意URL请求被成功阻止

## 安全特性

### SSRF（服务器端请求伪造）防护

为了防止恶意清单文件攻击内部网络服务，系统实现了严格的域名白名单机制：

**防护机制**：
- 🔍 **URL解析验证**：自动解析清单中的URL并提取域名
- 🛡️ **白名单检查**：只允许访问预配置的可信域名
- 🚫 **恶意请求阻止**：拒绝访问内网地址（如localhost、127.0.0.1、169.254.169.254等）
- 📝 **详细日志记录**：记录所有安全检查和拒绝访问的详细信息

**默认白名单**：
- `https://httpbin.org` - HTTP测试服务
- `https://api.github.com` - GitHub API
- `https://jsonplaceholder.typicode.com` - JSON测试API

**自定义配置**：
```bash
# 设置自定义域名白名单
export MCP_ALLOWED_DOMAINS="https://your-api.com,https://trusted-service.org"
```

**安全测试**：
```bash
# 运行SSRF防护测试
python test_ssrf_protection.py
```

## 认证功能

MCP工具采用**策略模式**实现认证功能，支持多种认证方式，并且易于扩展新的认证类型。

### 架构设计

认证功能基于策略模式设计，具有以下优势：
- **符合开闭原则**：新增认证方式无需修改核心代码
- **代码清晰**：每种认证方式独立实现
- **易于扩展**：只需创建新策略类并注册
- **易于测试**：每个策略可独立测试

### 支持的认证方式

#### 1. Bearer Token认证

适用于需要Bearer Token的API（如GitHub API、许多REST API）：

```yaml
execution:
  type: "http_request"
  url: "https://api.github.com/users/octocat"
  method: "GET"
  authentication:
    type: "bearer_token"
    secret_env_variable: "GITHUB_TOKEN"
```

#### 2. API Key认证

适用于需要在请求头中传递API Key的服务：

```yaml
execution:
  type: "http_request"
  url: "https://api.example.com/data"
  method: "GET"
  authentication:
    type: "api_key_in_header"
    header_name: "X-API-Key"  # 可选，默认为X-API-Key
    secret_env_variable: "EXAMPLE_API_KEY"
```

#### 3. Basic Auth认证

适用于需要用户名密码的基础认证：

```yaml
execution:
  type: "http_request"
  url: "https://httpbin.org/basic-auth/user/pass"
  method: "GET"
  authentication:
    type: "basic_auth"
    username_env_variable: "BASIC_AUTH_USERNAME"
    password_env_variable: "BASIC_AUTH_PASSWORD"
```

### 环境变量配置

在`.env`文件或系统环境变量中设置API密钥：

```bash
# GitHub API Token
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# 其他API密钥
WEATHER_API_KEY=your_weather_api_key_here
EXAMPLE_API_KEY=your_example_api_key_here
```

### 安全特性

- **环境变量存储**: 密钥存储在环境变量中，不会硬编码在配置文件中
- **自动头部生成**: 根据认证类型自动生成正确的HTTP头部
- **错误处理**: 当环境变量缺失时优雅降级，记录警告日志
- **调试支持**: 提供详细的认证过程日志（不包含敏感信息）

### 扩展新的认证策略

如需添加新的认证方式（如OAuth2），只需：

1. **创建策略类**：

```python
from .authentication_strategies import AuthenticationStrategy

class OAuth2Strategy(AuthenticationStrategy):
    def apply(self, auth_config: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, str]:
        # 实现OAuth2认证逻辑
        access_token = self._get_oauth2_token(auth_config)
        headers['Authorization'] = f'Bearer {access_token}'
        return headers
    
    def get_strategy_name(self) -> str:
        return "oauth2"
```

2. **注册策略**：

```python
from .authentication_strategies import authentication_registry

authentication_registry.register(OAuth2Strategy())
```

3. **在清单文件中使用**：

```yaml
authentication:
  type: "oauth2"
  client_id_env_variable: "OAUTH2_CLIENT_ID"
  client_secret_env_variable: "OAUTH2_CLIENT_SECRET"
```

### 认证测试

运行认证功能测试：

```bash
python scripts/test_authentication.py
python scripts/test_auth_integration.py
python scripts/test_authentication_strategies.py  # 策略模式测试
```

## 技术实现

### 核心组件

1. **MCPToolAdapter**：YAML解析和LangChain工具转换
2. **动态模型生成**：基于input_schema自动创建Pydantic模型
3. **HTTP执行器**：支持多种HTTP方法和参数映射
4. **工具注册集成**：无缝集成到现有工具系统

### 架构优势

- **模块化设计**：独立的适配器模块
- **配置驱动**：通过配置文件控制行为
- **扩展性强**：易于添加新的执行类型
- **向后兼容**：不影响现有功能

## 下一步计划

- [ ] 支持更多执行类型（Shell命令、Python函数等）
- [ ] 添加工具版本管理
- [ ] 实现工具依赖检查
- [ ] 支持工具热重载

---

**开发完成时间**：2024年
**状态**：✅ Phase 1 完成