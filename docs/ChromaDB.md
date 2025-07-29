## ChromaDB持久化机制
- persist_directory：参数指定 ChromaDB 数据库的持久化目录，用于存储向量数据库中的数据
- ChromaDB 会在该目录下创建以下文件结构：
  - chroma.sqlite3：主数据库文件，存储集合元数据、文档文本和索引配置
  - [uuid]/：向量索引文件夹，包含：
    - data_level0.bin：文档嵌入向量数据
    - header.bin：索引头部信息
    - length.bin：向量长度信息
    - link_lists.bin：HNSW算法的链接列表
    
