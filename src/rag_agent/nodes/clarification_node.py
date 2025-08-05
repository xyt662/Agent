#!/usr/bin/env python3
"""
主动澄清节点模块

当用户输入模糊或不明确时，主动向用户提问以获取更准确的信息。
"""

import uuid
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from ..core.agent_state import AgentState, EventType, EventStatus, EventMetadata
from ..core.event_utils import EventQueryHelper


class ClarificationEventFactory:
    """
    澄清事件工厂类
    
    负责创建澄清相关的事件消息。
    """
    
    @staticmethod
    def create_clarification_request_event(question: str,
                                         status: EventStatus = EventStatus.PENDING,
                                         context: Optional[Dict[str, Any]] = None) -> AIMessage:
        """
        创建主动澄清请求事件
        
        Args:
            question: 澄清问题
            status: 事件状态
            context: 额外的上下文信息
        
        Returns:
            包含澄清请求事件元数据的AIMessage
        """
        event_metadata = EventMetadata(
            event_type=EventType.CLARIFICATION_REQUEST,
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            status=status,
            clarification_question=question,
            context=context or {}
        )
        
        message_content = f"❓ 请求澄清: {question}"
        
        return AIMessage(
            content=message_content,
            additional_kwargs={"metadata": event_metadata.to_dict()}
        )
    
    @staticmethod
    def create_clarification_response_event(answer: str, 
                                          parent_event_id: str,
                                          status: EventStatus = EventStatus.SUCCESS,
                                          context: Optional[Dict[str, Any]] = None) -> HumanMessage:
        """
        创建澄清响应事件（通常是用户响应）
        
        Args:
            answer: 澄清答案
            parent_event_id: 对应的澄清请求事件ID
            status: 事件状态
            context: 额外的上下文信息
        
        Returns:
            包含澄清响应事件元数据的HumanMessage
        """
        event_metadata = EventMetadata(
            event_type=EventType.CLARIFICATION_RESPONSE,
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            status=status,
            parent_event_id=parent_event_id,
            context=context or {"answer": answer}
        )
        
        return HumanMessage(
            content=answer,
            additional_kwargs={"metadata": event_metadata.to_dict()}
        )


class AmbiguityDetector:
    """
    模糊性检测器
    
    检测用户输入中的模糊或不明确的部分。
    """
    
    def __init__(self):
        # 模糊指示词
        self.ambiguous_patterns = [
            r'这个|那个|它|他|她',  # 代词
            r'某个|一些|几个|很多',  # 不确定数量
            r'可能|也许|大概|估计',  # 不确定性词汇
            r'什么|哪个|怎么|为什么',  # 疑问词
            r'文件|东西|内容|资料',  # 泛指词
        ]
        
        # 需要澄清的关键词
        self.clarification_triggers = [
            '文件', '报告', '数据', '图片', '视频', '音频',
            '项目', '任务', '计划', '方案', '策略',
            '时间', '地点', '人员', '部门', '公司'
        ]
    
    def detect_ambiguity(self, text: str) -> Dict[str, Any]:
        """
        检测文本中的模糊性
        
        Args:
            text: 输入文本
        
        Returns:
            检测结果，包含模糊性类型和建议的澄清问题
        """
        ambiguities = []
        
        # 检查模糊模式
        for pattern in self.ambiguous_patterns:
            matches = re.findall(pattern, text)
            if matches:
                ambiguities.append({
                    'type': 'pronoun' if pattern == self.ambiguous_patterns[0] else 'uncertainty',
                    'matches': matches,
                    'pattern': pattern
                })
        
        # 检查是否包含需要澄清的关键词但缺乏具体信息
        missing_specifics = []
        for trigger in self.clarification_triggers:
            if trigger in text:
                # 检查是否有具体的描述
                if not self._has_specific_description(text, trigger):
                    missing_specifics.append(trigger)
        
        return {
            'has_ambiguity': len(ambiguities) > 0 or len(missing_specifics) > 0,
            'ambiguous_patterns': ambiguities,
            'missing_specifics': missing_specifics,
            'confidence': self._calculate_confidence(ambiguities, missing_specifics)
        }
    
    def _has_specific_description(self, text: str, keyword: str) -> bool:
        """
        检查关键词是否有具体描述
        
        Args:
            text: 文本
            keyword: 关键词
        
        Returns:
            是否有具体描述
        """
        # 简单的启发式规则
        keyword_index = text.find(keyword)
        if keyword_index == -1:
            return True
        
        # 检查关键词前后是否有修饰词
        before = text[:keyword_index].split()[-2:] if keyword_index > 0 else []
        after = text[keyword_index + len(keyword):].split()[:2]
        
        descriptors = before + after
        
        # 如果有具体的修饰词，认为有具体描述
        specific_words = ['具体', '详细', '特定', '明确', '准确']
        return any(word in ' '.join(descriptors) for word in specific_words)
    
    def _calculate_confidence(self, ambiguities: List[Dict], missing_specifics: List[str]) -> float:
        """
        计算模糊性检测的置信度
        
        Args:
            ambiguities: 模糊模式列表
            missing_specifics: 缺乏具体信息的关键词列表
        
        Returns:
            置信度分数 (0-1)
        """
        score = 0.0
        
        # 模糊模式权重
        for amb in ambiguities:
            if amb['type'] == 'pronoun':
                score += 0.3
            else:
                score += 0.2
        
        # 缺乏具体信息权重
        score += len(missing_specifics) * 0.25
        
        return min(score, 1.0)


