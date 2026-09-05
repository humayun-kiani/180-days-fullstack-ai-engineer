# app/runbooks/library.py
# Runbook library — operational playbooks for common failures

RUNBOOKS = {
    "high-error-rate": {
        "id": "high-error-rate",
        "title": "High Error Rate",
        "alert": "HighErrorRate",
        "severity": "PAGE",
        "description": "HTTP error rate exceeds 5% threshold",
        "estimated_resolution_minutes": 15,
        "steps": [
            {
                "step": 1,
                "title": "Acknowledge the alert",
                "action": "Acknowledge in PagerDuty. Post in #incidents: '[SEV-2] High error rate on task-api'",
                "command": None,
                "expected_outcome": "Team is aware, no duplicate response"
            },
            {
                "step": 2,
                "title": "Check current error rate",
                "action": "Open the metrics dashboard and note current error rate and when it started",
                "command": "GET /metrics/summary → look at error_rate_pct",
                "expected_outcome": "Know the current rate (e.g., 4.2%) and start time"
            },
            {
                "step": 3,
                "title": "Check for recent deployments",
                "action": "Look at deployment history for the past 30 minutes",
                "command": "GET /deployment/history",
                "expected_outcome": "Identify if a deploy coincides with the error spike"
            },
            {
                "step": 4,
                "title": "Check error logs",
                "action": "Find the specific error messages",
                "command": "GET /logs?level=ERROR&limit=20",
                "expected_outcome": "Understand what is actually failing"
            },
            {
                "step": 5,
                "title": "Decide: rollback or fix forward?",
                "action": (
                    "If errors started with a deployment AND rollback is safe: rollback. "
                    "If not deployment-related: investigate root cause first."
                ),
                "command": "POST /deployment/rollback  (if deployment-related)",
                "expected_outcome": "Error rate returns to < 0.5% within 3 minutes of rollback"
            },
            {
                "step": 6,
                "title": "Verify resolution",
                "action": "Monitor error rate for 5 minutes post-mitigation",
                "command": "GET /metrics/summary (every 30 seconds)",
                "expected_outcome": "Error rate < 0.5% sustained for 5 minutes"
            },
            {
                "step": 7,
                "title": "Write incident report",
                "action": "Document timeline, root cause, and fix",
                "command": "POST /incidents/{id}/resolve",
                "expected_outcome": "Incident closed, post-mortem scheduled"
            }
        ],
        "escalation": {
            "15_minutes": "Wake tech lead if not resolved",
            "30_minutes": "Wake VP Engineering, notify customer success",
            "60_minutes": "Executive escalation, consider maintenance page"
        }
    },

    "high-latency": {
        "id": "high-latency",
        "title": "High p99 Latency",
        "alert": "HighLatencyP99",
        "severity": "PAGE",
        "description": "p99 request latency exceeds 2000ms",
        "estimated_resolution_minutes": 20,
        "steps": [
            {
                "step": 1,
                "title": "Check current latency",
                "action": "Get p50/p95/p99 latency breakdown",
                "command": "GET /metrics/summary → look at p99_latency_ms",
                "expected_outcome": "Know which percentile is affected"
            },
            {
                "step": 2,
                "title": "Check pod CPU/memory",
                "action": "High CPU can cause latency spikes",
                "command": "GET /service/status",
                "expected_outcome": "Identify if pods are resource-constrained"
            },
            {
                "step": 3,
                "title": "Check traces for slow operations",
                "action": "Look at trace waterfall to find the slow span",
                "command": "GET /traces → find traces with duration > 2000ms",
                "expected_outcome": "Identify which operation (DB, external API, etc.) is slow"
            },
            {
                "step": 4,
                "title": "Scale up if CPU/memory constrained",
                "action": "Add more pods to spread load",
                "command": "kubectl scale deployment task-api --replicas=5",
                "expected_outcome": "p99 latency drops within 2 minutes"
            },
            {
                "step": 5,
                "title": "Check for slow DB queries",
                "action": "Look for N+1 queries or missing indexes",
                "command": "GET /logs?level=WARNING (look for slow_query events)",
                "expected_outcome": "Identify specific slow queries"
            }
        ],
        "escalation": {
            "20_minutes": "Wake tech lead",
            "45_minutes": "Consider enabling rate limiting to protect DB"
        }
    },

    "pod-crash": {
        "id": "pod-crash",
        "title": "Pod CrashLoopBackOff",
        "alert": "PodCrashLoop",
        "severity": "PAGE",
        "description": "One or more pods are in CrashLoopBackOff state",
        "estimated_resolution_minutes": 10,
        "steps": [
            {
                "step": 1,
                "title": "Identify crashing pod",
                "action": "Find which pods are crashing",
                "command": "kubectl get pods -n task-api | grep -v Running",
                "expected_outcome": "Know exactly which pod(s) are crashing"
            },
            {
                "step": 2,
                "title": "Check crash logs",
                "action": "Get logs from the crashed container",
                "command": "kubectl logs <pod-name> -n task-api --previous",
                "expected_outcome": "See the error that caused the crash"
            },
            {
                "step": 3,
                "title": "Check if new deployment caused it",
                "action": "Compare pod version with previous healthy version",
                "command": "GET /deployment/history",
                "expected_outcome": "Determine if crash is version-related"
            },
            {
                "step": 4,
                "title": "Rollback if deployment caused it",
                "action": "Revert to last known good version",
                "command": "kubectl rollout undo deployment/task-api -n task-api",
                "expected_outcome": "Pods restart with previous version and stop crashing"
            }
        ],
        "escalation": {
            "10_minutes": "Wake tech lead if > 50% pods crashing",
            "20_minutes": "Consider full service failover"
        }
    }
}


def get_runbook(runbook_id: str) -> dict | None:
    return RUNBOOKS.get(runbook_id)


def list_runbooks() -> list[dict]:
    return [
        {
            "id": k,
            "title": v["title"],
            "alert": v["alert"],
            "severity": v["severity"],
            "estimated_resolution_minutes": v["estimated_resolution_minutes"]
        }
        for k, v in RUNBOOKS.items()
    ]