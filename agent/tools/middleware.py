from typing import Optional
from utils.logger_handler import logger
from langchain_core.messages import AIMessage


def log_before_model_node(state: dict) -> dict:
    """Log before model execution"""
    messages = state.get("messages", [])
    logger.info(f"[middleware] Calling model with {len(messages)} messages")

    if messages:
        last_msg = messages[-1]
        if hasattr(last_msg, "content") and last_msg.content:
            logger.debug(
                f"[middleware] Last message: {type(last_msg).__name__} | {str(last_msg.content)[:200]}"
            )

    return state


def log_after_model_node(state: dict) -> dict:
    """Log after model execution"""
    messages = state.get("messages", [])

    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, AIMessage):
            has_tool_calls = hasattr(last_msg, "tool_calls") and last_msg.tool_calls
            logger.info(
                f"[middleware] Model response: {type(last_msg).__name__} "
                f"(tool_calls={bool(has_tool_calls)})"
            )

    return state


def log_tool_call(tool_name: str, tool_args: dict) -> None:
    """Log tool call"""
    logger.info(f"[middleware] Executing tool: {tool_name}")
    logger.debug(f"[middleware] Tool args: {tool_args}")


def log_tool_result(tool_name: str, success: bool, error: Optional[str] = None) -> None:
    """Log tool execution result"""
    if success:
        logger.info(f"[middleware] Tool {tool_name} succeeded")
    else:
        logger.error(f"[middleware] Tool {tool_name} failed: {error}")
