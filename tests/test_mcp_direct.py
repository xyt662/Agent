#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试MCP工具调用
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('..'))

from src.rag_agent.tools.tool_registry import get_all_tools

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mcp_tools_direct():
    """直接测试MCP工具调用"""
    try:
        # 加载所有工具
        tools = await get_all_tools()
        logger.info(f"加载了 {len(tools)} 个工具")
        
        # 查找百度地图地理编码工具
        map_geocode_tool = None
        for tool in tools:
            if tool.name == 'map_geocode':
                map_geocode_tool = tool
                break
        
        if not map_geocode_tool:
            logger.error("未找到map_geocode工具")
            return False
        
        logger.info(f"找到工具: {map_geocode_tool.name}")
        logger.info(f"工具描述: {map_geocode_tool.description}")
        
        # 测试异步调用
        logger.info("=== 测试异步调用 ===")
        try:
            result = await map_geocode_tool._arun(address="上海市")
            logger.info(f"异步调用成功: {result}")
        except Exception as e:
            logger.error(f"异步调用失败: {e}")
            return False
        
        # 测试同步调用
        logger.info("=== 测试同步调用 ===")
        try:
            result = map_geocode_tool._run(address="上海市")
            logger.info(f"同步调用成功: {result}")
        except Exception as e:
            logger.error(f"同步调用失败: {e}")
            return False
        
        logger.info("✅ 所有测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 直接测试MCP工具调用")
    print("=" * 50)
    
    success = asyncio.run(test_mcp_tools_direct())
    
    if success:
        print("\n🎉 测试通过！")
    else:
        print("\n💥 测试失败！")