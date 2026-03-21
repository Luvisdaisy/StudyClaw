import uuid
from typing import TypedDict, Annotated, Sequence, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph.message import add_messages

from agent.tools.rag_tool import get_rag_service, rag_summarize, rag_retrieve
from agent.tools.agent_tools import (
    get_current_month,
    get_weather,
    get_user_location,
    get_user_id,
    fetch_external_data,
    fill_context_for_report,
)
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts, load_report_prompts


class AgentState(TypedDict):
    """Agent state definition"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    context: dict
    project_id: Optional[str]


def create_langgraph_agent(project_id: Optional[str] = None):
    """Create a LangGraph agent with project context"""

    # Build tools list
    tools = [
        rag_summarize,
        rag_retrieve,
        get_weather,
        get_user_location,
        get_user_id,
        get_current_month,
        fetch_external_data,
        fill_context_for_report,
    ]

    # Create tool node
    tool_node = ToolNode(tools)

    def call_model_node(state: AgentState) -> AgentState:
        """Model call node - select prompt based on context"""
        context = state.get("context", {})

        # Select prompt based on context
        if context.get("report", False):
            system_prompt = load_report_prompts()
        else:
            system_prompt = load_system_prompts()

        # Add project context to system prompt
        if project_id:
            system_prompt = f"{system_prompt}\n\n[System] Current project ID: {project_id}"

        # Build message with system prompt
        system_msg = SystemMessage(content=system_prompt)
        response = chat_model.bind_tools(tools).invoke(
            [system_msg] + list(state["messages"])
        )

        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        """Conditional edge: check if tool call is needed"""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"

    # Build graph
    builder = StateGraph(AgentState)

    # Add nodes
    builder.add_node("model", call_model_node)
    builder.add_node("tools", tool_node)

    # Add edges
    builder.add_edge(START, "model")

    # Conditional edge: determine if tool call is needed
    builder.add_conditional_edges(
        "model",
        should_continue,
        {"tools": "tools", "end": END}
    )
    builder.add_edge("tools", "model")  # After tool execution, back to model

    # Compile with checkpointer for session persistence
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


class ReactAgent:
    """React Agent class with project support"""

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id
        self.agent = create_langgraph_agent(project_id)
        self._context = {"report": False}

    def _update_context_from_tool_calls(self, messages: list[BaseMessage]) -> None:
        """Extract tool calls from messages and update context"""
        for msg in messages:
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls"):
                if msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        if tool_call.get("name") == "fill_context_for_report":
                            self._context["report"] = True
                            return

    def execute_stream(self, query: str, session_id: str = "default"):
        """Execute query with streaming"""
        # Build messages
        messages = [HumanMessage(content=query)]

        # Use session_id as thread_id for session persistence
        config = {"configurable": {"thread_id": session_id}}

        # Prepare state with project context
        state = {
            "messages": messages,
            "context": self._context,
            "project_id": self.project_id,
        }

        try:
            # Stream execution
            for chunk in self.agent.stream(state, config=config):
                # Handle messages output
                if "messages" in chunk:
                    latest_message = chunk["messages"][-1]
                    if hasattr(latest_message, "content") and latest_message.content:
                        if isinstance(latest_message, AIMessage):
                            self._update_context_from_tool_calls([latest_message])
                        yield latest_message.content.strip() + "\n"

                # Handle model node output
                if "model" in chunk:
                    model_output = chunk["model"]
                    if "messages" in model_output:
                        latest_message = model_output["messages"][-1]
                        if hasattr(latest_message, "content") and latest_message.content:
                            yield latest_message.content.strip() + "\n"

        except Exception as e:
            yield f"Error: {str(e)}"

    def execute_stream_with_context(
        self,
        query: str,
        session_id: str = "default",
        context: dict = None
    ):
        """Execute with custom context (for report generation)"""
        if context:
            self._context = context
        return self.execute_stream(query, session_id)

    def reset_context(self):
        """Reset context"""
        self._context = {"report": False}

    def set_project(self, project_id: str):
        """Switch to a different project"""
        self.project_id = project_id
        self.agent = create_langgraph_agent(project_id)


class ProjectAgentFactory:
    """Factory for creating project-specific agents"""

    _agents: dict[str, ReactAgent] = {}

    @classmethod
    def get_agent(cls, project_id: str) -> ReactAgent:
        """Get or create agent for a project"""
        if project_id not in cls._agents:
            cls._agents[project_id] = ReactAgent(project_id=project_id)
        return cls._agents[project_id]

    @classmethod
    def clear_agent(cls, project_id: str):
        """Remove agent for a project"""
        if project_id in cls._agents:
            del cls._agents[project_id]

    @classmethod
    def clear_all(cls):
        """Clear all cached agents"""
        cls._agents.clear()
