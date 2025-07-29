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
    from rag_agent.factories.agent_factory import get_main_agent_runnable, shutdown_agent_services
    from langchain_core.messages import HumanMessage
    import logging
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    async def main():
        app = None
        try:
            # 使用工厂方法创建Agent
            app = await get_main_agent_runnable()
            logger.info("成功创建Agent")
            if app is None:
                logger.error("Agent创建失败,程序退出")
                return
            
            print("=== 测试1: RAG知识库查询 ===")
            # 使用一个需要背景知识的问题来测试RAG功能
            inputs = {"messages": [HumanMessage(content="LangGraph的核心优势是什么？请详细介绍一下。")]}
            
            try:
                logger.info("开始执行Agent流程")
                async for s in app.astream(inputs, stream_mode="values"):
                    print("--- 流输出 ---")
                    print(s)
                    print("-" * 40)
                logger.info("Agent流程执行完成")
            except Exception as e:
                logger.error(f"Agent执行失败: {e}", exc_info=True)
            
            print("\n=== 测试2: MCP工具测试 ===")
    
            # 测试MCP工具
            mcp_inputs = {"messages": [HumanMessage(content="请你使用百度mcp工具搜索杭州的经纬度")]}
            
            logger.info("开始执行MCP工具测试")
            async for s in app.astream(mcp_inputs, stream_mode="values"):
                print("--- MCP流输出 ---")
                print(s)
                print("-" * 40)
            logger.info("MCP工具测试完成")
            
        except Exception as e:
            logger.error(f"Agent执行期间发生未捕获的异常: {e}", exc_info=True)
        finally:
            # ❗❗❗ 无论上面发生什么，这个块总会被执行 ❗❗❗
            if app is not None:
                logger.info("开始关闭 Agent 服务和后台工具...")
                await shutdown_agent_services()
                logger.info("所有服务已成功关闭。程序退出。")
    
    # 运行异步主函数
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # (可选) 处理用户按 Ctrl+C 的情况
        print("\n检测到用户中断，正在清理资源...")
        # 在这种情况下，我们可能也需要一种方式来调用清理函数
        # 但 asyncio.run() 之后再清理会比较复杂，
        # 所以在 finally 中处理是最好的方式。