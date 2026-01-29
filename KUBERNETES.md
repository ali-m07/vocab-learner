# راهنمای استقرار در Kubernetes

## پیش‌نیازها

- Kubernetes cluster (v1.19+)
- Helm 3.x
- kubectl configured

## نصب با Helm

### نصب ساده

```bash
helm install vocab-learner ./helm/vocab-learner
```

### نصب با تنظیمات سفارشی

```bash
helm install vocab-learner ./helm/vocab-learner \
  --set replicaCount=3 \
  --set resources.limits.memory=2Gi \
  --set persistence.enabled=true \
  --set persistence.size=10Gi
```

### استفاده از فایل values سفارشی

```bash
# ایجاد فایل values-custom.yaml
cat > values-custom.yaml <<EOF
replicaCount: 2
resources:
  limits:
    memory: 2Gi
persistence:
  enabled: true
  size: 10Gi
ingress:
  enabled: true
  hosts:
    - host: vocab.example.com
      paths:
        - path: /
EOF

helm install vocab-learner ./helm/vocab-learner -f values-custom.yaml
```

## آپدیت

```bash
helm upgrade vocab-learner ./helm/vocab-learner
```

## حذف

```bash
helm uninstall vocab-learner
```

## دسترسی به اپلیکیشن

### Port Forward

```bash
kubectl port-forward svc/vocab-learner 5000:5000
```

سپس به `http://localhost:5000` بروید.

### Ingress

اگر Ingress فعال باشد:

```bash
# فعال کردن Ingress در values.yaml
ingress:
  enabled: true
  hosts:
    - host: vocab.example.com
      paths:
        - path: /
```

سپس DNS خود را به Ingress controller تنظیم کنید.

## Monitoring

### بررسی Pods

```bash
kubectl get pods -l app.kubernetes.io/name=vocab-learner
```

### بررسی Logs

```bash
kubectl logs -l app.kubernetes.io/name=vocab-learner -f
```

### بررسی Services

```bash
kubectl get svc vocab-learner
```

## Troubleshooting

### Pod در حال Crash

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### مشکل در Persistent Volume

```bash
kubectl get pvc
kubectl describe pvc vocab-learner-data
```

### مشکل در Health Check

```bash
kubectl exec -it <pod-name> -- curl http://localhost:5000/health
```

## تنظیمات پیشرفته

### Auto-scaling

```bash
helm upgrade vocab-learner ./helm/vocab-learner \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=2 \
  --set autoscaling.maxReplicas=5
```

### Resource Limits

```bash
helm upgrade vocab-learner ./helm/vocab-learner \
  --set resources.limits.cpu=2000m \
  --set resources.limits.memory=2Gi \
  --set resources.requests.cpu=1000m \
  --set resources.requests.memory=1Gi
```

### Node Selector

```bash
helm upgrade vocab-learner ./helm/vocab-learner \
  --set nodeSelector."kubernetes.io/os"=linux
```
