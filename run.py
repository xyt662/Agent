#!/usr/bin/env python3
"""
项目启动脚本
这个脚本会自动设置正确的Python路径并运行主程序
"""

import sys
import os
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent
src_path = project_root / "src"

# 将src目录添加到Python路径
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 现在可以正常导入模块了
if __name__ == "__main__":
    from rag_agent.factories.agent_factory import get_main_agent_runnable
    from langchain_core.messages import HumanMessage
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # 使用工厂方法创建Agent
        app = get_main_agent_runnable()
        logger.info("成功创建Agent")
        if app is None:
            logger.error("Agent创建失败,程序退出")
            exit(1)
    except Exception as e:
        logger.error(f"Agent创建失败: {e}")
        exit(1)
    
    # 测试Agent
    # 使用一个需要背景知识的问题来测试RAG功能
    inputs = {"messages": [HumanMessage(content="LangGraph的核心优势是什么？请详细介绍一下。")]}
    
    try:
        logger.info("开始执行Agent流程")
        for s in app.stream(inputs, stream_mode="values"):
            print("--- 流输出 ---")
            print(s)
            print("-" * 40)
        logger.info("Agent流程执行完成")
    except Exception as e:
        logger.error(f"Agent执行失败: {e}", exc_info=True)