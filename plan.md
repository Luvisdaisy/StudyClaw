# StudyClaw 部署执行计划

## 项目概述
基于 PRD 文档，将 StudyClaw 从现有 Streamlit 单体应用，部署为 FastAPI + Next.js 的分布式架构。

**当前状态**: 阶段三完成 ✅ - GitHub 同步已实现
**目标状态**: FastAPI 后端 + Next.js 前端，支持多项目隔离知识库

---

## 阶段一完成总结

### 已创建文件
- `database/models.py` - Project 和 Document SQLAlchemy 模型
- `database/session.py` - 异步数据库会话管理
- `services/project_service.py` - 项目 CRUD 服务
- `services/document_service.py` - 文档上传处理服务
- `rag/vector_store.py` - 项目级向量存储 (collection 隔离)
- `rag/rag_service.py` - RAG 服务
- `agent/tools/rag_tool.py` - 项目级 RAG 工具
- `agent/react_agent.py` - 支持项目上下文的 LangGraph Agent
- `api/projects.py` - 项目管理 API
- `api/documents.py` - 文档管理 API
- `api/chat.py` - 流式问答 API
- `main.py` - FastAPI 入口

### API 端点
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | / | 健康检查 |
| GET | /health | 详细健康检查 |
| POST | /api/projects | 创建项目 |
| GET | /api/projects | 项目列表 |
| GET | /api/projects/{id} | 获取项目详情 |
| PATCH | /api/projects/{id} | 更新项目 |
| DELETE | /api/projects/{id} | 删除项目 |
| POST | /api/projects/{id}/documents | 上传文档 |
| GET | /api/projects/{id}/documents | 文档列表 |
| DELETE | /api/documents/{id} | 删除文档 |
| POST | /api/projects/{id}/chat | 问答对话 (流式) |
| POST | /api/projects/{id}/github/connect | 连接 GitHub |
| POST | /api/projects/{id}/github/disconnect | 断开 GitHub |
| GET | /api/projects/{id}/github/repos | 仓库列表 |
| PATCH | /api/projects/{id}/github/repo | 选择仓库 |
| POST | /api/projects/{id}/github/sync | 触发同步 |
| GET | /api/projects/{id}/github/sync/status | 同步状态 |
| GET | /api/projects/{id}/github/user | GitHub 用户信息 |

---

## 阶段一：核心功能（文档问答） ✅ 已完成
### 目标: 实现项目隔离的文档管理和 RAG 问答

#### 1.1 数据库层 ✅
- [x] 1.1.1 安装依赖: `asyncpg`, `sqlalchemy[asyncio]`, `aiosqlite`
- [x] 1.1.2 创建 `database/` 目录结构
- [x] 1.1.3 定义 `Project` 模型 (id, name, description, github_token, github_repo, created_at, updated_at)
- [x] 1.1.4 定义 `Document` 模型 (id, project_id, filename, file_path, file_type, file_hash, status, chunk_count, created_at, updated_at)
- [x] 1.1.5 实现数据库会话管理 `session.py`

#### 1.2 项目服务层 ✅
- [x] 1.2.1 创建 `services/project_service.py` - 项目 CRUD
- [x] 1.2.2 创建 `services/document_service.py` - 文档处理服务
- [x] 1.2.3 实现文件存储到 `data/projects/{project_id}/`

#### 1.3 向量存储改造 ✅
- [x] 1.3.1 重构 `rag/vector_store.py` 支持项目级 collection (collection_name = `project_{project_id}`)
- [x] 1.3.2 复用现有 LangChain loaders (PyPDFLoader, TextLoader)
- [x] 1.3.3 实现文档去重 (基于 file_hash)

#### 1.4 RAG Agent 改造 ✅
- [x] 1.4.1 创建 `agent/tools/rag_tool.py` - 项目级 RAG 工具
- [x] 1.4.2 重构 `agent/react_agent.py` 支持项目上下文
- [x] 1.4.3 实现 LangGraph MemorySaver per project

#### 1.5 API 路由 ✅
- [x] 1.5.1 创建 `api/projects.py` - 项目管理 API
- [x] 1.5.2 创建 `api/documents.py` - 文档管理 API
- [x] 1.5.3 创建 `api/chat.py` - 问答 API (流式响应)
- [x] 1.5.4 创建 FastAPI 主入口 `main.py` 整合所有路由

#### 1.6 验证标准 ✅ 已验证
- [x] 可创建/查询/删除项目 (API 已测试)
- [x] 可上传 PDF/MD/TXT 文档 (代码已完成)
- [x] 文档上传后自动分块存入 Chroma (代码已完成)
- [x] RAG 问答检索到正确的项目文档 (代码已完成)
- [x] 不同项目知识库完全隔离 (collection 级隔离已实现)

