# راهنمای استقرار و Push

## آماده‌سازی برای Push

### 1. بررسی فایل‌ها

```bash
# بررسی ساختار پروژه
ls -la

# بررسی فایل‌های مهم
cat requirements.txt
cat Dockerfile
cat docker-compose.yml
```

### 2. تست محلی

```bash
# نصب وابستگی‌ها
make install
# یا
pip install -r requirements.txt

# تست اجرای Flask
make run
# یا
python app.py

# باز کردن مرورگر
open http://localhost:5000
```

### 3. تست Docker

```bash
# Build image
make build
# یا
docker build -t vocab-learner .

# Run container
make docker-run
# یا
docker run -d -p 5000:5000 vocab-learner

# تست
curl http://localhost:5000/health
```

### 4. تست Docker Compose

```bash
make docker-compose-up
# یا
docker-compose up -d

# مشاهده لاگ‌ها
make docker-logs
# یا
docker-compose logs -f
```

## Push به Git Repository

### ایجاد Repository جدید

```bash
# Initialize git (اگر قبلاً انجام نشده)
git init

# اضافه کردن remote
git remote add origin <your-repo-url>

# اضافه کردن فایل‌ها
git add .

# Commit
git commit -m "Initial commit: Vocabulary Learning App with Docker and Helm"

# Push
git push -u origin main
```

### ساختار فایل‌های Git

```
vocab-learner/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── helm-deploy.yml
├── helm/
│   └── vocab-learner/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── static/
│   ├── css/
│   └── js/
├── templates/
│   └── index.html
├── .dockerignore
├── .gitignore
├── Dockerfile
├── Makefile
├── README.md
├── DEPLOY.md
├── KUBERNETES.md
├── app.py
├── daily_review.py
├── docker-compose.yml
├── requirements.txt
└── vocab_learner.py
```

## Push به Docker Hub

### 1. Login به Docker Hub

```bash
docker login
```

### 2. Tag و Push

```bash
# Tag image
docker tag vocab-learner:latest <your-dockerhub-username>/vocab-learner:latest

# Push
docker push <your-dockerhub-username>/vocab-learner:latest

# یا با version
docker tag vocab-learner:latest <your-dockerhub-username>/vocab-learner:v1.0.0
docker push <your-dockerhub-username>/vocab-learner:v1.0.0
```

### 3. استفاده از Image در docker-compose

ویرایش `docker-compose.yml`:

```yaml
services:
  vocab-app:
    image: <your-dockerhub-username>/vocab-learner:latest
    # build: .  # این خط را comment کنید
```

## استقرار در Kubernetes

### با Helm

```bash
# نصب
helm install vocab-learner ./helm/vocab-learner \
  --set image.repository=<your-dockerhub-username>/vocab-learner \
  --set image.tag=latest

# یا با values file
helm install vocab-learner ./helm/vocab-learner -f values-custom.yaml
```

### بررسی استقرار

```bash
# Pods
kubectl get pods -l app.kubernetes.io/name=vocab-learner

# Services
kubectl get svc vocab-learner

# Logs
kubectl logs -l app.kubernetes.io/name=vocab-learner -f
```

## CI/CD با GitHub Actions

### تنظیم Secrets در GitHub

1. Settings > Secrets and variables > Actions
2. اضافه کردن:
   - `DOCKER_USERNAME`: نام کاربری Docker Hub
   - `DOCKER_PASSWORD`: رمز عبور Docker Hub
   - `KUBECONFIG`: محتوای فایل kubeconfig (برای Kubernetes)

### استفاده از Workflows

Workflow ها به صورت خودکار اجرا می‌شوند:
- `ci.yml`: در هر push/PR
- `helm-deploy.yml`: در push tag های v*

## نکات مهم

1. **Environment Variables**: برای production، از secrets استفاده کنید
2. **Persistent Storage**: در Kubernetes، storage class را تنظیم کنید
3. **Resource Limits**: بر اساس نیاز تنظیم کنید
4. **Health Checks**: endpoint `/health` برای monitoring استفاده می‌شود
5. **Security**: در production، HTTPS و authentication اضافه کنید

## Troubleshooting

### مشکل در Build

```bash
# بررسی Dockerfile
docker build --no-cache -t vocab-learner .

# بررسی logs
docker build -t vocab-learner . 2>&1 | tee build.log
```

### مشکل در Run

```bash
# بررسی container
docker ps -a
docker logs <container-id>

# بررسی port
netstat -an | grep 5000
```

### مشکل در Kubernetes

```bash
# Describe pod
kubectl describe pod <pod-name>

# Events
kubectl get events --sort-by='.lastTimestamp'

# Logs
kubectl logs <pod-name> --previous
```

## Next Steps

1. ✅ Push به Git
2. ✅ Build و Push به Docker Hub
3. ✅ استقرار در Kubernetes
4. ✅ تنظیم CI/CD
5. ✅ اضافه کردن Monitoring
6. ✅ اضافه کردن Authentication (اختیاری)