class ClarificationGenerator:
    """
    澄清问题生成器
    
    根据检测到的模糊性生成合适的澄清问题。
    """
    
    def __init__(self):
        self.question_templates = {
            'pronoun': [
                "您提到的'{}'具体指的是什么？",
                "能否具体说明一下'{}'是什么？",
                "请明确指出'{}'的具体内容。"
            ],
            'file': [
                "您指的是哪个具体的文件？请提供文件名或路径。",
                "能否提供更多关于该文件的信息，比如文件类型、位置等？",
                "请具体说明您要处理的文件。"
            ],
            'time': [
                "您指的是什么时间？请提供具体的日期或时间范围。",
                "能否明确时间要求？比如截止日期、开始时间等。",
                "请具体说明时间相关的要求。"
            ],
            'general': [
                "能否提供更多具体信息？",
                "请详细说明您的需求。",
                "为了更好地帮助您，请提供更多细节。"
            ]
        }
    
    def generate_clarification_question(self, ambiguity_result: Dict[str, Any], 
                                      original_text: str) -> str:
        """
        生成澄清问题
        
        Args:
            ambiguity_result: 模糊性检测结果
            original_text: 原始文本
        
        Returns:
            澄清问题
        """
        if not ambiguity_result['has_ambiguity']:
            return ""
        
        questions = []
        
        # 处理代词模糊性
        for amb in ambiguity_result['ambiguous_patterns']:
            if amb['type'] == 'pronoun':
                for match in amb['matches']:
                    template = self._select_template('pronoun')
                    questions.append(template.format(match))
        
        # 处理缺乏具体信息的关键词
        for keyword in ambiguity_result['missing_specifics']:
            if keyword in ['文件', '报告', '数据']:
                template = self._select_template('file')
            elif keyword in ['时间', '日期']:
                template = self._select_template('time')
            else:
                template = self._select_template('general')
            
            questions.append(template)
        
        # 如果没有具体问题，使用通用问题
        if not questions:
            questions.append(self._select_template('general'))
        
        # 合并问题
        if len(questions) == 1:
            return questions[0]
        else:
            return "我需要澄清几个问题：\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
    
    def _select_template(self, category: str) -> str:
        """
        选择问题模板
        
        Args:
            category: 问题类别
        
        Returns:
            问题模板
        """
        templates = self.question_templates.get(category, self.question_templates['general'])
        return templates[0]  # 简单选择第一个模板