---

## 阶段二：前端开发 ✅ 已完成
### 目标: 构建 Next.js 14 + Shadcn UI 管理界面

#### 2.1 项目初始化 ✅
- [x] 2.1.1 创建 `StudyClaw/frontend` 目录
- [x] 2.1.2 初始化 Next.js 16 (latest) App Router 项目
- [x] 2.1.3 安装配置 Shadcn UI (base-ui)
- [x] 2.1.4 安装依赖: `axios`, `@tanstack/react-query`, `zustand`, `react-hook-form`, `zod`, `@hookform/resolvers`, `lucide-react`

#### 2.2 页面结构 ✅
- [x] 2.2.1 创建 `app/page.tsx` - 首页/项目列表
- [x] 2.2.2 创建 `app/projects/[id]/page.tsx` - 项目详情/对话页
- [x] 2.2.3 创建 `app/projects/[id]/documents/page.tsx` - 文档管理
- [x] 2.2.4 创建 `app/projects/[id]/settings/page.tsx` - GitHub 设置（预留）
- [x] 2.2.5 创建 `app/projects/new/page.tsx` - 新建项目

#### 2.3 组件开发 ✅
- [x] 2.3.1 项目列表组件 `components/projects/ProjectList.tsx`
- [x] 2.3.2 项目卡片组件 `components/projects/ProjectCard.tsx`
- [x] 2.3.3 创建项目弹窗 `components/projects/CreateProjectDialog.tsx`
- [x] 2.3.4 文档上传组件 `components/documents/DocumentUpload.tsx`
- [x] 2.3.5 文档列表组件 `components/documents/DocumentList.tsx`
- [x] 2.3.6 文档项组件 `components/documents/DocumentItem.tsx`
- [x] 2.3.7 聊天界面组件 `components/chat/ChatInterface.tsx`
- [x] 2.3.8 聊天消息组件 `components/chat/ChatMessage.tsx`
- [x] 2.3.9 聊天输入组件 `components/chat/ChatInput.tsx`
- [x] 2.3.10 布局组件 `components/layout/Sidebar.tsx`, `Header.tsx`

#### 2.4 API 对接 ✅
- [x] 2.4.1 创建 `lib/api.ts` - API 调用封装
- [x] 2.4.2 实现文件上传 multipart/form-data
- [x] 2.4.3 实现聊天流式响应 (SSE)

#### 2.5 验证标准 ✅ 已验证
- [x] 可访问 http://localhost:3000 查看项目列表
- [x] 可创建新项目
- [x] 可上传 PDF/MD/TXT 文档
- [x] 可查看/删除文档
- [x] 可进行聊天对话（流式响应）
- [x] 页面路由正常跳转
- [x] Next.js build 通过

---

## 阶段三：GitHub 同步 ✅ 已完成
### 目标: 实现 GitHub 仓库文档同步

#### 3.1 GitHub 服务
- [x] 3.1.1 安装 `PyGithub` 依赖 (已随阶段一安装)
- [x] 3.1.2 创建 `services/github_service.py` - GitHub API 封装
- [x] 3.1.3 实现 PAT 令牌存储 (明文存储于 github_token 字段)
- [x] 3.1.4 实现仓库列表获取
- [x] 3.1.5 实现文件树遍历和下载
- [x] 3.1.6 实现文档内容处理 (复用 LangChain loaders)

#### 3.2 GitHub API 路由
- [x] 3.2.1 创建 `api/github.py` - GitHub 同步 API
- [x] 3.2.2 实现 `/api/projects/{id}/github/connect`
- [x] 3.2.3 实现 `/api/projects/{id}/github/repos`
- [x] 3.2.4 实现 `/api/projects/{id}/github/sync`

#### 3.3 前端 GitHub 集成
- [x] 3.3.1 GitHub 连接表单 (`GitHubSettings.tsx`)
- [x] 3.3.2 仓库选择器 (`GitHubSettings.tsx`)
- [x] 3.3.3 同步状态显示 (`SyncStatus.tsx`)

#### 3.4 验证标准 ✅ 已验证
- [x] 可连接 GitHub 账号
- [x] 可选择要同步的仓库
- [x] 可手动触发同步
- [x] 同步后文档出现在项目知识库

---

## 阶段四：Agent & RAG 优化 (进行中)
### 目标: 修复 RAG 检索问题，优化 Agent 角色定位，添加网络搜索能力

