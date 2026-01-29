# Vocabulary Learner

Modern vocabulary learning application.

## Quick Start

```bash
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
python backend/app.py
```

## Structure

```
vocab-learner/
├── backend/          # Python backend
│   ├── app.py
│   ├── vocab_learner.py
│   └── daily_review.py
├── frontend/         # TypeScript frontend
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   ├── templates/
│   │   └── index.html
│   ├── package.json
│   └── tsconfig.json
├── helm/            # Kubernetes charts
├── docs/            # Documentation
├── Dockerfile
└── docker-compose.yml
```

## Features

- Download and translate vocabulary datasets
- Daily vocabulary review
- Create Anki decks for spaced repetition
- Modern web interface
- Support for multiple languages

## Development

### Backend

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run Flask application
python backend/app.py
```

### Frontend

```bash
# Install Node dependencies
cd frontend
npm install

# Build TypeScript
npm run build

# Watch for changes (development)
npm run watch
```

### Using Makefile

```bash
# Install all dependencies
make install

# Run application
make run

# Build TypeScript
make build-ts

# Watch TypeScript
make watch-ts
```

## Docker

### Build and Run

```bash
# Build image
make build
# or
docker build -t vocab-learner .

# Run container
make docker-run
# or
docker run -d -p 5000:5000 vocab-learner
```

### Docker Compose

```bash
make docker-compose-up
# or
docker-compose up -d
```

## GitHub Pages

The project includes automatic GitHub Pages deployment. After pushing to the `main` branch, GitHub Actions will:

1. Build the TypeScript frontend
2. Generate static HTML files
3. Deploy to GitHub Pages

The site will be available at: `https://<your-username>.github.io/vocab-learner/`

**Note:** GitHub Pages serves static files only. The API features require a running backend server. For full functionality, deploy the Flask backend separately or use the Docker deployment.

### Manual Build for GitHub Pages

```bash
# Build static site locally
cd frontend && npm install && npm run build && cd ..
python3 build_static.py

# The _site/ directory contains the static files ready for deployment
```

## Deployment

See `DEPLOY.md` for detailed deployment instructions.

See `KUBERNETES.md` for Kubernetes deployment guide.

## Package

This project includes a root `package.json` for npm package management. Install dependencies with:

```bash
npm install
```

Or use the Makefile:

```bash
make install
```

## License

MIT
