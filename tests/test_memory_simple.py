#!/usr/bin/env python3
"""
简单的记忆存储测试
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag_agent.storage.factory import get_memory_store
from src.rag_agent.core.memory.memory_manager import MemoryManager

def test_simple_memory_storage():
    """测试简单的记忆存储"""
    print("=== 简单记忆存储测试 ===")
    
    try:
        # 创建存储后端
        store = get_memory_store()
        print(f"✅ 存储后端创建成功: {type(store).__name__}")
        
        # 创建记忆管理器
        memory_manager = MemoryManager(storage_backend=store)
        print(f"✅ 记忆管理器创建成功")
        
        # 测试存储记忆
        content = "这是一个测试记忆内容"
        context = {"category": "test", "user_id": "test_user"}
        tags = ["测试", "记忆"]
        importance = 7
        
        print(f"\n尝试存储记忆...")
        print(f"内容: {content}")
        print(f"上下文: {context}")
        print(f"标签: {tags}")
        print(f"重要性: {importance}")
        
        success = memory_manager.store_memory(
            content=content,
            context=context,
            tags=tags,
            importance=importance
        )
        
        if success:
            print(f"✅ 记忆存储成功!")
        else:
            print(f"❌ 记忆存储失败!")
            
        return success
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_memory_storage()
    if success:
        print("\n🎉 测试通过!")
    else:
        print("\n💥 测试失败!")
        sys.exit(1)