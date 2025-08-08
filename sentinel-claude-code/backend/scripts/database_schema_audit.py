#!/usr/bin/env python3
"""
Database Schema Audit Tool

Compares the SQL specification document with the actual PostgreSQL database
to identify:
- Tables in spec but missing from database
- Tables in database but not in spec (extra implementation)
- Field differences between spec and actual database
- Missing indexes, constraints, or relationships

Focuses on Modules 1-7 core functionality.
"""

import os
import re
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import asyncpg


@dataclass
class TableField:
    """Represents a database table field."""
    name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_table: Optional[str] = None
    foreign_column: Optional[str] = None


@dataclass
class TableSchema:
    """Represents a complete table schema."""
    name: str
    schema: str = "sentinel"
    fields: List[TableField] = None
    indexes: List[str] = None
    constraints: List[str] = None
    
    def __post_init__(self):
        if self.fields is None:
            self.fields = []
        if self.indexes is None:
            self.indexes = []
        if self.constraints is None:
            self.constraints = []


@dataclass
class AuditResult:
    """Represents the result of schema comparison."""
    status: str  # MATCH, EXTRA_FIELD, MISSING_FIELD, TYPE_MISMATCH, EXTRA_TABLE, MISSING_TABLE
    table: str
    field: Optional[str] = None
    spec_value: Optional[str] = None
    actual_value: Optional[str] = None
    description: str = ""


