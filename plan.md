# StudyClaw 部署执行计划

## 项目概述
基于 PRD 文档，将 StudyClaw 从现有 Streamlit 单体应用，部署为 FastAPI + Next.js 的分布式架构。

**当前状态**: 阶段一完成 ✅ - FastAPI 后端已验证可运行
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

## 阶段二：前端开发
### 目标: 构建 Next.js 14 + Shadcn UI 管理界面

#### 2.1 项目初始化
- [ ] 2.1.1 创建 `StudyClaw/frontend` 目录
- [ ] 2.1.2 初始化 Next.js 14 App Router 项目
- [ ] 2.1.3 安装配置 Shadcn UI
- [ ] 2.1.4 安装依赖: `axios`, `react-query`, `zustand`, `react-hook-form`, `zod`, `lucide-react`

#### 2.2 页面结构
- [ ] 2.2.1 创建 `app/page.tsx` - 首页/项目列表
- [ ] 2.2.2 创建 `app/projects/[id]/page.tsx` - 项目详情/对话页
- [ ] 2.2.3 创建 `app/projects/[id]/documents/page.tsx` - 文档管理
- [ ] 2.2.4 创建 `app/projects/[id]/settings/page.tsx` - GitHub 设置
- [ ] 2.2.5 创建 `app/projects/new/page.tsx` - 新建项目

#### 2.3 组件开发
- [ ] 2.3.1 项目列表组件 `components/projects/ProjectList.tsx`
- [ ] 2.3.2 文档上传组件 `components/documents/DocumentUpload.tsx`
- [ ] 2.3.3 文档列表组件 `components/documents/DocumentList.tsx`
- [ ] 2.3.4 聊天界面组件 `components/chat/ChatInterface.tsx`
- [ ] 2.3.5 GitHub 设置组件 `components/github/GithubSettings.tsx`

#### 2.4 API 对接
- [ ] 2.4.1 创建 `lib/api.ts` - API 调用封装
- [ ] 2.4.2 实现文件上传 multipart/form-data
- [ ] 2.4.3 实现聊天流式响应 (SSE)

#### 2.5 验证标准
- [ ] 可访问项目列表页面
- [ ] 可创建新项目
- [ ] 可上传文档
- [ ] 可查看/删除文档
- [ ] 可进行聊天对话
- [ ] 可配置 GitHub 同步

---

## 阶段三：GitHub 同步
### 目标: 实现 GitHub 仓库文档同步

#### 3.1 GitHub 服务
- [x] 3.1.1 安装 `PyGithub` 依赖 (已随阶段一安装)
- [ ] 3.1.2 创建 `services/github_service.py` - GitHub API 封装
- [ ] 3.1.3 实现 PAT 令牌存储 (加密)
- [ ] 3.1.4 实现仓库列表获取
- [ ] 3.1.5 实现文件树遍历和下载
- [ ] 3.1.6 实现文档内容处理 (复用 LangChain loaders)

#### 3.2 GitHub API 路由
- [ ] 3.2.1 创建 `api/github.py` - GitHub 同步 API
- [ ] 3.2.2 实现 `/api/projects/{id}/github/connect`
- [ ] 3.2.3 实现 `/api/projects/{id}/github/repos`
- [ ] 3.2.4 实现 `/api/projects/{id}/github/sync`

#### 3.3 前端 GitHub 集成
- [ ] 3.3.1 GitHub 连接表单
- [ ] 3.3.2 仓库选择器
- [ ] 3.3.3 同步状态显示

#### 3.4 验证标准
- [ ] 可连接 GitHub 账号
- [ ] 可选择要同步的仓库
- [ ] 可手动触发同步
- [ ] 同步后文档出现在项目知识库

---

## 阶段四：增强功能 (后续迭代)
- [ ] NotebookLM Audio Overview 功能
- [ ] 文档版本管理
- [ ] 协作功能
- [ ] 多租户支持

---

## 技术债务清理
- [x] 移除 Streamlit 相关代码 (uv sync 自动移除)
- [x] 更新 `pyproject.toml` 依赖
- [ ] 更新 `.env.example`
- [ ] 更新 `README.md`

---

## 部署检查清单
- [x] PostgreSQL 数据库配置 (使用 SQLite 替代，可切换)
- [x] FastAPI 服务启动验证 ✅
- [ ] Next.js 服务启动验证
- [x] API 端点测试 ✅ (health, projects 端点已验证)
- [ ] 前端功能测试

---

## 项目结构 (阶段一完成后)

```
StudyClaw/
├── api/                    # FastAPI 路由
│   ├── __init__.py
│   ├── projects.py         # 项目管理 API
│   ├── documents.py        # 文档管理 API
│   └── chat.py             # 问答 API
├── database/               # 数据库层
│   ├── __init__.py
│   ├── models.py           # SQLAlchemy 模型
│   └── session.py          # 异步会话管理
├── services/               # 业务逻辑层
│   ├── __init__.py
│   ├── project_service.py  # 项目 CRUD
│   └── document_service.py # 文档处理
├── agent/                  # Agent 层
│   ├── react_agent.py      # LangGraph Agent
│   └── tools/
│       ├── rag_tool.py     # 项目级 RAG 工具
│       └── ...
├── rag/                    # RAG 层
│   ├── vector_store.py     # 项目级向量存储
│   └── rag_service.py      # RAG 服务
├── main.py                 # FastAPI 入口
├── pyproject.toml
└── plan.md
```

---

## 时间线预估
| 阶段 | 主要任务 | 状态 |
|------|----------|------|
| 阶段一 | 核心功能 | ✅ 已完成 |
| 阶段二 | 前端开发 | ⏳ 待开始 |
| 阶段三 | GitHub 同步 | ⏸ 待开始 |
| 阶段四 | 增强功能 | ⏸ 待开始 |

---

## 最近更新
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
