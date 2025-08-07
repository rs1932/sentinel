#!/bin/bash

# Database Recreation Script
# This script drops and recreates the database with the updated schema

echo "🔄 Sentinel Database Recreation"
echo "==============================="

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
DB_PASS="${DB_PASS:-svr967567}"  # Your password
SQL_FILE="../docs/Sentinel_Schema_All_Tables.sql"

echo ""
echo -e "${YELLOW}⚠️  WARNING: This will DROP and RECREATE the database!${NC}"
echo -e "${YELLOW}   All data will be lost!${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo

if [[ ! $REPLY == "yes" ]]; then
    echo "Aborted."
    exit 1
fi

echo "Database Configuration:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  User: $DB_USER"
echo "  Database: $DB_NAME"
echo ""

# Drop existing database
echo -n "Dropping existing database '$DB_NAME'... "
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}Database may not exist, continuing...${NC}"
fi

# Create new database
echo -n "Creating new database '$DB_NAME'... "
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME;" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Failed to create database"
    exit 1
fi

# Run the schema
echo -n "Running SQL schema from $SQL_FILE... "
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
            'Columns with metadata' as object_type,
            COUNT(*) as count
        FROM information_schema.columns
        WHERE table_schema = 'sentinel'
        AND column_name LIKE '%_metadata';
    " 2>/dev/null
    
    echo ""
    echo -e "${GREEN}✅ Database recreated successfully!${NC}"
    echo ""
    echo "Metadata columns have been renamed:"
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
        SELECT 
            table_name,
            column_name
        FROM information_schema.columns
        WHERE table_schema = 'sentinel'
        AND column_name LIKE '%_metadata'
        ORDER BY table_name;
    " 2>/dev/null
else
    echo -e "${RED}✗${NC}"
    echo "Failed to run schema. Check /tmp/schema_output.log for details"
    tail -20 /tmp/schema_output.log
    exit 1
fi

echo ""
echo "Next steps:"
echo "1. Update model classes to use {table}_metadata columns"
echo "2. Test the application with: uvicorn src.main:app --reload"
echo "3. Seed sample data: python scripts/seed_tenants.py"