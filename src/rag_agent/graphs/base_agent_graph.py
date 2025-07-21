import logging
from functools import partial
from langchain_core.agents import AgentFinish
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from rag_agent.core.agent_state import AgentState
from rag_agent.core.config import get_deepseek_api_key, LLM_MODEL_NAME
from rag_agent.nodes.agent_node import agent_node
from rag_agent.nodes.tool_node import tool_node

# --- 1. 定义一个伪工具用于测试 ---
# 在任务1.2中，我们会用真实的知识库工具替换它
from langchain.tools import tool


@tool
def fake_tool(query: str) -> str:
    """这是一个用于测试的伪工具，它总是返回一个固定的字符串。"""
    print(f"伪工具被调用，查询: {query}")
    return "这是一个来自伪工具的回答。"


tools = [fake_tool]

# --- 2. 初始化模型和工具执行器 ---
# 确保 API Key 被加载
api_key = get_deepseek_api_key()

llm = init_chat_model(
    model="deepseek-chat", model_provider="deepseek", temperature=0, api_key=api_key
)
llm_with_tools = llm.bind_tools(tools)
# 使用新的 ToolNode 替代 ToolExecutor
tool_node_executor = ToolNode(tools)

# --- 3. 将节点函数与参数绑定 ---
# 使用 partial 来预先填充 agent 和 tool_executor 参数，使节点函数符合 LangGraph 的期望签名
agent_node_with_tools = partial(agent_node, agent=None, llm_with_tools=llm_with_tools)
# ToolNode 可以直接作为节点使用，不需要包装
# tool_node_with_executor = partial(tool_node, tool_executor=tool_executor)


# --- 4. 定义图的路由逻辑 (条件边) ---
def should_continue(state: AgentState) -> str:
    """
    决定流程走向的条件边
    """
    print("--- 路由判断 ---")
    if isinstance(state["agent_outcome"], AgentFinish):
        print("决策：结束")
        return "end"
    else:
        print("决策：继续调用工具")
        return "continue"


# --- 5. 定义并编译图 ---
def create_agent_graph():
    """
    创建并编译 Agent 的状态图
    已弃用：建议使用 agent_factory.get_main_agent_runnable() 替代
    """
    import warnings

    warnings.warn(
        "create_agent_graph() 已弃用，请使用 agent_factory.get_main_agent_runnable()",
        DeprecationWarning,
        stacklevel=2,
    )

    try:
        # 使用工厂方法创建Agent，保持向后兼容
        from rag_agent.factories.agent_factory import AgentBuilder

        builder = AgentBuilder(llm=llm, tools=tools)
        app = builder.build()
        print("Agent 图编译完成")
        return app
    except Exception as e:
        print(f"Agent 图创建失败: {e}")
        # 回退到原始实现
        graph = StateGraph(AgentState)

        # 添加节点
        graph.add_node("agent", agent_node_with_tools)
        graph.add_node("action", tool_node_executor)

        # 设置入口点
        graph.set_entry_point("agent")

        # 添加条件边
        graph.add_conditional_edges(
            "agent",
            should_continue,
            {
                "continue": "action",
                "end": END,
            },
        )

        # 添加普通边
        graph.add_edge("action", "agent")

        # 编译图
        app = graph.compile()
        print("Agent 图编译完成（回退模式）")
        return app


def create_modern_agent_graph():
    """
    推荐的Agent创建方法,使用工厂模式
    这是create_agent_graph()的现代化替代方案
    """
    try:
        from rag_agent.factories.agent_factory import get_main_agent_runnable

        return get_main_agent_runnable()
    except ImportError as e:
        logging.warning(f"无法导入agent_factory: {e}，回退到传统方法")
        return create_agent_graph()
    except Exception as e:
        logging.error(f"创建Agent失败: {e}")
        raise e