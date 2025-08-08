#!/usr/bin/env python3
"""
API Audit Tool - Compare API Specifications with Implementation

This tool compares the Sentinel_API_SPECS.md document with the actual
implemented API endpoints in src/api/v1/ for Modules 1-7.

Generates a comprehensive report showing:
- ✅ Implemented & Matches Spec
- 🔄 Implemented but Modified  
- ➕ Added (not in original spec)
- ❌ Missing (in spec but not implemented)
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class ImplementationStatus(Enum):
    MATCHES = "✅ Implemented & Matches Spec"
    MODIFIED = "🔄 Implemented but Modified"
    ADDED = "➕ Added (not in original spec)"
    MISSING = "❌ Missing (in spec but not implemented)"


@dataclass
class APIEndpoint:
    method: str
    path: str
    description: str
    module: str
    source: str  # "spec" or "implementation"
    status: ImplementationStatus = None


@dataclass
class ModuleAudit:
    module_name: str
    module_number: int
    api_file: str
    spec_section: str
    spec_endpoints: List[APIEndpoint]
    impl_endpoints: List[APIEndpoint]
    audit_results: Dict[str, ImplementationStatus]


class APIAuditor:
    def __init__(self, backend_root: str):
        self.backend_root = Path(backend_root)
        self.specs_file = self.backend_root / "docs" / "Sentinel_API_SPECS.md"
        self.api_dir = self.backend_root / "src" / "api" / "v1"
        
        # Module mapping: Module Number -> (Name, API File, Spec Section)
        self.modules = {
            1: ("Authentication", "auth.py", "1. Authentication & Token Management APIs"),
            2: ("Tenants", "tenants.py", "10. Tenant Management APIs (Admin Only)"),
            3: ("Users", "users.py", "2. User Management APIs"),
            4: ("Roles", "roles.py", "3. Role Management APIs"),
            5: ("Groups", "groups.py", "4. Group Management APIs"),
            6: ("Permissions", "permissions.py", "5. Permission Evaluation APIs"),
            7: ("Resources", "resources.py", "6. Resource Management APIs"),
            # Service Accounts is also implemented
            8: ("Service Accounts", "service_accounts.py", "11. Service Account Management APIs")
        }
        
        self.audit_results: List[ModuleAudit] = []

    def parse_spec_file(self) -> Dict[str, List[APIEndpoint]]:
        """Parse the API specification file and extract endpoints by section."""
        if not self.specs_file.exists():
            raise FileNotFoundError(f"API specs file not found: {self.specs_file}")
        
        content = self.specs_file.read_text()
        sections = {}
        
        for module_num, (module_name, _, spec_section) in self.modules.items():
            section_endpoints = self._extract_endpoints_from_section(content, spec_section)
            sections[spec_section] = [
                APIEndpoint(
                    method=ep["method"],
                    path=ep["path"],
                    description=ep.get("description", ""),
                    module=module_name,
                    source="spec"
                ) for ep in section_endpoints
            ]
        
        return sections

    def _extract_endpoints_from_section(self, content: str, section_name: str) -> List[Dict]:
        """Extract API endpoints from a specific section of the spec file."""
        endpoints = []
        
        # Find section start
        section_pattern = rf"### {re.escape(section_name)}"
        section_match = re.search(section_pattern, content)
        if not section_match:
            print(f"Warning: Section '{section_name}' not found in specs")
            return endpoints
        
        # Extract section content until next main section
        section_start = section_match.end()
        next_section_pattern = r"\n### \d+\."
        next_section_match = re.search(next_section_pattern, content[section_start:])
        
        if next_section_match:
            section_content = content[section_start:section_start + next_section_match.start()]
        else:
            section_content = content[section_start:]
        
        # Extract HTTP method and path patterns
        # Look for patterns like: POST /auth/login, GET /users/{id}, etc.
        endpoint_pattern = r"```http\n(GET|POST|PUT|PATCH|DELETE)\s+(/[^\n]*)\n```"
        endpoint_matches = re.findall(endpoint_pattern, section_content, re.MULTILINE)
        
        for method, path in endpoint_matches:
            # Try to find description from nearby text
            description = self._extract_endpoint_description(section_content, method, path)
            endpoints.append({
                "method": method,
                "path": path.strip(),
                "description": description
            })
        
        return endpoints

    def _extract_endpoint_description(self, section_content: str, method: str, path: str) -> str:
        """Extract description for an endpoint from surrounding context."""
        # Look for headers like #### 1.1 User Login before the endpoint
        pattern = rf"####.*?```http\n{method}\s+{re.escape(path)}"
        match = re.search(pattern, section_content, re.DOTALL)
        
        if match:
            header_match = re.search(r"#### \d+\.\d+\s+(.+)", match.group(0))
            if header_match:
                return header_match.group(1).strip()
        
        return f"{method} {path}"

    def parse_implementation_files(self) -> Dict[str, List[APIEndpoint]]:
        """Parse implemented API files and extract endpoints."""
        implementations = {}
        
        for module_num, (module_name, api_file, spec_section) in self.modules.items():
            file_path = self.api_dir / api_file
            if not file_path.exists():
                print(f"Warning: Implementation file not found: {file_path}")
                implementations[spec_section] = []
                continue
            
            endpoints = self._extract_endpoints_from_file(file_path, module_name)
            implementations[spec_section] = endpoints
        
        return implementations

    def _extract_endpoints_from_file(self, file_path: Path, module_name: str) -> List[APIEndpoint]:
        """Extract endpoints from a FastAPI implementation file."""
        content = file_path.read_text()
        endpoints = []
        
        # Pattern to match FastAPI route decorators
        # @router.post("/", ...) or @router.get("/{id}", ...)
        route_pattern = r'@router\.(get|post|put|patch|delete)\(\s*["\']([^"\']+)["\']'
        
        matches = re.findall(route_pattern, content, re.MULTILINE)
        
        for method, path in matches:
            # Try to extract function name or description
            # Look for the function definition after the decorator
            func_pattern = rf'@router\.{method}\([^)]*\)[^)]*\)\s*\n(?:async\s+)?def\s+(\w+)'
            func_match = re.search(func_pattern, content)
            
            description = func_match.group(1) if func_match else f"{method.upper()} {path}"
            
            endpoints.append(APIEndpoint(
                method=method.upper(),
                path=path,
                description=description,
                module=module_name,
                source="implementation"
            ))
        
        return endpoints

    def compare_endpoints(self, spec_endpoints: List[APIEndpoint], 
                         impl_endpoints: List[APIEndpoint]) -> Dict[str, ImplementationStatus]:
        """Compare specification endpoints with implementation endpoints."""
        results = {}
        
        # Create lookup sets for easier comparison
        spec_set = {(ep.method, self._normalize_path(ep.path)) for ep in spec_endpoints}
        impl_set = {(ep.method, self._normalize_path(ep.path)) for ep in impl_endpoints}
        
        # Check spec endpoints against implementation
        for spec_ep in spec_endpoints:
            key = f"{spec_ep.method} {spec_ep.path}"
            normalized_key = (spec_ep.method, self._normalize_path(spec_ep.path))
            
            if normalized_key in impl_set:
                results[key] = ImplementationStatus.MATCHES
            else:
                # Check for similar paths (might be modified)
                similar = self._find_similar_endpoint(spec_ep, impl_endpoints)
                if similar:
                    results[key] = ImplementationStatus.MODIFIED
                else:
                    results[key] = ImplementationStatus.MISSING
        
        # Check for endpoints in implementation but not in spec
        for impl_ep in impl_endpoints:
            key = f"{impl_ep.method} {impl_ep.path}"
            normalized_key = (impl_ep.method, self._normalize_path(impl_ep.path))
            
            if normalized_key not in spec_set:
                # Check if it's similar to any spec endpoint
                similar = self._find_similar_endpoint(impl_ep, spec_endpoints)
                if not similar:
                    results[key] = ImplementationStatus.ADDED
        
        return results

    def _normalize_path(self, path: str) -> str:
        """Normalize API path for comparison (handle parameter variations)."""
        # Replace {id} with {.*} for pattern matching
        # Replace {user_id} with {.*}, etc.
        normalized = re.sub(r'\{[^}]+\}', '{param}', path)
        return normalized.strip('/')

    def _find_similar_endpoint(self, target: APIEndpoint, candidates: List[APIEndpoint]) -> APIEndpoint:
        """Find similar endpoint with fuzzy matching."""
        target_norm = self._normalize_path(target.path)
        
        for candidate in candidates:
            if (target.method == candidate.method and 
                self._paths_similar(target_norm, self._normalize_path(candidate.path))):
                return candidate
        
        return None

    def _paths_similar(self, path1: str, path2: str) -> bool:
        """Check if two normalized paths are similar."""
        # Simple similarity check - same base path structure
        parts1 = path1.split('/')
        parts2 = path2.split('/')
        
        if len(parts1) != len(parts2):
            return False
        
        # Allow parameter differences
        for p1, p2 in zip(parts1, parts2):
            if p1 != p2 and not ('{param}' in p1 or '{param}' in p2):
                return False
        
        return True

    def run_audit(self) -> None:
        """Run the complete API audit process."""
        print("🔍 Starting API Audit for Modules 1-7...")
        
        # Parse specifications and implementations
        spec_sections = self.parse_spec_file()
        impl_sections = self.parse_implementation_files()
        
        # Audit each module
        for module_num, (module_name, api_file, spec_section) in self.modules.items():
            print(f"\n📋 Auditing Module {module_num}: {module_name}")
            
            spec_endpoints = spec_sections.get(spec_section, [])
            impl_endpoints = impl_sections.get(spec_section, [])
            
            audit_results = self.compare_endpoints(spec_endpoints, impl_endpoints)
            
            module_audit = ModuleAudit(
                module_name=module_name,
                module_number=module_num,
                api_file=api_file,
                spec_section=spec_section,
                spec_endpoints=spec_endpoints,
                impl_endpoints=impl_endpoints,
                audit_results=audit_results
            )
            
            self.audit_results.append(module_audit)
            
            # Print summary for this module
            self._print_module_summary(module_audit)
        
        # Generate comprehensive report
        self._generate_report()

    def _print_module_summary(self, audit: ModuleAudit) -> None:
        """Print summary for a single module audit."""
        total_spec = len(audit.spec_endpoints)
        total_impl = len(audit.impl_endpoints)
        
        status_counts = {}
        for status in ImplementationStatus:
            status_counts[status] = sum(1 for s in audit.audit_results.values() if s == status)
        
        print(f"  📊 Spec endpoints: {total_spec}, Implementation endpoints: {total_impl}")
        for status, count in status_counts.items():
            if count > 0:
                print(f"  {status.value}: {count}")

    def _generate_report(self) -> None:
        """Generate comprehensive audit report."""
        report_path = self.backend_root / "API_IMPLEMENTATION_STATUS.md"
        
        with open(report_path, 'w') as f:
            f.write("# API Implementation Status Report\n\n")
            f.write("Generated by API Audit Tool\n\n")
            f.write("## Summary\n\n")
            
            # Overall statistics
            total_spec_endpoints = sum(len(audit.spec_endpoints) for audit in self.audit_results)
            total_impl_endpoints = sum(len(audit.impl_endpoints) for audit in self.audit_results)
            
            f.write(f"- **Total Spec Endpoints**: {total_spec_endpoints}\n")
            f.write(f"- **Total Implementation Endpoints**: {total_impl_endpoints}\n\n")
            
            # Status summary
            overall_status_counts = {}
            for audit in self.audit_results:
                for status in audit.audit_results.values():
                    overall_status_counts[status] = overall_status_counts.get(status, 0) + 1
            
            f.write("### Overall Status Distribution\n\n")
            for status, count in overall_status_counts.items():
                f.write(f"- {status.value}: {count}\n")
            
            f.write("\n## Module Details\n\n")
            
            # Detailed module reports
            for audit in self.audit_results:
                f.write(f"### Module {audit.module_number}: {audit.module_name}\n\n")
                f.write(f"**API File**: `{audit.api_file}`  \n")
                f.write(f"**Spec Section**: {audit.spec_section}  \n")
                f.write(f"**Spec Endpoints**: {len(audit.spec_endpoints)}  \n")
                f.write(f"**Implementation Endpoints**: {len(audit.impl_endpoints)}  \n\n")
                
                if audit.audit_results:
                    f.write("#### Endpoint Status\n\n")
                    for endpoint, status in sorted(audit.audit_results.items()):
                        f.write(f"- {status.value}: `{endpoint}`\n")
                    f.write("\n")
                
                # List implementation endpoints
                if audit.impl_endpoints:
                    f.write("#### Implementation Endpoints\n\n")
                    for ep in audit.impl_endpoints:
                        f.write(f"- `{ep.method} {ep.path}` - {ep.description}\n")
                    f.write("\n")
        
        print(f"\n📄 Comprehensive report generated: {report_path}")
        
        # Also generate JSON report for programmatic use
        json_path = self.backend_root / "api_audit_results.json"
        with open(json_path, 'w') as f:
            json.dump([asdict(audit) for audit in self.audit_results], f, indent=2, default=str)
        
        print(f"📄 JSON report generated: {json_path}")


def main():
    """Main entry point for the API audit tool."""
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    auditor = APIAuditor(backend_root)
    auditor.run_audit()
    
    print("\n✅ API Audit Complete!")
    print("\nFiles generated:")
    print("- API_IMPLEMENTATION_STATUS.md")
    print("- api_audit_results.json")


if __name__ == "__main__":
    main()