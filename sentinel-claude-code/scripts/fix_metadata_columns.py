#!/usr/bin/env python3
"""
Script to rename all metadata columns in the SQL schema to {table_name}_metadata
to avoid conflicts with SQLAlchemy and Pydantic
"""

import re
import sys

def fix_metadata_columns(sql_file_path):
    """Fix metadata column names in SQL file"""
    
    # Mapping of tables to their metadata column names
    table_mappings = {
        'sentinel.tenants': 'tenant_metadata',
        'sentinel.roles': 'role_metadata',
        'sentinel.groups': 'group_metadata',
        'sentinel.audit_logs': 'audit_metadata',
        'sentinel.menu_items': 'menu_metadata'
    }
    
    with open(sql_file_path, 'r') as f:
        content = f.read()
    
    # Track current table being processed
    current_table = None
    lines = content.split('\n')
    updated_lines = []
    
    for line in lines:
        # Check if we're starting a new table definition
        table_match = re.match(r'CREATE TABLE (sentinel\.[a-z_]+)', line)
        if table_match:
            current_table = table_match.group(1)
        
        # If we're in a table that needs metadata renamed
        if current_table in table_mappings and 'metadata JSONB' in line:
            # Replace metadata with the table-specific name
            line = line.replace('metadata JSONB', f'{table_mappings[current_table]} JSONB')
            print(f"✅ Fixed {current_table}: metadata → {table_mappings[current_table]}")
        
        # Reset current_table when we hit the end of table definition
        if line.strip().startswith(');'):
            current_table = None
        
        updated_lines.append(line)
    
    # Write the updated content
    with open(sql_file_path, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print("\n✅ SQL schema updated successfully!")
    print("\nTables with renamed metadata columns:")
    for table, new_name in table_mappings.items():
        print(f"  - {table}: metadata → {new_name}")

if __name__ == "__main__":
    sql_file = "/Users/rs/Documents/workspaces/Neuwerx Products/sentinel/sentinel-claude-code/docs/Sentinel_Schema_All_Tables.sql"
    fix_metadata_columns(sql_file)
    print("\nNext steps:")
    print("1. Drop the existing database: dropdb sentinel_db")
    print("2. Create new database: createdb sentinel_db")
    print("3. Run the updated schema: psql -U postgres -d sentinel_db -f docs/Sentinel_Schema_All_Tables.sql")
    print("4. Or use the setup script: ./scripts/setup_database.sh")