-- Enable pgvector extension for similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create index for vector similarity search (will be used after tables are created)
-- Note: The actual index creation happens after SQLAlchemy creates the tables
