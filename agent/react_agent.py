from typing import TypedDict, Annotated, Sequence, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
import traceback

from agent.tools.rag_tool import rag_summarize, rag_retrieve
from agent.tools.web_search_tool import web_search
from agent.tools.middleware import (
    log_before_model_node,
    log_after_model_node,
    log_tool_call,
    log_tool_result,
)
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts
from session_store import get_session_checkpoint_saver
from utils.logger_handler import get_logger

logger = get_logger(__name__)


class AgentState(TypedDict):
    """Agent state definition"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    project_id: Optional[str]
    enable_web_search: bool


def create_langgraph_agent(project_id: Optional[str] = None, enable_web_search: bool = False):
    """Create a LangGraph agent with project context"""

    # Build tools list
    tools = [
        rag_summarize,
        rag_retrieve,
    ]

    # Add web search tool if enabled
    if enable_web_search:
        tools.append(web_search)

    # Create tool node with logging
    def logged_tool_node(state: AgentState) -> AgentState:
        """Tool node with middleware logging"""
        messages = state.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                for tc in last_msg.tool_calls:
                    tool_name = tc.get("name", "unknown")
                    tool_args = tc.get("args", {})
                    log_tool_call(tool_name, tool_args)

        try:
            # Call original tool node
            result = ToolNode(tools).invoke(state)
            log_tool_result("tool_node", True)
            return result
        except Exception as e:
            log_tool_result("tool_node", False, str(e))
            raise

    def call_model_node(state: AgentState) -> AgentState:
        """Model call node - generate response with middleware logging"""
        # Apply before-model middleware
        state = log_before_model_node(state)

        try:
            system_prompt = load_system_prompts()

            # Add project context to system prompt
            if project_id:
                system_prompt = f"{system_prompt}\n\n[System] Current project ID: {project_id}"

            # Build message with system prompt
            system_msg = SystemMessage(content=system_prompt)
            response = chat_model.bind_tools(tools).invoke(
                [system_msg] + list(state["messages"])
            )

            result = {"messages": [response]}

            # Apply after-model middleware
            result = log_after_model_node(result)

            return result
        except Exception as e:
            logger.error(
                f"Error in call_model_node: type={type(e).__name__}, message={str(e)}, "
                f"traceback={traceback.format_exc()}"
            )
            raise

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
    builder.add_node("tools", logged_tool_node)

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
    # Use SessionCheckpointSaver if available, otherwise fallback to MemorySaver
    checkpointer = get_session_checkpoint_saver()
    return builder.compile(checkpointer=checkpointer)


class ReactAgent:
    """React Agent class with project support"""

    def __init__(self, project_id: Optional[str] = None, enable_web_search: bool = False):
        self.project_id = project_id
        self.enable_web_search = enable_web_search
        self.agent = create_langgraph_agent(project_id, enable_web_search)

    async def async_execute_stream(self, query: str, session_id: str = "default"):
        """Execute query with async streaming (runs entirely in async context to avoid event loop mismatch)"""
        # Build messages
        messages = [HumanMessage(content=query)]

        # Use session_id as thread_id for session persistence
        config = {"configurable": {"thread_id": session_id}}

        # Prepare state with project context
        state = {
            "messages": messages,
            "project_id": self.project_id,
            "enable_web_search": self.enable_web_search,
        }

        try:
            # Async stream execution - runs entirely in the main async event loop
            async for chunk in self.agent.astream(state, config=config):
                # Handle messages output
                if "messages" in chunk:
                    latest_message = chunk["messages"][-1]
                    if hasattr(latest_message, "content") and latest_message.content:
                        yield latest_message.content.strip() + "\n"

                # Handle model node output
                if "model" in chunk:
                    model_output = chunk["model"]
                    if "messages" in model_output:
                        latest_message = model_output["messages"][-1]
                        if hasattr(latest_message, "content") and latest_message.content:
                            yield latest_message.content.strip() + "\n"

        except Exception as e:
            logger.error(
                f"Error in async_execute_stream: type={type(e).__name__}, message={str(e)}, "
                f"traceback={traceback.format_exc()}"
            )
            yield f"Error: {type(e).__name__}: {str(e)}\nSee server logs for details."

    def set_project(self, project_id: str):
        """Switch to a different project"""
        self.project_id = project_id
        self.agent = create_langgraph_agent(project_id, self.enable_web_search)


class ProjectAgentFactory:
    """Factory for creating project-specific agents"""

    _agents: dict[str, ReactAgent] = {}

    @classmethod
    def get_agent(cls, project_id: str, enable_web_search: bool = False) -> ReactAgent:
        """Get or create agent for a project"""
        # Ensure enable_web_search is an actual boolean to prevent string "False" being truthy
        enable_web_search = enable_web_search is True
        key = f"{project_id}_websearch_{enable_web_search}"
        if key not in cls._agents:
            cls._agents[key] = ReactAgent(project_id=project_id, enable_web_search=enable_web_search)
        return cls._agents[key]

    @classmethod
    def clear_agent(cls, project_id: str):
        """Remove agent for a project"""
        # Clear all variants of this project_id
        keys_to_remove = [k for k in cls._agents if k.startswith(f"{project_id}_")]
        for k in keys_to_remove:
            del cls._agents[k]

    @classmethod
    def clear_all(cls):
        """Clear all cached agents"""
        cls._agents.clear()
