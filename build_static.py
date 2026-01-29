#!/usr/bin/env python3
"""
Build static HTML version for GitHub Pages
"""
import os
import re
import shutil
from pathlib import Path

def build_static_site():
    """Build static site for GitHub Pages"""
    project_root = Path(__file__).parent
    frontend_dir = project_root / 'frontend'
    output_dir = project_root / '_site'
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Copy static files
    static_src = frontend_dir / 'static'
    static_dst = output_dir / 'static'
    if static_src.exists():
        if static_dst.exists():
            shutil.rmtree(static_dst)
        shutil.copytree(static_src, static_dst)
    
    # Read template
    template_file = frontend_dir / 'templates' / 'index.html'
    if not template_file.exists():
        print(f"Error: Template not found at {template_file}")
        return
    
    with open(template_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace Flask url_for with relative paths
    # {{ url_for('static', filename='css/style.css') }} -> static/css/style.css
    content = re.sub(
        r'\{\{\s*url_for\([\'"]static[\'"],\s*filename=[\'"]([^\'"]+)[\'"]\)\s*\}\}',
        r'static/\1',
        content
    )
    
    # Write index.html
    output_file = output_dir / 'index.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Create .nojekyll file for GitHub Pages
    nojekyll_file = output_dir / '.nojekyll'
    nojekyll_file.touch()
    
    print(f"✅ Static site built at {output_dir}")
    print(f"   - index.html")
    print(f"   - static/ directory")
    print(f"   - .nojekyll file")

if __name__ == '__main__':
    build_static_site()
