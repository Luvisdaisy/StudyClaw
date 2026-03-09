# Repository Guidelines

## Project Structure & Module Organization
This is a Python/Streamlit app for a floor-cleaning-robot support assistant.

- `app.py`: Streamlit entry point and chat UI.
- `agent/`: LangGraph ReAct agent and tool middleware (`agent/tools/`).
- `rag/`: Chroma-backed retrieval and document ingestion (`vector_store.py`, `rag_service.py`).
- `model/`: LLM/embedding model factory.
- `utils/`: shared config, logging, file, and prompt helpers.
- `config/`: YAML runtime configuration (`rag.yml`, `chroma.yml`, `prompts.yml`, `agent.yml`).
- `prompts/`: prompt templates.
- `data/`: knowledge-base content; `data/external/` for CSV inputs.
- `chroma_db/`: persisted vector store artifacts.

## Build, Test, and Development Commands
Use `uv` for environment and command execution.

- `uv sync`: install dependencies from `pyproject.toml`/`uv.lock`.
- `uv run streamlit run app.py`: start the local web app.
- `uv run python -m rag.vector_store`: ingest `data/` into Chroma.
- `uv run pytest`: run tests (when tests are present).
- `uv run ruff check .`: run linting for Python files.

Required env var:
- `DASHSCOPE_API_KEY`: API key for Tongyi Qwen (DashScope).

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation and type hints where practical.
- Use `snake_case` for functions/modules/variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants.
- Keep files focused by responsibility (agent logic in `agent/`, retrieval in `rag/`, shared helpers in `utils/`).
- Prefer explicit imports and small, composable functions.
- Run `ruff` before opening a PR.

## Testing Guidelines
- Framework: `pytest`.
- Place tests under `tests/` (create if missing), mirroring source layout (example: `tests/rag/test_vector_store.py`).
- Name test files `test_*.py` and test functions `test_*`.
- Add tests for new behavior and bug fixes; cover failure paths around tool calls and document loading.

## Commit & Pull Request Guidelines
- Existing history uses concise prefixes like `feat:` and `Update:`; keep that style and write imperative summaries.
- Recommended format: `<type>: <short description>` (e.g., `fix: handle empty retrieval results`).
- PR checklist:
1. Scope summary and rationale.
2. Linked issue/task (if available).
3. Repro/verification steps and command output (`uv run pytest`, `uv run ruff check .`).
4. UI screenshots/GIFs for Streamlit changes.
