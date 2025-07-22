#!/usr/bin/env python3
"""
向量数据库构建脚本

该脚本负责：
1. 加载原始文档
2. 切分文档为语义块
3. 生成嵌入向量
4. 存储到ChromaDB
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from rag_agent.core.config import (
    get_vector_db_path,
    get_collection_name,
    get_project_root,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP
)
from rag_agent.core.embedding_provider import get_embedding_model

def main():
    """构建向量数据库的主函数"""
    print("🚀 开始构建向量数据库...")
    
    try:
        # 1. 加载配置
        print("📋 加载配置...")
        vector_store_path = get_vector_db_path()
        collection_name = get_collection_name()
        
        print(f"   向量数据库路径: {vector_store_path}")
        print(f"   集合名称: {collection_name}")
        
        # 2. 加载原始文档
        print("📄 加载原始文档...")
        # 使用get_project_root()获取项目根目录
        doc_path = get_project_root() / "data" / "raw" / "internal_docs.txt"
        if not doc_path.exists():
            raise FileNotFoundError(f"文档文件不存在: {doc_path}")
            
        loader = TextLoader(str(doc_path), encoding='utf-8')
        documents = loader.load()
        print(f"   成功加载 {len(documents)} 个文档")
        
        # 3. 切分文档
        print("✂️ 切分文档...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=DEFAULT_CHUNK_SIZE,
            chunk_overlap=DEFAULT_CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        print(f"   文档切分完成，共 {len(chunks)} 个块")
        
        # 4. 初始化嵌入模型
        print("🤖 初始化嵌入模型...")
        embeddings = get_embedding_model()
        print(f"   嵌入模型初始化成功: {embeddings.__class__.__name__}")
        
        # 5. 创建并持久化ChromaDB
        print("💾 创建向量数据库...")
        
        # 确保向量存储目录存在
        vector_store_dir = get_project_root() / vector_store_path
        vector_store_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建ChromaDB实例
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=collection_name,
            persist_directory=str(vector_store_dir)
        )
        
        print(f"✅ 向量数据库构建成功！")
        print(f"   存储位置: {vector_store_dir}")
        print(f"   集合名称: {collection_name}")
        print(f"   文档块数量: {len(chunks)}")
        
        # 6. 测试检索功能
        print("🔍 测试检索功能...")
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        test_results = retriever.invoke("LangGraph的核心优势")
        print(f"   测试查询返回 {len(test_results)} 个结果")
        
        print("🎉 向量数据库构建完成！")
        
    except Exception as e:
        print(f"❌ 构建向量数据库时发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()