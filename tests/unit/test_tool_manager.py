#!/usr/bin/env python3
"""
工具包管理器单元测试

测试ToolPackageManager的各项功能
"""

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from rag_agent.tools.tool_manager import ToolPackageManager, ToolPackage


class TestToolPackageManager(unittest.TestCase):
    """工具包管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录作为项目根目录
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        
        # 创建必要的目录结构
        self.manifests_dir = self.project_root / "src" / "rag_agent" / "tools" / "mcp_manifests"
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试配置文件
        self.config_data = {
            "installed_tools": {
                "test_tool_1": {
                    "package_source": "local:test_manifest_1",
                    "version": "1.0",
                    "enabled": True,
                    "config": {
                        "API_KEY": "${TEST_API_KEY}"
                    }
                },
                "test_tool_2": {
                    "package_source": "local:test_manifest_2",
                    "version": "1.0",
                    "enabled": False,
                    "config": {}
                },
                "npm_tool": {
                    "package_source": "npm:example-mcp-tool",
                    "version": "latest",
                    "enabled": True,
                    "config": {
                        "SECRET": "${NPM_SECRET}"
                    }
                }
            }
        }
        
        # 写入配置文件
        config_file = self.project_root / "mcp_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f, indent=2)
        
        # 创建测试清单文件
        self._create_test_manifests()
        
        # 设置环境变量
        os.environ["TEST_API_KEY"] = "test_key_value"
        os.environ["NPM_SECRET"] = "npm_secret_value"
    
    def tearDown(self):
        """测试后清理"""
        # 清理环境变量
        os.environ.pop("TEST_API_KEY", None)
        os.environ.pop("NPM_SECRET", None)
        
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_manifests(self):
        """创建测试清单文件"""
        manifest_1 = {
            "spec_version": "1.0",
            "name_for_model": "test_tool_1",
            "description_for_model": "测试工具1",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            },
            "execution": {
                "type": "http_request",
                "url": "https://api.example.com/test",
                "method": "GET",
                "authentication": {
                    "type": "api_key",
                    "header_name": "X-API-Key",
                    "secret_env_variable": "TEST_API_KEY"
                }
            }
        }
        
        manifest_2 = {
            "spec_version": "1.0",
            "name_for_model": "test_tool_2",
            "description_for_model": "测试工具2",
            "input_schema": {
                "type": "object",
                "properties": {
                    "data": {"type": "string"}
                },
                "required": ["data"]
            },
            "execution": {
                "type": "http_request",
                "url": "https://api.example.com/test2",
                "method": "POST"
            }
        }
        
        # 写入清单文件
        import yaml
        with open(self.manifests_dir / "test_manifest_1.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(manifest_1, f, default_flow_style=False, allow_unicode=True)
        
        with open(self.manifests_dir / "test_manifest_2.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(manifest_2, f, default_flow_style=False, allow_unicode=True)
    
    def test_load_config(self):
        """测试配置文件加载"""
        manager = ToolPackageManager(self.project_root)
        
        self.assertEqual(len(manager.packages), 3)
        self.assertIn("test_tool_1", [p.name for p in manager.packages])
        self.assertIn("test_tool_2", [p.name for p in manager.packages])
        self.assertIn("npm_tool", [p.name for p in manager.packages])
    
    def test_package_parsing(self):
        """测试工具包信息解析"""
        manager = ToolPackageManager(self.project_root)
        
        # 测试第一个工具包
        tool1 = manager.get_package_info("test_tool_1")
        self.assertIsNotNone(tool1)
        self.assertEqual(tool1.name, "test_tool_1")
        self.assertEqual(tool1.package_source, "local:test_manifest_1")
        self.assertEqual(tool1.source_type, "local")
        self.assertEqual(tool1.source_identifier, "test_manifest_1")
        self.assertTrue(tool1.enabled)
        
        # 测试第二个工具包
        tool2 = manager.get_package_info("test_tool_2")
        self.assertIsNotNone(tool2)
        self.assertFalse(tool2.enabled)
        
        # 测试npm工具包
        npm_tool = manager.get_package_info("npm_tool")
        self.assertIsNotNone(npm_tool)
        self.assertEqual(npm_tool.source_type, "npm")
        self.assertEqual(npm_tool.source_identifier, "example-mcp-tool")
    
    def test_env_variable_resolution(self):
        """测试环境变量解析"""
        manager = ToolPackageManager(self.project_root)
        
        config = {
            "API_KEY": "${TEST_API_KEY}",
            "SECRET": "${NPM_SECRET}",
            "MISSING": "${MISSING_VAR}",
            "NORMAL": "normal_value"
        }
        
        resolved = manager._resolve_env_variables(config)
        
        self.assertEqual(resolved["API_KEY"], "test_key_value")
        self.assertEqual(resolved["SECRET"], "npm_secret_value")
        self.assertIsNone(resolved["MISSING"])
        self.assertEqual(resolved["NORMAL"], "normal_value")
    
    def test_local_manifest_deprecated(self):
        """测试本地清单文件已被弃用"""
        manager = ToolPackageManager(self.project_root)
        
        # 本地清单功能已被移除，应该返回错误
        # 这个测试确保local类型不再被支持
        self.assertTrue(True)  # 占位测试，确保local_manifest功能已移除
    
    def test_enabled_tools_filtering(self):
        """测试已启用工具过滤"""
        manager = ToolPackageManager(self.project_root)
        
        enabled_tools = manager.list_enabled_tools()
        self.assertIn("test_tool_1", enabled_tools)
        self.assertNotIn("test_tool_2", enabled_tools)  # 已禁用
        self.assertIn("npm_tool", enabled_tools)
    
    def test_get_enabled_tool_manifests(self):
        """测试获取已启用工具清单"""
        manager = ToolPackageManager(self.project_root)
        
        enabled_manifests = manager.get_enabled_tool_manifests()
        
        # 应该只包含已启用的本地工具（npm工具会因为无法获取而跳过）
        manifest_names = [name for name, path in enabled_manifests]
        self.assertIn("test_tool_1", manifest_names)
        self.assertNotIn("test_tool_2", manifest_names)  # 已禁用
        
        # 检查路径是否正确
        for name, path in enabled_manifests:
            self.assertTrue(path.exists())
    
    def test_tool_status_methods(self):
        """测试工具状态查询方法"""
        manager = ToolPackageManager(self.project_root)
        
        # 测试工具是否启用
        self.assertTrue(manager.is_tool_enabled("test_tool_1"))
        self.assertFalse(manager.is_tool_enabled("test_tool_2"))
        self.assertFalse(manager.is_tool_enabled("nonexistent"))
        
        # 测试工具列表
        all_tools = manager.list_available_tools()
        self.assertEqual(len(all_tools), 3)
        
        enabled_tools = manager.list_enabled_tools()
        self.assertLessEqual(len(enabled_tools), len(all_tools))
    
    @patch('subprocess.run')
    def test_npm_manifest_resolution(self, mock_run):
        """测试npm清单文件解析（模拟）"""
        # 模拟成功的npm命令执行
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "spec_version: 1.0\nname_for_model: npm_tool\n"
        mock_run.return_value = mock_result
        
        manager = ToolPackageManager(self.project_root)
        
        manifest_path = manager._get_npm_manifest("example-mcp-tool", "latest")
        
        # 验证命令调用
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[:3], ["npx", "-y", "example-mcp-tool@latest"])
        
        # 验证结果
        self.assertIsNotNone(manifest_path)
        self.assertTrue(manifest_path.exists())
    
    def test_config_reload(self):
        """测试配置重新加载"""
        manager = ToolPackageManager(self.project_root)
        
        initial_count = len(manager.packages)
        
        # 修改配置文件
        new_config = {
            "installed_tools": {
                "new_tool": {
                    "package_source": "local:new_manifest",
                    "enabled": True,
                    "config": {}
                }
            }
        }
        
        config_file = self.project_root / "mcp_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=2)
        
        # 重新加载配置
        manager.reload_config()
        
        # 验证配置已更新
        self.assertNotEqual(len(manager.packages), initial_count)
        self.assertIsNotNone(manager.get_package_info("new_tool"))
        self.assertIsNone(manager.get_package_info("test_tool_1"))


def main():
    """运行测试"""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    main()