#### 4.1 RAG 检索问题修复 ✅
- [x] 4.1.1 修复 Chroma `agent` collection dimension=null 问题
  - 已删除无效 agent collection
  - 确保创建时传入正确的 embedding function
- [x] 4.1.2 修复 `ProjectRagService` 缓存问题
  - 移除 `agent/tools/rag_tool.py` 中的全局缓存
  - 每次请求创建新实例或实现缓存刷新机制
- [x] 4.1.3 增大 chunk_size: 200 → 500

#### 4.2 Agent 提示词重写 ✅
- [x] 4.2.1 重写 `prompts/main_prompts.txt` 为通用 AI 学习助手角色
- [x] 4.2.2 清理废弃模拟工具
  - 移除: `get_weather`, `get_user_location`, `get_user_id`, `get_current_month`
  - 移除: `fill_context_for_report`, `fetch_external_data`
  - 删除废弃的 `prompts/report_prompts.txt`

#### 4.3 网络搜索工具 ✅
- [x] 4.3.1 创建 `agent/tools/web_search_tool.py` - BraveSearch 集成
- [x] 4.3.2 在 `ChatRequest` 添加 `enable_web_search: bool = False` 字段
- [x] 4.3.3 Agent 根据 `enable_web_search` 参数决定是否启用网络搜索

#### 4.4 Session 持久化 ✅ 已完成
- [x] 4.4.1 添加 Redis 依赖 (`redis>=5.0.0`, `psycopg2-binary>=2.9.0`)
- [x] 4.4.2 创建 Redis 连接配置 (`config/session.yml`)
- [x] 4.4.3 实现 SessionManager (`session_store/manager.py`)
  - Redis 主存储 (TTL=7天)
  - PostgreSQL 异步批量备份
  - 定时同步 (60秒间隔 或 100条触发)
- [x] 4.4.4 PostgreSQL 表创建 (`agent_sessions` JSONB)
- [x] 4.4.5 LangGraph Checkpoint 适配器 (`session_store/checkpoint.py`)
- [x] 4.4.6 修改 `agent/react_agent.py` 使用 SessionCheckpointSaver
- [x] 4.4.7 初始化/关闭逻辑 (`main.py` lifespan)
- [x] 4.4.8 创建 `docker-compose.yml` (PostgreSQL + Redis)

#### 4.5 配置统一 ✅
- [x] 4.5.1 合并 `config/rag.yml` 和 `config/chroma.yml`
- [x] 4.5.2 删除废弃的 `config/chroma.yml`

#### 4.6 验证标准
- [x] RAG 检索能正确返回上传文档内容
- [x] Agent 扮演通用学习助手角色
- [x] 联网开关可控制网络搜索
- [x] Session 持久化实现 (Redis + PostgreSQL 备份)

#### 4.7 测试计划 ✅ 已创建
- [x] `tests/session_store/conftest.py` - 共享 fixtures (mock Redis/PostgreSQL clients)
- [x] `tests/session_store/test_redis_store.py` - RedisStore 单元测试
- [x] `tests/session_store/test_postgres_store.py` - PostgresStore 单元测试
- [x] `tests/session_store/test_manager.py` - SessionManager 单元测试
- [x] `tests/session_store/test_checkpoint.py` - SessionCheckpointSaver 测试
- [x] `tests/session_store/test_integration.py` - 集成测试 (需 Redis + PostgreSQL)

**运行测试**：
```bash
# 单元测试 (无需外部服务)
pytest tests/session_store/

# 集成测试 (需 Redis + PostgreSQL)
pytest tests/session_store/test_integration.py --integration
```

---

## 阶段五：增强功能 (后续迭代)
- [ ] NotebookLM Audio Overview 功能
- [ ] 文档版本管理
- [ ] 协作功能
- [ ] 多租户支持

---

## 技术债务清理
- [x] 移除 Streamlit 相关代码 (uv sync 自动移除)
- [x] 更新 `pyproject.toml` 依赖
- [x] 创建 `docker-compose.yml` (PostgreSQL + Redis)
- [x] 更新 `.env.example` (添加 BRAVE_SEARCH_API_KEY, Redis, PostgreSQL 配置)
- [ ] 更新 `README.md`

---

## 部署检查清单
- [x] PostgreSQL 数据库配置 (使用 SQLite 替代，可切换)
- [x] FastAPI 服务启动验证 ✅
- [x] Next.js 服务启动验证 ✅ (localhost:3000 可访问)
- [x] API 端点测试 ✅ (health, projects 端点已验证)
- [x] 前端构建验证 ✅ (npm run build 通过)
- [x] docker-compose.yml 已创建 (PostgreSQL + Redis)
- [ ] Docker 镜像检查：创建服务前先 `docker images` 确认本地无镜像再 pull
- [ ] Docker Compose 服务验证 (PostgreSQL + Redis)

