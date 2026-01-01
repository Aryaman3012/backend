"""
Document processing service for extracting text from various file formats
"""
import io
from pathlib import Path
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import get_settings


class DocumentProcessor:
    """Handles document parsing and text extraction"""
    
    def __init__(self):
        self.settings = get_settings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    async def extract_text(self, file_content: bytes, filename: str) -> str:
        """
        Extract text from file content based on file type
        """
        suffix = Path(filename).suffix.lower()
        
        if suffix == ".pdf":
            return await self._extract_from_pdf(file_content)
        elif suffix == ".docx":
            return await self._extract_from_docx(file_content)
        elif suffix in [".txt", ".md"]:
            return file_content.decode("utf-8")
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    
    async def _extract_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF"""
        from pypdf import PdfReader
        
        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)
        
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    async def _extract_from_docx(self, content: bytes) -> str:
        """Extract text from DOCX"""
        from docx import Document
        
        docx_file = io.BytesIO(content)
        doc = Document(docx_file)
        
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        
        return "\n\n".join(text_parts)
    


