-- Initialize pgvector extension for PostgreSQL
-- This script runs automatically when the database is first created

-- Create the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
