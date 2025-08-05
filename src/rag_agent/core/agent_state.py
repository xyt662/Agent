"""事件流驱动的AgentState架构 - 支持高级功能的可扩展状态管理系统"""

import operator
from datetime import datetime
from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal, Union
from enum import Enum
from dataclasses import dataclass

# LangChain消息系统的基础类型
from langchain_core.messages import BaseMessage


class EventType(str, Enum):
    """事件类型枚举 - 定义所有可能的事件类型"""
    # 基础事件
    STANDARD = "standard"
    SYSTEM = "system"
    
    # 高级功能事件
    MEMORY_STORE = "memory_store"          # 长期记忆存储
    MEMORY_RETRIEVE = "memory_retrieve"    # 长期记忆检索
    CORRECTION_TRIGGER = "correction_trigger"  # 自我纠错触发
    CORRECTION_ATTEMPT = "correction_attempt"  # 纠错尝试
    CLARIFICATION_REQUEST = "clarification_request"  # 主动澄清请求
    CLARIFICATION_RESPONSE = "clarification_response"  # 澄清响应
    AGENT_DELEGATION = "agent_delegation"  # 多智能体委派
    AGENT_CALLBACK = "agent_callback"      # 子智能体回调
    MULTI_HOP_STEP = "multi_hop_step"      # 多跳查询步骤
    MULTI_HOP_COMPLETE = "multi_hop_complete"  # 多跳查询完成


class EventStatus(str, Enum):
    """事件状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class EventMetadata:
    """标准化的事件元数据结构"""
    event_type: EventType
    event_id: str
    timestamp: datetime
    status: EventStatus = EventStatus.PENDING
    
    # 功能特定字段
    memory_key: Optional[str] = None              # 记忆系统相关
    correction_reason: Optional[str] = None       # 纠错原因
    clarification_question: Optional[str] = None  # 澄清问题
    target_agent: Optional[str] = None            # 目标智能体
    hop_index: Optional[int] = None               # 多跳查询索引
    parent_event_id: Optional[str] = None         # 父事件ID（用于事件链）
    
    # 扩展字段
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于BaseMessage的metadata"""
        return {
            "event_type": self.event_type.value,                      # 事件类型
            "event_id": self.event_id,                                # 事件ID，用于追踪和关联
            "timestamp": self.timestamp.isoformat(),                  # 事件发生时间戳
            "status": self.status.value,                              # 事件状态 (pending, in_progress, success, failed, cancelled)
            "memory_key": self.memory_key,                            # 记忆系统相关键值，用于存储和检索记忆
            "correction_reason": self.correction_reason,              # 自我纠错原因描述
            "clarification_question": self.clarification_question,    # 主动澄清问题
            "target_agent": self.target_agent,                        # 多智能体协作目标智能体标识
            "hop_index": self.hop_index,                              # 多跳查询索引
            "parent_event_id": self.parent_event_id,                  # 父事件ID，用于构建事件链和追踪事件关系
            "context": self.context                                   # 灵活的字典结构，存储额外的上下文信息
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventMetadata':
        """从字典创建EventMetadata实例"""
        return cls(
            event_type=EventType(data["event_type"]),
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            status=EventStatus(data["status"]),
            memory_key=data.get("memory_key"),
            correction_reason=data.get("correction_reason"),
            clarification_question=data.get("clarification_question"),
            target_agent=data.get("target_agent"),
            hop_index=data.get("hop_index"),
            parent_event_id=data.get("parent_event_id"),
            context=data.get("context", {})
        )


class AgentState(TypedDict):
    """
    事件流驱动的Agent状态 - 单一事实来源架构
    
    核心设计哲学：
    - 状态即事件流：所有状态变化都通过事件（消息）记录
    - 单一事实来源：完整的Agent生命周期记录在messages中
    - 对扩展开放：通过metadata扩展新功能，无需修改核心结构
    - 可观测性优先：每个决策都可追溯和复盘
    
    支持的高级功能：
    - 长期记忆：通过MEMORY_*事件类型管理记忆存储和检索
    - 自我纠错：通过CORRECTION_*事件类型实现错误检测和修正
    - 多智能体协作：通过AGENT_*事件类型管理委派和回调
    - 主动澄清：通过CLARIFICATION_*事件类型处理歧义
    - 多跳查询：通过MULTI_HOP_*事件类型管理复杂查询流程
    
    Attributes:
        messages: 完整的事件流，每个消息的metadata包含结构化的事件信息
    """
    
    messages: Annotated[List[BaseMessage], operator.add]
