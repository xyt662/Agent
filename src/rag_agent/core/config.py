import os
from pathlib import Path
from dotenv import load_dotenv

# 项目启动时加载.env文件
# find_dotenv()会自动寻找.env文件的路径
from dotenv import find_dotenv

load_dotenv(find_dotenv())


def get_deepseek_api_key():
    """获取DeepSeek API密钥"""
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_api_key:
        raise ValueError("DEEPSEEK_API_KEY没有被你设置在环境变量中")
    return deepseek_api_key


# 你可以在这里添加更多配置，例如模型名称等
LLM_MODEL_NAME = "deepseek-v3"

# 嵌入模型配置
DASHSCOPE_EMBEDDING_MODEL_NAME = "text-embedding-v4"  # DashScope嵌入模型,Qwen3-Embedding
OPENAI_EMBEDDING_MODEL_NAME = "text-embedding-ada-002"  # OpenAI默认嵌入模型


def get_vector_db_path():
    """获取向量数据库路径"""
    vector_db_path = os.getenv("VECTOR_DB_PATH", "vector_store/")
    return vector_db_path

def get_embedding_model_name():
    """获取OpenAI嵌入模型名称
    
    如果环境变量中设置了EMBEDDING_MODEL_NAME，则使用该值
    否则使用默认的OpenAI嵌入模型名称
    """
    return os.getenv("EMBEDDING_MODEL_NAME", OPENAI_EMBEDDING_MODEL_NAME)


def get_collection_name():
    """获取ChromaDB集合名称"""
    collection_name = os.getenv("COLLECTION_NAME", "internal_docs")
    return collection_name


# 项目路径相关函数
def get_project_root():
    """获取项目根目录的绝对路径
    
    不管调用此函数的文件位于项目结构中的哪个位置，都能正确返回项目根目录
    
    Returns:
        Path: 项目根目录的绝对路径
    """
    # config.py位于src/rag_agent/core/目录下，所以需要向上三级才能到达项目根目录
    return Path(__file__).parent.parent.parent.parent


# RAG相关配置常量
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_RETRIEVAL_K = 3
