import os
import json
from typing import List, Optional
from langchain_chroma import Chroma
from langchain_core.documents import Document
from utils.config_handler import chroma_cfg
from model.factory import embedding_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.path_tool import get_abs_path
from utils.file_handler import (
    scan_directory,
    get_file_loader,
    get_md5_hex,
)
from utils.logger_handler import logger


class VectorStoreService:
    def __init__(self, collection_name: Optional[str] = None):
        """初始化向量存储服务

        Args:
            collection_name: collection名称，默认使用配置中的名称
        """
        self.collection_name = collection_name or chroma_cfg["collection_name"]
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=embedding_model,
            persist_directory=chroma_cfg["persist_directory"],
        )
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_cfg["chunk_size"],
            chunk_overlap=chroma_cfg["chunk_overlap"],
            separators=chroma_cfg["separators"],
        )
        self._init_metadata_store()

    def _init_metadata_store(self):
        """初始化元数据存储"""
        self.metadata_file = get_abs_path("vector_metadata.json")
        if not os.path.exists(self.metadata_file):
            self._save_metadata({"managed_directories": [], "file_md5": {}})

    def _load_metadata(self) -> dict:
        """加载元数据"""
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            return {"managed_directories": [], "file_md5": {}}

    def _save_metadata(self, metadata: dict):
        """保存元数据"""
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    def _check_file_processed(self, filepath: str) -> bool:
        """检查文件是否已处理"""
        metadata = self._load_metadata()
        file_md5 = get_md5_hex(filepath)
        if not file_md5:
            return False
        return file_md5 in metadata.get("file_md5", {})

    def _mark_file_processed(self, filepath: str):
        """标记文件已处理"""
        metadata = self._load_metadata()
        file_md5 = get_md5_hex(filepath)
        if file_md5:
            if "file_md5" not in metadata:
                metadata["file_md5"] = {}
            metadata["file_md5"][file_md5] = filepath
            self._save_metadata(metadata)

    def get_retriever(self):
        """获取检索器"""
        return self.vector_store.as_retriever(search_kwargs={"k": chroma_cfg["k"]})

    def add_documents_with_source(self, docs: List[Document], source_path: str) -> int:
        """添加文档并记录来源路径

        Args:
            docs: Document列表
            source_path: 源文件路径

        Returns:
            添加的文档数量
        """
        if not docs:
            return 0

        # 为每个文档添加source元数据
        for doc in docs:
            doc.metadata["source"] = source_path
            doc.metadata["filename"] = os.path.basename(source_path)

        # 分块文档
        split_docs = self.spliter.split_documents(docs)
        if not split_docs:
            logger.warning(
                f"Document splitting resulted in no chunks for {source_path}"
            )
            return 0

        # 添加到向量存储
        self.vector_store.add_documents(split_docs)
        self._mark_file_processed(source_path)

        logger.info(f"Added {len(split_docs)} chunks from {source_path}")
        return len(split_docs)

    def load_directory(self, directory: str, recursive: bool = True) -> dict:
        """扫描并加载整个目录

        Args:
            directory: 目录路径
            recursive: 是否递归子目录

        Returns:
            加载结果统计
        """
        directory = os.path.abspath(directory)

        if not os.path.isdir(directory):
            logger.error(f"Directory does not exist: {directory}")
            return {"status": "error", "message": "Directory does not exist"}

        # 获取支持的文件类型
        allowed_types = tuple(chroma_cfg["allow_knowledge_file_type"])

        # 扫描目录
        files = scan_directory(directory, allowed_types, recursive)
        logger.info(f"Found {len(files)} files in {directory}")

        if not files:
            return {
                "status": "success",
                "files_processed": 0,
                "files_skipped": 0,
                "message": "No supported files found",
            }

        # 加载每个文件
        files_processed = 0
        files_skipped = 0

        for filepath in files:
            if self._check_file_processed(filepath):
                logger.info(f"File already processed: {filepath}")
                files_skipped += 1
                continue

            try:
                docs = get_file_loader(filepath)
                if docs:
                    self.add_documents_with_source(docs, filepath)
                    files_processed += 1
                else:
                    logger.warning(f"No content extracted from: {filepath}")
                    files_skipped += 1
            except Exception as e:
                logger.error(f"Error processing {filepath}: {str(e)}", exc_info=True)
                files_skipped += 1

        # 更新管理的目录列表
        metadata = self._load_metadata()
        if directory not in metadata["managed_directories"]:
            metadata["managed_directories"].append(directory)
            self._save_metadata(metadata)

        return {
            "status": "success",
            "files_processed": files_processed,
            "files_skipped": files_skipped,
            "message": f"Processed {files_processed} files, skipped {files_skipped} files",
        }

    def get_source_files(self, doc_ids: List[str]) -> List[str]:
        """根据文档ID获取源文件路径

        Args:
            doc_ids: 文档ID列表

        Returns:
            源文件路径列表
        """
        sources = set()
        try:
            for doc_id in doc_ids:
                doc = self.vector_store.get(ids=[doc_id])
                if doc and doc.get("metadatas"):
                    source = doc["metadatas"][0].get("source")
                    if source:
                        sources.add(source)
        except Exception as e:
            logger.error(f"Error getting source files: {e}")

        return list(sources)

    def get_sources_with_content(self, docs: List[Document]) -> List[dict]:
        """获取文档的来源和相关内容

        Args:
            docs: Document列表

        Returns:
            来源信息列表，包含文件路径、相关内容片段和分数
        """
        sources_map = {}

        for doc in docs:
            source = doc.metadata.get("source", "Unknown")
            if source not in sources_map:
                sources_map[source] = {
                    "file": source,
                    "filename": doc.metadata.get("filename", os.path.basename(source)),
                    "content": [],
                }
            # 累积所有chunk的内容
            sources_map[source]["content"].append(doc.page_content)

        # 将content列表合并为单个字符串
        for source_info in sources_map.values():
            source_info["content"] = "\n\n".join(source_info["content"])

        return list(sources_map.values())

    def list_managed_directories(self) -> List[str]:
        """列出已管理的目录"""
        metadata = self._load_metadata()
        return metadata.get("managed_directories", [])

    def remove_directory(self, directory: str) -> dict:
        """移除指定目录的所有文档

        Args:
            directory: 目录路径

        Returns:
            删除结果
        """
        directory = os.path.abspath(directory)

        # 获取该目录下的所有文档
        docs = self.vector_store.get()
        if not docs or not docs.get("ids"):
            return {"status": "success", "deleted_count": 0}

        ids_to_delete = []
        for i, metadata in enumerate(docs.get("metadatas", [])):
            source = metadata.get("source", "")
            if source.startswith(directory):
                ids_to_delete.append(docs["ids"][i])

        if ids_to_delete:
            self.vector_store.delete(ids=ids_to_delete)
            logger.info(f"Deleted {len(ids_to_delete)} documents from {directory}")

        # 从管理的目录列表中移除
        metadata = self._load_metadata()
        if directory in metadata["managed_directories"]:
            metadata["managed_directories"].remove(directory)
            self._save_metadata(metadata)

        return {"status": "success", "deleted_count": len(ids_to_delete)}

    def get_stats(self) -> dict:
        """获取知识库统计信息"""
        docs = self.vector_store.get()
        doc_count = len(docs.get("ids", [])) if docs else 0
        directories = self.list_managed_directories()

        return {
            "document_count": doc_count,
            "directory_count": len(directories),
            "directories": directories,
        }


if __name__ == "__main__":
    vector_store_service = VectorStoreService()

    # # 测试加载目录 - data/test 目录
    # result = vector_store_service.load_directory("data/test")
    # print(result)

    # # 测试获取统计
    # stats = vector_store_service.get_stats()
    # print(f"Stats: {stats}")

    print("=== 测试检索器 ===")
    retriever = vector_store_service.get_retriever()
    query = "扫地机器人产品特点"
    retrieved_docs = retriever.invoke(query)
    print(f"Retrieved {len(retrieved_docs)} documents for query: '{query}'")
    for doc in retrieved_docs:
        print(
            f"Source: {doc.metadata.get('source')}, Content: {doc.page_content[:100]}..."
        )
