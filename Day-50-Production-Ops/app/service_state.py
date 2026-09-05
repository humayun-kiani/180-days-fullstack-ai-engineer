# app/service_state.py
# Simulated service state — the "production environment"

import time
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "unhealthy"
    DEPLOYING = "deploying"
    ROLLING_BACK = "rolling_back"


@dataclass
class PodState:
    pod_id: str
    version: str
    status: str       # Running, Pending, CrashLoopBackOff, Terminating
    node: str
    cpu_pct: float
    memory_mb: float
    restarts: int = 0
    started_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "pod_id": self.pod_id,
            "version": self.version,
            "status": self.status,
            "node": self.node,
            "cpu_pct": round(self.cpu_pct, 1),
            "memory_mb": round(self.memory_mb, 1),
            "restarts": self.restarts,
            "age_seconds": round(time.time() - self.started_at, 0)
        }


class ServiceState:
    """
    Simulates the state of a production service.

    Tracks pods, versions, metrics, and failures.
    """

    def __init__(self):
        self.current_version = "1.0.0"
        self.desired_replicas = 3
        self.pods: list[PodState] = []
        self.status = ServiceStatus.HEALTHY

        # Simulated metrics
        self._base_error_rate = 0.001     # 0.1% baseline
        self._base_latency_p99 = 145.0    # 145ms baseline
        self._error_rate = self._base_error_rate
        self._latency_p99 = self._base_latency_p99
        self._total_requests = 0
        self._total_errors = 0

        # Chaos state
        self._chaos_active = False
        self._chaos_type = None

        # Initialize pods
        self._init_pods()

    def _init_pods(self):
        nodes = ["node-1", "node-2", "node-3"]
        self.pods = [
            PodState(
                pod_id=f"task-api-{i+1:03d}",
                version=self.current_version,
                status="Running",
                node=nodes[i % len(nodes)],
                cpu_pct=random.uniform(15, 35),
                memory_mb=random.uniform(80, 120)
            )
            for i in range(self.desired_replicas)
        ]

    def simulate_traffic(self, requests: int = 100) -> dict:
        """Simulate N requests and return metrics."""
        errors = 0
        latencies = []

        for _ in range(requests):
            # Determine if this request errors
            if self._chaos_active and self._chaos_type == "high_error_rate":
                error_chance = 0.30
            elif self.status == ServiceStatus.DOWN:
                error_chance = 0.95
            elif self.status == ServiceStatus.DEGRADED:
                error_chance = 0.10
            else:
                error_chance = self._error_rate

            is_error = random.random() < error_chance
            if is_error:
                errors += 1

            # Determine latency
            if self._chaos_active and self._chaos_type == "high_latency":
                base = 2500
            elif self.status == ServiceStatus.DEGRADED:
                base = 800
            else:
                base = self._base_latency_p99 * 0.5

            latency = base + random.uniform(-20, 50)
            latencies.append(latency)

        self._total_requests += requests
        self._total_errors += errors

        latencies_sorted = sorted(latencies)
        p99_idx = int(len(latencies) * 0.99)
        p50_idx = int(len(latencies) * 0.50)

        return {
            "requests": requests,
            "errors": errors,
            "error_rate_pct": round(errors / requests * 100, 2),
            "p50_ms": round(latencies_sorted[p50_idx], 1),
            "p99_ms": round(latencies_sorted[p99_idx], 1),
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "overall_error_rate_pct": round(
                self._total_errors / self._total_requests * 100, 3
            ) if self._total_requests > 0 else 0
        }

    def get_pod_status(self) -> list[dict]:
        # Randomly fluctuate CPU/memory for realism
        for pod in self.pods:
            if pod.status == "Running":
                pod.cpu_pct = max(5, pod.cpu_pct + random.uniform(-3, 3))
                pod.memory_mb = max(50, pod.memory_mb + random.uniform(-5, 5))
        return [p.to_dict() for p in self.pods]

    def kill_pod(self, pod_id: str) -> Optional[PodState]:
        pod = next((p for p in self.pods if p.pod_id == pod_id), None)
        if pod:
            pod.status = "Terminating"
        return pod

    def restart_pod(self, pod_id: str) -> Optional[PodState]:
        pod = next((p for p in self.pods if p.pod_id == pod_id), None)
        if pod:
            pod.status = "Running"
            pod.restarts += 1
            pod.started_at = time.time()
            pod.cpu_pct = random.uniform(15, 35)
        return pod

    def start_chaos(self, chaos_type: str):
        self._chaos_active = True
        self._chaos_type = chaos_type

    def stop_chaos(self):
        self._chaos_active = False
        self._chaos_type = None

    def set_version(self, version: str):
        self.current_version = version
        for pod in self.pods:
            pod.version = version

    @property
    def error_rate(self) -> float:
        if self._chaos_active and self._chaos_type == "high_error_rate":
            return 0.30
        if self.status == ServiceStatus.DEGRADED:
            return 0.10
        return self._base_error_rate

    @property
    def latency_p99_ms(self) -> float:
        if self._chaos_active and self._chaos_type == "high_latency":
            return 2500.0
        if self.status == ServiceStatus.DEGRADED:
            return 800.0
        return self._base_latency_p99


# Global service state
service = ServiceState()