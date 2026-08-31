#!/bin/bash
# scripts/deploy.sh
# Deploy Task API to local Kind cluster
# Run after setup-kind.sh

set -e

CLUSTER_NAME="task-api-cluster"
IMAGE_NAME="task-api"
IMAGE_TAG="1.0.0"
NAMESPACE="task-api"

echo "================================================"
echo "  Deploying Task API to Kubernetes"
echo "  Day 47 — Kubernetes Fundamentals"
echo "================================================"
echo ""

# Step 1: Build Docker image
echo "Step 1: Building Docker image..."
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
echo "  ✅ Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""

# Step 2: Load image into Kind cluster
# (Kind cluster can't pull from Docker Hub by default)
echo "Step 2: Loading image into Kind cluster..."
kind load docker-image ${IMAGE_NAME}:${IMAGE_TAG} \
    --name ${CLUSTER_NAME}
echo "  ✅ Image loaded into cluster"
echo ""

# Step 3: Apply Kubernetes manifests
echo "Step 3: Applying Kubernetes manifests..."

# Apply in order (dependencies first)
kubectl apply -f k8s/base/namespace.yaml
echo "  ✅ Namespace created"

kubectl apply -f k8s/base/configmap.yaml
echo "  ✅ ConfigMap applied"

kubectl apply -f k8s/base/secret.yaml
echo "  ✅ Secret applied"

kubectl apply -f k8s/base/deployment.yaml
echo "  ✅ Deployment applied"

kubectl apply -f k8s/base/service.yaml
echo "  ✅ Service applied"

echo ""

# Step 4: Wait for deployment to be ready
echo "Step 4: Waiting for deployment to be ready..."
kubectl rollout status deployment/task-api \
    -n ${NAMESPACE} \
    --timeout=120s
echo "  ✅ Deployment ready!"
echo ""

# Step 5: Show status
echo "Step 5: Deployment status"
echo ""
echo "Pods:"
kubectl get pods -n ${NAMESPACE} -o wide
echo ""
echo "Service:"
kubectl get service -n ${NAMESPACE}
echo ""
echo "Deployment:"
kubectl get deployment -n ${NAMESPACE}
echo ""

# Step 6: Port-forward for local access
echo "Step 6: Setting up port forwarding..."
echo "  Forwarding localhost:8000 → task-api-service:80"
echo ""
echo "================================================"
echo "  ✅ Deployment complete!"
echo ""
echo "  Access the API:"
echo "  kubectl port-forward svc/task-api-service 8000:80 -n ${NAMESPACE}"
echo ""
echo "  Useful commands:"
echo "  kubectl get pods -n ${NAMESPACE}"
echo "  kubectl logs -f -l app=task-api -n ${NAMESPACE}"
echo "  kubectl describe deployment task-api -n ${NAMESPACE}"
echo "  kubectl scale deployment task-api --replicas=5 -n ${NAMESPACE}"
echo "================================================"