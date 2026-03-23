import yaml
from utils.path_tool import get_abs_path


def load_rag_config(
    config_path: str = get_abs_path("config/rag.yml"), encoding: str = "utf-8"
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


# Load configurations
rag_cfg = load_rag_config()
prompts_cfg = load_prompts_config()
agent_cfg = load_agent_config()

# Backward compatibility: chroma_cfg is now an alias for rag_cfg
# (chroma.yml has been merged into rag.yml)
chroma_cfg = rag_cfg

if __name__ == "__main__":
    print("RAG Config:", rag_cfg)
    print("Prompts Config:", prompts_cfg)
    print("Agent Config:", agent_cfg)