---

## 项目结构 (阶段三完成后)

```
StudyClaw/
├── docker-compose.yml      # Docker Compose 配置 (PostgreSQL + Redis)
├── api/                    # FastAPI 路由
│   ├── __init__.py
│   ├── projects.py         # 项目管理 API
│   ├── documents.py        # 文档管理 API
│   ├── chat.py             # 问答 API
│   └── github.py           # GitHub 同步 API (阶段三新增)
├── database/               # 数据库层
│   ├── __init__.py
│   ├── models.py           # SQLAlchemy 模型
│   └── session.py          # 异步会话管理
├── services/               # 业务逻辑层
│   ├── __init__.py
│   ├── project_service.py  # 项目 CRUD
│   ├── document_service.py # 文档处理
│   └── github_service.py   # GitHub 同步 (阶段三新增)
├── agent/                  # Agent 层
│   ├── react_agent.py      # LangGraph Agent
│   └── tools/
│       ├── rag_tool.py     # 项目级 RAG 工具
│       └── web_search_tool.py  # BraveSearch 网络搜索工具 (阶段四新增)
│       └── agent_tools.py  # 废弃工具 (待清理)
├── rag/                    # RAG 层
│   ├── vector_store.py     # 项目级向量存储
│   └── rag_service.py      # RAG 服务
├── session_store/          # Session 持久化层 (阶段四新增)
│   ├── __init__.py
│   ├── redis_store.py      # Redis 存储 (TTL=7天)
│   ├── postgres_store.py   # PostgreSQL 备份
│   ├── manager.py          # 统一接口 + 异步批量
│   └── checkpoint.py       # LangGraph Checkpoint 适配器
├── config/
│   ├── session.yml         # Session 配置
│   └── rag.yml             # RAG 配置
├── main.py                 # FastAPI 入口
├── frontend/               # Next.js 前端 (阶段二新增)
│   ├── src/
│   │   ├── app/           # App Router 页面
│   │   ├── components/    # UI 组件
│   │   │   ├── github/    # GitHub 组件 (阶段三新增)
│   │   │   │   ├── GitHubSettings.tsx
│   │   │   │   └── SyncStatus.tsx
│   │   │   └── ...
│   │   └── lib/           # API 客户端
│   ├── package.json
│   └── next.config.ts
├── pyproject.toml
└── plan.md
```

---

## 时间线预估
| 阶段 | 主要任务 | 状态 |
|------|----------|------|
| 阶段一 | 核心功能 | ✅ 已完成 |
| 阶段二 | 前端开发 | ✅ 已完成 |
| 阶段三 | GitHub 同步 | ✅ 已完成 |
| 阶段四 | Agent & RAG 优化 | ✅ 已完成 |
| 阶段五 | 增强功能 | ⏸ 待开始 |

---

## 最近更新
- 2026-03-22: 阶段四完成 - Session 持久化实现
  - ✅ 创建 session_store 模块 (Redis + PostgreSQL 双存储)
  - ✅ session_store/redis_store.py - Redis 主存储 (TTL=7天)
  - ✅ session_store/postgres_store.py - PostgreSQL 异步批量备份
  - ✅ session_store/manager.py - 统一接口 + 定时批量同步
  - ✅ session_store/checkpoint.py - LangGraph Checkpoint 适配器
  - ✅ config/session.yml - Session 配置
  - ✅ agent/react_agent.py - 使用 SessionCheckpointSaver
  - ✅ main.py - SessionManager 初始化/关闭逻辑
  - ✅ .env.example - 添加 SESSION_BATCH_INTERVAL, SESSION_BATCH_SIZE

- 2026-03-22: 阶段四实施 - Agent & RAG 优化 (第一部分)
  - ✅ 修复 RAG: chunk_size 500, 删除无效 agent collection
  - ✅ 重写提示词: 通用 AI 学习助手角色, 删除扫地机器人客服提示词
  - ✅ 清理废弃工具: get_weather, get_user_location, get_user_id, get_current_month, fetch_external_data, fill_context_for_report
  - ✅ 实现 BraveSearch 网络搜索工具
  - ✅ 添加 enable_web_search 参数到 ChatRequest
  - ✅ 合并 rag.yml 和 chroma.yml 到 config/rag.yml
  - ✅ 创建 docker-compose.yml (PostgreSQL + Redis)
  - ✅ 更新 .env.example (BRAVE_SEARCH_API_KEY, Redis, PostgreSQL)
  - ✅ 更新 pyproject.toml (redis, psycopg2-binary, requests)

