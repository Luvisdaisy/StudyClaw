# 研究生资料管理知识图谱系统 - 实施计划

## 背景 (Context)

当前项目是一个扫地机器人客服chatbot，用户希望将其改造为研究生资料管理系统：
- 用户有多个文件夹存放不同资料
- 提供目录路径，程序自动识别处理该目录下所有文件
- 构建知识图谱向量化数据库
- 通过对话获取相关数据，并给出参考文件来源

## 核心架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Streamlit Web UI                          │
├─────────────────────────────────────────────────────────────────┤
│                      LangGraph ReAct Agent                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ RAG检索工具   │  │ 文件查询工具  │  │ 知识图谱查询工具     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│              向量数据库 (Chroma) + 文件来源追踪                  │
├─────────────────────────────────────────────────────────────────┤
│              文件处理器 (支持多格式)                              │
├─────────────────────────────────────────────────────────────────┤
│              用户指定目录 ─────────────> 处理文件                 │
└─────────────────────────────────────────────────────────────────┘
```

## 实施步骤

### Phase 1: 基础设施重构 (Week 1)

#### Step 1.1: 扩展文件处理器
**目标**: 支持更多文件格式，扫描用户指定目录

**修改文件**:
- `utils/file_handler.py` - 新增文件类型支持
- `config/chroma.yml` - 新增配置项

**新增支持格式**:
- Markdown (.md)
- Word文档 (.docx)
- CSV (.csv)
- 代码文件 (.py, .js, .java, .cpp, .go, .rs)
- 幻灯片 (.pptx)
- HTML (.html, .htm)
- JSON/YAML (.json, .yaml, .yml)

**实现**:
```python
# 新增函数
def load_markdown(filepath: str) -> list[Document]
def load_docx(filepath: str) -> list[Document]
def load_csv(filepath: str) -> list[Document]
def load_code_file(filepath: str) -> list[Document]
def load_pptx(filepath: str) -> list[Document]
def load_html(filepath: str) -> list[Document]
def scan_directory(directory: str, recursive: bool = True) -> list[str]
```

#### Step 1.2: 重构向量存储服务
**目标**: 支持多目录管理，追踪文件来源

**修改文件**:
- `rag/vector_store.py` - 完全重构

**新增功能**:
```python
class VectorStoreService:
    def __init__(self, collection_name: str = "study_materials"):
        # 支持自定义collection名称

    def add_documents_with_source(self, docs: list[Document], source_path: str):
        """添加文档并记录来源路径"""

    def load_directory(self, directory: str, recursive: bool = True):
        """扫描并加载整个目录"""

    def get_source_files(self, doc_ids: list[str]) -> list[str]:
        """根据文档ID获取源文件路径"""

    def list_managed_directories(self) -> list[str]:
        """列出已管理的目录"""

    def remove_directory(self, directory: str):
        """移除指定目录的所有文档"""
```

#### Step 1.3: 配置文件更新
**修改文件**:
- `config/chroma.yml` - 扩展配置

```yaml
collection_name: study_materials
persist_directory: chroma_db
k: 5  # 增加检索数量
allow_knowledge_file_type:
  - txt
  - md
  - pdf
  - docx
  - csv
  - py
  - js
  - java
  - cpp
  - go
  - rs
  - pptx
  - html
  - json
  - yaml
managed_directories: []  # 用户添加的目录列表
```

---

### Phase 2: RAG服务增强 (Week 2)

#### Step 2.1: 增强RAG检索服务
**目标**: 返回参考文件来源

**修改文件**:
- `rag/rag_service.py` - 扩展返回格式

**实现**:
```python
class RagSummarizeService:
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()

    def rag_summarize(self, query: str) -> dict:
        """
        返回格式:
        {
            "answer": "生成的答案",
            "sources": [
                {"file": "文件路径", "content": "相关内容片段", "score": 0.95},
                ...
            ]
        }
        """
```

#### Step 2.2: 更新提示词
**新增文件**:
- `prompts/study_rag_prompts.txt`

**修改文件**:
- `config/prompts.yml`

---

### Phase 3: Agent工具扩展 (Week 3)

#### Step 3.1: 新增管理工具
**修改文件**:
- `agent/tools/agent_tools.py` - 新增工具

**新增工具**:
```python
@tool(description="添加一个目录到知识库，支持的文件格式会自动处理")
def add_directory_to_knowledge_base(directory_path: str) -> str:
    """扫描目录并添加到向量数据库"""
    ...

