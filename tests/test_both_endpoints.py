#!/usr/bin/env python3
"""
测试两种聊天端点的客户端

演示:
1. /chat/invoke - SSE流式响应
2. /chat/complete - 标准JSON响应
"""

import asyncio
import aiohttp
import json
from typing import AsyncGenerator

BASE_URL = "http://localhost:8000"

async def test_streaming_endpoint():
    """测试流式端点 /chat/invoke"""
    print("\n=== 测试流式端点 /chat/invoke ===")
    
    payload = {
        "session_id": "test_stream_001",
        "query": "帮我查询从杭州到南京的路线，并推荐南京的美食"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/chat/invoke",
            json=payload,
            headers={"Accept": "text/event-stream"}
        ) as response:
            print(f"响应状态: {response.status}")
            print(f"响应头: {dict(response.headers)}")
            print("\n流式输出:")
            print("-" * 50)
            
            async for line in response.content:
                line_str = line.decode('utf-8').strip()
                if line_str:
                    print(line_str)

async def test_complete_endpoint():
    """测试完整响应端点 /chat/complete"""
    print("\n=== 测试完整响应端点 /chat/complete ===")
    
    payload = {
        "session_id": "test_complete_001",
        "query": "帮我查询从杭州到南京的路线，并推荐南京的美食"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/chat/complete",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            print(f"响应状态: {response.status}")
            print(f"响应头: {dict(response.headers)}")
            
            if response.status == 200:
                result = await response.json()
                print("\n完整JSON响应:")
                print("-" * 50)
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                error_text = await response.text()
                print(f"错误响应: {error_text}")

async def test_health_check():
    """测试健康检查端点"""
    print("\n=== 测试健康检查 ===")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/health") as response:
            if response.status == 200:
                result = await response.json()
                print(f"服务状态: {result}")
                return True
            else:
                print(f"服务不可用: {response.status}")
                return False

async def main():
    """主函数"""
    print("SynapseAgent API 端点测试")
    print("=" * 50)
    
    # 1. 健康检查
    if not await test_health_check():
        print("\n❌ 服务不可用，请确保 FastAPI 服务正在运行")
        print("启动命令: python -m uvicorn src.rag_agent.main:app --reload")
        return
    
    print("\n✅ 服务正常运行")
    
    # 2. 测试完整响应端点（推荐用于测试）
    try:
        await test_complete_endpoint()
    except Exception as e:
        print(f"完整响应端点测试失败: {e}")
    
    # 3. 测试流式响应端点
    try:
        await test_streaming_endpoint()
    except Exception as e:
        print(f"流式响应端点测试失败: {e}")
    
    print("\n=== 测试总结 ===")
    print("1. /chat/complete - 适合测试和调试，返回完整JSON")
    print("2. /chat/invoke - 适合生产环境，提供实时流式体验")
    print("3. 两个端点功能相同，只是响应格式不同")

if __name__ == "__main__":
    asyncio.run(main())