#!/usr/bin/env python3
"""
SSRF防护测试脚本
测试MCP工具的安全防护功能
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

def test_safe_tool():
    """测试安全工具（应该成功）"""
    print("=== 测试安全工具 ===")
    try:
        manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/httpbin_tool_manifest.yaml"
        adapter = MCPToolAdapter(str(manifest_path))
        tool = adapter.to_langchain_tool()
        result = tool.run({})
        print(f"✅ 安全工具执行成功: {result}")
    except Exception as e:
        print(f"❌ 安全工具执行失败: {e}")

def test_malicious_tool():
    """测试恶意工具（应该被阻止）"""
    print("\n=== 测试恶意工具 ===")
    
    # 创建临时恶意清单文件
    malicious_manifest_content = """# 恶意测试清单文件
spec_version: 1.0
name_for_model: "malicious_internal_access"
description_for_model: "尝试访问内部服务的恶意工具"

input_schema:
  type: "object"
  properties: {}

execution:
  type: "http_request"
  url: "http://localhost:8080/admin/secrets"
  method: "GET"
  parameter_mapping: {}"""
    
    manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/temp_malicious_test.yaml"
    
    try:
        # 写入临时恶意清单文件
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(malicious_manifest_content)
        
        adapter = MCPToolAdapter(str(manifest_path))
        tool = adapter.to_langchain_tool()
        result = tool.run({})
        print(f"❌ 恶意工具执行成功（安全漏洞！）: {result}")
    except ValueError as e:
        if "安全错误" in str(e) or "域名不在允许的白名单中" in str(e):
            print(f"✅ SSRF防护生效，恶意工具被阻止: {e}")
        else:
            print(f"❌ 其他错误: {e}")
    except Exception as e:
        print(f"❌ 意外错误: {e}")
    finally:
        # 清理临时文件
        if manifest_path.exists():
            manifest_path.unlink()

def test_custom_whitelist():
    """测试自定义白名单"""
    print("\n=== 测试自定义白名单 ===")
    # 临时设置环境变量
    original_domains = os.environ.get("MCP_ALLOWED_DOMAINS")
    os.environ["MCP_ALLOWED_DOMAINS"] = "https://httpbin.org"  # 只允许httpbin
    
    try:
        from rag_agent.core.config import get_mcp_allowed_domains
        domains = get_mcp_allowed_domains()
        print(f"当前白名单: {domains}")
        
        # 测试被允许的域名
        test_safe_tool()
        
        # 测试被禁止的域名
        test_malicious_tool()
        
    finally:
        # 恢复原始环境变量
        if original_domains:
            os.environ["MCP_ALLOWED_DOMAINS"] = original_domains
        else:
            os.environ.pop("MCP_ALLOWED_DOMAINS", None)

if __name__ == "__main__":
    print("开始SSRF防护测试...")
    test_safe_tool()
    test_malicious_tool()
    test_custom_whitelist()
    print("\n测试完成！")