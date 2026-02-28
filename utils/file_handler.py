import os
import hashlib
from utils.logger_handler import logger
from langchain_community.document_loaders import PyPDFLoader, TextLoader


def get_md5_hex(filepath: str):
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


def listdir_with_allowed_types(directory: str, allowed_types: tuple[str]):
    files = []

    if not os.path.isdir(directory):
        logger.error(f"Directory does not exist: {directory}")
        return []

    for f in os.listdir(directory):
        if f.endswith(allowed_types):
            files.append(os.path.join(directory, f))

    return tuple(files)


def pdf_loader(filepath: str, password: str = None):
    return PyPDFLoader(filepath, password=password).load()


def txt_loader(filepath: str):
    return TextLoader(filepath, encoding="utf-8").load()
