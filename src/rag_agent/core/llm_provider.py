"""
将模型初始化逻辑从工厂中分离出来，职责更单一
"""

from langchain.chat_models import init_chat_model
from .config import get_deepseek_api_key


def get_llm():
    """
    获取配置好的LLM实例
    """
    api_key = get_deepseek_api_key()

    llm = init_chat_model(
        model="deepseek-chat", model_provider="deepseek", temperature=0, api_key=api_key
    )

    return llm
