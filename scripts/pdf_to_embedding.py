#!/usr/bin/env python3
"""
PDF to Embedding Ingestion Script

Scans the scripts/ folder for PDF files, extracts text, chunks it,
generates embeddings, and stores them in Supabase.

Usage:
    python scripts/pdf_to_embedding.py

Requirements:
    - PDF files must be placed in the scripts/ folder
    - Supabase credentials must be configured in .env
    - OpenAI API key must be configured in .env
"""

import os
import sys
import logging
from pathlib import Path
from typing import List

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.rag_repo import RAGRepo
from app.rag.embedder import Embedder
from app.core.config import settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# PDF parsing library
try:
    import pypdf
except ImportError:
    logger.error("pypdf library not found. Install it with: pip install pypdf")
    sys.exit(1)


class PDFProcessor:
    """Handles PDF text extraction and chunking."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize PDF processor.
        
        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                text_parts = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        if text.strip():
                            text_parts.append(text)
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1} of {pdf_path.name}: {e}")
                        continue
                
                full_text = "\n\n".join(text_parts)
                
                if not full_text.strip():
                    logger.warning(f"No text extracted from {pdf_path.name}")
                    return ""
                
                logger.info(f"Extracted {len(full_text)} characters from {pdf_path.name}")
                return full_text
                
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path.name}: {e}", exc_info=True)
            raise
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: Full text content
            
        Returns:
            List of text chunks
        """
        if not text.strip():
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Calculate end position
            end = start + self.chunk_size
            
            # Extract chunk
            chunk = text[start:end]
            
            # Try to break at sentence boundary if not at end
            if end < text_length:
                # Look for sentence endings
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                last_break = max(last_period, last_newline)
                
                if last_break > self.chunk_size * 0.5:  # Only break if reasonable
                    chunk = chunk[:last_break + 1]
                    end = start + last_break + 1
            
            chunks.append(chunk.strip())
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            # Prevent infinite loop
            if start >= text_length:
                break
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks


class PDFIngestionService:
    """Main service for ingesting PDFs into RAG system."""
    
    def __init__(self):
        self.rag_repo = RAGRepo()
        self.embedder = Embedder()
        self.processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
        self.scripts_dir = Path(__file__).parent
    
    def find_pdf_files(self) -> List[Path]:
        """
        Find all PDF files in the scripts directory.
        
        Returns:
            List of PDF file paths
        """
        pdf_files = list(self.scripts_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF file(s) in scripts/ directory")
        return pdf_files
    
    def process_pdf(self, pdf_path: Path) -> bool:
        """
        Process a single PDF file: extract, chunk, embed, and store.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if successful, False otherwise
        """
        file_name = pdf_path.name
        
        try:
            # Check if already processed (idempotent)
            if self.rag_repo.document_exists(file_name):
                logger.info(f"⏭️  Skipping {file_name} - already processed")
                return True
            
            logger.info(f"📄 Processing {file_name}...")
            
            # Extract text
            text = self.processor.extract_text(pdf_path)
            if not text.strip():
                logger.warning(f"⚠️  No text extracted from {file_name}, skipping")
                return False
            
            # Chunk text
            chunks = self.processor.chunk_text(text)
            if not chunks:
                logger.warning(f"⚠️  No chunks created from {file_name}, skipping")
                return False
            
            logger.info(f"📦 Created {len(chunks)} chunks from {file_name}")
            
            # Generate embeddings
            logger.info(f"🔮 Generating embeddings for {len(chunks)} chunks...")
            embeddings = self.embedder.embed_documents(chunks)
            
            if len(embeddings) != len(chunks):
                logger.error(f"❌ Embedding count mismatch: {len(embeddings)} vs {len(chunks)}")
                return False
            
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            
            # Store in database
            logger.info(f"💾 Storing document and embeddings in Supabase...")
            success = self.rag_repo.create_document_with_embeddings(
                file_name=file_name,
                content_chunks=chunks,
                embeddings=embeddings
            )
            
            if success:
                logger.info(f"✅ Successfully processed {file_name}")
                return True
            else:
                logger.error(f"❌ Failed to store {file_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error processing {file_name}: {e}", exc_info=True)
            return False
    
    def run(self) -> None:
        """Main execution method."""
        logger.info("🚀 Starting PDF ingestion process...")
        logger.info(f"📁 Scanning directory: {self.scripts_dir.absolute()}")
        
        # Validate configuration
        if not settings.CHATBOT_SUPABASE_URL or not settings.CHATBOT_SUPABASE_SERVICE_ROLE_KEY:
            logger.error("❌ CHATBOT_SUPABASE_URL or CHATBOT_SUPABASE_SERVICE_ROLE_KEY not configured")
            sys.exit(1)
        
        if not settings.OPENAI_API_KEY:
            logger.error("❌ OPENAI_API_KEY not configured")
            sys.exit(1)
        
        # Find PDF files
        pdf_files = self.find_pdf_files()
        
        if not pdf_files:
            logger.info("ℹ️  No PDF files found in scripts/ directory")
            logger.info("💡 Place PDF files in the scripts/ folder and run again")
            return
        
        # Process each PDF
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for pdf_path in pdf_files:
            try:
                if self.process_pdf(pdf_path):
                    success_count += 1
                else:
                    # Check if it was skipped (already exists)
                    if self.rag_repo.document_exists(pdf_path.name):
                        skip_count += 1
                    else:
                        error_count += 1
            except Exception as e:
                logger.error(f"❌ Unexpected error processing {pdf_path.name}: {e}", exc_info=True)
                error_count += 1
        
        # Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 Ingestion Summary:")
        logger.info(f"   ✅ Successfully processed: {success_count}")
        logger.info(f"   ⏭️  Skipped (already exists): {skip_count}")
        logger.info(f"   ❌ Errors: {error_count}")
        logger.info(f"   📄 Total files: {len(pdf_files)}")
        logger.info("=" * 60)


if __name__ == "__main__":
    try:
        service = PDFIngestionService()
        service.run()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)

