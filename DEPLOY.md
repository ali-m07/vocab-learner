# Deployment Guide

## Preparation for Push

### 1. Check Files

```bash
# Check project structure
ls -la

# Check important files
cat requirements.txt
cat Dockerfile
cat docker-compose.yml
```

### 2. Local Testing

```bash
# Install dependencies
make install
# or
pip install -r requirements.txt

# Test Flask application
make run
# or
python backend/app.py

# Open browser
open http://localhost:5000
```

### 3. Docker Testing

```bash
# Build image
make build
# or
docker build -t vocab-learner .

# Run container
make docker-run
# or
docker run -d -p 5000:5000 vocab-learner

# Test
curl http://localhost:5000/health
```

### 4. Docker Compose Testing

```bash
make docker-compose-up
# or
docker-compose up -d

# View logs
make docker-logs
# or
docker-compose logs -f
```

## Push to Git Repository

### Create New Repository

```bash
# Initialize git (if not already done)
git init

# Add remote
git remote add origin <your-repo-url>

# Add files
git add .

# Commit
git commit -m "Initial commit: Vocabulary Learning App with Docker and Helm"

# Push
git push -u origin main
```

### Git File Structure

```
vocab-learner/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── helm-deploy.yml
├── backend/
│   ├── app.py
│   ├── vocab_learner.py
│   └── daily_review.py
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   ├── templates/
│   │   └── index.html
│   ├── package.json
│   └── tsconfig.json
├── helm/
│   └── vocab-learner/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── .dockerignore
├── .gitignore
├── Dockerfile
├── Makefile
├── README.md
├── DEPLOY.md
├── KUBERNETES.md
├── docker-compose.yml
└── requirements.txt
```

## Push to Docker Hub

### 1. Login to Docker Hub

```bash
docker login
```

### 2. Tag and Push

```bash
# Tag image
docker tag vocab-learner:latest <your-dockerhub-username>/vocab-learner:latest

# Push
docker push <your-dockerhub-username>/vocab-learner:latest

# Or with version
docker tag vocab-learner:latest <your-dockerhub-username>/vocab-learner:v1.0.0
docker push <your-dockerhub-username>/vocab-learner:v1.0.0
```

### 3. Use Image in docker-compose

Edit `docker-compose.yml`:

```yaml
services:
  vocab-app:
    image: <your-dockerhub-username>/vocab-learner:latest
    # build: .  # Comment this line
```

## Deploy to Kubernetes

### With Helm

```bash
# Install
helm install vocab-learner ./helm/vocab-learner \
  --set image.repository=<your-dockerhub-username>/vocab-learner \
  --set image.tag=latest

# Or with values file
helm install vocab-learner ./helm/vocab-learner -f values-custom.yaml
```

### Check Deployment

```bash
# Pods
kubectl get pods -l app.kubernetes.io/name=vocab-learner

# Services
kubectl get svc vocab-learner

# Logs
kubectl logs -l app.kubernetes.io/name=vocab-learner -f
```

## CI/CD with GitHub Actions

### Configure Secrets in GitHub

1. Settings > Secrets and variables > Actions
2. Add:
   - `DOCKER_USERNAME`: Docker Hub username
   - `DOCKER_PASSWORD`: Docker Hub password
   - `KUBECONFIG`: kubeconfig file content (for Kubernetes)

### Using Workflows

Workflows run automatically:
- `ci.yml`: On every push/PR
- `helm-deploy.yml`: On push of v* tags

## Important Notes

1. **Environment Variables**: Use secrets for production
2. **Persistent Storage**: Configure storage class in Kubernetes
3. **Resource Limits**: Adjust based on needs
4. **Health Checks**: The `/health` endpoint is used for monitoring
5. **Security**: Add HTTPS and authentication for production

## Troubleshooting

### Build Issues

```bash
# Check Dockerfile
docker build --no-cache -t vocab-learner .

# Check logs
docker build -t vocab-learner . 2>&1 | tee build.log
```

### Run Issues

```bash
# Check container
docker ps -a
docker logs <container-id>

# Check port
netstat -an | grep 5000
```

### Kubernetes Issues

```bash
# Describe pod
kubectl describe pod <pod-name>

# Events
kubectl get events --sort-by='.lastTimestamp'

# Logs
kubectl logs <pod-name> --previous
```

## Next Steps

1. ✅ Push to Git
2. ✅ Build and Push to Docker Hub
3. ✅ Deploy to Kubernetes
4. ✅ Configure CI/CD
5. ✅ Add Monitoring
6. ✅ Add Authentication (optional)
