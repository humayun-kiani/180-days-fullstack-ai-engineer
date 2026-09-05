# app/main.py
# Production Operations Simulator — Day 50: Phase 6 Capstone

import time
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.service_state import service, ServiceStatus
from app.deployment.pipeline import pipeline, DeploymentStatus
from app.chaos.experiments import chaos_engine, EXPERIMENT_CATALOG
from app.incidents.manager import incident_manager
from app.capacity.planner import capacity_planner
from app.runbooks.library import get_runbook, list_runbooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 65)
    print("  Production Operations Simulator — Day 50")
    print("  Phase 6 Capstone: CI/CD + K8s + Terraform + Observability")
    print("=" * 65)
    print(f"\n  Service: task-api v{service.current_version}")
    print(f"  Pods: {len(service.pods)} Running")
    print(f"  Docs: http://localhost:8000/docs\n")
    yield
    print("\n  Shutting down...")


app = FastAPI(
    title="Production Operations Simulator",
    description="""
## 🏭 Production Operations Simulator — Day 50

**Phase 6 Capstone** — integrating CI/CD, Kubernetes, Terraform, and Observability.

### What This Simulates
- **Deployment pipeline** — pre-flight → build → test → roll out → verify
- **Chaos engineering** — deliberately inject failures, verify resilience
- **Incident management** — open, triage, resolve incidents
- **Capacity planning** — project resource usage and when to scale
- **Runbooks** — operational playbooks for common failures

### The Production Loop

### Scenario to Try
1. `POST /deployment/deploy` — deploy a new version
2. `POST /chaos/run/high-error-rate` — inject errors
3. `GET /alerts` — see alert firing
4. `POST /incidents/open` — open an incident
5. `POST /deployment/rollback` — roll back
6. `POST /incidents/{id}/resolve` — close incident
7. `GET /capacity/plan` — check resource runway
    """,
    version="1.0.0",
    lifespan=lifespan
)


# ── Schemas ───────────────────────────────────────────────────

class DeployRequest(BaseModel):
    version: str = Field(default="1.1.0", example="1.1.0")
    environment: str = Field(default="production")
    deployed_by: str = Field(default="engineer")
    simulate_failure: bool = Field(default=False)


class IncidentOpenRequest(BaseModel):
    title: str = Field(example="High error rate on task-api")
    severity: str = Field(default="sev2", pattern="^sev[1-4]$")
    description: str = Field(example="Error rate jumped to 4.2% at 14:32 UTC")
    affected_services: list[str] = Field(default=["task-api"])
    opened_by: str = Field(default="on-call")


class IncidentResolveRequest(BaseModel):
    root_cause: str = Field(example="DB migration added NOT NULL column without default value")
    resolution: str = Field(example="Rolled back to v1.0.0; will fix migration and redeploy tomorrow")
    resolved_by: str = Field(default="on-call")


class CapacityRequest(BaseModel):
    traffic_growth_monthly: float = Field(default=0.10, ge=0.01, le=1.0)
    current_rps: float = Field(default=150.0, ge=1.0)
    current_db_gb: float = Field(default=45.0, ge=1.0)
    current_pods: int = Field(default=3, ge=1, le=20)


# ── Service Status ────────────────────────────────────────────

