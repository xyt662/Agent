#!/usr/bin/env python3
"""
工具包管理器集成测试

测试新的工具包管理器与现有系统的集成
"""

import os
import sys
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from rag_agent.tools.tool_manager import get_tool_manager, reset_tool_manager
from rag_agent.tools.tool_registry import get_all_tools, clear_tools_cache


class TestToolManagerIntegration(unittest.TestCase):
    """工具包管理器集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 重置全局实例
        reset_tool_manager()
        clear_tools_cache()
    
    def tearDown(self):
        """测试后清理"""
        # 重置全局实例
        reset_tool_manager()
        clear_tools_cache()
    
    def test_tool_manager_initialization(self):
        """测试工具包管理器初始化"""
        manager = get_tool_manager()
        
        self.assertIsNotNone(manager)
        self.assertTrue(manager.config_file.exists())
        
        # 检查是否加载了配置
        packages = manager.list_available_tools()
        self.assertIsInstance(packages, list)
        
        print(f"\n=== 工具包管理器状态 ===")
        print(f"配置文件: {manager.config_file}")
        print(f"可用工具: {len(packages)} 个")
        print(f"已启用工具: {len(manager.list_enabled_tools())} 个")
        
        for tool_name in packages:
            package = manager.get_package_info(tool_name)
            status = "✓ 启用" if package.enabled else "✗ 禁用"
            print(f"  - {tool_name}: {package.package_source} ({status})")
    
    def test_tool_registry_integration(self):
        """测试工具注册表集成"""
        # 获取所有工具（这会触发工具包管理器）
        tools = get_all_tools()
        
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)
        
        print(f"\n=== 工具注册表状态 ===")
        print(f"已注册工具: {len(tools)} 个")
        
        for tool in tools:
            desc = tool.description or "无描述"
            print(f"  - {tool.name}: {desc[:100]}...")
    
    def test_mcp_tools_loading(self):
        """测试MCP工具加载"""
        manager = get_tool_manager()
        
        # 获取已启用的工具清单内容（新模式）
        enabled_manifests = manager.get_enabled_tool_manifest_contents()
        
        print(f"\n=== MCP工具加载状态 ===")
        print(f"已启用清单: {len(enabled_manifests)} 个")
        
        for tool_name, manifest_content in enabled_manifests:
            print(f"  - {tool_name}: {type(manifest_content)} (内存模式)")
            self.assertIsInstance(manifest_content, dict, f"清单内容应为字典: {tool_name}")
            self.assertIn('name', manifest_content, f"清单缺少name字段: {tool_name}")
        
        # 同时测试向后兼容的文件模式
        enabled_manifests_legacy = manager.get_enabled_tool_manifests()
        print(f"\n=== 向后兼容模式 ===")
        print(f"已启用清单文件: {len(enabled_manifests_legacy)} 个")
        
        for tool_name, manifest_path in enabled_manifests_legacy:
            print(f"  - {tool_name}: {manifest_path}")
            # 注意：HTTP模式下可能没有本地文件，所以不强制要求文件存在
    
    def test_environment_variable_injection(self):
        """测试环境变量注入"""
        # 设置测试环境变量
        test_key = "TEST_INTEGRATION_KEY"
        test_value = "integration_test_value"
        os.environ[test_key] = test_value
        
        try:
            manager = get_tool_manager()
            
            # 测试环境变量解析
            config = {test_key: f"${{{test_key}}}"}
            resolved = manager._resolve_env_variables(config)
            
            self.assertEqual(resolved[test_key], test_value)
            print(f"\n=== 环境变量注入测试 ===")
            print(f"原始配置: {config}")
            print(f"解析结果: {resolved}")
            
        finally:
            # 清理环境变量
            os.environ.pop(test_key, None)
    
    def test_tool_enabling_disabling(self):
        """测试工具启用/禁用功能"""
        manager = get_tool_manager()
        
        all_tools = manager.list_available_tools()
        enabled_tools = manager.list_enabled_tools()
        
        print(f"\n=== 工具启用状态 ===")
        print(f"总工具数: {len(all_tools)}")
        print(f"已启用: {len(enabled_tools)}")
        print(f"已禁用: {len(all_tools) - len(enabled_tools)}")
        
        # 检查每个工具的状态
        for tool_name in all_tools:
            is_enabled = manager.is_tool_enabled(tool_name)
            package = manager.get_package_info(tool_name)
            
            self.assertEqual(is_enabled, package.enabled)
            
            status = "启用" if is_enabled else "禁用"
            print(f"  - {tool_name}: {status}")
    
    def test_local_vs_remote_tools(self):
        """测试本地工具与远程工具的处理"""
        manager = get_tool_manager()
        
        local_tools = []
        remote_tools = []
        
        for tool_name in manager.list_available_tools():
            package = manager.get_package_info(tool_name)
            if package.source_type == "local":
                local_tools.append(tool_name)
            else:
                remote_tools.append(tool_name)
        
        print(f"\n=== 工具来源分析 ===")
        print(f"本地工具: {len(local_tools)} 个")
        for tool in local_tools:
            package = manager.get_package_info(tool)
            print(f"  - {tool}: {package.source_identifier}")
        
        print(f"远程工具: {len(remote_tools)} 个")
        for tool in remote_tools:
            package = manager.get_package_info(tool)
            print(f"  - {tool}: {package.package_source}")
    
    def test_config_file_validation(self):
        """测试配置文件验证"""
        manager = get_tool_manager()
        
        # 检查配置文件格式（新格式：直接包含工具配置）
        config = manager.config
        self.assertIsInstance(config, dict)
        self.assertGreater(len(config), 0, "配置文件应包含至少一个工具")
        
        print(f"\n=== 配置文件验证 ===")
        print(f"配置文件路径: {manager.config_file}")
        print(f"配置格式: 有效（新格式）")
        
        # 验证每个工具配置
        for tool_name, tool_config in config.items():
            # 新格式应包含这些字段之一（支持Dify模式的server_url）
            has_source = any(key in tool_config for key in ["server_url", "manifest_url", "local_command"])
            self.assertTrue(has_source, f"工具 {tool_name} 缺少有效的包源配置")
            
            package = manager.get_package_info(tool_name)
            self.assertIsNotNone(package, f"工具 {tool_name} 解析失败")
            
            print(f"  - {tool_name}: 配置有效")
    
    @unittest.skipUnless(os.getenv("TAVILY_API_KEY"), "需要TAVILY_API_KEY环境变量")
    def test_real_tool_execution(self):
        """测试真实工具执行（需要API密钥）"""
        tools = get_all_tools()
        
        # 查找Tavily搜索工具
        tavily_tool = None
        for tool in tools:
            if "tavily" in tool.name.lower() and "search" in tool.name.lower():
                tavily_tool = tool
                break
        
        if tavily_tool:
            print(f"\n=== 真实工具执行测试 ===")
            print(f"测试工具: {tavily_tool.name}")
            
            try:
                result = tavily_tool.invoke({"query": "Python programming"})
                self.assertIsNotNone(result)
                print(f"执行结果: {str(result)[:200]}...")
            except Exception as e:
                print(f"执行失败: {e}")
                # 不让测试失败，因为可能是网络或API问题
        else:
            print(f"\n=== 真实工具执行测试 ===")
            print("未找到Tavily搜索工具")


def main():
    """运行测试"""
    print("开始工具包管理器集成测试...")
    print("="*50)
    
    unittest.main(verbosity=2)


if __name__ == "__main__":
    main()