#!/usr/bin/env python3
"""
工具包管理器演示脚本

展示如何使用新的工具包管理器来管理和使用 MCP 工具
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from rag_agent.tools.tool_manager import get_tool_manager
from rag_agent.tools.tool_registry import get_all_tools


def main():
    """演示工具包管理器的功能"""
    print("🚀 工具包管理器演示")
    print("=" * 50)
    
    # 1. 获取工具包管理器实例
    print("\n📦 1. 初始化工具包管理器")
    manager = get_tool_manager()
    print(f"✓ 配置文件: {manager.config_file}")
    print(f"✓ 管理器已初始化")
    
    # 2. 查看所有可用工具包
    print("\n📋 2. 查看所有可用工具包")
    all_tools = manager.list_available_tools()
    print(f"总共发现 {len(all_tools)} 个工具包:")
    
    for tool_name in all_tools:
        package = manager.get_package_info(tool_name)
        status = "✅ 启用" if package.enabled else "❌ 禁用"
        print(f"  - {tool_name}: {package.package_source} ({status})")
    
    # 3. 查看已启用的工具
    print("\n🔧 3. 查看已启用的工具")
    enabled_tools = manager.list_enabled_tools()
    print(f"已启用 {len(enabled_tools)} 个工具:")
    
    for tool_name in enabled_tools:
        package = manager.get_package_info(tool_name)
        print(f"  ✅ {tool_name}: {package.source_identifier}")
        
        # 显示配置信息
        if package.config:
            print(f"     配置: {list(package.config.keys())}")
    
    # 4. 获取工具清单文件
    print("\n📄 4. 获取工具清单文件")
    manifests = manager.get_enabled_tool_manifests()
    print(f"已处理 {len(manifests)} 个清单文件:")
    
    for tool_name, manifest_path in manifests:
        exists = "✓" if manifest_path.exists() else "✗"
        print(f"  {exists} {tool_name}: {manifest_path}")
    
    # 5. 演示环境变量解析
    print("\n🔑 5. 演示环境变量解析")
    test_config = {
        "API_KEY": "${TAVILY_API_KEY}",
        "STATIC_VALUE": "hello",
        "MISSING_VAR": "${MISSING_VAR}"
    }
    
    resolved_config = manager._resolve_env_variables(test_config)
    print("原始配置:", test_config)
    print("解析结果:", resolved_config)
    
    # 6. 获取实际的 LangChain 工具
    print("\n🛠️ 6. 获取实际的 LangChain 工具")
    tools = get_all_tools()
    print(f"已注册 {len(tools)} 个 LangChain 工具:")
    
    for tool in tools:
        tool_name = tool.name or "未命名工具"
        tool_desc = (tool.description or "无描述")[:80]
        print(f"  🔧 {tool_name}: {tool_desc}...")
    
    # 7. 演示工具状态查询
    print("\n📊 7. 工具状态统计")
    total_tools = len(all_tools)
    enabled_count = len(enabled_tools)
    disabled_count = total_tools - enabled_count
    
    print(f"总工具数: {total_tools}")
    print(f"已启用: {enabled_count} ({enabled_count/total_tools*100:.1f}%)")
    print(f"已禁用: {disabled_count} ({disabled_count/total_tools*100:.1f}%)")
    
    # 8. 按来源分类工具
    print("\n🏷️ 8. 按来源分类工具")
    source_stats = {}
    
    for tool_name in all_tools:
        package = manager.get_package_info(tool_name)
        source_type = package.source_type
        
        if source_type not in source_stats:
            source_stats[source_type] = []
        source_stats[source_type].append(tool_name)
    
    for source_type, tools_list in source_stats.items():
        print(f"  📁 {source_type}: {len(tools_list)} 个工具")
        for tool_name in tools_list:
            package = manager.get_package_info(tool_name)
            status = "✅" if package.enabled else "❌"
            print(f"    {status} {tool_name}")
    
    # 9. 演示工具功能（如果有可用的工具）
    print("\n🎯 9. 演示工具功能")
    
    # 查找可以无需API密钥使用的工具
    usable_tools = []
    for tool in tools:
        tool_name = tool.name or "未命名"
        if any(keyword in tool_name.lower() for keyword in ["httpbin", "ip", "knowledge"]):
            usable_tools.append(tool)
    
    if usable_tools:
        print(f"找到 {len(usable_tools)} 个可直接使用的工具:")
        
        for tool in usable_tools[:2]:  # 只演示前2个工具
            tool_name = tool.name or "未命名工具"
            print(f"\n  🔧 测试工具: {tool_name}")
            
            try:
                if "ip" in tool_name.lower():
                    result = tool.invoke({})
                elif "knowledge" in tool_name.lower():
                    result = tool.invoke({"query": "什么是MCP工具?"})
                elif "httpbin" in tool_name.lower():
                    result = tool.invoke({"method": "GET", "endpoint": "/ip"})
                else:
                    result = "跳过测试"
                
                print(f"    ✓ 执行成功: {str(result)[:100]}...")
                
            except Exception as e:
                print(f"    ✗ 执行失败: {e}")
    else:
        print("  ℹ️ 没有找到可直接使用的工具")
    
    # 10. 配置建议
    print("\n💡 10. 配置建议")
    
    missing_env_vars = []
    for tool_name in enabled_tools:
        package = manager.get_package_info(tool_name)
        if package.config:
            for key, value in package.config.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    if not os.getenv(env_var):
                        missing_env_vars.append((tool_name, env_var))
    
    if missing_env_vars:
        print("  ⚠️ 以下环境变量未设置，相关工具可能无法正常工作:")
        for tool_name, env_var in missing_env_vars:
            print(f"    - {env_var} (用于 {tool_name})")
        print("\n  💡 请在 .env 文件中设置这些环境变量")
    else:
        print("  ✅ 所有已启用工具的环境变量都已正确配置")
    
    print("\n🎉 演示完成！")
    print("\n📚 使用指南:")
    print("  1. 编辑 mcp_config.json 来启用/禁用工具")
    print("  2. 在 .env 文件中设置必要的 API 密钥")
    print("  3. 使用 get_all_tools() 获取所有可用工具")
    print("  4. 工具会自动从配置中加载并注入认证信息")


if __name__ == "__main__":
    main()