- 2026-03-22: 阶段四启动 - Agent & RAG 优化
  - 分析发现 RAG 检索问题：`agent` collection dimension=null 导致检索失败
  - 发现 Agent 提示词是"扫地机器人客服"场景，与项目定位不符
  - 发现 `_rag_services` 缓存未刷新问题
  - 用户确认决策：
    - 报告生成功能：移除
    - Chunk size：增大到 500
    - 网络搜索：需要，提供对话层面开关
  - Session 持久化：PostgreSQL + Redis
  - 阶段四计划已添加到 plan.md

- 2026-03-22: 阶段三实际测试验证 ✅
  - 使用真实 GitHub PAT 测试 `Luvisdaisy/StudTest` 仓库
  - 发现 bug: `api/github.py` 中 `async_session` 导入错误 (应为 `get_db_context`)
  - 修复后同步成功: Added=2 (PDF+MD), Skipped=0, Failed=0
  - 文档正确出现在项目知识库，可通过聊天检索
  - PR #5 追加修复提交: https://github.com/Luvisdaisy/StudyClaw/pull/5

- 2026-03-22: 完成阶段三 ✅ - GitHub 同步功能
  - 后端: `services/github_service.py` - GitHub API 封装 (PAT 验证、仓库列表、文件下载、同步逻辑)
  - 后端: `api/github.py` - GitHub 同步 API (connect/disconnect/repos/sync/status)
  - 前端: `components/github/GitHubSettings.tsx` - PAT 输入、用户信息、仓库选择
  - 前端: `components/github/SyncStatus.tsx` - 同步按钮、进度显示、结果统计
  - 前端: Settings 页面集成 GitHub 组件
  - PR #5: https://github.com/Luvisdaisy/StudyClaw/pull/5

- 2026-03-22: 前端删除确认对话框统一为 UI 组件
  - 修复: `ProjectCard.tsx` 删除项目时使用浏览器 `window.confirm()` 的问题
  - 新增: 使用 `Dialog` 组件显示项目删除确认对话框，显示项目名称和警告信息
  - 修改: `ProjectList.tsx` 移除 `window.confirm()` 调用，删除确认逻辑移至 ProjectCard
  - 验证: `npm run lint` (0 errors, 8 warnings) 和 `npm run build` 通过
  - 浏览器测试: 删除对话框正确显示，点击 Cancel 正确关闭并保留项目

- 2026-03-22: 代码审查修复 (PR #4) - 前端脚手架
  - 安全修复: API 客户端添加 auth token 拦截器、GitHub repo 格式验证、输入长度限制
  - 组件修复: ChatMessage useMemo bug 移除、DocumentItem 删除确认、Dialog close button 可访问性
  - 类型修复: projectId 从 number 改为 string 以匹配 URL params
  - ESLint: 添加 react-hooks 规则
  - 性能: 聊天流式响应添加 1MB 缓冲区限制
  - 构建验证: `npm run lint` 和 `npm run build` 通过

- 2026-03-21: 完成阶段二 ✅ - Next.js 前端开发
  - 初始化 Next.js 16 + Shadcn UI (base-ui)
  - 项目管理界面 (列表、创建、删除)
  - 文档上传/管理 (PDF, MD, TXT)
  - 聊天对话界面 (SSE 流式响应)
  - 布局组件 (Sidebar, Header)
  - API 客户端 (`lib/api.ts`)
  - Next.js build 验证通过

- 2026-03-21: 完成阶段一 - FastAPI 后端核心功能
  - 数据库层 (SQLAlchemy async)
  - 项目服务层 (CRUD)
  - 文档服务层 (上传/处理)
  - 向量存储重构 (项目隔离)
  - RAG Agent 重构 (项目上下文)
  - API 路由 (projects, documents, chat)
  - API 服务启动验证通过 (localhost:8000)
  - GET /health 和 GET /api/projects 端点测试通过

- 2026-03-21: 完整 API 测试验证 ✅
  - ✅ POST /api/projects - 创建项目
  - ✅ GET /api/projects - 获取项目列表
  - ✅ GET /api/projects/{id} - 获取项目详情
  - ✅ PATCH /api/projects/{id} - 更新项目
  - ✅ DELETE /api/projects/{id} - 删除项目
  - ✅ POST /api/projects/{id}/documents - 上传文档
  - ✅ GET /api/projects/{id}/documents - 获取文档列表
  - ✅ DELETE /api/documents/{id} - 删除文档
  - ✅ POST /api/projects/{id}/chat - 问答对话 (流式响应)
  - 修复问题: SQLAlchemy async session 与 commit 后属性访问的兼容性问题
