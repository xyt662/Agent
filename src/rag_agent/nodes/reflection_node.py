"""反思节点 - 演示事件驱动状态系统的高级功能实现"""

import uuid
from datetime import datetime
from typing import Dict, Any, List

from langchain_core.messages import AIMessage, BaseMessage
from ..core.agent_state import AgentState, EventType, EventStatus, EventMetadata
from ..core.state_aggregator import StateAggregator
from ..core.memory.memory_event_handler import MemoryEventHandler, create_memory_event_handler
from ..core.memory.memory_manager import MemoryManager


class ReflectionNode:
    """
    反思节点 - 实现自我纠错和长期记忆功能的示例节点
    
    这个节点演示了如何在LangGraph中与事件驱动的AgentState交互：
    1. 从状态中读取事件流
    2. 使用StateAggregator分析当前状态
    3. 基于分析结果做出决策
    4. 生成新的事件消息追加到状态
    
    支持的功能：
    - 错误检测和自我纠错
    - 长期记忆的存储和检索
    - 模式识别和学习
    """
    
    def __init__(self, error_threshold: int = 3, memory_retention_days: int = 30, storage_backend=None):
        self.error_threshold = error_threshold
        self.memory_retention_days = memory_retention_days
        # 初始化统一的记忆事件处理器
        self.memory_manager = MemoryManager(storage_backend=storage_backend)
        self.memory_event_handler = create_memory_event_handler(self.memory_manager)
    
    def __call__(self, state: AgentState) -> AgentState:
        """
        反思节点的主要逻辑
        
        工作流程：
        1. 读取当前状态（事件流）
        2. 聚合分析状态
        3. 检测是否需要纠错或记忆操作
        4. 生成相应的事件消息
        5. 返回更新后的状态
        """
        messages = state["messages"]
        new_messages = []
        
        # 1. 聚合当前状态
        current_state = StateAggregator.get_comprehensive_state(messages)
        
        # 2. 检查是否需要自我纠错
        correction_messages = self._check_and_trigger_correction(messages, current_state)
        new_messages.extend(correction_messages)
        
        # 3. 检查是否需要记忆操作（使用统一的事件处理器）
        memory_state = self.memory_event_handler.handle_memory_events(state)
        if len(memory_state["messages"]) > len(messages):
            # 如果有新的记忆事件消息，添加到结果中
            new_memory_messages = memory_state["messages"][len(messages):]
            new_messages.extend(new_memory_messages)
        
        # 4. 生成反思总结（如果有重要发现）
        reflection_message = self._generate_reflection_summary(current_state)
        if reflection_message:
            new_messages.append(reflection_message)
        
        # 5. 返回更新后的状态
        return {"messages": messages + new_messages}
    
    def _check_and_trigger_correction(self, messages: List[BaseMessage], 
                                     current_state: Dict[str, Any]) -> List[BaseMessage]:
        """
        检查是否需要触发自我纠错机制
        
        检查逻辑：
        1. 分析最近的错误模式
        2. 检测工具执行失败
        3. 识别重复性错误
        4. 触发纠错事件
        """
        correction_state = current_state['correction']
        new_messages = []
        
        # 检查错误模式
        error_patterns = correction_state['error_patterns']
        for error_type, count in error_patterns.items():
            if count >= self.error_threshold:
                # 触发纠错事件
                correction_event = self._create_correction_event(
                    reason=f"重复错误模式检测: {error_type} (出现{count}次)",
                    error_type=error_type
                )
                new_messages.append(correction_event)
        
        # 检查最近的工具执行失败
        recent_failures = self._detect_recent_tool_failures(messages)
        for failure in recent_failures:
            correction_event = self._create_correction_event(
                reason=f"工具执行失败: {failure['tool_name']}",
                error_type="tool_failure",
                context=failure
            )
            new_messages.append(correction_event)
        
        return new_messages
    
    # 记忆管理功能已迁移到统一的 MemoryEventHandler 中
    
    def _create_correction_event(self, reason: str, error_type: str, 
                               context: Dict[str, Any] = None) -> AIMessage:
        """
        创建自我纠错事件消息
        
        这个方法演示了如何创建包含结构化事件元数据的消息
        """
        event_id = str(uuid.uuid4())
        
        # 创建事件元数据
        event_metadata = EventMetadata(
            event_type=EventType.CORRECTION_TRIGGER,
            event_id=event_id,
            timestamp=datetime.now(),
            status=EventStatus.PENDING,
            correction_reason=reason,
            context=context or {}
        )
        
        # 创建AI消息，包含事件元数据
        message_content = f"🔍 检测到需要纠错的情况: {reason}"
        
        return AIMessage(
            content=message_content,
            additional_kwargs={
                "metadata": event_metadata.to_dict()
            }
        )
    
    # 记忆存储事件创建功能已迁移到 MemoryEventHandler 中
    
    # 记忆检索事件创建功能已迁移到 MemoryEventHandler 中
    
    def _detect_recent_tool_failures(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """
        检测最近的工具执行失败
        
        分析最近的ToolMessage，识别执行失败的工具
        """
        failures = []
        
        # 检查最近10条消息中的工具失败
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        
        for message in recent_messages:
            if hasattr(message, 'tool_call_id') and hasattr(message, 'content'):
                # 这是一个ToolMessage
                if "error" in message.content.lower() or "failed" in message.content.lower():
                    failures.append({
                        "tool_name": getattr(message, 'name', 'unknown'),
                        "error_content": message.content,
                        "timestamp": datetime.now()
                    })
        
        return failures
    
    def _extract_important_information(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """
        从消息中提取重要信息
        
        识别值得存储到长期记忆的信息
        """
        important_info = []
        
        # 简单的启发式规则：包含特定关键词的消息
        keywords = ["学习到", "发现", "重要", "记住", "经验", "教训"]
        
        for message in messages[-5:]:  # 检查最近5条消息
            if hasattr(message, 'content') and any(keyword in message.content for keyword in keywords):
                # 生成记忆键
                memory_key = f"insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                important_info.append({
                    "key": memory_key,
                    "content": message.content[:200]  # 限制长度
                })
        
        return important_info
    
    def _should_retrieve_memory(self, messages: List[BaseMessage]) -> bool:
        """
        判断是否需要检索记忆
        
        基于当前对话上下文判断是否需要检索相关的历史记忆
        """
        if not messages:
            return False
        
        # 检查最近的消息是否包含需要记忆检索的信号
        recent_message = messages[-1]
        if hasattr(recent_message, 'content'):
            retrieval_triggers = ["之前", "历史", "记得", "以前", "曾经"]
            return any(trigger in recent_message.content for trigger in retrieval_triggers)
        
        return False
    
    def _extract_current_context(self, messages: List[BaseMessage]) -> str:
        """
        提取当前对话上下文
        
        用于记忆检索的查询上下文
        """
        if not messages:
            return "general_context"
        
        recent_message = messages[-1]
        if hasattr(recent_message, 'content'):
            # 提取关键词作为上下文
            return recent_message.content[:100]  # 前100个字符作为上下文
        
        return "general_context"
    
    def _generate_reflection_summary(self, current_state: Dict[str, Any]) -> AIMessage:
        """
        生成反思总结
        
        基于当前状态生成反思和洞察
        """
        # 检查是否有值得总结的活动
        total_events = (
            len(current_state['correction']['active_corrections']) +
            len(current_state['memory']['recent_retrievals']) +
            len(current_state['collaboration']['active_delegations'])
        )
        
        if total_events == 0:
            return None
        
        # 生成反思总结
        summary_parts = []
        
        if current_state['correction']['active_corrections']:
            summary_parts.append(f"当前有{len(current_state['correction']['active_corrections'])}个纠错任务")
        
        if current_state['memory']['stored_memories']:
            summary_parts.append(f"长期记忆中存储了{len(current_state['memory']['stored_memories'])}条信息")
        
        if current_state['collaboration']['active_delegations']:
            summary_parts.append(f"有{len(current_state['collaboration']['active_delegations'])}个活跃的协作任务")
        
        summary_content = f"🤔 反思总结: {'; '.join(summary_parts)}"
        
        # 创建系统事件
        event_metadata = EventMetadata(
            event_type=EventType.SYSTEM,
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            status=EventStatus.SUCCESS,
            context={"reflection_summary": True}
        )
        
        return AIMessage(
            content=summary_content,
            additional_kwargs={
                "metadata": event_metadata.to_dict()
            }
        )


# 使用示例函数
def create_reflection_node() -> ReflectionNode:
    """
    创建反思节点的工厂函数
    
    可以根据需要配置不同的参数
    """
    return ReflectionNode(
        error_threshold=3,  # 错误阈值
        memory_retention_days=30  # 记忆保留天数
    )