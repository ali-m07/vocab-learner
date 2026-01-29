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
    import sys
    
    project_root = Path(__file__).parent
    frontend_dir = project_root / 'frontend'
    output_dir = project_root / '_site'
    
    # Verify frontend directory exists
    if not frontend_dir.exists():
        print(f"❌ Error: Frontend directory not found at {frontend_dir}")
        sys.exit(1)
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Copy static files
    static_src = frontend_dir / 'static'
    static_dst = output_dir / 'static'
    if not static_src.exists():
        print(f"⚠️  Warning: Static directory not found at {static_src}")
    else:
        if static_dst.exists():
            shutil.rmtree(static_dst)
        shutil.copytree(static_src, static_dst)
        print(f"✅ Copied static files from {static_src} to {static_dst}")
    
    # Prefer a dedicated Pages homepage at repo root (index.html)
    # Fallback to the Flask template for local backend usage.
    root_index = project_root / 'index.html'
    template_file = frontend_dir / 'templates' / 'index.html'
    source_file = root_index if root_index.exists() else template_file
    if not source_file.exists():
        print(f"❌ Error: No index source found at {root_index} or {template_file}")
        sys.exit(1)

    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace Flask url_for with relative paths
    # {{ url_for('static', filename='css/style.css') }} -> static/css/style.css
    content = re.sub(
        r'\{\{\s*url_for\([\'"]static[\'"],\s*filename=[\'"]([^\'"]+)[\'"]\)\s*\}\}',
        r'static/\1',
        content
    )

    # If using the repo-root Pages homepage, rewrite asset paths:
    # frontend/static/... -> static/...
    content = content.replace('href="frontend/static/', 'href="static/')
    content = content.replace("href='frontend/static/", "href='static/")
    content = content.replace('src="frontend/static/', 'src="static/')
    content = content.replace("src='frontend/static/", "src='static/")
    
    # Cache-bust static assets (avoid GitHub Pages serving stale JS/CSS)
    version = os.getenv("GITHUB_SHA", "")[:8] or os.getenv("SOURCE_VERSION", "")[:8]
    if not version:
        version = "v1"
    content = content.replace("static/css/style.css", f"static/css/style.css?v={version}")
    content = content.replace("static/js/app.js", f"static/js/app.js?v={version}")

    # Write index.html
    output_file = output_dir / 'index.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Create .nojekyll file for GitHub Pages
    nojekyll_file = output_dir / '.nojekyll'
    nojekyll_file.touch()
    
    # Verify output
    if not output_file.exists():
        print(f"❌ Error: Failed to create index.html")
        sys.exit(1)
    
    print(f"✅ Static site built successfully at {output_dir}")
    print(f"   ✓ index.html")
    print(f"   ✓ static/ directory")
    print(f"   ✓ .nojekyll file")

if __name__ == '__main__':
    build_static_site()
