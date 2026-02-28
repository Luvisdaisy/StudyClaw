import asyncio
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph.message import add_messages

from agent.tools.agent_tools import (
    get_current_month,
    get_weather,
    get_user_location,
    get_user_id,
    fetch_external_data,
    fill_context_for_report,
    rag_summarize,
)
from agent.tools.middleware import (
    log_before_model_node,
    log_after_model_node,
    should_use_report_prompt,
    get_prompt_for_context,
)
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts, load_report_prompts


class AgentState(TypedDict):
    """Agent 状态定义"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    context: dict


def create_langgraph_agent():
    """创建自定义 LangGraph Agent"""

    # 定义工具列表
    tools = [
        rag_summarize,
        get_weather,
        get_user_location,
        get_user_id,
        get_current_month,
        fetch_external_data,
        fill_context_for_report,
    ]

    # 创建工具节点
    tool_node = ToolNode(tools)

    def call_model_node(state: AgentState) -> AgentState:
        """模型调用节点 - 根据 context 选择提示词"""
        context = state.get("context", {})

        # 根据 context 选择提示词
        if context.get("report", False):
            system_prompt = load_report_prompts()
        else:
            system_prompt = load_system_prompts()

        # 构建带系统提示的消息
        system_msg = SystemMessage(content=system_prompt)
        response = chat_model.bind_tools(tools).invoke([system_msg] + list(state["messages"]))

        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        """条件边：判断是否需要工具调用"""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"

    # 构建图
    builder = StateGraph(AgentState)

    # 添加节点
    builder.add_node("log_before_model", log_before_model_node)
    builder.add_node("model", call_model_node)
    builder.add_node("tools", tool_node)
    builder.add_node("log_after_model", log_after_model_node)

    # 添加边
    builder.add_edge(START, "log_before_model")
    builder.add_edge("log_before_model", "model")

    # 条件边：判断是否需要工具调用
    builder.add_conditional_edges("model", should_continue, {"tools": "tools", "end": "log_after_model"})
    builder.add_edge("tools", "model")  # 工具执行后回到模型

    # 后置日志后结束
    builder.add_edge("log_after_model", END)

    # 编译并添加 checkpointer
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


class ReactAgent:
    """React Agent 类 - 使用自定义 StateGraph"""

    def __init__(self):
        self.agent = create_langgraph_agent()
        self._context = {"report": False}

    def _update_context_from_tool_calls(self, messages: list[BaseMessage]) -> None:
        """从消息中提取工具调用并更新上下文"""
        for msg in messages:
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls"):
                if msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        if tool_call.get("name") == "fill_context_for_report":
                            self._context["report"] = True
                            return

    def execute_stream(self, query: str, session_id: str = "default"):
        """流式执行查询"""
        # 根据上下文获取适当的提示词
        prompt = get_prompt_for_context(self._context)

        # 构建消息
        messages = [HumanMessage(content=query)]

        # 使用 session_id 作为 thread_id 实现会话持久化
        config = {"configurable": {"thread_id": session_id}}

        # 如果有系统提示词，先添加
        if prompt:
            # 检查是否已有系统消息
            if not any(isinstance(m, SystemMessage) for m in []):
                # 在消息前添加系统提示
                messages.insert(0, SystemMessage(content=prompt))

        try:
            # 流式执行
            for chunk in self.agent.stream(
                {"messages": messages, "context": self._context},
                config=config,
            ):
                # 处理每个 chunk
                if "messages" in chunk:
                    latest_message = chunk["messages"][-1]
                    if hasattr(latest_message, "content") and latest_message.content:
                        # 检查是否有工具调用，更新上下文
                        if isinstance(latest_message, AIMessage):
                            self._update_context_from_tool_calls([latest_message])
                        yield latest_message.content.strip() + "\n"

                # 处理 agent 节点的输出
                if "agent" in chunk:
                    agent_output = chunk["agent"]
                    if "messages" in agent_output:
                        latest_message = agent_output["messages"][-1]
                        if hasattr(latest_message, "content") and latest_message.content:
                            yield latest_message.content.strip() + "\n"

                # 处理 model 节点的输出
                if "model" in chunk:
                    model_output = chunk["model"]
                    if "messages" in model_output:
                        latest_message = model_output["messages"][-1]
                        if hasattr(latest_message, "content") and latest_message.content:
                            yield latest_message.content.strip() + "\n"

        except Exception as e:
            yield f"Error: {str(e)}"

    def execute_stream_with_context(self, query: str, session_id: str = "default", context: dict = None):
        """带上下文的流式执行查询（用于报告生成）"""
        if context:
            self._context = context

        return self.execute_stream(query, session_id)

    def reset_context(self):
        """重置上下文"""
        self._context = {"report": False}


if __name__ == "__main__":
    agent = ReactAgent()

    # 测试正常对话
    print("=== 测试正常对话 ===")
    for chunk in agent.execute_stream("你好，请介绍一下你自己"):
        print(chunk, end="", flush=True)

    print("\n" + "=" * 50)

    # 测试报告生成
    print("=== 测试报告生成 ===")
    agent.reset_context()
    for chunk in agent.execute_stream("给我生成我的使用报告"):
        print(chunk, end="", flush=True)
