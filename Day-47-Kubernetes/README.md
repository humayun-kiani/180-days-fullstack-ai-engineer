# Day 47 — Docker & Kubernetes Fundamentals

> **Phase 6 — DevOps & Infrastructure** | Week 9 | Day 47 of 180

---

## 📌 What I Learned Today

- Kubernetes vs Docker Compose: cluster of machines vs single machine
- Control plane: API server (REST), etcd (state), scheduler, controller manager
- kubelet: agent on each node that runs containers
- Pod: smallest unit, wraps 1+ containers, ephemeral IP
- Deployment: manages pods, rolling updates, rollbacks, desired state
- ReplicaSet: ensures N pods always running (managed by Deployment)
- Service: stable IP/DNS for a set of pods, load balancing across them
- ClusterIP: internal only, NodePort: external on node port, LoadBalancer: cloud LB
- ConfigMap: non-sensitive config injected as env vars or files
- Secret: sensitive data (base64-encoded, not encrypted by default)
- Downward API: inject pod metadata as env vars (POD_NAME, NODE_NAME)
- readinessProbe: is pod ready for traffic? (taken out of Service if fails)
- livenessProbe: is pod alive? (killed and restarted if fails)
- startupProbe: for slow-starting containers (disables liveness until ready)
- resources.requests: scheduler uses this to place pods on nodes
- resources.limits: memory → OOMKill if exceeded; CPU → throttle
- 100m CPU = 0.1 vCPU (millicores), 128Mi = 128 megabytes
- HPA: auto-scale based on CPU/memory metrics
- Rolling update: maxSurge=1 maxUnavailable=0 → zero downtime
- kubectl rollout undo: instant rollback to previous version
- Namespace: isolate resources (dev, staging, prod in same cluster)
- Kustomize: overlay patches for different environments
- podAntiAffinity: spread pods across nodes for HA
- Kind: Kubernetes in Docker (local development cluster)
- kind load docker-image: load local image into Kind (no registry needed)
- terminationGracePeriodSeconds: graceful shutdown window

## 🔨 Project Built

**Task API on Kubernetes:**

**7 Kubernetes manifests (k8s/base/):**

- namespace.yaml: isolated task-api namespace
- configmap.yaml: LOG_LEVEL, MAX_TASKS, ENVIRONMENT
- secret.yaml: ANTHROPIC_API_KEY, DATABASE_URL (template)
- deployment.yaml: 3 replicas, rolling update, resources, probes, Downward API
- service.yaml: ClusterIP routes to task-api pods
- hpa.yaml: auto-scale 2-10 pods at 70% CPU / 80% memory
- ingress.yaml: HTTP routing rules with nginx annotations

**2 Kustomize overlays:**

- development: 1 replica, DEBUG log, 100 max tasks
- production: 5 replicas, WARNING log, 100K max tasks

**FastAPI app enhancements:**

- /health: for liveness probe
- /ready: for readiness probe (checks MAX_TASKS capacity)
- /info: shows POD_NAME and NODE_NAME (Downward API demo!)

**Scripts:**

- setup-kind.sh: 3-node Kind cluster (1 control + 2 workers)
- deploy.sh: build → load → apply manifests → wait → port-forward

## 🚀 How to Run

```bash
# Prerequisites: Docker, kind, kubectl
cd Day-47-Kubernetes

python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Tests
pytest tests/ -v

# Local Kubernetes
./scripts/setup-kind.sh
./scripts/deploy.sh
kubectl port-forward svc/task-api-service 8000:80 -n task-api

# See load balancing in action:
for i in {1..6}; do curl -s http://localhost:8000/info | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d['pod_name'])"; done

# Scale
kubectl scale deployment task-api --replicas=5 -n task-api

# Cleanup
kubectl delete namespace task-api
kind delete cluster --name task-api-cluster
```

## 🧠 Key Concepts Quick Reference

| Concept        | What it does           |
| -------------- | ---------------------- |
| Pod            | Runs your containers   |
| Deployment     | Manages pod lifecycle  |
| Service        | Routes traffic to pods |
| ConfigMap      | Non-secret config      |
| Secret         | Sensitive config       |
| HPA            | Auto-scale pods        |
| Namespace      | Isolate environments   |
| readinessProbe | Traffic routing check  |
| livenessProbe  | Pod restart check      |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
