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
DASHSCOPE_EMBEDDING_MODEL_NAME = "text-embedding-v1"  # DashScope嵌入模型,1024维向量
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

# RAG检索优化配置
DEFAULT_SCORE_THRESHOLD = 0.6  # 相似度阈值
DEFAULT_USE_MMR = False  # 是否使用MMR算法
DEFAULT_USE_QUERY_EXPANSION = True  # 是否使用查询扩展
DEFAULT_USE_RERANKING = True  # 是否使用重排序
DEFAULT_MMR_FETCH_K = 20  # MMR算法获取文档数
DEFAULT_MMR_LAMBDA = 0.5  # MMR多样性参数


def get_retrieval_config():
    """获取检索优化配置
    
    Returns:
        dict: 包含所有检索优化参数的字典
    """
    return {
        'score_threshold': float(os.getenv('RAG_SCORE_THRESHOLD', DEFAULT_SCORE_THRESHOLD)),
        'use_mmr': os.getenv('RAG_USE_MMR', str(DEFAULT_USE_MMR)).lower() == 'true',
        'use_query_expansion': os.getenv('RAG_USE_QUERY_EXPANSION', str(DEFAULT_USE_QUERY_EXPANSION)).lower() == 'true',
        'use_reranking': os.getenv('RAG_USE_RERANKING', str(DEFAULT_USE_RERANKING)).lower() == 'true',
        'mmr_fetch_k': int(os.getenv('RAG_MMR_FETCH_K', DEFAULT_MMR_FETCH_K)),
        'mmr_lambda': float(os.getenv('RAG_MMR_LAMBDA', DEFAULT_MMR_LAMBDA))
    }


# MCP工具配置
def get_mcp_enabled():
    """获取MCP工具启用状态"""
    return os.getenv("MCP_ENABLED", "true").lower() == "true"


def get_mcp_manifests_dir():
    """获取MCP清单文件目录路径"""
    default_path = get_project_root() / "src" / "rag_agent" / "tools" / "mcp_manifests"
    return Path(os.getenv("MCP_MANIFESTS_DIR", str(default_path)))


def get_mcp_allowed_domains():
    """获取MCP工具允许访问的域名白名单
    
    Returns:
        list: 允许访问的域名列表
    """
    # 默认白名单包含一些常用的安全API服务
    default_domains = "https://httpbin.org,https://api.github.com,https://jsonplaceholder.typicode.com"
    domains_str = os.getenv("MCP_ALLOWED_DOMAINS", default_domains)
    
    # 解析逗号分隔的域名列表
    domains = [domain.strip() for domain in domains_str.split(",") if domain.strip()]
    return domains
