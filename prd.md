# StudyClaw 产品需求文档 (PRD)

## 1. 项目概述

### 项目目标
开发类似 NotebookLM 的 AI 学习助手应用，帮助用户从大量文档中快速获取答案，支持小组协作。

### 目标用户
- 个人学习者
- 小型团队（<10人）
- 教学场景

---

## 2. 功能需求

### 2.1 文档管理与 RAG 问答

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 文档上传 | 支持 PDF、Markdown、TXT 文件上传 | P0 |
| 项目创建 | 创建独立的学习项目 | P0 |
| 项目级知识库隔离 | 每个项目拥有独立知识库 | P0 |
| RAG 对话 | 基于项目文档的智能问答 | P0 |
| 文档管理 | 查看已上传文档列表 | P1 |
| 文档删除 | 删除指定文档 | P1 |

### 2.2 文件 CRUD 功能

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 上传文件 | 添加新文档到知识库 | P0 |
| 删除文件 | 从知识库移除文档 | P1 |
| 修改文件 | 更新文档内容 | P2 |
| 查询文件 | 检索文档列表 | P1 |

### 2.3 GitHub 仓库同步

| 功能 | 描述 | 优先级 |
|------|------|--------|
| GitHub 连接 | 通过 PAT 认证连接仓库 | P1 |
| 仓库选择 | 选择要同步的仓库 | P1 |
| 手动同步 | 用户触发同步操作 | P1 |
| 文档处理 | 自动处理仓库中的文档 | P1 |

### 2.4 Agent 能力

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 通用学习助手 | 基于项目文档回答问题的 AI 助手 | P0 |
| RAG 检索 | 从项目知识库检索相关文档 | P0 |
| 网络搜索 | 当文档检索不足时联网搜索（可选开关） | P1 |
| Session 持久化 | 跨请求保持对话历史 | P1 |

### 2.5 对话控制

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 联网开关 | 每次对话可选启用网络搜索 | P1 |
| 流式响应 | SSE 实时返回 Agent 思考过程 | P0 |

---

## 3. 技术架构

### 3.1 技术栈

| 层级 | 技术选择 | 说明 |
|------|----------|------|
| **API 服务** | FastAPI | 高性能异步 API 框架 |
| **前端管理界面** | Next.js 14 (App Router) + Shadcn UI | 独立前端 |
| **LLM** | 阿里云通义千问 (qwen3-max) | 现有配置保留 |
| **Embeddings** | DashScope (text-embedding-v4) | 现有配置保留 |
| **向量数据库** | Chroma | 每个项目独立 collection |
| **元数据存储** | PostgreSQL | 项目、文档等元数据 |
| **Agent 框架** | LangGraph | ReAct Agent + RAG |
| **Session 持久化** | Redis + PostgreSQL | 活跃会话缓存 + 历史持久化 |
| **网络搜索** | Tavily/DuckDuckGo | RAG 补充（可选） |
| **文档处理** | LangChain 文档加载器 | PyPDFLoader, TextLoader 等 |
| **文件存储** | 本地文件系统 | 上传文件存到本地目录 |
| **GitHub 集成** | PyGithub | PAT 令牌认证 |
| **容器化** | Docker + Docker Compose | 开发环境服务隔离 |

### 3.2 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Next.js + Shadcn UI                         │
│                        (StudyClaw/frontend)                      │
│  ┌─────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐  │
│  │ 项目列表 │  │ 文档管理    │  │  聊天界面   │  │ GitHub  │  │
│  └─────────┘  └─────────────┘  └─────────────┘  └─────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP API
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Server (后端)                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  API Routes:                                            │    │
│  │  - POST /api/projects (创建项目)                         │    │
│  │  - GET  /api/projects (项目列表)                         │    │
│  │  - POST /api/projects/{id}/documents (上传文档)          │    │
│  │  - GET  /api/projects/{id}/documents (文档列表)         │    │
│  │  - DELETE /api/documents/{id} (删除文档)               │    │
│  │  - POST /api/projects/{id}/chat (对话)                  │    │
│  │  - POST /api/projects/{id}/github/sync (GitHub 同步)    │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  项目服务      │  │  LangGraph    │  │ GitHub 服务   │
│  (PostgreSQL) │  │  Agent + RAG  │  │  (PyGithub)   │
└───────────────┘  └───────┬───────┘  └───────────────┘
        │                  │
        │          ┌───────┴───────┐
        │          ▼               ▼
        │   ┌─────────────┐  ┌─────────────┐
        │   │   Chroma    │  │  网络搜索    │
        │   │ (向量存储)   │  │ (Tavily)    │
        │   └─────────────┘  └─────────────┘
        │          │               │
        └──────────┼───────────────┘
                   ▼
         ┌─────────────────┐
         │ Redis (Session) │
         │ PostgreSQL       │
         └─────────────────┘
