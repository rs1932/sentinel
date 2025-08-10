#!/usr/bin/env python3
"""
Fix all import issues in the Sentinel API code
"""
import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix imports that go too far up (4 dots)
    content = re.sub(r'from \.\.\.\.(\w+)', r'from ..\1', content)
    
    # Fix specific problematic imports
    replacements = [
        # In core/security_utils.py
        ('from ....database import get_db', 'from ..database import get_db'),
        ('from ....models', 'from ..models'),
        ('from ....utils', 'from ..utils'),
        ('from ....services', 'from ..services'),
        ('from ....core', 'from ..core'),
        ('from ....schemas', 'from ..schemas'),
        
        # In utils files
        ('from ...config', 'from ..config'),
        ('from ...database', 'from ..database'),
        
        # In middleware files  
        ('from ...utils', 'from ..utils'),
        ('from ...core', 'from ..core'),
        ('from ...services', 'from ..services'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    # Find all Python files in the sentinel directory
    sentinel_dir = Path('/Users/rs/Documents/workspaces/Neuwerx Products/sentinel/sentinel-claude-code/neuwerx-platform/api/src/v1/sentinel')
    
    fixed_count = 0
    for py_file in sentinel_dir.rglob('*.py'):
        if py_file.suffix == '.py' and '.bak' not in str(py_file):
            if fix_imports_in_file(py_file):
                fixed_count += 1
                print(f"Fixed: {py_file.relative_to(sentinel_dir)}")
    
    print(f"\n✅ Fixed {fixed_count} files")

if __name__ == '__main__':
    main()