#!/usr/bin/env python3
"""
嵌入模型提供者模块

该模块负责提供统一的嵌入模型获取接口，解耦嵌入模型的选择逻辑
"""

import os
from typing import Any

from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings

from .config import (
    get_embedding_model_name,
    DASHSCOPE_EMBEDDING_MODEL_NAME,
    OPENAI_EMBEDDING_MODEL_NAME
)

def get_embedding_model() -> Any:
    """
    获取嵌入模型实例
    
    根据环境变量配置，优先使用DashScope嵌入模型，如果没有则使用OpenAI嵌入模型
    
    Returns:
        嵌入模型实例
    
    Raises:
        ValueError: 如果没有配置有效的API密钥
    """
    # 优先使用DashScope（阿里云）嵌入模型，如果没有则使用OpenAI
    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if dashscope_api_key and dashscope_api_key != "your_dashscope_api_key_here":
        return DashScopeEmbeddings(
            model=DASHSCOPE_EMBEDDING_MODEL_NAME,
            dashscope_api_key=dashscope_api_key
        )
    elif openai_api_key and openai_api_key != "your_openai_api_key_here":
        # 对于OpenAI，使用环境变量中配置的模型名称
        openai_model = get_embedding_model_name() 
        return OpenAIEmbeddings(
            model=openai_model,
            openai_api_key=openai_api_key
        )
    else:
        raise ValueError(
            "请在.env文件中设置有效的DASHSCOPE_API_KEY或OPENAI_API_KEY"
        )