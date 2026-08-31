#!/bin/bash
# scripts/setup-kind.sh
# Set up a local Kubernetes cluster using Kind (Kubernetes in Docker)
# Prerequisites: Docker, kind, kubectl

set -e

CLUSTER_NAME="task-api-cluster"

echo "================================================"
echo "  Setting up local Kubernetes with Kind"
echo "  Day 47 — Kubernetes Fundamentals"
echo "================================================"
echo ""

# Check prerequisites
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ $1 not found. Install it first."
        echo "   kind: https://kind.sigs.k8s.io/docs/user/quick-start/"
        echo "   kubectl: https://kubernetes.io/docs/tasks/tools/"
        exit 1
    fi
    echo "  ✅ $1 found"
}

echo "Checking prerequisites..."
check_command docker
check_command kind
check_command kubectl
echo ""

# Create Kind cluster config
cat > /tmp/kind-config.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: task-api-cluster
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 8080
        protocol: TCP
  - role: worker
  - role: worker
EOF

# Check if cluster already exists
if kind get clusters 2>/dev/null | grep -q "$CLUSTER_NAME"; then
    echo "Cluster '$CLUSTER_NAME' already exists."
    echo "Deleting and recreating..."
    kind delete cluster --name "$CLUSTER_NAME"
fi

# Create the cluster
echo "Creating Kind cluster (1 control-plane + 2 workers)..."
kind create cluster --config /tmp/kind-config.yaml
echo ""

# Verify cluster
echo "Cluster info:"
kubectl cluster-info --context kind-$CLUSTER_NAME
echo ""

# Get nodes
echo "Nodes:"
kubectl get nodes
echo ""

echo "================================================"
echo "  ✅ Kind cluster ready!"
echo "  Run: ./scripts/deploy.sh"
echo "================================================"