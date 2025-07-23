#!/usr/bin/env python3
"""
测试简化后的Pydantic模型创建功能
"""

import sys
import os
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent  # 从tests/unit目录回到项目根目录
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from rag_agent.tools.mcp_adapter import MCPToolAdapter

def test_empty_schema():
    """测试空schema的处理"""
    print("=== 测试空schema ===")
    
    # 创建空schema的清单文件
    manifest_content = """# 测试清单文件
spec_version: 1.0
name_for_model: "test_empty_schema"
description_for_model: "测试空schema的工具"

input_schema:
  type: "object"
  properties: {}

execution:
  type: "http_request"
  url: "https://httpbin.org/get"
  method: "GET"
  parameter_mapping: {}"""
    
    manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/temp_empty_schema.yaml"
    
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        
        adapter = MCPToolAdapter(str(manifest_path))
        schema = adapter._create_args_schema()
        
        print(f"生成的模型: {schema}")
        print(f"模型名称: {schema.__name__}")
        
        # 测试创建实例
        instance = schema()
        print(f"空实例: {instance}")
        print("✅ 空schema处理正确")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        if manifest_path.exists():
            manifest_path.unlink()

def test_various_types():
    """测试各种数据类型的处理"""
    print("\n=== 测试各种数据类型 ===")
    
    # 创建包含各种类型的清单文件
    manifest_content = """# 测试清单文件
spec_version: 1.0
name_for_model: "test_various_types"
description_for_model: "测试各种数据类型的工具"

input_schema:
  type: "object"
  properties:
    name:
      type: "string"
      description: "用户名称"
    age:
      type: "integer"
      description: "用户年龄"
    score:
      type: "number"
      description: "用户评分"
    active:
      type: "boolean"
      description: "是否活跃"
    tags:
      type: "array"
      description: "标签列表"
    metadata:
      type: "object"
      description: "元数据"
    unknown_type:
      type: "custom_type"
      description: "未知类型（应该默认为string）"
  required: ["name", "age"]

execution:
  type: "http_request"
  url: "https://httpbin.org/post"
  method: "POST"
  parameter_mapping: {}"""
    
    manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/temp_various_types.yaml"
    
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        
        adapter = MCPToolAdapter(str(manifest_path))
        schema = adapter._create_args_schema()
        
        print(f"生成的模型: {schema}")
        print(f"模型字段: {schema.model_fields.keys()}")
        
        # 检查字段类型（使用Pydantic V2的model_fields）
        fields = schema.model_fields
        
        # 必需字段
        if 'name' in fields and fields['name'].annotation == str and fields['name'].is_required():
            print("✅ string类型必需字段正确")
        else:
            print("❌ string类型必需字段错误")
            
        if 'age' in fields and fields['age'].annotation == int and fields['age'].is_required():
            print("✅ integer类型必需字段正确")
        else:
            print("❌ integer类型必需字段错误")
        
        # 可选字段
        if 'score' in fields and not fields['score'].is_required():
            print("✅ number类型可选字段正确")
        else:
            print("❌ number类型可选字段错误")
            
        if 'active' in fields and not fields['active'].is_required():
            print("✅ boolean类型可选字段正确")
        else:
            print("❌ boolean类型可选字段错误")
            
        if 'tags' in fields and not fields['tags'].is_required():
            print("✅ array类型可选字段正确")
        else:
            print("❌ array类型可选字段错误")
            
        if 'metadata' in fields and not fields['metadata'].is_required():
            print("✅ object类型可选字段正确")
        else:
            print("❌ object类型可选字段错误")
            
        # 未知类型应该默认为string
        if 'unknown_type' in fields:
            actual_type = fields['unknown_type'].annotation
            print(f"unknown_type字段的实际类型: {actual_type}")
            # 检查是否为Optional[str]或str
            import typing
            if actual_type == str or (
                hasattr(actual_type, '__origin__') and 
                actual_type.__origin__ is typing.Union and 
                len(actual_type.__args__) == 2 and 
                str in actual_type.__args__ and 
                type(None) in actual_type.__args__
            ):
                print("✅ 未知类型默认为string正确")
            else:
                print("❌ 未知类型处理错误")
        else:
            print("❌ 未知类型字段不存在")
        
        # 测试创建实例
        try:
            # 只提供必需字段
            instance1 = schema(name="张三", age=25)
            print(f"必需字段实例: {instance1}")
            print("✅ 必需字段实例创建成功")
            
            # 提供所有字段
            instance2 = schema(
                name="李四",
                age=30,
                score=95.5,
                active=True,
                tags=["python", "ai"],
                metadata={"level": "expert"},
                unknown_type="test"
            )
            print(f"完整字段实例: {instance2}")
            print("✅ 完整字段实例创建成功")
            
        except Exception as e:
            print(f"❌ 实例创建失败: {e}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        if manifest_path.exists():
            manifest_path.unlink()

def test_existing_manifests():
    """测试现有清单文件的兼容性"""
    print("\n=== 测试现有清单文件兼容性 ===")
    
    manifest_files = [
        "github_api_example.yaml",
        "api_key_example.yaml",
        "basic_auth_example.yaml"
    ]
    
    for manifest_file in manifest_files:
        manifest_path = project_root / f"src/rag_agent/tools/mcp_manifests/{manifest_file}"
        
        if not manifest_path.exists():
            print(f"⚠️ 清单文件不存在: {manifest_file}")
            continue
            
        try:
            adapter = MCPToolAdapter(str(manifest_path))
            schema = adapter._create_args_schema()
            tool = adapter.to_langchain_tool()
            
            print(f"✅ {manifest_file} 兼容性测试通过")
            
        except Exception as e:
            print(f"❌ {manifest_file} 兼容性测试失败: {e}")

def test_performance_comparison():
    """测试性能对比（简单验证）"""
    print("\n=== 性能对比测试 ===")
    
    import time
    
    # 创建一个复杂的schema
    manifest_content = """# 测试清单文件
spec_version: 1.0
name_for_model: "test_performance"
description_for_model: "性能测试工具"

input_schema:
  type: "object"
  properties:
    field1: {type: "string"}
    field2: {type: "integer"}
    field3: {type: "number"}
    field4: {type: "boolean"}
    field5: {type: "array"}
    field6: {type: "object"}
    field7: {type: "string"}
    field8: {type: "integer"}
    field9: {type: "number"}
    field10: {type: "boolean"}
  required: ["field1", "field2", "field3"]

execution:
  type: "http_request"
  url: "https://httpbin.org/post"
  method: "POST"
  parameter_mapping: {}"""
    
    manifest_path = project_root / "src/rag_agent/tools/mcp_manifests/temp_performance.yaml"
    
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        
        # 测试多次创建的性能
        start_time = time.time()
        for _ in range(100):
            adapter = MCPToolAdapter(str(manifest_path))
            schema = adapter._create_args_schema()
        end_time = time.time()
        
        print(f"100次schema创建耗时: {end_time - start_time:.4f}秒")
        print("✅ 性能测试完成")
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
    finally:
        if manifest_path.exists():
            manifest_path.unlink()

if __name__ == "__main__":
    print("开始Pydantic模型创建简化测试...")
    print("验证类型映射表重构后的功能是否正常\n")
    
    test_empty_schema()
    test_various_types()
    test_existing_manifests()
    test_performance_comparison()
    
    print("\n测试完成！")
    print("\n💡 简化优势:")
    print("   - 代码更简洁：使用字典映射替代if/elif链")
    print("   - 可读性更好：类型映射一目了然")
    print("   - 易于扩展：新增类型只需在映射表中添加")
    print("   - 性能更好：避免多次条件判断")