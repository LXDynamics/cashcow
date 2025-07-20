-- Initialize CashCow PostgreSQL database
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create database if it doesn't exist (handled by POSTGRES_DB env var)
-- CREATE DATABASE cashcow;

-- Create schema for application tables
CREATE SCHEMA IF NOT EXISTS cashcow;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA cashcow TO cashcow;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cashcow TO cashcow;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA cashcow TO cashcow;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA cashcow GRANT ALL ON TABLES TO cashcow;
ALTER DEFAULT PRIVILEGES IN SCHEMA cashcow GRANT ALL ON SEQUENCES TO cashcow;

-- Create indexes for common queries (these will be created by the application)
-- This is just a placeholder for any initial DB setup