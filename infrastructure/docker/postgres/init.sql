-- PostgreSQL initialization script
-- This runs when the database is first created

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE evo_ai TO evo_user;

-- Set timezone
ALTER DATABASE evo_ai SET timezone TO 'UTC';
