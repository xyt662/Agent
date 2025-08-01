#!/usr/bin/env python3
# 文件: test_api_client.py
"""
FastAPI 服务测试客户端

使用方法:
    python test_api_client.py

功能:
    - 测试健康检查端点
    - 测试流式聊天端点
    - 测试会话管理功能
"""

import requests
import json
import time
from typing import Generator

API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """测试健康检查端点"""
    print("🔍 测试健康检查端点...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"   响应: {response.json()}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_streaming_chat(session_id: str, query: str):
    """测试流式聊天端点"""
    print(f"💬 测试流式聊天 (会话: {session_id})...")
    print(f"   问题: {query}")
    
    try:
        # 准备请求数据
        chat_data = {
            "session_id": session_id,
            "query": query
        }
        
        # 发送流式请求
        response = requests.post(
            f"{API_BASE_URL}/chat/invoke",
            json=chat_data,
            headers={"Accept": "text/event-stream"},
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ 开始接收流式响应:")
            print("   回答: ", end="", flush=True)
            
            # 处理流式响应
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('event: '):
                        # 这是事件类型行，跳过
                        continue
                    elif line_str.startswith('data: '):
                        data = line_str[6:]  # 移除 'data: ' 前缀
                        
                        # 处理特殊标记
                        if data in ["[STREAM_START]", "[STREAM_END]"]:
                            continue
                        elif data.startswith("[TOOL_START]") or data.startswith("[TOOL_END]"):
                            print(f"\n   🔧 {data}")
                            print("   回答: ", end="", flush=True)
                        elif data.startswith("[ERROR]"):
                            print(f"\n   ❌ {data}")
                        else:
                            # 尝试解析JSON格式的数据
                            try:
                                json_data = json.loads(data)
                                if "chunk" in json_data:
                                    # 这是LLM的流式输出
                                    print(json_data["chunk"], end="", flush=True)
                                elif "tool_name" in json_data:
                                    # 工具调用事件
                                    if "tool_input" in json_data:
                                        print(f"\n   🔧 工具调用: {json_data['tool_name']}")
                                    elif "tool_output_preview" in json_data:
                                        print(f"\n   ✅ 工具完成: {json_data['tool_name']}")
                                    print("   回答: ", end="", flush=True)
                                else:
                                    # 其他结构化数据，不显示详细内容
                                    pass
                            except json.JSONDecodeError:
                                # 如果不是JSON格式，直接输出
                                print(data, end="", flush=True)
            
            print("\n✅ 流式响应完成")
            return True
        else:
            print(f"❌ 聊天请求失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 聊天请求异常: {e}")
        return False

def test_session_history(session_id: str):
    """测试会话历史查询"""
    print(f"📜 测试会话历史查询 (会话: {session_id})...")
    try:
        response = requests.get(f"{API_BASE_URL}/chat/sessions/{session_id}/history")
        if response.status_code == 200:
            history = response.json()
            print("✅ 会话历史查询成功")
            print(f"   消息数量: {history['message_count']}")
            for i, msg in enumerate(history['messages']):
                print(f"   [{i+1}] {msg['type']}: {msg['content'][:100]}...")
            return True
        else:
            print(f"❌ 会话历史查询失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 会话历史查询异常: {e}")
        return False

def test_list_sessions():
    """测试会话列表查询"""
    print("📋 测试会话列表查询...")
    try:
        response = requests.get(f"{API_BASE_URL}/chat/sessions")
        if response.status_code == 200:
            sessions = response.json()
            print("✅ 会话列表查询成功")
            print(f"   活跃会话数: {sessions['active_sessions']}")
            for session in sessions['sessions']:
                print(f"   - {session['session_id']}: {session['message_count']} 条消息")
            return True
        else:
            print(f"❌ 会话列表查询失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 会话列表查询异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 RAG-Agent FastAPI 服务测试")
    print("=" * 50)
    
    # 1. 测试健康检查
    if not test_health_check():
        print("❌ 服务未启动或不可用，请先启动服务")
        return
    
    print("\n" + "-" * 50)
    
    # 2. 测试流式聊天
    session_id = f"test_session_{int(time.time())}"
    
    # 第一轮对话
    test_streaming_chat(session_id, "你好，请介绍一下你自己")
    
    print("\n" + "-" * 50)
    
    # 第二轮对话（测试会话连续性）
    test_streaming_chat(session_id, "我刚才问了什么问题？")
    
    print("\n" + "-" * 50)
    
    # 3. 测试会话历史
    test_session_history(session_id)
    
    print("\n" + "-" * 50)
    
    # 4. 测试会话列表
    test_list_sessions()
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")

if __name__ == "__main__":
    main()