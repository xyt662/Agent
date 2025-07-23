#!/usr/bin/env python3
"""
认证功能测试脚本
测试MCP工具的认证支持功能
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

def test_bearer_token_auth():
    """测试Bearer Token认证"""
    print("=== 测试Bearer Token认证 ===")
    
    # 设置测试环境变量
    os.environ["GITHUB_TOKEN"] = "test_token_123"
    
    try:
        manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/github_api_example.yaml"
        adapter = MCPToolAdapter(str(manifest_path))
        
        # 测试认证头部准备
        headers = adapter._prepare_authentication_headers()
        print(f"生成的认证头部: {headers}")
        
        if 'Authorization' in headers and headers['Authorization'] == 'Bearer test_token_123':
            print("✅ Bearer Token认证头部生成正确")
        else:
            print("❌ Bearer Token认证头部生成错误")
            
    except Exception as e:
        print(f"❌ Bearer Token认证测试失败: {e}")
    finally:
        # 清理环境变量
        os.environ.pop("GITHUB_TOKEN", None)

def test_api_key_auth():
    """测试API Key认证"""
    print("\n=== 测试API Key认证 ===")
    
    # 设置测试环境变量
    os.environ["WEATHER_API_KEY"] = "test_api_key_456"
    
    try:
        manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/api_key_example.yaml"
        adapter = MCPToolAdapter(str(manifest_path))
        
        # 测试认证头部准备
        headers = adapter._prepare_authentication_headers()
        print(f"生成的认证头部: {headers}")
        
        if 'X-API-Key' in headers and headers['X-API-Key'] == 'test_api_key_456':
            print("✅ API Key认证头部生成正确")
        else:
            print("❌ API Key认证头部生成错误")
            
    except Exception as e:
        print(f"❌ API Key认证测试失败: {e}")
    finally:
        # 清理环境变量
        os.environ.pop("WEATHER_API_KEY", None)

def test_no_auth():
    """测试无认证情况"""
    print("\n=== 测试无认证情况 ===")
    
    try:
        manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/httpbin_tool_manifest.yaml"
        adapter = MCPToolAdapter(str(manifest_path))
        
        # 测试认证头部准备
        headers = adapter._prepare_authentication_headers()
        print(f"生成的认证头部: {headers}")
        
        if not headers:
            print("✅ 无认证配置时正确返回空头部")
        else:
            print("❌ 无认证配置时应返回空头部")
            
    except Exception as e:
        print(f"❌ 无认证测试失败: {e}")

def test_missing_env_var():
    """测试环境变量缺失情况"""
    print("\n=== 测试环境变量缺失情况 ===")
    
    try:
        manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/github_api_example.yaml"
        adapter = MCPToolAdapter(str(manifest_path))
        
        # 确保环境变量不存在
        os.environ.pop("GITHUB_TOKEN", None)
        
        # 测试认证头部准备
        headers = adapter._prepare_authentication_headers()
        print(f"生成的认证头部: {headers}")
        
        if not headers:
            print("✅ 环境变量缺失时正确返回空头部")
        else:
            print("❌ 环境变量缺失时应返回空头部")
            
    except Exception as e:
        print(f"❌ 环境变量缺失测试失败: {e}")

if __name__ == "__main__":
    print("开始认证功能测试...")
    test_bearer_token_auth()
    test_api_key_auth()
    test_no_auth()
    test_missing_env_var()
    print("\n测试完成！")