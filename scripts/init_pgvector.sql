-- Initialize pgvector extension for PostgreSQL
-- This script is run when the PostgreSQL container starts

-- Create the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a function to calculate cosine similarity
CREATE OR REPLACE FUNCTION cosine_similarity(a vector, b vector)
RETURNS float
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN 1 - (a <=> b);
END;
$$;

-- Create indexes for better performance
-- Note: These will be created after the tables are created by the application

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension initialized successfully';
END $$;
