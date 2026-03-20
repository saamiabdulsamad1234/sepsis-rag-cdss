import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from config.settings import settings

class VectorStoreManager:
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or settings.chroma_persist_dir
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key
        )
        self.collection_name = "sepsis_guidelines"
        self.vectorstore = None
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        try:
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
        except Exception as e:
            print(f"Error initializing vector store: {e}")
            self.vectorstore = None
    
    def add_documents(self, documents: List[Document]) -> bool:
        try:
            if not self.vectorstore:
                self._initialize_vectorstore()
            
            self.vectorstore.add_documents(documents)
            return True
        except Exception as e:
            print(f"Error adding documents: {e}")
            return False
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Document]:
        try:
            if not self.vectorstore:
                return []
            
            if filter_dict:
                results = self.vectorstore.similarity_search(
                    query, 
                    k=k,
                    filter=filter_dict
                )
            else:
                results = self.vectorstore.similarity_search(query, k=k)
            
            return results
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []
    
    def similarity_search_with_score(
        self, 
        query: str, 
        k: int = 5
    ) -> List[tuple[Document, float]]:
        try:
            if not self.vectorstore:
                return []
            
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            print(f"Error in similarity search with score: {e}")
            return []
    
    def delete_collection(self) -> bool:
        try:
            if self.vectorstore:
                self.vectorstore.delete_collection()
                self.vectorstore = None
            return True
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False
    
    def get_collection_count(self) -> int:
        try:
            if self.vectorstore:
                return self.vectorstore._collection.count()
            return 0
        except Exception as e:
            print(f"Error getting collection count: {e}")
            return 0