```

### 3.3 Docker 基础设施

为避免污染本地系统环境，所有依赖服务通过 Docker 运行：

| 服务 | 镜像 | 端口 | 用途 |
|------|------|------|------|
| PostgreSQL | postgres:16 | 5432 | 元数据存储 |
| Redis | redis:7 | 6379 | Session 缓存 |
| Chroma | chromadb/chroma | 8000 | 向量数据库（可选，本地开发用 SQLite 文件） |

**镜像使用规范**：
- **创建新 Docker 服务前**，必须先检查本地是否已有可用镜像：`docker images`
- 如本地已有对应镜像，优先使用本地镜像（节省带宽和时间）
- 如本地无镜像，pull 时使用 `postgres:16-alpine`、`redis:7-alpine` 等轻量镜像

**docker-compose.yml 示例**：
```yaml
services:
  postgres:
    image: postgres:16-alpine  # 优先使用 alpine 轻量镜像
    environment:
      POSTGRES_DB: studclaw
      POSTGRES_USER: studclaw
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secret}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  redis_data:
```

---

## 4. 数据模型

### 4.1 项目 (Project)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | UUID | 项目唯一标识 |
| name | string | 项目名称（唯一） |
| description | string | 项目描述 |
| github_token | string | GitHub PAT 令牌（加密存储） |
| github_repo | string | 关联的 GitHub 仓库 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 4.2 文档 (Document)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | UUID | 文档唯一标识 |
| project_id | UUID | 所属项目 |
| filename | string | 原始文件名 |
| file_path | string | 本地存储路径 |
| file_type | string | 文件类型 (pdf/md/txt) |
| file_hash | string | MD5 哈希（去重） |
| status | string | 处理状态 (pending/processing/completed/failed) |
| chunk_count | int | 分割后的 chunk 数量 |
| created_at | datetime | 上传时间 |
| updated_at | datetime | 更新时间 |

---

## 5. API 接口设计

### 5.1 项目管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/projects | 创建项目 |
| GET | /api/projects | 获取项目列表 |
| GET | /api/projects/{id} | 获取项目详情 |
| DELETE | /api/projects/{id} | 删除项目 |

### 5.2 文档管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/projects/{id}/documents | 上传文档 |
| GET | /api/projects/{id}/documents | 获取文档列表 |
| DELETE | /api/documents/{id} | 删除文档 |

### 5.3 问答对话

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/projects/{id}/chat | 项目对话（流式） |

### 5.4 GitHub 同步

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/projects/{id}/github/connect | 连接 GitHub 仓库 |
| GET | /api/projects/{id}/github/repos | 获取可同步的仓库列表 |
| POST | /api/projects/{id}/github/sync | 手动触发同步 |

---

## 6. 开发阶段

---

### 阶段一：核心功能（文档问答） ✅ 已完成

**完成时间**: 2026-03-21

**摘要**: FastAPI 后端核心功能，项目隔离的文档管理和 RAG 问答

**已创建文件**:
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

**验收标准**:
- [x] 可创建/查询/删除项目 (API 已测试)
- [x] 可上传 PDF/MD/TXT 文档
- [x] 文档上传后自动分块存入 Chroma
- [x] RAG 问答检索到正确的项目文档
- [x] 不同项目知识库完全隔离 (collection 级隔离)

#### 技术方案

| 功能 | 技术实现 |
|------|----------|
| **PostgreSQL 连接** | SQLAlchemy 2.0 + asyncpg |
| **项目管理** | FastAPI + Pydantic 模型 |
| **文档上传** | FastAPI FileUpload + 本地存储 |
| **文档处理** | LangChain loaders (PyPDFLoader, TextLoader, UnstructuredMarkdownLoader) |
| **文本分块** | RecursiveCharacterTextSplitter |
| **向量存储** | Chroma (按 project_id 命名 collection) |
| **RAG 问答** | LangGraph Agent + Retriever Tool |
| **会话管理** | LangGraph MemorySaver |

#### 实现思路

1. **项目服务层**：使用 SQLAlchemy 定义 Project、Document 模型，实现 CRUD
2. **文档处理流程**：
   - 接收上传文件 → 存到本地 `data/projects/{project_id}/` 目录
   - 使用 LangChain 加载器提取文本
   - 文本分块 → 存入 Chroma（collection 名为 `project_{uuid}`）
   - 记录元数据到 PostgreSQL
3. **RAG Agent**：
   - 创建项目专属的 retriever
   - 将 retriever 封装为 LangGraph Tool
   - Agent 根据问题自动判断是否需要检索文档
4. **知识库隔离**：每个项目独立 Chroma collection，通过 project_id 隔离

#### 关键文件

```
rag/
├── vector_store.py      # 复用，改造为支持 project_id
├── rag_service.py       # 复用，改造为项目级别
agent/
├── react_agent.py       # 复用，添加 RAG Tool
├── tools/
│   └── rag_tool.py     # 新增：项目级 RAG 工具
services/
├── project_service.py   # 新增：项目 CRUD
├── document_service.py  # 新增：文档处理
database/
├── models.py            # 新增：SQLAlchemy 模型
├── session.py           # 新增：数据库会话
api/
├── projects.py          # 新增：项目 API 路由
├── documents.py         # 新增：文档 API 路由
├── chat.py              # 新增：问答 API 路由
```

---

### 阶段二：前端开发 ✅ 已完成

**完成时间**: 2026-03-21

**摘要**: Next.js 14 + Shadcn UI 管理界面

**已创建文件**:
- `frontend/src/app/page.tsx` - 首页/项目列表
- `frontend/src/app/projects/[id]/page.tsx` - 项目详情/对话页
- `frontend/src/app/projects/[id]/documents/page.tsx` - 文档管理
- `frontend/src/app/projects/[id]/settings/page.tsx` - GitHub 设置
- `frontend/src/app/projects/new/page.tsx` - 新建项目
- `frontend/src/components/projects/ProjectList.tsx`, `ProjectCard.tsx`, `CreateProjectDialog.tsx`
- `frontend/src/components/documents/DocumentUpload.tsx`, `DocumentList.tsx`, `DocumentItem.tsx`
- `frontend/src/components/chat/ChatInterface.tsx`, `ChatMessage.tsx`, `ChatInput.tsx`
- `frontend/src/components/layout/Sidebar.tsx`, `Header.tsx`
- `frontend/src/lib/api.ts` - API 调用封装

**验收标准**:
- [x] 可访问 http://localhost:3000 查看项目列表
- [x] 可创建新项目
- [x] 可上传 PDF/MD/TXT 文档
- [x] 可查看/删除文档
- [x] 可进行聊天对话（流式响应）
- [x] Next.js build 通过

#### 技术方案

| 功能 | 技术实现 |
|------|----------|
| **框架** | Next.js 14 (App Router) |
| **UI 组件** | Shadcn UI + Tailwind CSS |
| **状态管理** | React Query (服务端状态) + Zustand (客户端状态) |
| **HTTP 客户端** | Axios / Fetch |
| **表单处理** | React Hook Form + Zod |
| **图标** | Lucide React |

#### 实现思路

1. **项目初始化**
   - 创建 `StudyClaw/frontend` 目录
   - 使用 `npx create-next-app@latest` 初始化
   - 安装 Shadcn UI 并配置

2. **页面结构**

```
frontend/
├── app/
│   ├── layout.tsx          # 根布局
│   ├── page.tsx            # 首页（项目列表）
│   ├── projects/
│   │   ├── page.tsx        # 项目列表页
│   │   ├── [id]/
│   │   │   ├── page.tsx    # 项目详情/对话页
│   │   │   ├── documents/  # 文档管理
│   │   │   └── settings/   # 项目设置
│   │   └── new/            # 新建项目
│   └── api/                # API 代理 (可选)
├── components/
│   ├── ui/                 # Shadcn 基础组件
│   ├── projects/           # 项目相关组件
│   ├── documents/          # 文档相关组件
│   ├── chat/               # 聊天组件
│   └── layout/             # 布局组件
├── lib/
│   ├── api.ts              # API 调用封装
│   └── utils.ts             # 工具函数
└── types/                  # TypeScript 类型定义
```

3. **核心页面功能**

| 页面 | 功能 |
|------|------|
| **项目列表** | 显示所有项目，创建/删除项目 |
| **项目详情** | 项目信息、文档列表、对话入口 |
| **文档管理** | 上传、查看、删除文档 |
| **对话界面** | 聊天界面，流式响应显示 |
| **GitHub 设置** | 连接仓库、同步操作 |
| **对话历史** | 查看历史对话记录 |

4. **与 FastAPI 通信**
   - 前端调用 FastAPI 暴露的 REST API
   - 文件上传使用 `multipart/form-data`
   - 聊天使用流式响应 (SSE)

#### API 对接

| 前端页面 | 调用 API |
|----------|----------|
| 项目列表 | GET /api/projects |
| 创建项目 | POST /api/projects |
| 上传文档 | POST /api/projects/{id}/documents |
| 文档列表 | GET /api/projects/{id}/documents |
| 删除文档 | DELETE /api/documents/{id} |
| 发送消息 | POST /api/projects/{id}/chat |
| GitHub 同步 | POST /api/projects/{id}/github/sync |

---

### 阶段三：GitHub 同步 ✅ 已完成

**完成时间**: 2026-03-22

**摘要**: GitHub 仓库文档同步功能

**已创建文件**:
- `services/github_service.py` - GitHub API 封装
- `api/github.py` - GitHub 同步 API
- `frontend/src/components/github/GitHubSettings.tsx` - GitHub 连接表单
- `frontend/src/components/github/SyncStatus.tsx` - 同步状态显示

**API 端点**:
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/projects/{id}/github/connect | 连接 GitHub |
| POST | /api/projects/{id}/github/disconnect | 断开 GitHub |
| GET | /api/projects/{id}/github/repos | 仓库列表 |
| PATCH | /api/projects/{id}/github/repo | 选择仓库 |
| POST | /api/projects/{id}/github/sync | 触发同步 |
| GET | /api/projects/{id}/github/sync/status | 同步状态 |
| GET | /api/projects/{id}/github/user | GitHub 用户信息 |

**验收标准**:
- [x] 可连接 GitHub 账号
- [x] 可选择要同步的仓库
- [x] 可手动触发同步
- [x] 同步后文档出现在项目知识库

---

### 阶段四：Agent & RAG 优化 ✅ 已完成

**完成时间**: 2026-03-22

**摘要**: 修复 RAG 检索问题，优化 Agent 角色定位，添加网络搜索能力，Session 持久化

#### 4.1 RAG 检索修复
- 修复 Chroma `agent` collection dimension=null 问题
- 移除 `rag_tool.py` 中的全局缓存
- 增大 chunk_size: 200 → 500

#### 4.2 Agent 提示词重写
- 重写 `prompts/main_prompts.txt` 为通用 AI 学习助手角色
- 清理废弃模拟工具: `get_weather`, `get_user_location`, `get_user_id`, `get_current_month`, `fetch_external_data`, `fill_context_for_report`

#### 4.3 网络搜索能力
- 创建 `agent/tools/web_search_tool.py` - BraveSearch 集成
- `ChatRequest` 添加 `enable_web_search: bool = False` 字段
- Agent 根据参数决定是否启用网络搜索

#### 4.4 Session 持久化 ✅ 已实现
- Redis 主存储 (TTL=7天)
- PostgreSQL 异步批量备份
- 定时同步 (60秒间隔 或 100条触发)

**已创建文件**:
- `session_store/redis_store.py` - Redis 存储 (TTL=7天)
- `session_store/postgres_store.py` - PostgreSQL 异步批量备份
- `session_store/manager.py` - 统一接口 + 异步批量
- `session_store/checkpoint.py` - LangGraph Checkpoint 适配器
- `session_store/conftest.py` - 共享 fixtures
- `config/session.yml` - Session 配置

**验收标准**:
- [x] RAG 检索能正确返回上传文档内容
- [x] Agent 扮演通用学习助手角色
- [x] 联网开关可控制网络搜索
- [x] Session 持久化实现 (Redis + PostgreSQL 备份)

---

## 7. 验收标准

### 功能验收 ✅ 全部通过
- [x] 可创建多个独立项目
- [x] 每个项目的知识库完全隔离
- [x] 支持 PDF、Markdown、TXT 上传
- [x] RAG 问答能正确检索项目内文档
- [x] 文件增删改查功能正常
- [x] GitHub 仓库可手动同步
- [x] Next.js 前端可正常访问
- [x] 项目管理功能正常
- [x] 文档上传/删除功能正常
- [x] 聊天对话功能正常

### 性能验收
- [x] 文档上传后 5 秒内可检索
- [x] 问答响应时间 < 10 秒
- [ ] 支持 10 人同时使用 (待验证)

---

## 8. 后续迭代 (Phase 5)

- [ ] NotebookLM Audio Overview 功能
- [ ] 多租户支持
- [ ] 文档版本管理
- [ ] 协作功能

---

## 9. Recent Updates

| 日期 | 变更 |
|------|------|
| 2026-03-22 | 阶段四完成 - Session 持久化 (Redis + PostgreSQL) |
| 2026-03-22 | 阶段四 - Agent & RAG 优化 (网络搜索, 提示词重写) |
| 2026-03-22 | 阶段三完成 - GitHub 同步功能 |
| 2026-03-22 | 前端删除确认对话框统一为 UI 组件 |
| 2026-03-22 | 代码审查修复 (PR #4) - 安全、组件、类型修复 |
| 2026-03-21 | 阶段二完成 - Next.js 前端开发 |
| 2026-03-21 | 阶段一完成 - FastAPI 后端核心功能 |
