#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度地图MCP工具测试脚本
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rag_agent.factories.agent_factory import get_main_agent_runnable

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_baidu_map_tools():
    """测试百度地图MCP工具"""
    try:
        # 创建agent
        agent = await get_main_agent_runnable()
        logger.info("Agent创建成功")
        
        # 测试地理编码
        logger.info("=== 测试百度地图工具 ===")
        
        # 测试查询：从上海到北京的路线规划
        test_query = "请使用百度地图工具帮我查询上海市的经纬度坐标"
        
        logger.info(f"测试查询: {test_query}")
        
        # 执行查询
        result = await agent.ainvoke({"messages": [{"role": "user", "content": test_query}]})
        
        logger.info("测试完成")
        logger.info(f"查询结果: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_baidu_map_tools())
    if success:
        print("\n✅ 百度地图MCP工具测试通过！")
    else:
        print("\n❌ 百度地图MCP工具测试失败！")