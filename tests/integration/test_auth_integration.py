#!/usr/bin/env python3
"""
认证集成测试脚本
测试带认证的实际API调用
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent  # 从tests/integration目录回到项目根目录
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from rag_agent.tools.mcp_adapter import MCPToolAdapter

def test_github_api_with_auth():
    """测试GitHub API（如果有token的话）"""
    print("=== 测试GitHub API认证调用 ===")
    
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("⚠️  GITHUB_TOKEN环境变量未设置，跳过GitHub API测试")
        print("   如需测试，请设置: export GITHUB_TOKEN=your_github_token")
        return
    
    try:
        manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/github_api_example.yaml"
        adapter = MCPToolAdapter(str(manifest_path))
        tool = adapter.to_langchain_tool()
        
        print(f"工具名称: {tool.name}")
        print(f"工具描述: {tool.description}")
        
        # 执行API调用
        result = tool.run({})
        print(f"✅ GitHub API调用成功")
        print(f"返回结果: {result[:200]}..." if len(result) > 200 else f"返回结果: {result}")
        
    except Exception as e:
        print(f"❌ GitHub API调用失败: {e}")

def test_httpbin_without_auth():
    """测试无认证的httpbin API"""
    print("\n=== 测试无认证API调用 ===")
    
    try:
        manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/httpbin_tool_manifest.yaml"
        adapter = MCPToolAdapter(str(manifest_path))
        tool = adapter.to_langchain_tool()
        
        print(f"工具名称: {tool.name}")
        print(f"工具描述: {tool.description}")
        
        # 执行API调用
        result = tool.run({})
        print(f"✅ httpbin API调用成功")
        print(f"返回结果: {result}")
        
    except Exception as e:
        print(f"❌ httpbin API调用失败: {e}")

def test_auth_header_generation():
    """测试认证头部生成（不实际调用API）"""
    print("\n=== 测试认证头部生成 ===")
    
    # 设置临时环境变量
    test_cases = [
        ("GITHUB_TOKEN", "test_github_token_123", "github_api_example.yaml"),
        ("WEATHER_API_KEY", "test_weather_key_456", "api_key_example.yaml")
    ]
    
    for env_var, test_value, manifest_file in test_cases:
        print(f"\n--- 测试 {manifest_file} ---")
        
        # 设置测试环境变量
        original_value = os.getenv(env_var)
        os.environ[env_var] = test_value
        
        try:
            manifest_path = project_root / f"src/rag_agent/tools/mcp_manifests/{manifest_file}"
            adapter = MCPToolAdapter(str(manifest_path))
            
            # 测试认证头部生成
            headers = adapter._prepare_authentication_headers()
            print(f"生成的认证头部: {headers}")
            
            if headers:
                print(f"✅ 成功生成认证头部")
            else:
                print(f"❌ 未生成认证头部")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
        finally:
            # 恢复原始环境变量
            if original_value:
                os.environ[env_var] = original_value
            else:
                os.environ.pop(env_var, None)

def show_available_manifests():
    """显示可用的清单文件"""
    print("\n=== 可用的清单文件 ===")
    
    manifests_dir = project_root / "src/rag_agent/tools/mcp_manifests"
    if manifests_dir.exists():
        for manifest_file in manifests_dir.glob("*.yaml"):
            print(f"📄 {manifest_file.name}")
            
            try:
                adapter = MCPToolAdapter(str(manifest_file))
                manifest_data = adapter.manifest_data
                
                name = manifest_data.get('name_for_model', 'Unknown')
                description = manifest_data.get('description_for_model', 'No description')
                auth_config = manifest_data.get('execution', {}).get('authentication')
                
                print(f"   名称: {name}")
                print(f"   描述: {description}")
                if auth_config:
                    auth_type = auth_config.get('type', 'Unknown')
                    env_var = auth_config.get('secret_env_variable', 'Unknown')
                    print(f"   认证: {auth_type} (环境变量: {env_var})")
                else:
                    print(f"   认证: 无")
                print()
                
            except Exception as e:
                print(f"   ❌ 解析失败: {e}")
                print()

if __name__ == "__main__":
    print("开始认证集成测试...")
    
    show_available_manifests()
    test_auth_header_generation()
    test_httpbin_without_auth()
    test_github_api_with_auth()
    
    print("\n测试完成！")
    print("\n💡 提示:")
    print("   - 要测试GitHub API，请设置 GITHUB_TOKEN 环境变量")
    print("   - 要测试其他API，请设置相应的环境变量")
    print("   - 所有密钥都应该存储在环境变量中，不要硬编码")