class ClarificationNode:
    """
    主动澄清节点
    
    检测用户输入的模糊性并主动提出澄清问题。
    """
    
    def __init__(self):
        self.detector = AmbiguityDetector()
        self.generator = ClarificationGenerator()
        self.min_confidence = 0.3  # 最小置信度阈值
    
    def should_clarify(self, state: AgentState) -> bool:
        """
        判断是否需要澄清
        
        Args:
            state: 当前状态
        
        Returns:
            是否需要澄清
        """
        # 获取最新的用户消息
        user_message = None
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                user_message = message.content
                break
        
        if not user_message:
            return False
        
        # 检测模糊性
        ambiguity_result = self.detector.detect_ambiguity(user_message)
        
        # 检查是否已经有待处理的澄清请求
        pending_clarifications = EventQueryHelper.find_events_by_status(
            state["messages"], EventStatus.PENDING
        )
        
        clarification_pending = any(
            event.additional_kwargs.get("metadata", {}).get("event_type") == EventType.CLARIFICATION_REQUEST.value
            for event in pending_clarifications
        )
        
        return (ambiguity_result['has_ambiguity'] and 
                ambiguity_result['confidence'] >= self.min_confidence and
                not clarification_pending)
    
    def process_clarification(self, state: AgentState) -> AgentState:
        """
        处理澄清逻辑
        
        Args:
            state: 当前状态
        
        Returns:
            更新后的状态
        """
        # 获取最新的用户消息
        user_message = None
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                user_message = message.content
                break
        
        if not user_message:
            return state
        
        # 检测模糊性
        ambiguity_result = self.detector.detect_ambiguity(user_message)
        
        if not ambiguity_result['has_ambiguity']:
            return state
        
        # 生成澄清问题
        clarification_question = self.generator.generate_clarification_question(
            ambiguity_result, user_message
        )
        
        if clarification_question:
            # 创建澄清请求事件
            clarification_event = ClarificationEventFactory.create_clarification_request_event(
                question=clarification_question,
                status=EventStatus.PENDING,
                context={
                    "original_message": user_message,
                    "ambiguity_result": ambiguity_result
                }
            )
            
            # 添加到消息流
            state["messages"].append(clarification_event)
            
            # 设置澄清状态
            state["needs_clarification"] = True
            state["clarification_event_id"] = clarification_event.additional_kwargs["metadata"]["event_id"]
        
        return state
    
    def handle_clarification_response(self, state: AgentState, user_response: str) -> AgentState:
        """
        处理用户的澄清响应
        
        Args:
            state: 当前状态
            user_response: 用户响应
        
        Returns:
            更新后的状态
        """
        clarification_event_id = state.get("clarification_event_id")
        
        if clarification_event_id:
            # 创建澄清响应事件
            response_event = ClarificationEventFactory.create_clarification_response_event(
                answer=user_response,
                parent_event_id=clarification_event_id,
                status=EventStatus.SUCCESS
            )
            
            # 添加到消息流
            state["messages"].append(response_event)
            
            # 更新原澄清请求的状态
            for message in state["messages"]:
                if (message.additional_kwargs.get("metadata", {}).get("event_id") == clarification_event_id):
                    message.additional_kwargs["metadata"]["status"] = EventStatus.SUCCESS.value
                    break
            
            # 清理澄清状态
            state["needs_clarification"] = False
            state.pop("clarification_event_id", None)
        
        return state


def create_clarification_node() -> ClarificationNode:
    """
    创建澄清节点实例
    
    Returns:
        配置好的澄清节点
    """
    return ClarificationNode()


def clarification_node_function(state: AgentState) -> AgentState:
    """
    澄清节点函数，用于集成到LangGraph中
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    node = create_clarification_node()
    
    # 检查是否需要澄清
    if node.should_clarify(state):
        state = node.process_clarification(state)
    
    return state