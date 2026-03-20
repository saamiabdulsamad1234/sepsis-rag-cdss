import os
from typing import List, Dict
from pathlib import Path
import markdown
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class DocumentLoader:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def load_pdf(self, file_path: str) -> List[Document]:
        documents = []
        try:
            reader = PdfReader(file_path)
            text = ""
            for page_num, page in enumerate(reader.pages):
                text += page.extract_text()
            
            chunks = self.text_splitter.split_text(text)
            for i, chunk in enumerate(chunks):
                documents.append(Document(
                    page_content=chunk,
                    metadata={
                        "source": os.path.basename(file_path),
                        "chunk_id": i,
                        "type": "pdf"
                    }
                ))
        except Exception as e:
            print(f"Error loading PDF {file_path}: {e}")
        
        return documents
    
    def load_markdown(self, file_path: str) -> List[Document]:
        documents = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            html = markdown.markdown(content)
            chunks = self.text_splitter.split_text(content)
            
            for i, chunk in enumerate(chunks):
                documents.append(Document(
                    page_content=chunk,
                    metadata={
                        "source": os.path.basename(file_path),
                        "chunk_id": i,
                        "type": "markdown"
                    }
                ))
        except Exception as e:
            print(f"Error loading Markdown {file_path}: {e}")
        
        return documents
    
    def load_text(self, file_path: str) -> List[Document]:
        documents = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            chunks = self.text_splitter.split_text(content)
            
            for i, chunk in enumerate(chunks):
                documents.append(Document(
                    page_content=chunk,
                    metadata={
                        "source": os.path.basename(file_path),
                        "chunk_id": i,
                        "type": "text"
                    }
                ))
        except Exception as e:
            print(f"Error loading text file {file_path}: {e}")
        
        return documents
    
    def load_directory(self, directory_path: str) -> List[Document]:
        all_documents = []
        path = Path(directory_path)
        
        for file_path in path.rglob("*"):
            if file_path.is_file():
                if file_path.suffix.lower() == '.pdf':
                    all_documents.extend(self.load_pdf(str(file_path)))
                elif file_path.suffix.lower() in ['.md', '.markdown']:
                    all_documents.extend(self.load_markdown(str(file_path)))
                elif file_path.suffix.lower() in ['.txt']:
                    all_documents.extend(self.load_text(str(file_path)))
        
        return all_documents
