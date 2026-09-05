# Day 50 — Production Operations Simulation (Phase 6 Capstone)

> **Phase 6 — DevOps & Infrastructure** | Capstone | Day 50 of 180

---

## 📌 What I Learned Today

- Production deployment lifecycle: pre-flight → build → stage → roll out → verify
- Pre-deployment checklist: error budget, no active incidents, staging passed
- Rollback trigger: error rate > 2%, p99 > 3s, health check failing
- Rollback execution: kubectl rollout undo → 2-3 minute recovery
- Chaos engineering: deliberately inject failures to build resilience
- Blast radius: the scope of impact a chaos experiment can have
- Pod kill: Kubernetes self-healing — restarts pod within 30s
- Error rate injection: validates alert fires and recovery happens
- Latency injection: validates SLO degradation detection
- Memory pressure: validates OOMKill and automatic restart
- Chaos experiment structure: name, hypothesis, blast radius, observations, validated
- Incident severity: SEV-1 (critical), SEV-2 (high), SEV-3 (medium), SEV-4 (low)
- Incident lifecycle: open → assign → investigating → mitigating → resolved
- Time to detect (TTD): alert fires → engineer aware
- Time to mitigate (TTM): aware → service restored (most important metric)
- Time to resolve (TTR): aware → root cause fixed permanently
- Blameless post-mortem: focus on systems not people
- Action items from post-mortem prevent recurrence
- Capacity planning: project resource usage at current growth rate
- Months to limit: when each resource will hit its threshold
- Alert on symptoms: error rate (symptom), not CPU % (cause)
- Runbook: step-by-step operational playbook for a specific failure
- SRE vs DevOps: SRE applies software engineering to operations
- Error budget: the amount of unreliability users will accept
- Freeze deploys when error budget low: prioritize reliability

## 🔨 Project Built

**Production Operations Simulator:**

**Deployment Pipeline** (5 steps):
- Pre-flight: error budget, incident check, staging
- Image pull: vulnerability scan
- Staging smoke tests: 8 key endpoints
- Rolling update: pod-by-pod with health verification
- Post-deploy monitoring: 2-minute error rate and latency check

**Chaos Engine** (4 experiments):
- pod-kill: kill one pod, verify Kubernetes restarts it
- high-error-rate: inject 30% errors, verify alert fires
- high-latency: inject 2500ms latency, verify SLO breach detected
- memory-pressure: ramp to 90% memory, verify OOMKill + restart

**Incident Manager**:
- Full lifecycle: open → assign → update status → resolve
- Event log: timestamped timeline of all actions
- Post-mortem template with blameless principles

**Capacity Planner**:
- 4 resources: API traffic, DB storage, pod memory, compute
- Monthly projections for 12 months
- Status: healthy / warning / critical
- Recommended pod count

**Runbook Library** (3 runbooks):
- high-error-rate: 7 steps, escalation matrix
- high-latency: 5 steps
- pod-crash: 4 steps

## 🚀 How to Run

```bash
cd Day-50-Production-Ops
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload

# Full scenario:
curl -X POST http://localhost:8000/deployment/deploy \
  -d '{"version": "1.1.0", "simulate_failure": false}'
curl -X POST http://localhost:8000/chaos/run/high-error-rate
curl http://localhost:8000/alerts
curl -X POST http://localhost:8000/deployment/rollback
curl http://localhost:8000/capacity/quick
```

## 🧠 Phase 6 at a Glance

| Day | Topic | Key Tool | Core Concept |
|-----|-------|---------|-------------|
| 46 | CI/CD | GitHub Actions | Automate every push |
| 47 | Kubernetes | kubectl | Desired state reconciliation |
| 48 | Terraform | HCL + plan/apply | Infra as reviewable code |
| 49 | Observability | Prometheus + structured logs | Three pillars |
| 50 | Production Ops | Runbooks + chaos | Reliability engineering |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)