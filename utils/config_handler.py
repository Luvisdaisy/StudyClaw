import yaml
from utils.path_tool import get_abs_path


def load_rag_config(
    config_path: str = get_abs_path("config/rag.yml"), encoding: str = "utf-8"
):
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def load_chroma_config(
    config_path: str = get_abs_path("config/chroma.yml"), encoding: str = "utf-8"
):
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def load_prompts_config(
    config_path: str = get_abs_path("config/prompts.yml"), encoding: str = "utf-8"
):
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def load_agent_config(
    config_path: str = get_abs_path("config/agent.yml"), encoding: str = "utf-8"
):
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


rag_cfg = load_rag_config()
chroma_cfg = load_chroma_config()
prompts_cfg = load_prompts_config()
agent_cfg = load_agent_config()

if __name__ == "__main__":
    print("RAG Config:", rag_cfg)
    print("Chroma Config:", chroma_cfg)
    print("Prompts Config:", prompts_cfg)
    print("Agent Config:", agent_cfg)
