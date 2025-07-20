import os
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

