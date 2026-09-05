# app/chaos/experiments.py
# Chaos engineering experiments

import time
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.service_state import service, ServiceStatus


class ExperimentStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"


@dataclass
class ChaosExperiment:
    experiment_id: str
    name: str
    hypothesis: str
    blast_radius: str      # what is affected
    duration_seconds: float
    status: ExperimentStatus = ExperimentStatus.PENDING
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    observations: list[str] = field(default_factory=list)
    hypothesis_validated: Optional[bool] = None

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "hypothesis": self.hypothesis,
            "blast_radius": self.blast_radius,
            "duration_seconds": self.duration_seconds,
            "status": self.status.value,
            "started_at": datetime.fromtimestamp(
                self.started_at, tz=timezone.utc
            ).isoformat() if self.started_at else None,
            "completed_at": datetime.fromtimestamp(
                self.completed_at, tz=timezone.utc
            ).isoformat() if self.completed_at else None,
            "observations": self.observations,
            "hypothesis_validated": self.hypothesis_validated
        }


EXPERIMENT_CATALOG = [
    {
        "id": "pod-kill",
        "name": "Pod Termination",
        "hypothesis": "When one pod is killed, Kubernetes restarts it within 30s and no requests fail",
        "blast_radius": "1 of 3 pods (33% of capacity)",
        "duration_seconds": 30,
        "chaos_type": "pod_kill"
    },
    {
        "id": "high-error-rate",
        "name": "High Error Rate Injection",
        "hypothesis": "When error rate > 5%, the HighErrorRate alert fires within 35 seconds",
        "blast_radius": "30% of requests will return errors",
        "duration_seconds": 45,
        "chaos_type": "high_error_rate"
    },
    {
        "id": "high-latency",
        "name": "Latency Injection",
        "hypothesis": "When p99 > 2000ms, users experience degraded UX and HighLatencyP99 alert fires",
        "blast_radius": "All requests — 2500ms injected latency",
        "duration_seconds": 30,
        "chaos_type": "high_latency"
    },
    {
        "id": "memory-pressure",
        "name": "Memory Pressure",
        "hypothesis": "When a pod reaches 90% memory, it is OOMKilled and Kubernetes restarts it automatically",
        "blast_radius": "1 pod's memory will be consumed",
        "duration_seconds": 20,
        "chaos_type": "memory_pressure"
    }
]


