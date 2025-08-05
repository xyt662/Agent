#!/usr/bin/env python3
"""
统一记忆管理系统演示

展示重构后的记忆管理系统的主要功能：
1. 统一的存储后端初始化
2. 合并后的记忆管理器
3. 统一的事件处理器
4. 简化的节点职责分工
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag_agent.storage import create_storage_backend, get_memory_store
from src.rag_agent.core.memory import MemoryManager, MemoryEventHandler, create_memory_event_handler
from src.rag_agent.nodes.memory_node import create_memory_node
from src.rag_agent.core.agent_state import AgentState
from langchain_core.messages import HumanMessage, AIMessage

def demo_unified_storage_backend():
    """演示统一的存储后端初始化"""
    print("=== 1. 统一存储后端初始化演示 ===")
    
    # 方式1：使用新的便捷函数
    store1 = create_storage_backend(collection_name="demo_storage")
    print(f"✅ 方式1 - 便捷函数: {type(store1).__name__}")
    
    # 方式2：使用专用函数
    store2 = get_memory_store()
    print(f"✅ 方式2 - 专用函数: {type(store2).__name__}")
    
    # 方式3：禁用缓存创建新实例
    store3 = create_storage_backend(collection_name="demo_storage", enable_cache=False)
    print(f"✅ 方式3 - 禁用缓存: {type(store3).__name__}")
    
    print(f"实例对比: store1 == store2: {store1 is store2}, store1 == store3: {store1 is store3}")
    print()

def demo_unified_memory_manager():
    """演示合并后的记忆管理器"""
    print("=== 2. 统一记忆管理器演示 ===")
    
    # 创建存储后端
    storage = create_storage_backend(collection_name="unified_memory")
    
    # 创建统一的记忆管理器
    memory_manager = MemoryManager(storage_backend=storage)
    print(f"✅ 记忆管理器创建成功: {type(memory_manager).__name__}")
    
    # 测试基础功能
    success = memory_manager.store_memory(
        content="这是统一记忆管理器的测试内容",
        context={"source": "demo", "type": "test"},
        tags=["演示", "统一"],
        importance=8
    )
    print(f"✅ 记忆存储: {'成功' if success else '失败'}")
    
    # 测试搜索功能
    results = memory_manager.search_memories("统一记忆", limit=3)
    print(f"✅ 记忆搜索: 找到 {len(results)} 条记录")
    
    # 测试统计功能
    stats = memory_manager.get_memory_stats()
    print(f"✅ 记忆统计: {stats}")
    print()

def demo_unified_event_handler():
    """演示统一的事件处理器"""
    print("=== 3. 统一事件处理器演示 ===")
    
    # 创建存储后端和记忆管理器
    storage = create_storage_backend(collection_name="event_demo")
    memory_manager = MemoryManager(storage_backend=storage)
    
    # 创建统一的事件处理器
    event_handler = create_memory_event_handler(memory_manager)
    print(f"✅ 事件处理器创建成功: {type(event_handler).__name__}")
    
    # 模拟Agent状态
    state = AgentState({
        "messages": [
            HumanMessage(content="记住我的名字是张三，我喜欢编程"),
            AIMessage(content="好的，我已经记住了您的信息")
        ]
    })
    
    # 处理记忆事件
    updated_state = event_handler.handle_memory_events(state)
    print(f"✅ 事件处理完成: 消息数量从 {len(state['messages'])} 增加到 {len(updated_state['messages'])}")
    
    # 显示新增的事件消息
    if len(updated_state["messages"]) > len(state["messages"]):
        new_messages = updated_state["messages"][len(state["messages"]):]
        for i, msg in enumerate(new_messages, 1):
            print(f"  新消息 {i}: {msg.content[:50]}...")
    print()

def demo_simplified_memory_node():
    """演示简化的记忆节点"""
    print("=== 4. 简化记忆节点演示 ===")
    
    # 创建存储后端
    storage = create_storage_backend(collection_name="node_demo")
    
    # 创建记忆节点
    memory_node = create_memory_node(storage_backend=storage)
    print(f"✅ 记忆节点创建成功: {type(memory_node).__name__}")
    
    # 模拟Agent状态
    state = AgentState({
        "messages": [
            HumanMessage(content="请帮我记住今天学习了Python编程"),
            AIMessage(content="当然可以，我会帮您记住这个信息")
        ]
    })
    
    # 通过节点处理记忆
    updated_state = memory_node(state)
    print(f"✅ 节点处理完成: 消息数量从 {len(state['messages'])} 变为 {len(updated_state['messages'])}")
    
    # 测试节点的其他功能
    stats = memory_node.get_memory_stats()
    print(f"✅ 节点统计功能: {stats}")
    
    recent_memories = memory_node.list_recent_memories(limit=3)
    print(f"✅ 最近记忆: {len(recent_memories)} 条")
    print()

def demo_backward_compatibility():
    """演示向后兼容性"""
    print("=== 5. 向后兼容性演示 ===")
    
    # 测试旧的导入方式仍然有效
    from src.rag_agent.core.memory import EnhancedMemoryManager
    
    storage = create_storage_backend(collection_name="compatibility_demo")
    enhanced_manager = EnhancedMemoryManager(storage_backend=storage)
    print(f"✅ 向后兼容: EnhancedMemoryManager 仍然可用")
    print(f"✅ 实际类型: {type(enhanced_manager).__name__}")
    print(f"✅ 是否为同一类: {EnhancedMemoryManager is MemoryManager}")
    print()

def main():
    """主演示函数"""
    print("🚀 统一记忆管理系统演示")
    print("=" * 50)
    print()
    
    try:
        demo_unified_storage_backend()
        demo_unified_memory_manager()
        demo_unified_event_handler()
        demo_simplified_memory_node()
        demo_backward_compatibility()
        
        print("🎉 所有演示完成！")
        print()
        print("📋 重构总结:")
        print("✅ 合并了重复的记忆管理器实现")
        print("✅ 统一了存储后端初始化方式")
        print("✅ 提取了公共事件处理逻辑")
        print("✅ 优化了节点间的职责分工")
        print("✅ 保持了向后兼容性")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()