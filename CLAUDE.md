# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Thinking Principles

Apply first principles thinking. Do not assume I fully understand my own requirements and implementation path. Stay prudent, start from original requirements and problems, and discuss with me first if motives or goals are unclear. When proposing modifications or refactoring plans, adhere to:
1. No compatibility or patch-work solutions allowed
2. No over-engineering — implement via the shortest path without violating rule 1
3. Do not proactively offer solutions beyond stated requirements (e.g., fallbacks, degradation strategies) to avoid business logic drift
4. Ensure solutions are logically correct and verified through full-chain validation

## Project Overview

StudyClaw is an AI-powered learning assistant (like NotebookLM) that helps users get answers from documents through RAG, with project-based knowledge isolation and GitHub repository sync.

## Python Version

Python 3.12 required. The project uses `uv` for dependency management.

## Environment Setup

1. Copy `.env.example` to `.env` and fill in required API keys:
   - `DASHSCOPE_API_KEY` - LLM provider (Alibaba Cloud)
   - `DATABASE_URL` - PostgreSQL connection string
   - `REDIS_*` - Redis configuration for session persistence
   - `BRAVE_SEARCH_API_KEY` - Optional, for web search feature

2. Start infrastructure services:

   ```bash
   docker compose up -d
   ```

3. Install dependencies:
   ```bash
   uv sync
   ```

## Running the Application

**Backend** (FastAPI on port 8000):

```bash
uvicorn main:app --reload --port 8000
# or
uv run main.py
```

**Frontend** (Next.js on port 3000):

```bash
cd frontend && npm run dev
```

## Testing

Tests use pytest with async support. All tests require PostgreSQL and Redis running.

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run a specific test file
pytest tests/unit/test_document_service.py

# Run a specific test
pytest tests/unit/test_document_service.py::test_function_name
```

## Architecture

### Core Flow

```
Frontend (Next.js) → FastAPI (uvicorn) → Services → PostgreSQL / Chroma / Redis
                                          ↓
                                    LangGraph Agent
                                          ↓
                              RAG Tool / Web Search Tool
```

### Key Modules

| Directory        | Purpose                                                            |
| ---------------- | ------------------------------------------------------------------ |
| `api/`           | FastAPI route handlers (projects, documents, chat, github)         |
| `agent/`         | LangGraph ReAct agent + RAG tool + web search tool + middleware    |
| `database/`      | SQLAlchemy models (Project, Document) and async session management |
| `rag/`           | Chroma vector store (per-project collections) and RAG service      |
| `services/`      | Business logic layer (project, document, github services)          |
| `session_store/` | Session persistence (Redis primary + PostgreSQL backup)            |
| `utils/`         | Config loading from `config.yml`, path utilities                   |

### Knowledge Isolation

Each project has its own Chroma collection named `project_{project_uuid}`. All RAG operations scope to the current project context passed through the request chain.

### Session Persistence

LangGraph checkpointer uses Redis as primary store (TTL=7 days) with async batched PostgreSQL backup. The `SessionManager` handles initialization/shutdown via FastAPI lifespan.

### Configuration

All settings are in `config.yml` (consolidated from prior separate YAML files):

- Model names: `qwen3-max`, `text-embedding-v4`
- Chroma: `chroma_db` directory, `k=3` retrieval count
- Chunking: 500 char blocks with 20 char overlap

### API Routers

- `projects_router` - Project CRUD
- `documents_router` - Document upload/management
- `chat_router` - Streaming RAG conversation
- `github_router` - GitHub sync operations

### Frontend

Next.js 16 with App Router, React 19, Shadcn UI, TailwindCSS 4, Zustand (client state), React Query (server state). Has its own `frontend/CLAUDE.md`.

## Data Models

**Project**: id, name (unique), description, github_token, github_repo, timestamps

**Document**: id, project_id (FK), filename, file_path, file_type, file_hash, status (pending/processing/completed/failed), chunk_count, timestamps

## LLM Integration

Uses DashScope (Alibaba Cloud). The `chat_model_name` in config must match a available DashScope model. Embeddings use `text-embedding-v4`.

## PRD Source

`prd.md` is the single source of truth for product requirements and completed phases.
