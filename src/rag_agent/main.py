# 文件: src/rag_agent/main.py

import logging
from contextlib import asynccontextmanager
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage, AIMessage

from .factories.agent_factory import get_main_agent_runnable, shutdown_agent_services
from .core.agent_state import AgentState

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API 数据模型 (DTOs)
class ChatRequest(BaseModel):
    """聊天请求模型"""
    session_id: str
    query: str

class ChatResponse(BaseModel):
    """聊天响应模型（用于文档生成）"""
    response: str
    session_id: str

# 会话管理 (MVP - 内存版)
# 注意：这是一个简单的 MVP 实现，服务器重启后会话将丢失
# 生产环境应替换为 Redis 或其他持久化存储
SESSION_STATES: Dict[str, AgentState] = {}

# FastAPI 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理器"""
    # 应用启动时执行:
    logger.info("应用启动 - 正在预热 Agent 和 MCP 工具...")
    try:
        await get_main_agent_runnable()  # 这会初始化 ToolManager 和所有工具
        logger.info("Agent 和 MCP 工具已成功初始化。")
    except Exception as e:
        logger.error(f"Agent 初始化失败: {e}")
        raise
    
    yield  # 应用在此处运行
    
    # 应用关闭时执行:
    logger.info("应用关闭 - 正在清理 Agent 和 MCP 工具...")
    try:
        await shutdown_agent_services()
        logger.info("所有后台服务已成功关闭。")
    except Exception as e:
        logger.error(f"服务关闭时出错: {e}")

# 创建 FastAPI 应用实例
app = FastAPI(
    title="RAG-Agent API",
    description="一个集成了高级RAG和动态工具(MCP)的智能代理服务",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    """根路径健康检查"""
    return {"status": "RAG-Agent API is running."}

@app.get("/health")
def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "RAG-Agent API",
        "version": "1.0.0"
    }

@app.post("/chat/invoke")
async def chat_invoke(request: ChatRequest):
    """
    核心聊天端点 - 支持流式响应和会话管理
    
    Args:
        request: 包含 session_id 和 query 的聊天请求
    
    Returns:
        EventSourceResponse: 流式 SSE 响应
    """
    import json
    
    try:
        async def event_stream():
            try:
                # 1. 获取 Agent 实例
                app_runnable = await get_main_agent_runnable()
                
                # 2. 恢复或创建会话状态
                session_id = request.session_id
                current_state = SESSION_STATES.get(session_id, AgentState(messages=[]))
                
                # 3. 将新问题添加到状态中
                current_state["messages"].append(HumanMessage(content=request.query))
                
                # 4. 发送 agent_start 事件
                yield {
                    "event": "agent_start",
                    "data": json.dumps({"session_id": session_id, "query": request.query})
                }
                
                # 5. 使用 astream_events 迭代 Agent 的输出事件
                final_answer = ""
                
                async for event in app_runnable.astream_events(current_state, version="v1"):
                    kind = event["event"]
                    
                    # 处理工具调用开始事件
                    if kind == "on_tool_start":
                        tool_name = event.get("name", "unknown_tool")
                        tool_input = event.get("data", {}).get("input", {})
                        yield {
                            "event": "tool_start",
                            "data": json.dumps({
                                "tool_name": tool_name,
                                "tool_input": tool_input
                            })
                        }
                    
                    # 处理工具调用结束事件
                    elif kind == "on_tool_end":
                        tool_name = event.get("name", "unknown_tool")
                        tool_output = event.get("data", {}).get("output", "")
                        # 截断输出以避免过长
                        tool_output_preview = str(tool_output)[:200] + "..." if len(str(tool_output)) > 200 else str(tool_output)
                        yield {
                            "event": "tool_end",
                            "data": json.dumps({
                                "tool_name": tool_name,
                                "tool_output_preview": tool_output_preview
                            })
                        }
                    
                    # 处理 LLM 流式输出
                    elif kind == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        if hasattr(chunk, 'content') and chunk.content:
                            final_answer += chunk.content
                            # 发送结构化的 LLM chunk 事件
                            yield {
                                "event": "llm_chunk",
                                "data": json.dumps({"chunk": chunk.content})
                            }
                
                # 6. 更新会话状态
                if final_answer:
                    current_state["messages"].append(AIMessage(content=final_answer))
                    SESSION_STATES[session_id] = current_state
                
                # 7. 发送 agent_end 事件
                yield {
                    "event": "agent_end",
                    "data": json.dumps({"session_id": session_id, "final_answer_length": len(final_answer)})
                }
                
            except Exception as e:
                logger.error(f"流式处理过程中出错: {e}")
                yield {"data": f"[ERROR] 处理请求时出错: {str(e)}"}
        
        return EventSourceResponse(event_stream())
    
    except Exception as e:
        logger.error(f"聊天端点出错: {e}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")

@app.get("/chat/sessions/{session_id}/history")
def get_session_history(session_id: str):
    """
    获取指定会话的对话历史
    
    Args:
        session_id: 会话ID
    
    Returns:
        dict: 包含消息历史的字典
    """
    if session_id not in SESSION_STATES:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    state = SESSION_STATES[session_id]
    messages = []
    
    for msg in state["messages"]:
        messages.append({
            "type": msg.__class__.__name__,
            "content": msg.content if hasattr(msg, 'content') else str(msg)
        })
    
    return {
        "session_id": session_id,
        "message_count": len(messages),
        "messages": messages
    }

@app.delete("/chat/sessions/{session_id}")
def clear_session(session_id: str):
    """
    清除指定会话的状态
    
    Args:
        session_id: 会话ID
    
    Returns:
        dict: 操作结果
    """
    if session_id in SESSION_STATES:
        del SESSION_STATES[session_id]
        return {"message": f"会话 {session_id} 已清除"}
    else:
        raise HTTPException(status_code=404, detail="会话不存在")

@app.get("/chat/sessions")
def list_sessions():
    """
    列出所有活跃会话
    
    Returns:
        dict: 包含会话列表的字典
    """
    sessions = []
    for session_id, state in SESSION_STATES.items():
        sessions.append({
            "session_id": session_id,
            "message_count": len(state["messages"])
        })
    
    return {
        "active_sessions": len(sessions),
        "sessions": sessions
    }

@app.post("/tools/reload")
async def reload_tools():
    """
    热重载工具配置端点
    
    重新加载 tools.config.json 配置文件并重新初始化所有 MCP 工具，
    无需重启 FastAPI 服务。
    
    Returns:
        dict: 操作结果
    """
    try:
        logger.info("收到工具重载请求...")
        
        # 获取全局工具管理器并执行热重载
        from .tools.tool_manager import get_tool_manager
        tool_manager = await get_tool_manager()
        await tool_manager.reload_config_and_tools()
        
        # 重新初始化 Agent（这会使用新的工具配置）
        from .factories.agent_factory import reset_agent_cache
        await reset_agent_cache()
        
        logger.info("工具配置热重载成功")
        return {
            "status": "success",
            "message": "Tool configuration reloaded successfully",
            "tool_count": len(tool_manager.list_available_tools())
        }
        
    except Exception as e:
        logger.error(f"工具重载失败: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to reload tool configuration: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)