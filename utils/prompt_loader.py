from typing import Literal
from utils.config_handler import prompts_cfg
from utils.path_tool import get_abs_path
from utils.logger_handler import get_logger

logger = get_logger(__name__)


def load_prompt(prompt_type: Literal["main", "rag"]) -> str:
    """
    Load prompt template by type.

    Args:
        prompt_type: One of "main" or "rag"

    Returns:
        The prompt template string

    Raises:
        KeyError: If the prompt path is not configured
        IOError: If the prompt file cannot be read
    """
    config_key = f"{prompt_type}_prompt_path"
    try:
        relative_path = prompts_cfg[config_key]
    except KeyError:
        logger.error(f"{config_key} not found in prompts configuration")
        raise

    try:
        full_path = get_abs_path(relative_path)
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading {prompt_type} prompt from {relative_path}: {e}")
        raise


# Backward compatibility functions
def load_system_prompts() -> str:
    """Load main/system prompt template."""
    return load_prompt("main")


def load_rag_prompts() -> str:
    """Load RAG prompt template."""
    return load_prompt("rag")


if __name__ == "__main__":
    print(load_system_prompts())
    print(load_rag_prompts())
