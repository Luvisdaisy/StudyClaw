from utils.logger_handler import logger
from utils.prompt_loader import load_report_prompts, load_system_prompts
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


def log_before_model_node(state: dict) -> dict:
    """在模型执行前输出日志的节点"""
    messages = state.get("messages", [])
    logger.info(f"[log_before_model]即将调用模型，带有{len(messages)}条消息。")

    if messages:
        last_msg = messages[-1]
        if hasattr(last_msg, "content"):
            logger.debug(
                f"[log_before_model]{type(last_msg).__name__} | {last_msg.content.strip()[:200]}"
            )

    return state


def log_after_model_node(state: dict) -> dict:
    """在模型执行后检测工具调用，更新上下文"""
    messages = state.get("messages", [])
    context = state.get("context", {}).copy()

    # 检测 fill_context_for_report 调用
    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls"):
            for tc in msg.tool_calls:
                if tc.get("name") == "fill_context_for_report":
                    context["report"] = True
                    logger.info("[middleware]检测到 fill_context_for_report 调用，设置 report=True")

    return {"context": context}


def should_use_report_prompt(state: dict) -> str:
    """条件边：根据 context 决定使用哪个提示词"""
    return "report" if state.get("context", {}).get("report", False) else "main"


def should_switch_prompt(state: dict) -> str:
    """检查是否需要切换到报告提示词"""
    context = state.get("context", {})
    return "report" if context.get("report", False) else "main"


def get_prompt_for_context(context: dict) -> str:
    """根据上下文获取适当的提示词"""
    if context.get("report", False):
        return load_report_prompts()
    return load_system_prompts()


def log_tool_call(tool_name: str, tool_args: dict) -> None:
    """记录工具调用"""
    logger.info(f"[tool monitor]执行工具：{tool_name}")
    logger.info(f"[tool monitor]传入参数：{tool_args}")


def log_tool_result(tool_name: str, success: bool) -> None:
    """记录工具执行结果"""
    if success:
        logger.info(f"[tool monitor]工具{tool_name}调用成功")
    else:
        logger.error(f"[tool monitor]工具{tool_name}调用失败")


def check_and_set_report_context(tool_calls: list) -> dict:
    """检查工具调用并设置报告上下文"""
    context = {}
    if tool_calls:
        for tool_call in tool_calls:
            if tool_call.get("name") == "fill_context_for_report":
                context["report"] = True
                break
    return context
