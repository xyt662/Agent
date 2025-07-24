#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的MCP工具测试脚本
测试多个MCP工具的调用
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rag_agent.factories.agent_factory import get_main_agent_runnable

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

async def test_multiple_mcp_tools():
    """测试多个MCP工具"""
    try:
        # 创建Agent
        logger.info("创建Agent...")
        agent = await get_main_agent_runnable()
        logger.info("Agent创建成功")
        
        # 测试用例
        test_cases = [
            "请查询北京市的经纬度坐标",
            "请查询经纬度116.404,39.915对应的地址",
            "请查询北京到上海的驾车路线"
        ]
        
        for i, query in enumerate(test_cases, 1):
            logger.info(f"=== 测试 {i}: {query} ===")
            
            result = await agent.ainvoke({
                "messages": [{"role": "user", "content": query}]
            })
            
            # 获取最后一条消息
            last_message = result["messages"][-1]
            logger.info(f"测试 {i} 完成")
            logger.info(f"回答: {last_message.content[:100]}...")
            print(f"\n测试 {i} - {query}")
            print(f"回答: {last_message.content}\n")
            print("-" * 80)
        
        logger.info("✅ 所有MCP工具测试通过！")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        raise
    finally:
        # 清理MCP适配器资源
        try:
            from rag_agent.tools.tool_manager import get_tool_manager
            tool_manager = get_tool_manager()
            await tool_manager.cleanup()
            logger.info("MCP适配器资源清理完成")
        except Exception as e:
            logger.warning(f"清理资源时出现警告: {e}")

if __name__ == "__main__":
    asyncio.run(test_multiple_mcp_tools())