class ChaosEngine:
    """
    Runs chaos experiments against the simulated service.

    In production: uses tools like Chaos Monkey, LitmusChaos, Gremlin.
    Here: manipulates the ServiceState to simulate failures.
    """

    def __init__(self):
        self._experiments: list[ChaosExperiment] = []
        self._counter = 0

    def run_experiment(self, experiment_id: str) -> ChaosExperiment:
        """Run a specific chaos experiment."""
        catalog_entry = next(
            (e for e in EXPERIMENT_CATALOG if e["id"] == experiment_id),
            None
        )
        if not catalog_entry:
            raise ValueError(f"Unknown experiment: {experiment_id}")

        self._counter += 1
        exp = ChaosExperiment(
            experiment_id=f"chaos-{self._counter:03d}",
            name=catalog_entry["name"],
            hypothesis=catalog_entry["hypothesis"],
            blast_radius=catalog_entry["blast_radius"],
            duration_seconds=catalog_entry["duration_seconds"]
        )
        self._experiments.append(exp)

        exp.status = ExperimentStatus.RUNNING
        exp.started_at = time.time()

        chaos_type = catalog_entry["chaos_type"]
        print(f"\n  💣 Chaos Experiment: {exp.name}")
        print(f"     Hypothesis: {exp.hypothesis}")
        print(f"     Blast radius: {exp.blast_radius}")

        # ── Execute experiment ─────────────────────────────────
        if chaos_type == "pod_kill":
            self._run_pod_kill(exp)
        elif chaos_type == "high_error_rate":
            self._run_high_error_rate(exp)
        elif chaos_type == "high_latency":
            self._run_high_latency(exp)
        elif chaos_type == "memory_pressure":
            self._run_memory_pressure(exp)

        exp.status = ExperimentStatus.COMPLETED
        exp.completed_at = time.time()
        return exp

    def _run_pod_kill(self, exp: ChaosExperiment):
        """Kill one pod and observe recovery."""
        if not service.pods:
            exp.observations.append("No pods to kill")
            exp.hypothesis_validated = False
            return

        target = service.pods[0]
        exp.observations.append(f"Killing pod {target.pod_id} on {target.node}")
        service.kill_pod(target.pod_id)
        print(f"     💀 Killed pod: {target.pod_id}")

        # Wait for "Kubernetes" to restart it
        time.sleep(min(exp.duration_seconds * 0.1, 2))

        # Simulate Kubernetes self-healing
        running_count = sum(1 for p in service.pods if p.status == "Running")
        exp.observations.append(f"Running pods: {running_count}/{service.desired_replicas}")

        # Restart the pod (Kubernetes would do this automatically)
        time.sleep(0.5)
        service.restart_pod(target.pod_id)
        exp.observations.append(f"Pod {target.pod_id} restarted by Kubernetes")

        # Verify traffic continued flowing
        traffic = service.simulate_traffic(50)
        exp.observations.append(
            f"During recovery: error_rate={traffic['error_rate_pct']}%, p99={traffic['p99_ms']}ms"
        )

        exp.hypothesis_validated = traffic['error_rate_pct'] < 5.0
        exp.observations.append(
            "✅ Hypothesis VALIDATED: pod recovered, no significant error rate increase"
            if exp.hypothesis_validated else
            "❌ Hypothesis FAILED: error rate exceeded 5% during pod kill"
        )
        print(f"     {'✅' if exp.hypothesis_validated else '❌'} Hypothesis: {'validated' if exp.hypothesis_validated else 'failed'}")

    def _run_high_error_rate(self, exp: ChaosExperiment):
        """Inject 30% error rate and verify alert fires."""
        exp.observations.append("Injecting 30% error rate into service")
        service.start_chaos("high_error_rate")
        print(f"     🔴 Error rate injection active")

        # Simulate traffic during chaos
        traffic = service.simulate_traffic(100)
        exp.observations.append(
            f"Error rate during chaos: {traffic['error_rate_pct']}% "
            f"(threshold: 5%)"
        )

        # Check if error rate exceeds alert threshold
        alert_would_fire = traffic['error_rate_pct'] > 5.0
        exp.observations.append(
            f"HighErrorRate alert would fire: {alert_would_fire}"
        )

        time.sleep(min(exp.duration_seconds * 0.05, 1))

        # Stop chaos
        service.stop_chaos()
        exp.observations.append("Error rate injection stopped — service recovering")

        # Verify recovery
        time.sleep(0.3)
        recovery_traffic = service.simulate_traffic(50)
        exp.observations.append(
            f"Error rate after recovery: {recovery_traffic['error_rate_pct']}%"
        )

        exp.hypothesis_validated = alert_would_fire and recovery_traffic['error_rate_pct'] < 1.0
        exp.observations.append(
            "✅ Hypothesis VALIDATED: alert fires and service recovers"
            if exp.hypothesis_validated else
            "❌ Hypothesis needs review"
        )
        print(f"     {'✅' if exp.hypothesis_validated else '❌'} Hypothesis: {'validated' if exp.hypothesis_validated else 'failed'}")

    def _run_high_latency(self, exp: ChaosExperiment):
        """Inject high latency and observe impact."""
        exp.observations.append("Injecting 2500ms p99 latency")
        service.start_chaos("high_latency")
        print(f"     🐌 Latency injection active")

        traffic = service.simulate_traffic(100)
        exp.observations.append(
            f"p99 during chaos: {traffic['p99_ms']}ms (SLO threshold: 500ms)"
        )

        latency_above_slo = traffic['p99_ms'] > 500
        exp.observations.append(f"SLO breach: {latency_above_slo}")

        time.sleep(min(exp.duration_seconds * 0.05, 1))

        service.stop_chaos()
        exp.observations.append("Latency injection stopped")

        time.sleep(0.3)
        recovery = service.simulate_traffic(50)
        exp.observations.append(f"p99 after recovery: {recovery['p99_ms']}ms")

        exp.hypothesis_validated = latency_above_slo
        exp.observations.append(
            "✅ Hypothesis VALIDATED: latency injection measurably degraded SLO"
            if exp.hypothesis_validated else
            "❌ Latency did not affect SLO as expected"
        )
        print(f"     {'✅' if exp.hypothesis_validated else '❌'} Hypothesis: {'validated' if exp.hypothesis_validated else 'failed'}")

    def _run_memory_pressure(self, exp: ChaosExperiment):
        """Simulate memory pressure on a pod."""
        if not service.pods:
            exp.hypothesis_validated = False
            return

        target = service.pods[0]
        original_memory = target.memory_mb
        exp.observations.append(f"Pod {target.pod_id}: memory {original_memory:.0f}MB")

        # Ramp up memory
        target.memory_mb = 480.0  # near 512MB limit
        exp.observations.append(f"Memory ramping to {target.memory_mb:.0f}MB (limit: 512MB)")
        print(f"     💾 Memory pressure: {target.memory_mb:.0f}MB / 512MB")

        time.sleep(min(exp.duration_seconds * 0.1, 1))

        # Simulate OOMKill
        target.status = "OOMKilled"
        target.restarts += 1
        exp.observations.append(f"Pod OOMKilled! Restart #{target.restarts}")
        print(f"     ⚡ Pod OOMKilled — Kubernetes restarting...")

        time.sleep(0.5)

        # Restart with fresh memory
        target.status = "Running"
        target.memory_mb = original_memory
        target.started_at = time.time()
        exp.observations.append("Pod restarted with fresh memory state")

        exp.hypothesis_validated = True
        exp.observations.append("✅ Hypothesis VALIDATED: OOMKill triggers automatic restart")
        print(f"     ✅ Hypothesis: validated")

    def get_experiments(self) -> list[dict]:
        return [e.to_dict() for e in self._experiments]

    def get_catalog(self) -> list[dict]:
        return EXPERIMENT_CATALOG


# Global chaos engine
chaos_engine = ChaosEngine()