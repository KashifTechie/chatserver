from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import (
    UnstructuredWordDocumentLoader,
    CSVLoader,
    WebBaseLoader,
    TextLoader,
    YoutubeLoader,
    GitLoader,
    PyPDFLoader
)
from rag_system.models import RagStore, RagChuks
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
from typing import Type, Union
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


# LoaderType = Union[
#     Type[PyPDFLoader],
#     Type[UnstructuredWordDocumentLoader],
#     Type[TextLoader],
#     Type[CSVLoader],
#     Type[WebBaseLoader],
# ]

class StoreRAG:
    def __init__(self, rag_uuid):
        self.rag_uuid = rag_uuid

    def initiate_rag_storage(self):
        
        try:
            logger.info("vector storing initiated.")
            rag = RagStore.objects.get(uuid=self.rag_uuid)
            rag.status = RagStore.StatusChoices.PROCESSING
            rag.save(update_fields=["status"])
            loader = self.get_loader(rag)
            if not loader:
                logger.info("loader for the type:%s does not exist",rag.type)
                raise f"Loader does not exist for the type {rag.type}"
            documents = loader.load()

            splitter = self.get_splitter()

            chunks = splitter.split_documents(documents)

            embeddings = self.get_embeddings()

            vectors = embeddings.embed_documents([
                doc.page_content for doc in chunks
            ])

            num_chunks = self.store(rag, chunks, vectors)

            logger.info("%s chunks successfuly stored.",num_chunks)

        except Exception as e:
            logger.info("Error while storing vector: %s",str(e))


    def get_loader(self, rag:RagStore ):
        
        logger.info("getting the loader.")
        rag_type = rag.type

        if rag_type == RagStore.SourceType.PDF:
            return PyPDFLoader(rag.file_content.path)
        
        elif rag_type == RagStore.SourceType.DOCX:
            return UnstructuredWordDocumentLoader(rag.file_content.path)
        
        elif rag_type == RagStore.SourceType.TXT:
            return TextLoader(rag.text_content)
        
        elif rag_type == RagStore.SourceType.CSV:
            return CSVLoader(rag.file_content.path)
        
        elif rag_type == RagStore.SourceType.URL:
            return WebBaseLoader(rag.url_content)
        else:
            return None
        
    def get_splitter(self):
        return RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
        )
        
    def get_embeddings(self):
        return OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPEN_AI_KEY
            )   
    
    def store(self, rag_doc, chunks, vectors):

        records = []
        for i, (doc, vector) in enumerate(zip(chunks, vectors)):
            records.append(RagChuks(
                rag_store=rag_doc,
                chunk_index=i,
                content=doc.page_content,
                embedding=vector
            ))
        RagChuks.objects.bulk_create(records)   
        return len(records)