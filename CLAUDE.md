# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered customer service chatbot for floor cleaning robots (扫地机器人). It's a **Streamlit** web application that uses **LangChain/LangGraph** with **Alibaba Tongyi Qwen** (via DashScope API) as the LLM and **Chroma** as the vector database for RAG-based knowledge retrieval.

## Running the Application

```bash
# Run the Streamlit app
uv run streamlit run app.py

# Initialize/load documents to vector store
uv run python -m rag.vector_store

# Run tests
uv run pytest

# Add new lib
uv add
```

**Required Environment Variable:**

- `DASHSCOPE_API_KEY` - Alibaba DashScope API key for LLM access

## Architecture

```
app.py                 # Streamlit entry point - handles UI and message streaming
agent/
  react_agent.py       # ReAct agent using LangGraph
  tools/
    agent_tools.py     # Custom tools: RAG, weather, user info, external data, report generation
    middleware.py     # Middleware for prompt switching and logging
model/
  factory.py           # Chat and embedding model factory (Tongyi Qwen + DashScope)
rag/
  rag_service.py       # RAG summarization using LangChain LCEL
  vector_store.py      # Chroma vector store service
utils/
  config_handler.py    # YAML config loader
  prompt_loader.py    # System prompt loader
  logger_handler.py   # Logging utilities
  file_handler.py     # File utilities
```

## Configuration

All configuration is in YAML files under `config/`:

- `rag.yml` - Chat model (`qwen3-max`) and embedding model (`text-embedding-v4`)
- `chroma.yml` - Vector store settings (collection name "agent", chunk_size 200)
- `prompts.yml` - Prompt configuration
- `agent.yml` - External data path configuration

## Prompt System

Prompts are stored in `prompts/` directory:

- `main_prompts.txt` - Main system prompt
- `rag_prompts.txt` - RAG summarization prompt
- `report_prompts.txt` - Report generation prompt

The agent supports dynamic prompt switching via middleware (see `agent/tools/middleware.py`).

## Knowledge Base

Knowledge base documents are stored in `data/` as Chinese TXT files:

- `扫地机器人100问2.txt`
- `扫拖一体机器人100问.txt`
- `故障排除.txt`
- `维护保养.txt`
- `选购指南.txt`

Vector store persists to `chroma_db/` directory.

## Available Agent Tools

1. `rag_summarize` - Query knowledge base for relevant information
2. `get_weather` - Get current weather for user's location
3. `get_user_location` - Get user's location
4. `get_user_id` - Get user ID
5. `get_current_month` - Get current month
6. `fetch_external_data` - Fetch external user usage data
7. `fill_context_for_report` - Generate personalized usage reports
