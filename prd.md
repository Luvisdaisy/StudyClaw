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

### 阶段一：核心功能（文档问答）

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

### 阶段二：前端开发

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

### 阶段三：GitHub 同步

#### 技术方案

| 功能 | 技术实现 |
|------|----------|
| **GitHub API** | PyGithub 库 |
| **仓库列表** | GitHub API 列出用户仓库 |
| **文件下载** | GitHub Contents API |
| **同步触发** | 手动 POST 触发 |

#### 实现思路

1. **连接 GitHub**：用户输入 PAT 令牌，存储到项目配置
2. **获取仓库列表**：调用 GitHub API 获取用户有权限的仓库
3. **选择仓库**：用户选择后保存到项目配置
4. **手动同步流程**：
   - 调用 GitHub API 获取仓库文件树
   - 过滤 pdf/md/txt 文件
   - 下载文件内容
   - 调用 LangChain 加载器处理
   - 存入项目对应的 Chroma collection
5. **去重**：使用 file_hash (GitHub commit ID + path) 避免重复

#### 关键文件

```
services/
├── github_service.py    # 新增：GitHub API 封装
api/
└── github.py           # 新增：GitHub 同步 API
```

---

### 阶段四：增强功能

| 功能 | 技术实现 |
|------|----------|
| **NotebookLM Audio** | TTS 生成（后续考虑） |
| **文档版本管理** | PostgreSQL 版本表 |
| **高级搜索** | 混合搜索 (BM25 + 向量) |

---

## 7. 验收标准

### 功能验收
- [ ] 可创建多个独立项目
- [ ] 每个项目的知识库完全隔离
- [ ] 支持 PDF、Markdown、TXT 上传
- [ ] RAG 问答能正确检索项目内文档
- [ ] 文件增删改查功能正常
- [ ] GitHub 仓库可手动同步
- [ ] Next.js 前端可正常访问
- [ ] 项目管理功能正常
- [ ] 文档上传/删除功能正常
- [ ] 聊天对话功能正常

### 性能验收
- [ ] 文档上传后 5 秒内可检索
- [ ] 问答响应时间 < 10 秒
- [ ] 支持 10 人同时使用

---

## 8. Agent & RAG 优化

### 8.1 RAG 检索修复
| 功能 | 技术实现 |
|------|----------|
| Chroma collection 修复 | 删除 dimension=null 的无效 collection |
| 缓存问题修复 | 移除 `rag_tool.py` 中的全局缓存 |
| Chunk size 优化 | 增大到 500（当前 200） |

### 8.2 Agent 提示词重写
| 功能 | 技术实现 |
|------|----------|
| 角色转换 | 从"扫地机器人客服"改为"通用 AI 学习助手" |
| 工具清理 | 移除模拟工具（天气、位置、报告生成等） |
| 保留工具 | `rag_summarize`, `rag_retrieve` |

### 8.3 网络搜索能力
| 功能 | 技术实现 |
|------|----------|
| 网络搜索工具 | Tavily API / DuckDuckGo |
| 联网开关 | 每次对话请求可选 `enable_web_search: bool` |
| 检索策略 | 本地 RAG 优先，不足时启用网络搜索 |

### 8.4 Session 持久化 ✅ 已实现
| 功能 | 技术实现 |
|------|----------|
| 会话缓存 | Redis（TTL 7天） |
| 持久化存储 | PostgreSQL |
| 实现方式 | SessionManager (Redis + PostgreSQL) + SessionCheckpointSaver |

**实现细节**：
- `session_store/redis_store.py` - Redis 主存储，TTL=7天
- `session_store/postgres_store.py` - PostgreSQL 异步批量备份
- `session_store/manager.py` - 统一接口，定时同步（60秒或100条触发）
- `session_store/checkpoint.py` - LangGraph Checkpoint 适配器
- `config/session.yml` - Session 配置

**PostgreSQL 表**：
```sql
CREATE TABLE agent_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    messages JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 8.5 关键文件清单

| 文件 | 修改内容 |
|------|----------|
| `rag/vector_store.py` | 修复 collection 创建 |
| `rag/rag_service.py` | 检查检索流程 |
| `agent/tools/rag_tool.py` | 移除缓存 |
| `agent/tools/agent_tools.py` | 清理废弃模拟工具 |
| `agent/tools/web_search_tool.py` | **新建** - 网络搜索工具 |
| `agent/react_agent.py` | Session 持久化 + 网络搜索分支 |
| `prompts/main_prompts.txt` | 重写为通用学习助手 |
| `config/rag.yml` | 合并配置，chunk_size: 500 |
| `config/session.yml` | **新建** - Session 配置 |
| `api/chat.py` | 添加 `enable_web_search` 参数 |
| `session_store/__init__.py` | **新建** - 模块导出 |
| `session_store/redis_store.py` | **新建** - Redis 存储 |
| `session_store/postgres_store.py` | **新建** - PostgreSQL 存储 |
| `session_store/manager.py` | **新建** - 统一接口 + 异步批量 |
| `session_store/checkpoint.py` | **新建** - LangGraph Checkpoint 适配器 |
| `main.py` | SessionManager 初始化/关闭 |

### 8.6 验收标准
- [x] RAG 检索能正确返回上传文档内容
- [x] Agent 扮演通用学习助手角色
- [x] 联网开关可控制网络搜索
- [x] Session 持久化实现 (Redis + PostgreSQL)

---

## 9. 后续迭代

- [ ] NotebookLM Audio Overview 功能
- [ ] 多租户支持
- [ ] 文档版本管理
- [ ] 协作功能
