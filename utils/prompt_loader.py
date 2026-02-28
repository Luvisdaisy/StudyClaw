from utils.config_handler import prompts_cfg
from utils.path_tool import get_abs_path
from utils.logger_handler import logger


def load_system_prompts():
    try:
        system_prompt_path = get_abs_path(prompts_cfg["main_prompt_path"])
    except KeyError as e:
        logger.error("main_prompt_path not found in prompts configuration.")
        raise e
    try:
        return open(system_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"Error loading system prompt from {system_prompt_path}: {str(e)}")
        raise e


def load_rag_prompts():
    try:
        rag_prompt_path = get_abs_path(prompts_cfg["rag_prompt_path"])
    except KeyError as e:
        logger.error("rag_prompt_path not found in prompts configuration.")
        raise e
    try:
        return open(rag_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"Error loading rag prompt from {rag_prompt_path}: {str(e)}")
        raise e


def load_report_prompts():
    try:
        report_prompt_path = get_abs_path(prompts_cfg["report_prompt_path"])
    except KeyError as e:
        logger.error("report_prompt_path not found in prompts configuration.")
        raise e
    try:
        return open(report_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"Error loading report prompt from {report_prompt_path}: {str(e)}")
        raise e


if __name__ == "__main__":
    print(load_system_prompts())
    print(load_rag_prompts())
    print(load_report_prompts())
