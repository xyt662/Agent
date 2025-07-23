#!/usr/bin/env python3
"""
HTTP错误处理综合测试
测试MCP工具的完整HTTP错误处理功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent  # 从tests/unit目录回到项目根目录
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from rag_agent.tools.mcp_adapter import MCPToolAdapter

def create_test_manifest(url, auth_required=False):
    """创建测试清单文件"""
    if auth_required:
        manifest_content = f"""# 测试清单文件
spec_version: 1.0
name_for_model: "test_http_error"
description_for_model: "测试HTTP错误处理的工具"

input_schema:
  type: "object"
  properties: {{}}

execution:
  type: "http_request"
  url: "{url}"
  method: "GET"
  parameter_mapping: {{}}
  authentication:
    type: "bearer_token"
    secret_env_variable: "TEST_TOKEN"""
    else:
        manifest_content = f"""# 测试清单文件
spec_version: 1.0
name_for_model: "test_http_error"
description_for_model: "测试HTTP错误处理的工具"

input_schema:
  type: "object"
  properties: {{}}

execution:
  type: "http_request"
  url: "{url}"
  method: "GET"
  parameter_mapping: {{}}"""
    
    return manifest_content

def test_401_error():
    """测试401认证错误"""
    print("=== 测试401 Unauthorized错误 ===")
    
    # 创建访问需要认证端点的清单（不提供认证信息）
    manifest_content = create_test_manifest("https://httpbin.org/status/401", auth_required=False)
    manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/temp_401_test.yaml"
    
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        
        adapter = MCPToolAdapter(str(manifest_path))
        tool = adapter.to_langchain_tool()
        result = tool.run({})
        
        print(f"返回结果: {result}")
        
        if "HTTP 401" in result and "认证密钥" in result:
            print("✅ 401错误处理正确，提供了认证密钥检查建议")
        else:
            print("❌ 401错误处理不正确")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        if manifest_path.exists():
            manifest_path.unlink()

def test_403_error():
    """测试403 Forbidden错误"""
    print("\n=== 测试403 Forbidden错误 ===")
    
    # 创建访问被禁止端点的清单
    manifest_content = create_test_manifest("https://httpbin.org/status/403")
    manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/temp_403_test.yaml"
    
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        
        adapter = MCPToolAdapter(str(manifest_path))
        tool = adapter.to_langchain_tool()
        result = tool.run({})
        
        print(f"返回结果: {result}")
        
        if "HTTP 403" in result and "认证密钥" in result:
            print("✅ 403错误处理正确，提供了认证密钥检查建议")
        else:
            print("❌ 403错误处理不正确")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        if manifest_path.exists():
            manifest_path.unlink()

def test_404_error():
    """测试404错误"""
    print("\n=== 测试404 Not Found错误 ===")
    
    # 创建指向不存在页面的清单
    manifest_content = create_test_manifest("https://httpbin.org/status/404")
    manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/temp_404_test.yaml"
    
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        
        adapter = MCPToolAdapter(str(manifest_path))
        tool = adapter.to_langchain_tool()
        result = tool.run({})
        
        print(f"返回结果: {result}")
        
        if "HTTP 404" in result and "URL配置" in result:
            print("✅ 404错误处理正确，提供了URL配置检查建议")
        else:
            print("❌ 404错误处理不正确")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        if manifest_path.exists():
            manifest_path.unlink()

def test_429_rate_limit():
    """测试429频率限制错误"""
    print("\n=== 测试429 Rate Limit错误 ===")
    
    # 创建返回429状态的清单
    manifest_content = create_test_manifest("https://httpbin.org/status/429")
    manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/temp_429_test.yaml"
    
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        
        adapter = MCPToolAdapter(str(manifest_path))
        tool = adapter.to_langchain_tool()
        result = tool.run({})
        
        print(f"返回结果: {result}")
        
        if "HTTP 429" in result and "频率超限" in result:
            print("✅ 429错误处理正确，提供了频率限制建议")
        else:
            print("❌ 429错误处理不正确")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        if manifest_path.exists():
            manifest_path.unlink()

def test_500_server_error():
    """测试500服务器错误"""
    print("\n=== 测试500 Server Error错误 ===")
    
    # 创建返回500状态的清单
    manifest_content = create_test_manifest("https://httpbin.org/status/500")
    manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/temp_500_test.yaml"
    
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        
        adapter = MCPToolAdapter(str(manifest_path))
        tool = adapter.to_langchain_tool()
        result = tool.run({})
        
        print(f"返回结果: {result}")
        
        if "HTTP 500" in result and "服务器内部错误" in result:
            print("✅ 500错误处理正确，提供了服务器错误建议")
        else:
            print("❌ 500错误处理不正确")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        if manifest_path.exists():
            manifest_path.unlink()

def test_timeout_error():
    """测试超时错误"""
    print("\n=== 测试超时错误 ===")
    
    # 创建会超时的请求（httpbin的delay端点会延迟响应）
    manifest_content = create_test_manifest("https://httpbin.org/delay/15")  # 15秒延迟，会超过10秒超时
    manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/temp_timeout_test.yaml"
    
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        
        adapter = MCPToolAdapter(str(manifest_path))
        tool = adapter.to_langchain_tool()
        result = tool.run({})
        
        print(f"返回结果: {result}")
        
        if "无法连接到服务器" in result or "timeout" in result.lower():
            print("✅ 超时错误处理正确")
        else:
            print("❌ 超时错误处理不正确")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        if manifest_path.exists():
            manifest_path.unlink()

def test_successful_request():
    """测试成功请求（对比）"""
    print("=== 测试成功请求（对比） ===")
    
    try:
        manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/httpbin_tool_manifest.yaml"
        adapter = MCPToolAdapter(str(manifest_path))
        tool = adapter.to_langchain_tool()
        result = tool.run({})
        
        print(f"返回结果: {result}")
        
        if "origin" in result:
            print("✅ 成功请求正常工作")
        else:
            print("❌ 成功请求异常")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("开始HTTP错误处理综合测试...")
    print("注意：这些测试会故意触发各种HTTP错误来验证错误处理逻辑")
    print()
    
    test_successful_request()
    test_401_error()
    test_403_error()
    test_404_error()
    test_429_rate_limit()
    test_500_server_error()
    test_timeout_error()
    
    print("\n测试完成！")
    print("\n💡 错误处理改进:")
    print("   - 401/403: 提示检查认证密钥")
    print("   - 404: 提示检查URL配置")
    print("   - 429: 提示API频率限制")
    print("   - 500+: 提示服务器错误")
    print("   - 连接错误: 提示网络连接问题")