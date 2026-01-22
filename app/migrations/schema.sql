-- ============================================================================
-- Edify Admin AI Service Agent - Complete Database Schema
-- ============================================================================
-- 
-- This file contains ALL database schemas for the Chatbot Supabase project.
-- Execute this entire file in Supabase SQL Editor to set up the database.
--
-- NOTE: Edify Supabase tables (crm_leads, lms_batches, rms_candidates) 
--       are NOT included here as they exist in a separate database.
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- STEP 1: Cleanup Old/Unused Tables
-- ============================================================================

-- Old/Unused tables from previous versions
DROP TABLE IF EXISTS embeddings_history CASCADE;
DROP TABLE IF EXISTS vector_store CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS chat_state CASCADE;

-- Remove redundant tables (consolidated into chat_history and improved retrieved_context)
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS admin_query CASCADE;

-- Unwanted tables that may exist in Supabase
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS document_embeddings CASCADE;
DROP TABLE IF EXISTS knowledge_documents CASCADE;

-- ============================================================================
-- STEP 2: Create admin_sessions Table
-- ============================================================================

DROP TABLE IF EXISTS admin_sessions CASCADE;

CREATE TABLE admin_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'ended', 'expired')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_admin_sessions_admin_id ON admin_sessions(admin_id);
CREATE INDEX idx_admin_sessions_status ON admin_sessions(status);
CREATE INDEX idx_admin_sessions_created_at ON admin_sessions(created_at DESC);
CREATE INDEX idx_admin_sessions_last_activity ON admin_sessions(last_activity DESC);

-- ============================================================================
-- STEP 3: Create retrieved_context Table (Improved)
-- ============================================================================

DROP TABLE IF EXISTS retrieved_context CASCADE;

CREATE TABLE retrieved_context (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES admin_sessions(session_id) ON DELETE CASCADE,
    admin_id UUID NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('crm', 'lms', 'rms', 'rag', 'none')),
    query_text TEXT NOT NULL,
    record_count INTEGER DEFAULT 0,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    retrieval_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_retrieved_context_session_id ON retrieved_context(session_id);
CREATE INDEX idx_retrieved_context_admin_id ON retrieved_context(admin_id);
CREATE INDEX idx_retrieved_context_source_type ON retrieved_context(source_type);
CREATE INDEX idx_retrieved_context_created_at ON retrieved_context(created_at DESC);
CREATE INDEX idx_retrieved_context_payload ON retrieved_context USING GIN(payload);
CREATE INDEX idx_retrieved_context_session_created ON retrieved_context(session_id, created_at DESC);

-- ============================================================================
-- STEP 5: Create RAG Tables (rag_documents, rag_embeddings)
-- ============================================================================

DROP TABLE IF EXISTS rag_embeddings CASCADE;
DROP TABLE IF EXISTS rag_documents CASCADE;

CREATE TABLE rag_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_rag_documents_file_name ON rag_documents(file_name);
CREATE INDEX idx_rag_documents_created_at ON rag_documents(created_at DESC);

CREATE TABLE rag_embeddings (
    document_id UUID NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
    embedding vector(3072) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- NOTE: Vector indexes (IVFFlat/HNSW) are limited to 2000 dimensions in this pgvector version
-- Since we're using vector(3072), we cannot create an index
-- Queries will use sequential scan (slower but functional)
-- To use an index, reduce dimension to 2000 or less, or upgrade pgvector version

CREATE INDEX idx_rag_embeddings_created_at ON rag_embeddings(created_at DESC);

-- RPC Function: match_documents
-- Performs vector similarity search for RAG retrieval
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(3072),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    content text,
    similarity float,
    file_name text
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.content,
        1 - (e.embedding <=> query_embedding) as similarity,
        d.file_name
    FROM rag_embeddings e
    INNER JOIN rag_documents d ON e.document_id = d.id
    WHERE 1 - (e.embedding <=> query_embedding) > match_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- STEP 6: Create audit_logs Table
-- ============================================================================

DROP TABLE IF EXISTS audit_logs CASCADE;

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    admin_id UUID NOT NULL,
    session_id UUID REFERENCES admin_sessions(session_id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_admin_id ON audit_logs(admin_id);
CREATE INDEX idx_audit_logs_session_id ON audit_logs(session_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_metadata ON audit_logs USING GIN(metadata);

-- ============================================================================
-- STEP 7: Create chat_history Table
-- ============================================================================

DROP TABLE IF EXISTS chat_history CASCADE;

CREATE TABLE chat_history (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES admin_sessions(session_id) ON DELETE CASCADE,
    admin_id UUID NOT NULL,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    source_type TEXT CHECK (source_type IN ('crm', 'lms', 'rms', 'rag', 'none')),
    response_time_ms INTEGER,
    tokens_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chat_history_session_id ON chat_history(session_id);
CREATE INDEX idx_chat_history_admin_id ON chat_history(admin_id);
CREATE INDEX idx_chat_history_source_type ON chat_history(source_type);
CREATE INDEX idx_chat_history_created_at ON chat_history(created_at DESC);
CREATE INDEX idx_chat_history_session_created ON chat_history(session_id, created_at DESC);


-- ============================================================================
-- Schema Creation Complete
-- ============================================================================