@app.get("/service/status", summary="Current service status")
def service_status() -> dict:
    """Real-time service status — pods, version, health."""
    traffic = service.simulate_traffic(50)
    return {
        "status": service.status.value,
        "version": service.current_version,
        "desired_replicas": service.desired_replicas,
        "pods": service.get_pod_status(),
        "live_metrics": {
            "error_rate_pct": traffic["error_rate_pct"],
            "p50_ms": traffic["p50_ms"],
            "p99_ms": traffic["p99_ms"],
            "requests_simulated": traffic["requests"]
        },
        "chaos_active": service._chaos_active,
        "chaos_type": service._chaos_type,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ── Deployment Endpoints ──────────────────────────────────────

@app.post(
    "/deployment/deploy",
    summary="Deploy a new version through the full pipeline"
)
async def deploy(request: DeployRequest, background_tasks: BackgroundTasks) -> dict:
    """
    Run the full deployment pipeline:
    pre-flight → image pull → staging tests → rolling update → smoke tests → monitoring
    """
    deployment = pipeline.deploy(
        version=request.version,
        environment=request.environment,
        deployed_by=request.deployed_by,
        simulate_failure=request.simulate_failure
    )

    if deployment.status == DeploymentStatus.FAILED:
        return {
            "result": "failed",
            "deployment": deployment.to_dict(),
            "next_steps": [
                "POST /deployment/rollback — roll back immediately",
                "POST /incidents/open — open an incident",
                "GET /logs?level=ERROR — check what went wrong"
            ]
        }

    return {
        "result": "success",
        "deployment": deployment.to_dict(),
        "next_steps": [
            "GET /service/status — verify pods are healthy",
            "GET /alerts — confirm no alerts firing",
            "POST /chaos/run/high-error-rate — test resilience"
        ]
    }


@app.post("/deployment/rollback", summary="Roll back to previous version")
def rollback(reason: str = "Elevated error rate detected") -> dict:
    """Instantly roll back to the previous deployment."""
    result = pipeline.rollback(reason=reason)
    if not result:
        raise HTTPException(400, "No previous deployment to roll back to")

    # Auto-resolve any active incidents
    for incident in incident_manager.get_active_incidents():
        incident_manager.update_status(
            incident["incident_id"],
            "mitigating",
            "system",
            f"Rollback completed to v{result['rolled_back_to']}"
        )

    return {
        "result": "success",
        "rollback": result,
        "service_version": service.current_version,
        "service_status": service.status.value
    }


@app.get("/deployment/history", summary="Deployment history")
def deployment_history(limit: int = 10) -> dict:
    return {"deployments": pipeline.get_history(limit=limit)}


# ── Chaos Engineering ─────────────────────────────────────────

@app.get("/chaos/catalog", summary="Available chaos experiments")
def chaos_catalog() -> dict:
    return {
        "experiments": chaos_engine.get_catalog(),
        "tip": "Start with 'pod-kill' — it's the safest and most instructive"
    }


@app.post(
    "/chaos/run/{experiment_id}",
    summary="Run a chaos experiment"
)
async def run_chaos(experiment_id: str) -> dict:
    """
    Run a named chaos experiment against the service.

    Available: pod-kill, high-error-rate, high-latency, memory-pressure
    """
    try:
        experiment = chaos_engine.run_experiment(experiment_id)
        return {
            "experiment": experiment.to_dict(),
            "service_status": service.status.value,
            "next_steps": (
                ["POST /deployment/rollback — rollback if needed",
                 "POST /chaos/stop — stop chaos if still active"]
                if not experiment.hypothesis_validated else
                ["GET /service/status — verify service recovered",
                 "GET /alerts — check alert states"]
            )
        }
    except ValueError as e:
        available = [e["id"] for e in EXPERIMENT_CATALOG]
        raise HTTPException(404, f"{str(e)}. Available: {available}")


@app.post("/chaos/stop", summary="Stop all active chaos")
def stop_chaos() -> dict:
    """Emergency stop for all active chaos injection."""
    was_active = service._chaos_active
    service.stop_chaos()
    return {
        "stopped": was_active,
        "chaos_type_stopped": service._chaos_type if was_active else None,
        "service_status": service.status.value
    }


@app.get("/chaos/experiments", summary="Experiment history")
def chaos_experiments() -> dict:
    return {"experiments": chaos_engine.get_experiments()}


# ── Incident Management ───────────────────────────────────────

@app.post("/incidents/open", summary="Open a new incident")
def open_incident(request: IncidentOpenRequest) -> dict:
    incident = incident_manager.open_incident(
        title=request.title,
        severity=request.severity,
        description=request.description,
        affected_services=request.affected_services,
        opened_by=request.opened_by
    )
    return {
        "incident": incident.to_dict(),
        "runbook": f"GET /runbooks/{incident.severity.value.replace('sev', '')}",
        "next_steps": [
            f"POST /incidents/{incident.incident_id}/assign",
            f"POST /incidents/{incident.incident_id}/update",
            f"GET /runbooks/high-error-rate — follow the playbook"
        ]
    }


@app.post("/incidents/{incident_id}/assign", summary="Assign incident to engineer")
def assign_incident(incident_id: str, assignee: str = "on-call-engineer") -> dict:
    try:
        incident = incident_manager.assign(incident_id, assignee)
        return {"incident": incident.to_dict()}
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.post("/incidents/{incident_id}/update", summary="Update incident status")
def update_incident(
    incident_id: str,
    status: str,
    actor: str = "on-call",
    details: str = ""
) -> dict:
    valid_statuses = ["investigating", "mitigating", "resolved"]
    if status not in valid_statuses:
        raise HTTPException(400, f"Status must be one of: {valid_statuses}")
    try:
        incident = incident_manager.update_status(incident_id, status, actor, details)
        return {"incident": incident.to_dict()}
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.post("/incidents/{incident_id}/resolve", summary="Resolve an incident")
def resolve_incident(incident_id: str, request: IncidentResolveRequest) -> dict:
    try:
        incident = incident_manager.resolve(
            incident_id,
            root_cause=request.root_cause,
            resolution=request.resolution,
            resolved_by=request.resolved_by
        )
        return {
            "incident": incident.to_dict(),
            "message": "Incident resolved. Schedule post-mortem within 24 hours.",
            "postmortem_template": "GET /incidents/postmortem-template"
        }
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.get("/incidents", summary="All incidents")
def list_incidents(active_only: bool = False) -> dict:
    if active_only:
        incidents = incident_manager.get_active_incidents()
    else:
        incidents = incident_manager.get_all_incidents()
    return {"incidents": incidents, "count": len(incidents)}


@app.get("/incidents/postmortem-template", summary="Post-mortem template")
def postmortem_template() -> dict:
    return {
        "template": "Post-Incident Review (Blameless)",
        "sections": {
            "incident_summary": {
                "what": "What failed?",
                "impact": "How many users affected? For how long?",
                "severity": "What was the severity level?",
                "ttd": "Time to Detect (alert fired → engineer aware)",
                "ttm": "Time to Mitigate (aware → service restored)",
                "ttr": "Time to Resolve (aware → root cause fixed)"
            },
            "timeline": {
                "format": "HH:MM UTC — What happened",
                "example": [
                    "14:30 UTC — Deployment v1.1.0 started",
                    "14:32 UTC — Error rate spike detected by alerting",
                    "14:33 UTC — On-call acknowledged alert",
                    "14:38 UTC — Root cause identified (bad migration)",
                    "14:40 UTC — Rollback initiated",
                    "14:42 UTC — Service restored (TTM: 10 minutes)"
                ]
            },
            "root_cause": "What was the underlying technical cause?",
            "contributing_factors": [
                "What made this worse?",
                "What slowed down detection or response?"
            ],
            "what_went_well": [
                "Alert fired before users reported",
                "Rollback completed in < 3 minutes"
            ],
            "action_items": {
                "format": "Owner | Action | Due date",
                "example": [
                    "humayun | Add migration safety check to CI | 2025-06-02",
                    "ali | Add staging DB for migration testing | 2025-06-09"
                ]
            }
        },
        "principle": "Blameless means: focus on SYSTEMS, not PEOPLE. The goal is learning, not punishment."
    }


# ── Capacity Planning ─────────────────────────────────────────

@app.post("/capacity/plan", summary="Run capacity planning assessment")
def capacity_plan(request: CapacityRequest) -> dict:
    """
    Project when each resource will hit its limit.

    Shows: months until limit, monthly projections, recommended actions.
    """
    plan = capacity_planner.run_full_assessment(
        traffic_growth_monthly=request.traffic_growth_monthly,
        current_rps=request.current_rps,
        current_db_gb=request.current_db_gb,
        current_pods=request.current_pods
    )
    return plan


@app.get("/capacity/quick", summary="Quick capacity check with current service state")
def capacity_quick() -> dict:
    """Run capacity check using current service metrics."""
    pod_count = len([p for p in service.pods if p.status == "Running"])
    avg_cpu = sum(p.cpu_pct for p in service.pods) / len(service.pods) if service.pods else 0
    avg_mem = sum(p.memory_mb for p in service.pods) / len(service.pods) if service.pods else 0

    return capacity_planner.run_full_assessment(
        current_pods=pod_count,
        current_db_gb=45.0,  # simulated
    )


# ── Runbooks ──────────────────────────────────────────────────

@app.get("/runbooks", summary="List all runbooks")
def runbooks() -> dict:
    return {"runbooks": list_runbooks()}


@app.get("/runbooks/{runbook_id}", summary="Get runbook")
def runbook(runbook_id: str) -> dict:
    rb = get_runbook(runbook_id)
    if not rb:
        available = [r["id"] for r in list_runbooks()]
        raise HTTPException(404, f"Runbook not found. Available: {available}")
    return rb


# ── Simulated Alerts (based on service state) ────────────────

@app.get("/alerts", summary="Current alert states")
def alerts() -> dict:
    traffic = service.simulate_traffic(200)
    error_rate = traffic["error_rate_pct"]
    p99_ms = traffic["p99_ms"]

    alert_states = [
        {
            "name": "HighErrorRate",
            "severity": "PAGE",
            "state": "firing" if error_rate > 5.0 else "ok",
            "current_value": f"{error_rate}%",
            "threshold": "5%",
            "runbook": "/runbooks/high-error-rate"
        },
        {
            "name": "HighLatencyP99",
            "severity": "PAGE",
            "state": "firing" if p99_ms > 2000 else "ok",
            "current_value": f"{p99_ms}ms",
            "threshold": "2000ms",
            "runbook": "/runbooks/high-latency"
        },
        {
            "name": "PodCrashLoop",
            "severity": "PAGE",
            "state": "firing" if any(p.status not in ("Running", "Pending")
                                     for p in service.pods) else "ok",
            "current_value": f"{sum(1 for p in service.pods if p.status not in ('Running', 'Pending'))} crashing",
            "threshold": "any pod",
            "runbook": "/runbooks/pod-crash"
        }
    ]

    firing = [a for a in alert_states if a["state"] == "firing"]

    return {
        "firing_count": len(firing),
        "alerts": alert_states,
        "service_healthy": len(firing) == 0,
        "tip": "POST /chaos/run/high-error-rate to trigger HighErrorRate alert"
    }


# ── Phase 6 Summary ───────────────────────────────────────────

@app.get("/phase6/summary", summary="Phase 6 learning summary")
def phase6_summary() -> dict:
    return {
        "phase": "Phase 6 — DevOps & Infrastructure",
        "days": {
            "day_46": {
                "topic": "CI/CD Pipelines with GitHub Actions",
                "what_you_built": "4 workflows: CI (lint+test+docker), CD (staging+prod), security scan, PR checks",
                "key_concept": "Every git push triggers automated testing and deployment"
            },
            "day_47": {
                "topic": "Docker & Kubernetes Fundamentals",
                "what_you_built": "7 K8s manifests: namespace, configmap, secret, deployment, service, HPA, ingress",
                "key_concept": "Kubernetes reconciliation loop: desired state → actual state, self-healing"
            },
            "day_48": {
                "topic": "Infrastructure as Code with Terraform",
                "what_you_built": "3 Terraform modules (network, compute, security) + dev/prod environments",
                "key_concept": "terraform plan shows changes before applying — infrastructure as reviewable code"
            },
            "day_49": {
                "topic": "Monitoring, Observability & Alerting",
                "what_you_built": "Metrics registry, structured logging, distributed tracing, health checks, SLO report",
                "key_concept": "Three pillars: metrics (what), logs (why this request), traces (how it flowed)"
            },
            "day_50": {
                "topic": "Production Operations Simulation (Capstone)",
                "what_you_built": "Deployment pipeline, chaos engine, incident manager, capacity planner, runbooks",
                "key_concept": "Production operations is the discipline of running software reliably at scale"
            }
        },
        "next_phase": "Phase 7 — Full Stack Integration & Portfolio Projects (Days 51-70)"
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": service.status.value,
        "version": service.current_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "day": "Day 50 — Production Operations Simulation"
    }


@app.get("/")
def root() -> dict:
    return {
        "name": "Production Operations Simulator",
        "day": "Day 50 — Phase 6 Capstone",
        "docs": "/docs",
        "scenario": {
            "1_deploy": "POST /deployment/deploy",
            "2_inject_failure": "POST /chaos/run/high-error-rate",
            "3_check_alerts": "GET /alerts",
            "4_open_incident": "POST /incidents/open",
            "5_rollback": "POST /deployment/rollback",
            "6_resolve": "POST /incidents/{id}/resolve",
            "7_capacity": "GET /capacity/quick",
            "8_runbook": "GET /runbooks/high-error-rate"
        }
    }