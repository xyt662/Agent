#!/usr/bin/env python3
"""
测试运行脚本
提供便捷的测试执行入口
"""

import sys
import subprocess
from pathlib import Path

def run_unit_tests():
    """运行单元测试"""
    print("🧪 运行单元测试...")
    print("=" * 50)
    
    unit_tests = [
        "tests/unit/test_authentication.py",
        "tests/unit/test_authentication_strategies.py",
        "tests/unit/test_pydantic_schema.py",
        "tests/unit/test_ssrf_protection.py",
        "tests/unit/test_http_error_handling.py"
    ]
    
    for test in unit_tests:
        test_path = Path(test)
        if test_path.exists():
            print(f"\n📋 运行 {test}...")
            try:
                result = subprocess.run([sys.executable, str(test_path)], 
                                       capture_output=True, text=True, cwd=Path.cwd())
                if result.returncode == 0:
                    print(f"✅ {test} 通过")
                else:
                    print(f"❌ {test} 失败")
                    print(f"错误输出: {result.stderr}")
            except Exception as e:
                print(f"❌ 运行 {test} 时出错: {e}")
        else:
            print(f"⚠️ 测试文件不存在: {test}")

def run_integration_tests():
    """运行集成测试"""
    print("\n🔗 运行集成测试...")
    print("=" * 50)
    
    integration_tests = [
        "tests/integration/test_auth_integration.py"
    ]
    
    for test in integration_tests:
        test_path = Path(test)
        if test_path.exists():
            print(f"\n📋 运行 {test}...")
            try:
                result = subprocess.run([sys.executable, str(test_path)], 
                                       capture_output=True, text=True, cwd=Path.cwd())
                if result.returncode == 0:
                    print(f"✅ {test} 通过")
                else:
                    print(f"❌ {test} 失败")
                    print(f"错误输出: {result.stderr}")
            except Exception as e:
                print(f"❌ 运行 {test} 时出错: {e}")
        else:
            print(f"⚠️ 测试文件不存在: {test}")

def run_utility_scripts():
    """运行工具脚本"""
    print("\n🛠️ 可用的工具脚本:")
    print("=" * 50)
    
    scripts = [
        ("tools/scripts/build_vectorstore.py", "构建向量存储"),
        ("tools/scripts/visualize_graph.py", "可视化图结构")
    ]
    
    for script, description in scripts:
        script_path = Path(script)
        if script_path.exists():
            print(f"📄 {script} - {description}")
        else:
            print(f"⚠️ 脚本不存在: {script}")
    
    print("\n💡 使用方法: python tools/scripts/script_name.py")

def main():
    """主函数"""
    print("RAG-Agent 测试套件")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "unit":
            run_unit_tests()
        elif command == "integration":
            run_integration_tests()
        elif command == "all":
            run_unit_tests()
            run_integration_tests()
        elif command == "scripts":
            run_utility_scripts()
        else:
            print(f"未知命令: {command}")
            print_usage()
    else:
        print_usage()

def print_usage():
    """打印使用说明"""
    print("\n使用方法:")
    print("  python run_tests.py unit        # 运行单元测试")
    print("  python run_tests.py integration # 运行集成测试")
    print("  python run_tests.py all         # 运行所有测试")
    print("  python run_tests.py scripts     # 显示可用工具脚本")
    print("\n项目结构:")
    print("  tests/unit/        # 单元测试")
    print("  tests/integration/ # 集成测试")
    print("  tools/scripts/     # 工具脚本")

if __name__ == "__main__":
    main()