@tool(description="列出当前知识库管理的所有目录")
def list_knowledge_directories() -> str:
    """返回已管理的目录列表"""
    ...

@tool(description="从知识库中移除指定目录")
def remove_directory_from_knowledge_base(directory_path: str) -> str:
    """删除指定目录的所有文档"""
    ...

@tool(description="获取当前知识库状态统计")
def get_knowledge_base_stats() -> str:
    """返回文档数量、目录数量等统计信息"""
    ...
```

#### Step 3.2: 修改RAG工具返回格式
**修改文件**:
- `agent/tools/agent_tools.py`

```python
@tool(description="从知识库中检索相关信息并生成回答，同时返回参考文件来源")
def rag_summarize_with_sources(query: str) -> str:
    """RAG检索，返回答案和参考文件"""
    result = rag.rag_summarize(query)
    # 格式化输出，包含文件来源
    output = f"{result['answer']}\n\n📚 参考文件:\n"
    for i, source in enumerate(result['sources'], 1):
        output += f"{i}. {source['file']}\n"
    return output
```

---

### Phase 4: UI界面更新 (Week 4)

#### Step 4.1: 更新Streamlit界面
**修改文件**:
- `app.py` - 完全重构UI

**新增功能**:
1. 侧边栏 - 知识库管理
   - 添加目录输入框
   - 目录列表展示
   - 删除目录按钮
   - 知识库统计信息

2. 主界面 - 对话区域
   - 参考文件高亮显示
   - 点击查看原文
   - 引用来源折叠/展开

**UI布局**:
```python
# 侧边栏
with st.sidebar:
    st.title("📚 知识库管理")
    # 添加目录
    new_dir = st.text_input("添加目录路径")
    if st.button("添加"):
        add_directory(new_dir)

    # 目录列表
    st.subheader("已管理目录")
    for dir_path in directories:
        col1, col2 = st.columns([4, 1])
        col1.write(dir_path)
        if col2.button("删除", key=dir_path):
            remove_directory(dir_path)

    # 统计
    st.metric("文档数", doc_count)
    st.metric("目录数", dir_count)

# 主界面
st.title("🔍 研究生资料助手")
# 对话逻辑，显示参考文件
```

---

### Phase 5: 知识图谱功能 (可选，Week 5-6)

#### Step 5.1: 实体关系抽取
**新增文件**:
- `kg/entity_extractor.py`

**实现**:
- 使用LLM从文档中抽取实体和关系
- 实体类型: 论文、概念、人物、方法、数据集
- 关系类型: 引用、提出、使用、属于、相关

#### Step 5.2: 图数据库集成
**新增文件**:
- `kg/graph_service.py`

**实现**:
- 支持NetworkX本地图谱（简单）
- 可选Neo4j云图谱（进阶）

#### Step 5.3: 混合检索
**修改文件**:
- `rag/rag_service.py`

**实现**:
- 向量检索 + 知识图谱联合查询
- 图谱路径可视化

---

## 关键文件修改清单

| 文件 | 操作 | 描述 |
|------|------|------|
| `utils/file_handler.py` | 修改 | 扩展文件加载器 |
| `config/chroma.yml` | 修改 | 扩展配置 |
| `rag/vector_store.py` | 重构 | 多目录支持 |
| `rag/rag_service.py` | 修改 | 返回源文件 |
| `prompts/study_rag_prompts.txt` | 新增 | 新提示词 |
| `config/prompts.yml` | 修改 | 提示词配置 |
| `agent/tools/agent_tools.py` | 修改 | 新增管理工具 |
| `app.py` | 重构 | 新UI |

## 验证方法

### 功能验证
1. 添加测试目录，运行添加目录功能
2. 询问与测试资料相关的问题
3. 验证返回的参考文件是否正确
4. 测试删除目录功能

### 运行命令
```bash
# 启动应用
uv run streamlit run app.py

# 测试向量存储
uv run python -m rag.vector_store  # 需要先配置目录
```

## 技术要点

- 保持使用阿里云DashScope (通义千问) 作为LLM
- 继续使用Chroma作为向量数据库
- LangGraph ReAct Agent架构不变
- 所有配置可通过YAML调整
