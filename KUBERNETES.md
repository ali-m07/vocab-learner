# Kubernetes Deployment Guide

## Prerequisites

- Kubernetes cluster (v1.19+)
- Helm 3.x
- kubectl configured

## Installation with Helm

### Simple Installation

```bash
helm install vocab-learner ./helm/vocab-learner
```

### Installation with Custom Settings

```bash
helm install vocab-learner ./helm/vocab-learner \
  --set replicaCount=3 \
  --set resources.limits.memory=2Gi \
  --set persistence.enabled=true \
  --set persistence.size=10Gi
```

### Using Custom Values File

```bash
# Create values-custom.yaml file
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

## Update

```bash
helm upgrade vocab-learner ./helm/vocab-learner
```

## Uninstall

```bash
helm uninstall vocab-learner
```

## Access the Application

### Port Forward

```bash
kubectl port-forward svc/vocab-learner 5000:5000
```

Then go to `http://localhost:5000`.

### Ingress

If Ingress is enabled:

```bash
# Enable Ingress in values.yaml
ingress:
  enabled: true
  hosts:
    - host: vocab.example.com
      paths:
        - path: /
```

Then configure your DNS to point to the Ingress controller.

## Monitoring

### Check Pods

```bash
kubectl get pods -l app.kubernetes.io/name=vocab-learner
```

### Check Logs

```bash
kubectl logs -l app.kubernetes.io/name=vocab-learner -f
```

### Check Services

```bash
kubectl get svc vocab-learner
```

## Troubleshooting

### Pod Crashing

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Persistent Volume Issues

```bash
kubectl get pvc
kubectl describe pvc vocab-learner-data
```

### Health Check Issues

```bash
kubectl exec -it <pod-name> -- curl http://localhost:5000/health
```

## Advanced Settings

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
