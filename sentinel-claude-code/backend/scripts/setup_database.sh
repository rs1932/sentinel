#!/bin/bash

# Sentinel Database Setup Script
# This script sets up the database using the provided SQL schema

echo "🚀 Sentinel Database Setup"
echo "========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-sentinel_db}"
SQL_FILE="../docs/Sentinel_Schema_All_Tables.sql"

echo "Database Configuration:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  User: $DB_USER"
echo "  Database: $DB_NAME"
echo ""

# Function to check if PostgreSQL is running
check_postgres() {
    echo -n "Checking PostgreSQL connection... "
    if PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        echo -e "${YELLOW}PostgreSQL is not running or credentials are incorrect${NC}"
        echo ""
        echo "Please ensure PostgreSQL is running:"
        echo "  - On macOS with Homebrew: brew services start postgresql@14"
        echo "  - On Linux: sudo systemctl start postgresql"
        echo "  - Using Docker: docker-compose up -d postgres"
        return 1
    fi
}

# Function to create database
create_database() {
    echo -n "Creating database '$DB_NAME'... "
    
    # Check if database exists
    if PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
        echo -e "${YELLOW}already exists${NC}"
        
        read -p "Do you want to drop and recreate the database? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -n "Dropping existing database... "
            PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;" > /dev/null 2>&1
            echo -e "${GREEN}✓${NC}"
            
            echo -n "Creating new database... "
            PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME;" > /dev/null 2>&1
            echo -e "${GREEN}✓${NC}"
        fi
    else
        PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME;" > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
            echo "Failed to create database"
            return 1
        fi
    fi
    return 0
}

# Function to run SQL schema
run_schema() {
    echo -n "Running SQL schema from $SQL_FILE... "
    
    if [ ! -f "$SQL_FILE" ]; then
        echo -e "${RED}✗${NC}"
        echo "SQL file not found: $SQL_FILE"
        return 1
    fi
    
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$SQL_FILE" > /tmp/schema_output.log 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC}"
        
        # Count created objects
        echo ""
        echo "Schema creation summary:"
        PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
            SELECT 
                'Tables' as object_type, 
                COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = 'sentinel'
            UNION ALL
            SELECT 
                'Enums' as object_type, 
                COUNT(*) as count 
            FROM pg_type t 
            JOIN pg_namespace n ON t.typnamespace = n.oid 
            WHERE n.nspname = 'sentinel' AND t.typtype = 'e';
        " 2>/dev/null
        
        return 0
    else
        echo -e "${RED}✗${NC}"
        echo "Failed to run schema. Check /tmp/schema_output.log for details"
        tail -20 /tmp/schema_output.log
        return 1
    fi
}

# Main execution
main() {
    echo ""
    
    # Get database password if not set
    if [ -z "$DB_PASS" ]; then
        read -sp "Enter PostgreSQL password for user '$DB_USER': " DB_PASS
        echo ""
        export DB_PASS
    fi
    
    # Check PostgreSQL connection
    if ! check_postgres; then
        exit 1
    fi
    
    # Create database
    if ! create_database; then
        exit 1
    fi
    
    # Run schema
    if ! run_schema; then
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}✅ Database setup complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Copy .env.example to .env and update DATABASE_URL if needed"
    echo "2. Start the FastAPI server: uvicorn src.main:app --reload"
    echo "3. Seed sample data: python scripts/seed_tenants.py"
    echo "4. Access API docs at: http://localhost:8000/api/docs"
}

# Run main function
main