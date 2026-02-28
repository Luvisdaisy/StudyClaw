import os
from langchain_chroma import Chroma
from utils.config_handler import chroma_cfg
from model.factory import embedding_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.path_tool import get_abs_path
from utils.file_handler import (
    pdf_loader,
    txt_loader,
    listdir_with_allowed_types,
    get_md5_hex,
)
from utils.logger_handler import logger


class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name=chroma_cfg["collection_name"],
            embedding_function=embedding_model,
            persist_directory=chroma_cfg["persist_directory"],
        )
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_cfg["chunk_size"],
            chunk_overlap=chroma_cfg["chunk_overlap"],
            separators=chroma_cfg["separators"],
        )

    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": chroma_cfg["k"]})

    def load_documents(self):

        def check_md5_hex(md5_to_check: str):
            if not os.path.exists(get_abs_path(chroma_cfg["md5_hex_store"])):
                open(
                    get_abs_path(chroma_cfg["md5_hex_store"]), "w", encoding="utf-8"
                ).close()
                return False
            with open(
                get_abs_path(chroma_cfg["md5_hex_store"]), "r", encoding="utf-8"
            ) as f:
                for line in f.readlines():
                    if line.strip() == md5_to_check:
                        return True

        def save_md5_hex(md5_to_save: str):
            with open(
                get_abs_path(chroma_cfg["md5_hex_store"]), "a", encoding="utf-8"
            ) as f:
                f.write(md5_to_save + "\n")

        def get_all_documents(filepath: str):
            if filepath.endswith("txt"):
                return txt_loader(filepath)
            if filepath.endswith("pdf"):
                return pdf_loader(filepath)
            return []

        allowed_files = listdir_with_allowed_types(
            get_abs_path(chroma_cfg["data_path"]),
            tuple(chroma_cfg["allow_knowledge_file_type"]),
        )

        for path in allowed_files:
            md5_hex = get_md5_hex(path)
            if check_md5_hex(md5_hex):
                logger.info(f"File {path} has already been processed. Skipping.")
                continue
            try:
                documents = get_all_documents(path)

                if not documents:
                    logger.warning(f"No documents found in file {path}. Skipping.")
                    continue
                split_docs = self.spliter.split_documents(documents)
                if not split_docs:
                    logger.warning(
                        f"Document splitting resulted in no chunks for file {path}. Skipping."
                    )
                    continue
                self.vector_store.add_documents(split_docs)
                save_md5_hex(md5_hex)
                logger.info(f"File {path} processed and added to vector store.")
            except Exception as e:
                logger.error(f"Error processing file {path}: {str(e)}", exc_info=True)
                continue


if __name__ == "__main__":
    vector_store_service = VectorStoreService()
    vector_store_service.load_documents()

    retriever = vector_store_service.get_retriever()
    result = retriever.invoke("What is the capital of France?")
    for r in result:
        print(r.page_content)
        print("-" * 20)
