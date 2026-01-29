# GitHub Pages Setup Guide

## Overview

This project is configured for automatic deployment to GitHub Pages. The static site is automatically built and deployed when you push to the `main` branch.

## How It Works

1. **GitHub Actions Workflow** (`.github/workflows/pages.yml`)
   - Triggers on push to `main` branch
   - Builds TypeScript frontend
   - Generates static HTML files
   - Deploys to GitHub Pages

2. **Static Site Builder** (`build_static.py`)
   - Converts Flask templates to static HTML
   - Replaces Flask `url_for()` with relative paths
   - Copies static assets (CSS, JS, images)
   - Creates `.nojekyll` file for GitHub Pages

## Enabling GitHub Pages

1. Go to your repository settings on GitHub
2. Navigate to **Pages** section
3. Under **Source**, select **GitHub Actions**
4. The site will be available at: `https://<username>.github.io/vocab-learner/`

## File Structure for GitHub Pages

```
_site/                    # Generated static site (not committed)
├── index.html           # Main HTML file
├── .nojekyll           # Disables Jekyll processing
└── static/             # Static assets
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

## Path Fixes

The build script automatically converts:
- `{{ url_for('static', filename='css/style.css') }}` → `static/css/style.css`
- `{{ url_for('static', filename='js/app.js') }}` → `static/js/app.js`

This ensures all assets load correctly on GitHub Pages.

## Local Testing

Test the static build locally:

```bash
# Build static site
python3 build_static.py

# Serve locally (requires Python)
cd _site
python3 -m http.server 8000

# Open http://localhost:8000
```

## Important Notes

⚠️ **GitHub Pages Limitations:**
- Only serves static files (HTML, CSS, JS)
- Backend API endpoints won't work
- Features requiring server-side processing are disabled

For full functionality, deploy the Flask backend separately:
- Use Docker deployment
- Deploy to Heroku, Railway, or similar
- Use Kubernetes (see `KUBERNETES.md`)

## Troubleshooting

### Styles Not Loading

1. Check that `build_static.py` ran successfully
2. Verify paths in `_site/index.html` are relative (start with `static/`)
3. Ensure `.nojekyll` file exists in `_site/`
4. Check browser console for 404 errors

### Build Fails

1. Check GitHub Actions logs
2. Ensure TypeScript compiles: `cd frontend && npm run build`
3. Verify `build_static.py` runs locally

### Pages Not Updating

1. Wait a few minutes for GitHub Actions to complete
2. Check Actions tab for workflow status
3. Clear browser cache (Ctrl+Shift+R / Cmd+Shift+R)

## Manual Deployment

If automatic deployment isn't working:

```bash
# Build static site
python3 build_static.py

# Commit and push _site/ directory
git add _site/
git commit -m "Update GitHub Pages"
git push origin main
```

Then in repository settings, set source to `_site/` directory.
