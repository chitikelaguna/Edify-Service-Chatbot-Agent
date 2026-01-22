from typing import List, Dict, Any, Optional
from app.db.supabase import get_chatbot_supabase_client
import logging
import uuid

logger = logging.getLogger(__name__)

class RAGRepo:
    """
    Repository for RAG data access.
    Manages rag_documents and rag_embeddings tables.
    Uses Chatbot Supabase client (read/write).
    """
    
    def __init__(self):
        self.supabase = get_chatbot_supabase_client()
        self.documents_table = "rag_documents"
        self.embeddings_table = "rag_embeddings"

    def document_exists(self, file_name: str) -> bool:
        """
        Check if a document with the given file_name already exists.
        Checks for any chunks from this file (file_name::chunk_*).
        
        Args:
            file_name: Name of the PDF file
            
        Returns:
            True if any chunks from this file exist, False otherwise
        """
        try:
            # Check if any chunks exist for this file
            # Chunks are stored as "filename.pdf::chunk_1", "filename.pdf::chunk_2", etc.
            response = (
                self.supabase.table(self.documents_table)
                .select("id")
                .like("file_name", f"{file_name}::chunk_%")
                .limit(1)
                .execute()
            )
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking document existence: {e}", exc_info=True)
            return False

    def create_document(self, file_name: str, content: str) -> Optional[str]:
        """
        Create a new document record.
        
        Args:
            file_name: Name of the PDF file
            content: Extracted text content
            
        Returns:
            Document ID (UUID) if successful, None otherwise
        """
        try:
            response = (
                self.supabase.table(self.documents_table)
                .insert({
                    "file_name": file_name,
                    "content": content
                })
                .execute()
            )
            
            if response.data:
                doc_id = response.data[0]["id"]
                logger.info(f"Created document record: {file_name} (ID: {doc_id})")
                return doc_id
            else:
                logger.error(f"Failed to create document record: {file_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating document: {e}", exc_info=True)
            return None

    def create_embedding(self, document_id: str, embedding: List[float]) -> bool:
        """
        Create an embedding record linked to a document.
        
        Args:
            document_id: UUID of the document
            embedding: Embedding vector (list of floats)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = (
                self.supabase.table(self.embeddings_table)
                .insert({
                    "document_id": document_id,
                    "embedding": embedding
                })
                .execute()
            )
            
            if response.data:
                logger.debug(f"Created embedding for document {document_id}")
                return True
            else:
                logger.error(f"Failed to create embedding for document {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating embedding: {e}", exc_info=True)
            return False

    def create_document_with_embeddings(
        self, 
        file_name: str, 
        content_chunks: List[str], 
        embeddings: List[List[float]],
        token_counts: List[int] = None
    ) -> bool:
        """
        Create a document and its associated embeddings.
        Each chunk is stored as a separate document entry with its embedding.
        This allows proper chunk-level retrieval.
        
        Args:
            file_name: Name of the PDF file
            content_chunks: List of text chunks
            embeddings: List of embedding vectors (one per chunk)
            token_counts: Optional list of token counts (one per chunk)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if len(content_chunks) != len(embeddings):
                logger.error(f"Mismatch: {len(content_chunks)} chunks but {len(embeddings)} embeddings")
                return False
            
            # Validate token_counts if provided
            if token_counts is not None and len(token_counts) != len(content_chunks):
                logger.warning(f"Token counts length mismatch, ignoring token counts")
                token_counts = None
            
            # Create document records and embeddings in batch
            # Each chunk becomes a document entry with its embedding
            records = []
            for chunk_idx, (chunk, embedding) in enumerate(zip(content_chunks, embeddings)):
                # Create document record for this chunk
                # Use file_name with chunk index to make it unique
                chunk_file_name = f"{file_name}::chunk_{chunk_idx + 1}"
                
                # Prepare document data
                doc_data = {
                    "file_name": chunk_file_name,
                    "content": chunk
                }
                
                # Add token count if provided
                if token_counts is not None:
                    doc_data["token_count"] = token_counts[chunk_idx]
                
                # Insert document
                doc_response = (
                    self.supabase.table(self.documents_table)
                    .insert(doc_data)
                    .execute()
                )
                
                if not doc_response.data:
                    logger.error(f"Failed to create document record for chunk {chunk_idx + 1}")
                    continue
                
                doc_id = doc_response.data[0]["id"]
                
                # Insert embedding
                emb_response = (
                    self.supabase.table(self.embeddings_table)
                    .insert({
                        "document_id": doc_id,
                        "embedding": embedding
                    })
                    .execute()
                )
                
                if emb_response.data:
                    records.append((chunk_idx + 1, doc_id))
            
            if len(records) == len(content_chunks):
                total_tokens = sum(token_counts) if token_counts else 0
                logger.info(f"Created {len(records)} document-embedding pairs for {file_name}" + 
                          (f" (total tokens: {total_tokens})" if total_tokens > 0 else ""))
                return True
            else:
                logger.warning(f"Created {len(records)}/{len(content_chunks)} document-embedding pairs for {file_name}")
                return len(records) > 0  # Partial success
                
        except Exception as e:
            logger.error(f"Error creating document with embeddings: {e}", exc_info=True)
            return False

    def get_document_by_name(self, file_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by file name.
        
        Args:
            file_name: Name of the PDF file
            
        Returns:
            Document record if found, None otherwise
        """
        try:
            response = (
                self.supabase.table(self.documents_table)
                .select("*")
                .eq("file_name", file_name)
                .single()
                .execute()
            )
            
            return response.data if response.data else None
            
        except Exception as e:
            logger.error(f"Error retrieving document: {e}", exc_info=True)
            return None

