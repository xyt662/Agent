from setuptools import setup, find_packages

setup(
    name="rag-agent",
    version="0.1.0",
    description="A RAG-based AI Agent using LangGraph",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "langchain",
        "langchain-core",
        "langgraph",
        "python-dotenv",
        # 添加其他依赖项
    ],
    entry_points={
        "console_scripts": [
            "rag-agent=rag_agent.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)