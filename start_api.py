#!/usr/bin/env python3
# 文件: start_api.py
"""
FastAPI 服务启动脚本

使用方法:
    python start_api.py

服务启动后可以访问:
    - API 文档: http://localhost:8000/docs
    - 健康检查: http://localhost:8000/health
    - 聊天端点: POST http://localhost:8000/chat/invoke
"""

import uvicorn
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    print("🚀 启动 RAG-Agent FastAPI 服务...")
    print("📖 API 文档: http://localhost:8000/docs")
    print("🔍 健康检查: http://localhost:8000/health")
    print("💬 聊天端点: POST http://localhost:8000/chat/invoke")
    print("\n按 Ctrl+C 停止服务\n")
    
    try:
        uvicorn.run(
            "src.rag_agent.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,  # 开发模式下启用热重载
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")