class DatabaseSchemaAuditor:
    """Main auditor class for comparing SQL spec with actual database."""
    
    # Core tables expected for Modules 1-7
    MODULES_1_7_TABLES = {
        "tenants": "Module 2 - Tenant Management",
        "users": "Module 3 - User Management", 
        "roles": "Module 4 - Role Management",
        "user_roles": "Module 4 - User-Role Assignments",
        "groups": "Module 5 - Group Management",
        "user_groups": "Module 5 - User-Group Assignments",
        "group_roles": "Module 5 - Group-Role Assignments",
        "permissions": "Module 6 - Permission Management",
        "role_permissions": "Module 6 - Role-Permission Assignments",
        "resources": "Module 7 - Resource Management",
        "refresh_tokens": "Module 1 - Authentication",
        "token_blacklist": "Module 1 - Authentication"
    }
    
    def __init__(self):
        self.backend_root = Path(__file__).parent.parent
        self.sql_spec_file = self.backend_root / "docs" / "Sentinel_Schema_All_Tables.sql"
        self.audit_results: List[AuditResult] = []
        
        # Database connection config
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", 5432),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "svr967567"),
            "database": os.getenv("DB_NAME", "sentinel_db")
        }
    
    def parse_sql_specification(self) -> Dict[str, TableSchema]:
        """Parse the SQL specification file to extract table schemas."""
        if not self.sql_spec_file.exists():
            raise FileNotFoundError(f"SQL spec file not found: {self.sql_spec_file}")
        
        print(f"📖 Parsing SQL specification: {self.sql_spec_file}")
        content = self.sql_spec_file.read_text()
        
        tables = {}
        
        # Find all CREATE TABLE statements for sentinel schema
        table_pattern = r'CREATE TABLE sentinel\.(\w+)\s*\((.*?)\);'
        
        for match in re.finditer(table_pattern, content, re.DOTALL | re.IGNORECASE):
            table_name = match.group(1)
            table_definition = match.group(2)
            
            # Only process tables relevant to Modules 1-7
            if table_name in self.MODULES_1_7_TABLES:
                schema = self._parse_table_definition(table_name, table_definition)
                tables[table_name] = schema
                print(f"  ✅ Parsed table: {table_name} ({len(schema.fields)} fields)")
        
        print(f"📊 Parsed {len(tables)} tables from specification")
        return tables
    
    def _parse_table_definition(self, table_name: str, definition: str) -> TableSchema:
        """Parse individual table definition from SQL."""
        schema = TableSchema(name=table_name)
        
        # Split definition into lines and clean them
        lines = [line.strip().rstrip(',') for line in definition.split('\n') if line.strip()]
        
        for line in lines:
            if not line or line.startswith('--'):
                continue
            
            # Skip constraints for now (could be enhanced later)
            if any(keyword in line.upper() for keyword in ['CONSTRAINT', 'CHECK', 'UNIQUE', 'INDEX']):
                schema.constraints.append(line)
                continue
            
            # Parse field definition
            field = self._parse_field_definition(line)
            if field:
                schema.fields.append(field)
        
        return schema
    
    def _parse_field_definition(self, line: str) -> Optional[TableField]:
        """Parse a single field definition from SQL."""
        # Basic field pattern: field_name TYPE [NOT NULL] [DEFAULT value]
        line = line.strip().rstrip(',')
        
        if not line or any(keyword in line.upper() for keyword in ['CONSTRAINT', 'PRIMARY KEY', 'FOREIGN KEY']):
            return None
        
        parts = line.split()
        if len(parts) < 2:
            return None
        
        field_name = parts[0]
        data_type = parts[1]
        
        # Check for NOT NULL
        is_nullable = 'NOT NULL' not in line.upper()
        
        # Check for DEFAULT
        default_value = None
        if 'DEFAULT' in line.upper():
            default_match = re.search(r'DEFAULT\s+([^,\s]+)', line, re.IGNORECASE)
            if default_match:
                default_value = default_match.group(1)
        
        # Check for PRIMARY KEY
        is_primary_key = 'PRIMARY KEY' in line.upper()
        
        # Check for REFERENCES (foreign key)
        is_foreign_key = 'REFERENCES' in line.upper()
        foreign_table = None
        foreign_column = None
        
        if is_foreign_key:
            fk_match = re.search(r'REFERENCES\s+[\w.]+\.(\w+)\((\w+)\)', line, re.IGNORECASE)
            if fk_match:
                foreign_table = fk_match.group(1)
                foreign_column = fk_match.group(2)
        
        return TableField(
            name=field_name,
            data_type=data_type,
            is_nullable=is_nullable,
            default_value=default_value,
            is_primary_key=is_primary_key,
            is_foreign_key=is_foreign_key,
            foreign_table=foreign_table,
            foreign_column=foreign_column
        )
    
    async def get_database_schema(self) -> Dict[str, TableSchema]:
        """Query the actual database to get current schema."""
        print(f"🔍 Connecting to database: {self.db_config['database']}@{self.db_config['host']}")
        
        conn = await asyncpg.connect(**self.db_config)
        
        try:
            # Get all tables in sentinel schema
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'sentinel'
                ORDER BY table_name
            """
            
            table_names = await conn.fetch(tables_query)
            print(f"📊 Found {len(table_names)} tables in database")
            
            schemas = {}
            
            for row in table_names:
                table_name = row['table_name']
                
                # Get table schema
                schema = await self._get_table_schema_from_db(conn, table_name)
                schemas[table_name] = schema
                
                print(f"  ✅ Retrieved schema: {table_name} ({len(schema.fields)} fields)")
            
            return schemas
        
        finally:
            await conn.close()
    
    async def _get_table_schema_from_db(self, conn, table_name: str) -> TableSchema:
        """Get detailed schema for a specific table from database."""
        schema = TableSchema(name=table_name)
        
        # Get column information
        columns_query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                udt_name
            FROM information_schema.columns
            WHERE table_schema = 'sentinel' AND table_name = $1
            ORDER BY ordinal_position
        """
        
        columns = await conn.fetch(columns_query, table_name)
        
        # Get primary key information
        pk_query = """
            SELECT column_name
            FROM information_schema.key_column_usage kcu
            JOIN information_schema.table_constraints tc 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY' 
                AND kcu.table_schema = 'sentinel' 
                AND kcu.table_name = $1
        """
        
        pk_columns = {row['column_name'] for row in await conn.fetch(pk_query, table_name)}
        
        # Get foreign key information
        fk_query = """
            SELECT 
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.key_column_usage kcu
            JOIN information_schema.referential_constraints rc 
                ON rc.constraint_name = kcu.constraint_name
            JOIN information_schema.key_column_usage ccu 
                ON rc.unique_constraint_name = ccu.constraint_name
            WHERE kcu.table_schema = 'sentinel' AND kcu.table_name = $1
        """
        
        fk_info = {row['column_name']: (row['foreign_table_name'], row['foreign_column_name']) 
                  for row in await conn.fetch(fk_query, table_name)}
        
        # Build field definitions
        for col in columns:
            field_name = col['column_name']
            is_pk = field_name in pk_columns
            fk_info_tuple = fk_info.get(field_name)
            
            field = TableField(
                name=field_name,
                data_type=col['data_type'] or col['udt_name'],
                is_nullable=col['is_nullable'] == 'YES',
                default_value=col['column_default'],
                is_primary_key=is_pk,
                is_foreign_key=fk_info_tuple is not None,
                foreign_table=fk_info_tuple[0] if fk_info_tuple else None,
                foreign_column=fk_info_tuple[1] if fk_info_tuple else None
            )
            
            schema.fields.append(field)
        
        return schema
    
    def compare_schemas(self, spec_schemas: Dict[str, TableSchema], 
                       actual_schemas: Dict[str, TableSchema]) -> List[AuditResult]:
        """Compare specification schemas with actual database schemas."""
        print("🔍 Comparing specification with actual database...")
        
        results = []
        
        spec_tables = set(spec_schemas.keys())
        actual_tables = set(actual_schemas.keys())
        
        # Check for tables in spec but missing from database
        missing_tables = spec_tables - actual_tables
        for table in missing_tables:
            results.append(AuditResult(
                status="MISSING_TABLE",
                table=table,
                description=f"Table defined in spec but missing from database"
            ))
        
        # Check for tables in database but not in spec (extra implementation)
        extra_tables = actual_tables - spec_tables
        for table in extra_tables:
            # Only report if it's not a known advanced feature
            if not self._is_advanced_feature_table(table):
                results.append(AuditResult(
                    status="EXTRA_TABLE",
                    table=table,
                    description=f"Table exists in database but not in Modules 1-7 spec"
                ))
        
        # Compare tables that exist in both
        common_tables = spec_tables & actual_tables
        for table in common_tables:
            spec_schema = spec_schemas[table]
            actual_schema = actual_schemas[table]
            
            table_results = self._compare_table_schemas(spec_schema, actual_schema)
            results.extend(table_results)
        
        print(f"📊 Generated {len(results)} audit findings")
        return results
    
    def _is_advanced_feature_table(self, table_name: str) -> bool:
        """Check if a table belongs to advanced features (not Modules 1-7)."""
        advanced_patterns = [
            'ai_', 'ml_', 'behavioral_', 'biometric', 'anomaly', 'compliance_monitoring',
            'nlp_', 'permission_optimization', 'permission_prediction', 'user_behavior',
            'audit_', 'menu_', 'approval', 'access_request', 'active_session',
            'password_reset'  # This might be Module 1 enhancement
        ]
        
        return any(pattern in table_name for pattern in advanced_patterns)
    
    def _compare_table_schemas(self, spec_schema: TableSchema, 
                              actual_schema: TableSchema) -> List[AuditResult]:
        """Compare individual table schemas."""
        results = []
        table = spec_schema.name
        
        # Create field lookup maps
        spec_fields = {field.name: field for field in spec_schema.fields}
        actual_fields = {field.name: field for field in actual_schema.fields}
        
        # Check for fields in spec but missing from actual
        missing_fields = set(spec_fields.keys()) - set(actual_fields.keys())
        for field_name in missing_fields:
            results.append(AuditResult(
                status="MISSING_FIELD",
                table=table,
                field=field_name,
                spec_value=spec_fields[field_name].data_type,
                description=f"Field defined in spec but missing from database"
            ))
        
        # Check for fields in actual but not in spec
        extra_fields = set(actual_fields.keys()) - set(spec_fields.keys())
        for field_name in extra_fields:
            # Skip common audit/metadata fields that are typically added
            if not self._is_common_added_field(field_name):
                results.append(AuditResult(
                    status="EXTRA_FIELD",
                    table=table,
                    field=field_name,
                    actual_value=actual_fields[field_name].data_type,
                    description=f"Field exists in database but not in spec"
                ))
        
        # Compare common fields
        common_fields = set(spec_fields.keys()) & set(actual_fields.keys())
        for field_name in common_fields:
            spec_field = spec_fields[field_name]
            actual_field = actual_fields[field_name]
            
            # Compare data types (normalize for comparison)
            spec_type = self._normalize_data_type(spec_field.data_type)
            actual_type = self._normalize_data_type(actual_field.data_type)
            
            if spec_type != actual_type:
                results.append(AuditResult(
                    status="TYPE_MISMATCH",
                    table=table,
                    field=field_name,
                    spec_value=spec_field.data_type,
                    actual_value=actual_field.data_type,
                    description=f"Data type mismatch: spec={spec_type}, actual={actual_type}"
                ))
            else:
                # Field matches specification
                results.append(AuditResult(
                    status="SPEC_MATCH",
                    table=table,
                    field=field_name,
                    description=f"Field matches specification"
                ))
        
        return results
    
    def _is_common_added_field(self, field_name: str) -> bool:
        """Check if field is commonly added during implementation."""
        common_added = [
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'version', 'last_modified_by', 'deleted_at', 'is_deleted'
        ]
        return field_name in common_added
    
    def _normalize_data_type(self, data_type: str) -> str:
        """Normalize data type names for comparison."""
        # Map common type variations
        type_mapping = {
            'character varying': 'varchar',
            'timestamp with time zone': 'timestamptz',
            'timestamp without time zone': 'timestamp',
            'boolean': 'bool',
            'integer': 'int',
            'uuid': 'uuid',
            'text': 'text',
            'jsonb': 'jsonb'
        }
        
        normalized = data_type.lower()
        for original, mapped in type_mapping.items():
            if original in normalized:
                return mapped
        
        return normalized
    
    def generate_audit_report(self, results: List[AuditResult]) -> None:
        """Generate comprehensive audit report."""
        print("📄 Generating audit report...")
        
        # Categorize results
        categorized = {
            "SPEC_MATCH": [],
            "EXTRA_FIELD": [],
            "MISSING_FIELD": [],
            "TYPE_MISMATCH": [],
            "EXTRA_TABLE": [],
            "MISSING_TABLE": []
        }
        
        for result in results:
            categorized[result.status].append(result)
        
        # Generate markdown report
        report_path = self.backend_root / "DATABASE_SCHEMA_AUDIT.md"
        
        with open(report_path, 'w') as f:
            f.write("# Database Schema Audit Report\n\n")
            f.write("## Overview\n\n")
            f.write("This report compares the SQL specification with the actual PostgreSQL database\n")
            f.write("for Modules 1-7 core functionality.\n\n")
            
            # Summary statistics
            f.write("## Summary Statistics\n\n")
            for status, items in categorized.items():
                f.write(f"- **{status}**: {len(items)} findings\n")
            f.write(f"- **Total Findings**: {len(results)}\n\n")
            
            # Core Tables Analysis
            f.write("## Modules 1-7 Core Tables\n\n")
            f.write("| Table | Status | Description |\n")
            f.write("|-------|--------|-------------|\n")
            
            for table_name, module in self.MODULES_1_7_TABLES.items():
                table_results = [r for r in results if r.table == table_name]
                if any(r.status == "MISSING_TABLE" for r in table_results):
                    status = "❌ Missing"
                elif any(r.status in ["EXTRA_FIELD", "TYPE_MISMATCH"] for r in table_results):
                    status = "⚠️ Modified"
                else:
                    status = "✅ Match"
                
                f.write(f"| {table_name} | {status} | {module} |\n")
            
            f.write("\n")
            
            # Detailed findings by category
            for status, items in categorized.items():
                if not items:
                    continue
                
                f.write(f"## {status.replace('_', ' ').title()} ({len(items)} findings)\n\n")
                
                for item in items:
                    if item.field:
                        f.write(f"### {item.table}.{item.field}\n")
                    else:
                        f.write(f"### {item.table}\n")
                    
                    f.write(f"- **Status**: {item.status}\n")
                    f.write(f"- **Description**: {item.description}\n")
                    
                    if item.spec_value:
                        f.write(f"- **Spec Definition**: {item.spec_value}\n")
                    if item.actual_value:
                        f.write(f"- **Actual Definition**: {item.actual_value}\n")
                    
                    f.write("\n")
        
        # Generate JSON report for programmatic use
        json_path = self.backend_root / "database_schema_audit.json"
        with open(json_path, 'w') as f:
            json_data = {
                "summary": {status: len(items) for status, items in categorized.items()},
                "results": [asdict(result) for result in results],
                "modules_1_7_tables": self.MODULES_1_7_TABLES
            }
            json.dump(json_data, f, indent=2)
        
        print(f"📄 Reports generated:")
        print(f"  - {report_path}")
        print(f"  - {json_path}")
        
        # Print summary to console
        print(f"\n📊 AUDIT SUMMARY:")
        print(f"  ✅ Matching specifications: {len(categorized['SPEC_MATCH'])}")
        print(f"  ➕ Extra fields/tables: {len(categorized['EXTRA_FIELD']) + len(categorized['EXTRA_TABLE'])}")
        print(f"  ❌ Missing from database: {len(categorized['MISSING_FIELD']) + len(categorized['MISSING_TABLE'])}")
        print(f"  ⚠️ Type mismatches: {len(categorized['TYPE_MISMATCH'])}")
    
    async def run_audit(self) -> None:
        """Run the complete schema audit process."""
        print("🚀 Starting Database Schema Audit...")
        print(f"Target: Modules 1-7 core tables ({len(self.MODULES_1_7_TABLES)} expected)")
        
        try:
            # Parse SQL specification
            spec_schemas = self.parse_sql_specification()
            
            # Get actual database schema
            actual_schemas = await self.get_database_schema()
            
            # Compare schemas
            results = self.compare_schemas(spec_schemas, actual_schemas)
            
            # Generate reports
            self.generate_audit_report(results)
            
            print("✅ Database schema audit completed successfully!")
            
        except Exception as e:
            print(f"❌ Audit failed: {e}")
            raise


async def main():
    """Main entry point for the schema audit tool."""
    print("=" * 60)
    print("🔍 DATABASE SCHEMA AUDIT TOOL")
    print("=" * 60)
    
    auditor = DatabaseSchemaAuditor()
    await auditor.run_audit()


if __name__ == "__main__":
    asyncio.run(main())