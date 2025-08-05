#!/usr/bin/env python3
"""
ChromaDB 存储实现

基于 ChromaDB 的高性能向量存储实现，支持：
- 向量相似性搜索
- 元数据过滤
- 混合查询
- 会话历史管理
- 长期记忆存储
"""

import json
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.embeddings import Embeddings

from .base import BaseStore, StorageDocument, SearchResult
try:
    from ..core.embedding_provider import get_embedding_model
except ImportError:
    get_embedding_model = None
from ..core.config import get_project_root


class ChromaStore(BaseStore):
    """
    基于 ChromaDB 的存储实现
    
    利用 ChromaDB 的向量存储和元数据过滤能力，
    为 AI 应用提供高性能的存储服务。
    """
    
    def __init__(
        self,
        storage_dir: Optional[Union[str, Path]] = None,
        collection_name: str = "synapseagent_storage",
        embedding_model: Optional[Embeddings] = None
    ):
        """
        初始化 ChromaDB 存储
        
        Args:
            storage_dir: 存储目录路径
            collection_name: 集合名称
            embedding_model: 嵌入模型
        """
        # 设置存储目录
        if storage_dir is None:
            project_root = get_project_root()
            storage_dir = project_root / "data" / "chroma_storage"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(
            path=str(self.storage_dir),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 初始化嵌入模型
        if embedding_model:
            self.embedding_model = embedding_model
        elif get_embedding_model:
            self.embedding_model = get_embedding_model()
        else:
            raise ValueError("No embedding model provided and get_embedding_model is not available")
        
        # 初始化集合
        self.collection_name = collection_name
        self.collection = self._get_or_create_collection(collection_name)
        
        # 专用集合
        self.session_collection = self._get_or_create_collection(f"{collection_name}_sessions")
        self.memory_collection = self._get_or_create_collection(f"{collection_name}_memories")
    
    def _get_or_create_collection(self, name: str):
        """获取或创建集合"""
        try:
            return self.client.get_collection(name=name)
        except Exception:
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def _embed_text(self, text: str) -> List[float]:
        """生成文本嵌入"""
        try:
            embeddings = self.embedding_model.embed_documents([text])
            return embeddings[0]
        except Exception as e:
            print(f"生成嵌入时出错: {e}")
            # 返回零向量作为后备
            return [0.0] * 1536  # 假设使用 OpenAI 嵌入维度
    
    def _message_to_dict(self, message: BaseMessage) -> Dict[str, Any]:
        """将消息转换为字典"""
        return {
            'type': message.__class__.__name__,
            'content': message.content,
            'additional_kwargs': getattr(message, 'additional_kwargs', {})
        }
    
    def _dict_to_message(self, data: Dict[str, Any]) -> BaseMessage:
        """将字典转换为消息"""
        message_type = data.get('type', 'HumanMessage')
        content = data.get('content', '')
        additional_kwargs = data.get('additional_kwargs', {})
        
        if message_type == 'HumanMessage':
            return HumanMessage(content=content, additional_kwargs=additional_kwargs)
        elif message_type == 'AIMessage':
            return AIMessage(content=content, additional_kwargs=additional_kwargs)
        elif message_type == 'ToolMessage':
            return ToolMessage(content=content, additional_kwargs=additional_kwargs)
        else:
            return HumanMessage(content=content, additional_kwargs=additional_kwargs)
    
    def store_document(self, document: StorageDocument) -> bool:
        """
        存储文档
        """
        try:
            # 生成嵌入
            if document.embedding is None:
                document.embedding = self._embed_text(document.content)
            
            # 准备元数据
            metadata = document.metadata.copy()
            metadata['timestamp'] = document.timestamp.isoformat()
            
            # 存储到 ChromaDB
            self.collection.add(
                ids=[document.id],
                documents=[document.content],
                embeddings=[document.embedding],
                metadatas=[metadata]
            )
            
            return True
            
        except Exception as e:
            print(f"存储文档时出错: {e}")
            return False
    
    def store_documents(self, documents: List[StorageDocument]) -> bool:
        """
        批量存储文档
        """
        try:
            ids = []
            contents = []
            embeddings = []
            metadatas = []
            
            for doc in documents:
                # 生成嵌入
                if doc.embedding is None:
                    doc.embedding = self._embed_text(doc.content)
                
                # 准备数据
                metadata = doc.metadata.copy()
                metadata['timestamp'] = doc.timestamp.isoformat()
                
                ids.append(doc.id)
                contents.append(doc.content)
                embeddings.append(doc.embedding)
                metadatas.append(metadata)
            
            # 批量存储
            self.collection.add(
                ids=ids,
                documents=contents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            return True
            
        except Exception as e:
            print(f"批量存储文档时出错: {e}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[StorageDocument]:
        """
        根据 ID 获取文档
        """
        try:
            result = self.collection.get(
                ids=[doc_id],
                include=['documents', 'metadatas', 'embeddings']
            )
            
            if not result['ids']:
                return None
            
            # 构造文档对象
            metadata = result['metadatas'][0]
            timestamp_str = metadata.pop('timestamp', datetime.now().isoformat())
            
            return StorageDocument(
                id=result['ids'][0],
                content=result['documents'][0],
                metadata=metadata,
                timestamp=datetime.fromisoformat(timestamp_str),
                embedding=result['embeddings'][0] if result['embeddings'] else None
            )
            
        except Exception as e:
            print(f"获取文档时出错: {e}")
            return None
    
    def delete_document(self, doc_id: str) -> bool:
        """
        删除文档
        """
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            print(f"删除文档时出错: {e}")
            return False
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        向量相似性搜索
        """
        try:
            # 生成查询嵌入
            query_embedding = self._embed_text(query)
            
            # 执行搜索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=metadata_filter,
                include=['documents', 'metadatas', 'distances']
            )
            
            # 构造搜索结果
            search_results = []
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i].copy()
                timestamp_str = metadata.pop('timestamp', datetime.now().isoformat())
                
                # 解析存储的字符串格式数据
                if 'tags' in metadata and metadata['tags']:
                    metadata['tags'] = metadata['tags'].split(',') if metadata['tags'] else []
                else:
                    metadata['tags'] = []
                    
                if 'context' in metadata and metadata['context']:
                    try:
                        metadata['context'] = json.loads(metadata['context'])
                    except (json.JSONDecodeError, TypeError):
                        metadata['context'] = {}
                else:
                    metadata['context'] = {}
                
                document = StorageDocument(
                    id=results['ids'][0][i],
                    content=results['documents'][0][i],
                    metadata=metadata,
                    timestamp=datetime.fromisoformat(timestamp_str)
                )
                
                # 计算相似度评分（距离转换为相似度）
                distance = results['distances'][0][i]
                score = 1.0 - distance  # 余弦距离转相似度
                
                search_results.append(SearchResult(
                    document=document,
                    score=score,
                    distance=distance
                ))
            
            return search_results
            
        except Exception as e:
            print(f"相似性搜索时出错: {e}")
            return []
    
    def metadata_search(
        self,
        metadata_filter: Dict[str, Any],
        limit: int = 10
    ) -> List[StorageDocument]:
        """
        基于元数据的精确搜索
        """
        try:
            results = self.collection.get(
                where=metadata_filter,
                limit=limit,
                include=['documents', 'metadatas']
            )
            
            documents = []
            for i in range(len(results['ids'])):
                metadata = results['metadatas'][i]
                timestamp_str = metadata.pop('timestamp', datetime.now().isoformat())
                
                documents.append(StorageDocument(
                    id=results['ids'][i],
                    content=results['documents'][i],
                    metadata=metadata,
                    timestamp=datetime.fromisoformat(timestamp_str)
                ))
            
            return documents
            
        except Exception as e:
            print(f"元数据搜索时出错: {e}")
            return []
    
    def hybrid_search(
        self,
        query: str,
        metadata_filter: Optional[Dict[str, Any]] = None,
        k: int = 10,
        similarity_threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        混合搜索（语义相似性 + 元数据过滤）
        """
        # 执行相似性搜索，同时应用元数据过滤
        results = self.similarity_search(query, k, metadata_filter)
        
        # 应用相似度阈值过滤
        filtered_results = [
            result for result in results 
            if result.score >= similarity_threshold
        ]
        
        return filtered_results
    
    def store_session_message(
        self,
        session_id: str,
        message: BaseMessage,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        存储会话消息
        """
        try:
            # 生成消息 ID
            message_id = f"{session_id}_{uuid.uuid4().hex[:8]}"
            
            # 准备消息内容
            message_dict = self._message_to_dict(message)
            content = json.dumps(message_dict, ensure_ascii=False)
            
            # 准备元数据
            msg_metadata = {
                'session_id': session_id,
                'message_type': message.__class__.__name__,
                'timestamp': datetime.now().isoformat()
            }
            if metadata:
                msg_metadata.update(metadata)
            
            # 生成嵌入
            embedding = self._embed_text(message.content)
            
            # 存储到会话集合
            self.session_collection.add(
                ids=[message_id],
                documents=[content],
                embeddings=[embedding],
                metadatas=[msg_metadata]
            )
            
            return True
            
        except Exception as e:
            print(f"存储会话消息时出错: {e}")
            return False
    
    def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[BaseMessage]:
        """
        获取会话历史
        """
        try:
            # 构建查询条件
            where_filter = {'session_id': session_id}
            
            if start_time or end_time:
                time_filter = {}
                if start_time:
                    time_filter['$gte'] = start_time.isoformat()
                if end_time:
                    time_filter['$lte'] = end_time.isoformat()
                where_filter['timestamp'] = time_filter
            
            # 查询消息
            results = self.session_collection.get(
                where=where_filter,
                limit=limit,
                include=['documents', 'metadatas']
            )
            
            # 转换为消息对象
            messages = []
            for i in range(len(results['ids'])):
                content = results['documents'][i]
                message_dict = json.loads(content)
                message = self._dict_to_message(message_dict)
                messages.append(message)
            
            # 按时间戳排序
            messages.sort(key=lambda m: getattr(m, 'timestamp', datetime.now()))
            
            return messages
            
        except Exception as e:
            print(f"获取会话历史时出错: {e}")
            return []
    
    def store_memory(
        self,
        memory_key: str,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        importance: int = 5,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> bool:
        """
        存储长期记忆
        """
        try:
            # 准备元数据（ChromaDB只支持基本类型）
            metadata = {
                'memory_key': memory_key,
                'importance': importance,
                'timestamp': datetime.now().isoformat(),
                'tags': ','.join(tags) if tags else '',  # 转换为字符串
                'context': json.dumps(context or {})  # 转换为JSON字符串
            }
            
            if user_id:
                metadata['user_id'] = user_id
            if event_type:
                metadata['event_type'] = event_type
            
            # 生成嵌入
            embedding = self._embed_text(content)
            
            # 存储到记忆集合
            self.memory_collection.add(
                ids=[memory_key],
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata]
            )
            
            return True
            
        except Exception as e:
            print(f"存储记忆时出错: {e}")
            return False
    
    def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        importance_threshold: Optional[int] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        搜索长期记忆
        """
        try:
            # 构建元数据过滤条件
            where_filter = {}
            
            if user_id:
                where_filter['user_id'] = user_id
            
            if importance_threshold:
                where_filter['importance'] = {'$gte': importance_threshold}
            
            if tags:
                # 由于标签现在存储为逗号分隔的字符串，需要使用包含查询
                # 简化处理：检查标签字符串是否包含任一指定标签
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append({'tags': {'$contains': tag}})
                if len(tag_conditions) == 1:
                    where_filter.update(tag_conditions[0])
                else:
                    where_filter['$or'] = tag_conditions
            
            # 生成查询嵌入
            query_embedding = self._embed_text(query)
            
            # 执行搜索
            results = self.memory_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter if where_filter else None,
                include=['documents', 'metadatas', 'distances']
            )
            
            # 构造搜索结果
            search_results = []
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i].copy()
                timestamp_str = metadata.pop('timestamp', datetime.now().isoformat())
                
                # 解析存储的字符串格式数据
                if 'tags' in metadata and metadata['tags']:
                    metadata['tags'] = metadata['tags'].split(',') if metadata['tags'] else []
                else:
                    metadata['tags'] = []
                    
                if 'context' in metadata and metadata['context']:
                    try:
                        metadata['context'] = json.loads(metadata['context'])
                    except (json.JSONDecodeError, TypeError):
                        metadata['context'] = {}
                else:
                    metadata['context'] = {}
                
                document = StorageDocument(
                    id=results['ids'][0][i],
                    content=results['documents'][0][i],
                    metadata=metadata,
                    timestamp=datetime.fromisoformat(timestamp_str)
                )
                
                # 计算相似度评分
                distance = results['distances'][0][i]
                score = 1.0 - distance
                
                search_results.append(SearchResult(
                    document=document,
                    score=score,
                    distance=distance
                ))
            
            return search_results
            
        except Exception as e:
            print(f"搜索记忆时出错: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        """
        try:
            # 获取各集合的统计信息
            main_count = self.collection.count()
            session_count = self.session_collection.count()
            memory_count = self.memory_collection.count()
            
            return {
                'total_documents': main_count,
                'session_messages': session_count,
                'stored_memories': memory_count,
                'storage_directory': str(self.storage_dir),
                'collections': {
                    'main': self.collection_name,
                    'sessions': f"{self.collection_name}_sessions",
                    'memories': f"{self.collection_name}_memories"
                }
            }
            
        except Exception as e:
            print(f"获取统计信息时出错: {e}")
            return {}
    
    def clear_collection(self, collection_name: Optional[str] = None) -> bool:
        """
        清空集合
        """
        try:
            if collection_name:
                collection = self.client.get_collection(collection_name)
                collection.delete()
            else:
                # 清空所有集合
                self.collection.delete()
                self.session_collection.delete()
                self.memory_collection.delete()
            
            return True
            
        except Exception as e:
            print(f"清空集合时出错: {e}")
            return False