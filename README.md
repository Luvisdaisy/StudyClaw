# StudyClaw

AI-powered customer service chatbot for floor cleaning robots (扫地机器人智能客服).

## Features

- **RAG-based Knowledge Retrieval**: Uses Chroma vector database for intelligent document search
- **ReAct Agent**: Powered by LangChain/LangGraph with Alibaba Tongyi Qwen (DashScope API)
- **Dynamic Prompt Switching**: Supports multiple conversation modes
- **Streamlit Web UI**: Clean and intuitive chat interface

## Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/Luvisdaisy/StudyClaw.git
cd StudyClaw

# Install dependencies
uv sync

# Set environment variable
export DASHSCOPE_API_KEY=your_api_key_here
```

### Running

```bash
streamlit run app.py
```

## Project Structure

```
StudyClaw/
├── app.py                 # Streamlit entry point
├── agent/                 # ReAct agent implementation
│   ├── react_agent.py
│   └── tools/             # Custom tools
├── model/                 # Model factory (Tongyi Qwen)
├── rag/                   # RAG vector store & service
├── utils/                 # Utilities
├── config/                # YAML configuration
├── prompts/               # System prompts
└── data/                  # Knowledge base documents
```

## Configuration

All configuration files are in `config/`:
- `rag.yml` - Chat and embedding model settings
- `chroma.yml` - Vector store settings
- `prompts.yml` - Prompt configuration
- `agent.yml` - Agent settings

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DASHSCOPE_API_KEY` | Alibaba DashScope API key for LLM access |

## License

MIT
