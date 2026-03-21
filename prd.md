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
| **文档处理** | LangChain 文档加载器 | PyPDFLoader, TextLoader 等 |
| **文件存储** | 本地文件系统 | 上传文件存到本地目录 |
| **GitHub 集成** | PyGithub | PAT 令牌认证 |

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
└───────────────┘  └───────────────┘  └───────────────┘
        │                  │
        ▼                  ▼
┌───────────────┐  ┌───────────────┐
│   本地文件     │  │  Chroma DB    │
│   存储目录     │  │ (向量存储)     │
└───────────────┘  └───────────────┘
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

## 8. 后续迭代

- [ ] NotebookLM Audio Overview 功能
- [ ] 多租户支持
- [ ] 文档版本管理
- [ ] 协作功能
