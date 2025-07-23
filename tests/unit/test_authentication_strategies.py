#!/usr/bin/env python3
"""
测试认证策略重构后的功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent  # 从tests/unit目录回到项目根目录
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from rag_agent.tools.mcp_adapter import MCPToolAdapter
from rag_agent.tools.authentication_strategies import authentication_registry

def test_strategy_registry():
    """测试策略注册表"""
    print("=== 测试策略注册表 ===")
    
    strategies = authentication_registry.list_strategies()
    print(f"可用的认证策略: {strategies}")
    
    expected_strategies = ['bearer_token', 'api_key_in_header', 'basic_auth']
    for strategy in expected_strategies:
        if strategy in strategies:
            print(f"✅ {strategy} 策略已注册")
        else:
            print(f"❌ {strategy} 策略未注册")

def test_bearer_token_strategy():
    """测试Bearer Token策略"""
    print("\n=== 测试Bearer Token策略 ===")
    
    # 设置测试环境变量
    os.environ["GITHUB_TOKEN"] = "test_token_123"
    
    try:
        manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/github_api_example.yaml"
        adapter = MCPToolAdapter(str(manifest_path))
        headers = adapter._prepare_authentication_headers()
        
        print(f"生成的认证头部: {headers}")
        
        if 'Authorization' in headers and headers['Authorization'] == 'Bearer test_token_123':
            print("✅ Bearer Token策略工作正常")
        else:
            print("❌ Bearer Token策略工作异常")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        os.environ.pop("GITHUB_TOKEN", None)

def test_api_key_strategy():
    """测试API Key策略"""
    print("\n=== 测试API Key策略 ===")
    
    # 设置测试环境变量
    os.environ["WEATHER_API_KEY"] = "test_api_key_456"
    
    try:
        manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/api_key_example.yaml"
        adapter = MCPToolAdapter(str(manifest_path))
        headers = adapter._prepare_authentication_headers()
        
        print(f"生成的认证头部: {headers}")
        
        if 'X-API-Key' in headers and headers['X-API-Key'] == 'test_api_key_456':
            print("✅ API Key策略工作正常")
        else:
            print("❌ API Key策略工作异常")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        os.environ.pop("WEATHER_API_KEY", None)

def test_basic_auth_strategy():
    """测试Basic Auth策略"""
    print("\n=== 测试Basic Auth策略 ===")
    
    # 设置测试环境变量
    os.environ["BASIC_AUTH_USERNAME"] = "testuser"
    os.environ["BASIC_AUTH_PASSWORD"] = "testpass"
    
    try:
        manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/basic_auth_example.yaml"
        adapter = MCPToolAdapter(str(manifest_path))
        headers = adapter._prepare_authentication_headers()
        
        print(f"生成的认证头部: {headers}")
        
        if 'Authorization' in headers and headers['Authorization'].startswith('Basic '):
            print("✅ Basic Auth策略工作正常")
            # 验证编码是否正确
            import base64
            expected_credentials = base64.b64encode("testuser:testpass".encode()).decode()
            expected_header = f"Basic {expected_credentials}"
            if headers['Authorization'] == expected_header:
                print("✅ Basic Auth编码正确")
            else:
                print("❌ Basic Auth编码错误")
        else:
            print("❌ Basic Auth策略工作异常")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        os.environ.pop("BASIC_AUTH_USERNAME", None)
        os.environ.pop("BASIC_AUTH_PASSWORD", None)

def test_unsupported_auth_type():
    """测试不支持的认证类型"""
    print("\n=== 测试不支持的认证类型 ===")
    
    # 创建临时清单文件
    manifest_content = """# 测试清单文件
spec_version: 1.0
name_for_model: "test_unsupported_auth"
description_for_model: "测试不支持认证类型的工具"

input_schema:
  type: "object"
  properties: {}

execution:
  type: "http_request"
  url: "https://httpbin.org/get"
  method: "GET"
  parameter_mapping: {}
  authentication:
    type: "oauth2"
    client_id: "test_client"
"""

    
    manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/temp_unsupported_auth.yaml"
    
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        
        adapter = MCPToolAdapter(str(manifest_path))
        headers = adapter._prepare_authentication_headers()
        
        print(f"生成的认证头部: {headers}")
        
        if not headers:  # 应该返回空字典
            print("✅ 不支持的认证类型处理正确")
        else:
            print("❌ 不支持的认证类型处理异常")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        if manifest_path.exists():
            manifest_path.unlink()

def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n=== 测试向后兼容性 ===")
    
    # 测试现有的认证功能是否仍然工作
    os.environ["GITHUB_TOKEN"] = "test_github_token"
    
    try:
        manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/github_api_example.yaml"
        adapter = MCPToolAdapter(str(manifest_path))
        tool = adapter.to_langchain_tool()
        
        # 检查工具是否能正常创建
        if tool:
            print("✅ 向后兼容性测试通过 - 工具创建成功")
        else:
            print("❌ 向后兼容性测试失败 - 工具创建失败")
            
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {e}")
    finally:
        os.environ.pop("GITHUB_TOKEN", None)

if __name__ == "__main__":
    print("开始认证策略重构测试...")
    print("这些测试验证策略模式重构后的认证功能是否正常工作\n")
    
    test_strategy_registry()
    test_bearer_token_strategy()
    test_api_key_strategy()
    test_basic_auth_strategy()
    test_unsupported_auth_type()
    test_backward_compatibility()
    
    print("\n测试完成！")
    print("\n💡 策略模式优势:")
    print("   - 符合开闭原则：新增认证方式无需修改核心代码")
    print("   - 代码更清晰：每种认证方式独立实现")
    print("   - 易于扩展：只需创建新策略类并注册")
    print("   - 易于测试：每个策略可独立测试")