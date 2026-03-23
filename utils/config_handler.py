import yaml
from utils.path_tool import get_abs_path


def load_config(
    config_path: str = get_abs_path("config.yml"), encoding: str = "utf-8"
):
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


# Load consolidated configuration
cfg = load_config()

# Backward compatibility aliases
rag_cfg = cfg
chroma_cfg = cfg
prompts_cfg = cfg


def load_prompts_config(
    config_path: str = get_abs_path("config.yml"), encoding: str = "utf-8"
):
    """Kept for backward compatibility - loads same config."""
    return load_config(config_path, encoding)


def load_agent_config(
    config_path: str = get_abs_path("config.yml"), encoding: str = "utf-8"
):
    """Kept for backward compatibility - loads same config."""
    return load_config(config_path, encoding)


# Backward compatibility: chroma_cfg is now an alias for rag_cfg
# (chroma.yml has been merged into rag.yml)
chroma_cfg = rag_cfg

if __name__ == "__main__":
    print("Config:", cfg)
