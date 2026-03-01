import os
import hashlib
from typing import List
from utils.logger_handler import logger
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    JSONLoader,
    PythonLoader,
    UnstructuredMarkdownLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
    UnstructuredHTMLLoader,
)
from langchain_core.documents import Document


def get_md5_hex(filepath: str):
    """计算文件的MD5哈希值"""
    if not os.path.exists(filepath):
        logger.error(f"File does not exist: {filepath}")
        return None

    if not os.path.isfile(filepath):
        logger.error(f"Path is not a file: {filepath}")
        return None

    md5_obj = hashlib.md5()

    chunk_size = 4096
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)

        return md5_obj.hexdigest()
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return None


def scan_directory(
    directory: str, allowed_types: tuple[str], recursive: bool = True
) -> List[str]:
    """
    扫描目录获取所有支持的文件

    Args:
        directory: 目录路径
        allowed_types: 支持的文件扩展名元组
        recursive: 是否递归扫描子目录

    Returns:
        文件路径列表
    """
    files = []

    if not os.path.isdir(directory):
        logger.error(f"Directory does not exist: {directory}")
        return []

    if recursive:
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith(allowed_types):
                    files.append(os.path.join(root, filename))
    else:
        for f in os.listdir(directory):
            filepath = os.path.join(directory, f)
            if os.path.isfile(filepath) and f.endswith(allowed_types):
                files.append(filepath)

    return files


def get_file_loader(filepath: str) -> List[Document]:
    """
    根据文件扩展名获取对应的加载器

    Args:
        filepath: 文件路径

    Returns:
        Document列表
    """
    ext = os.path.splitext(filepath)[1].lower()

    try:
        if ext == ".pdf":
            return pdf_loader(filepath)
        elif ext == ".txt":
            return txt_loader(filepath)
        elif ext == ".md":
            return markdown_loader(filepath)
        elif ext == ".docx":
            return docx_loader(filepath)
        elif ext == ".csv":
            return csv_loader(filepath)
        elif ext == ".pptx":
            return pptx_loader(filepath)
        elif ext == ".html" or ext == ".htm":
            return html_loader(filepath)
        elif ext == ".json":
            return json_loader(filepath)
        elif ext in [".yaml", ".yml"]:
            return yaml_loader(filepath)
        elif ext == ".py":
            return python_loader(filepath)
        elif ext in [".js", ".java", ".cpp", ".go", ".rs"]:
            return code_loader(filepath)
        else:
            logger.warning(f"Unsupported file type: {ext}")
            return []
    except Exception as e:
        logger.error(f"Error loading file {filepath}: {str(e)}", exc_info=True)
        return []


# ============ 现有的加载器 ============


def pdf_loader(filepath: str, password: str = None) -> List[Document]:
    """加载PDF文件"""
    return PyPDFLoader(filepath, password=password).load()


def txt_loader(filepath: str) -> List[Document]:
    """加载文本文件"""
    return TextLoader(filepath, encoding="utf-8").load()


# ============ 新增的加载器 ============


def markdown_loader(filepath: str) -> List[Document]:
    """加载Markdown文件"""
    return UnstructuredMarkdownLoader(filepath).load()


def docx_loader(filepath: str) -> List[Document]:
    """加载Word文档"""
    return UnstructuredWordDocumentLoader(filepath).load()


def csv_loader(filepath: str) -> List[Document]:
    """加载CSV文件"""
    return CSVLoader(filepath, encoding="utf-8").load()


def pptx_loader(filepath: str) -> List[Document]:
    """加载PowerPoint文件"""
    return UnstructuredPowerPointLoader(filepath).load()


def html_loader(filepath: str) -> List[Document]:
    """加载HTML文件"""
    return UnstructuredHTMLLoader(filepath).load()


def json_loader(filepath: str) -> List[Document]:
    """加载JSON文件"""
    # 使用 "." 提取整个JSON内容，设置text_content=False处理dict类型
    return JSONLoader(filepath, jq_schema=".", text_content=False).load()


def yaml_loader(filepath: str) -> List[Document]:
    """加载YAML文件"""
    return TextLoader(filepath, encoding="utf-8").load()


def python_loader(filepath: str) -> List[Document]:
    """加载Python文件"""
    return PythonLoader(filepath).load()


def code_loader(filepath: str) -> List[Document]:
    """加载代码文件 (js, java, cpp, go, rs等)"""
    return TextLoader(filepath, encoding="utf-8").load()
