# app/deployment/pipeline.py
# Deployment pipeline simulation

import time
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.service_state import service, ServiceStatus


class DeploymentStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class DeploymentStep:
    name: str
    status: str = "pending"     # pending, running, passed, failed, skipped
    duration_ms: float = 0.0
    output: str = ""
    started_at: Optional[float] = None
    finished_at: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "duration_ms": round(self.duration_ms, 0),
            "output": self.output[:200] if self.output else ""
        }


@dataclass
class Deployment:
    deployment_id: str
    version: str
    environment: str
    deployed_by: str
    status: DeploymentStatus = DeploymentStatus.PENDING
    steps: list[DeploymentStep] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    previous_version: str = ""
    rollback_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "deployment_id": self.deployment_id,
            "version": self.version,
            "environment": self.environment,
            "deployed_by": self.deployed_by,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "started_at": datetime.fromtimestamp(
                self.started_at, tz=timezone.utc
            ).isoformat(),
            "finished_at": datetime.fromtimestamp(
                self.finished_at, tz=timezone.utc
            ).isoformat() if self.finished_at else None,
            "duration_seconds": round(
                (self.finished_at or time.time()) - self.started_at, 1
            ),
            "previous_version": self.previous_version,
            "rollback_reason": self.rollback_reason
        }


class DeploymentPipeline:
    """
    Simulates the full production deployment pipeline.

    Steps:
    1. Pre-flight checks
    2. Build and push Docker image
    3. Run tests
    4. Security scan
    5. Update Kubernetes deployment
    6. Wait for rollout
    7. Smoke tests
    8. Post-deployment monitoring
    """

    def __init__(self):
        self._history: list[Deployment] = []
        self._deploy_counter = 0

    def _run_step(
        self,
        deployment: Deployment,
        step_name: str,
        duration_ms: float,
        success: bool = True,
        output: str = "",
        failure_output: str = ""
    ) -> DeploymentStep:
        step = DeploymentStep(name=step_name)
        step.status = "running"
        step.started_at = time.time()
        deployment.steps.append(step)

        # Simulate work
        time.sleep(duration_ms / 1000)

        step.finished_at = time.time()
        step.duration_ms = (step.finished_at - step.started_at) * 1000
        step.status = "passed" if success else "failed"
        step.output = output if success else failure_output
        return step

    def deploy(
        self,
        version: str,
        environment: str = "production",
        deployed_by: str = "ci-bot",
        simulate_failure: bool = False
    ) -> Deployment:
        """
        Execute a full deployment pipeline.

        Args:
            version: Docker image tag to deploy
            environment: Target environment
            deployed_by: Who triggered the deployment
            simulate_failure: Whether to simulate a deployment failure
        """
        self._deploy_counter += 1
        deploy_id = f"deploy-{self._deploy_counter:04d}"

        deployment = Deployment(
            deployment_id=deploy_id,
            version=version,
            environment=environment,
            deployed_by=deployed_by,
            previous_version=service.current_version,
            status=DeploymentStatus.RUNNING
        )
        self._history.append(deployment)

        # Mark service as deploying
        service.status = ServiceStatus.DEPLOYING

        print(f"\n  🚀 Deployment {deploy_id}: {version} → {environment}")

        # ── Step 1: Pre-flight checks ──────────────────────────
        self._run_step(
            deployment, "pre_flight_checks", 200,
            success=True,
            output="✅ Error budget: 94% remaining | ✅ No active incidents | ✅ Staging passed"
        )
        print(f"    ✅ Pre-flight checks passed")

        # ── Step 2: Pull image ─────────────────────────────────
        self._run_step(
            deployment, "pull_image", 800,
            success=True,
            output=f"✅ Pulled task-api:{version} from registry | Size: 142MB | No CVEs found"
        )
        print(f"    ✅ Image pulled and scanned")

        # ── Step 3: Run smoke tests on staging ────────────────
        self._run_step(
            deployment, "staging_smoke_tests", 1500,
            success=True,
            output="✅ /health → 200 | ✅ POST /tasks → 201 | ✅ GET /tasks → 200 (8 tests)"
        )
        print(f"    ✅ Staging smoke tests passed")

        # ── Step 4: Rolling update (simulate failure here) ────
        fail_here = simulate_failure and random.random() < 0.7
        self._run_step(
            deployment, "rolling_update", 3000,
            success=not fail_here,
            output="✅ Pod 1/3 updated (healthy) | ✅ Pod 2/3 updated (healthy) | ✅ Pod 3/3 updated",
            failure_output="❌ Pod 1/3 updated | ❌ Pod 2/3 updated (CrashLoopBackOff!) | ⏸ Pod 3/3 paused"
        )

        if fail_here:
            deployment.status = DeploymentStatus.FAILED
            deployment.finished_at = time.time()
            service.status = ServiceStatus.DEGRADED
            print(f"    ❌ Rolling update FAILED — pod in CrashLoopBackOff")
            return deployment

        # Update service version
        service.set_version(version)
        service.status = ServiceStatus.HEALTHY
        print(f"    ✅ Rolling update complete")

        # ── Step 5: Production smoke tests ────────────────────
        self._run_step(
            deployment, "production_smoke_tests", 1000,
            success=True,
            output="✅ /health → 200 (healthy) | ✅ API functional | ✅ Error rate: 0.05%"
        )
        print(f"    ✅ Production smoke tests passed")

        # ── Step 6: 2-minute monitoring window ────────────────
        self._run_step(
            deployment, "post_deploy_monitoring", 500,
            success=True,
            output="✅ Error rate: 0.08% (baseline: 0.1%) | ✅ p99: 142ms | ✅ No alerts firing"
        )
        print(f"    ✅ Post-deploy monitoring window clear")

        deployment.status = DeploymentStatus.SUCCESS
        deployment.finished_at = time.time()
        duration = deployment.finished_at - deployment.started_at
        print(f"\n  ✅ Deployment {deploy_id} complete in {duration:.1f}s")

        return deployment

    def rollback(self, reason: str = "Elevated error rate") -> Optional[dict]:
        """Rollback to the previous deployment."""
        if not self._history:
            return None

        # Find last successful deployment
        last_success = next(
            (d for d in reversed(self._history) if d.status == DeploymentStatus.SUCCESS),
            None
        )
        if not last_success:
            return None

        print(f"\n  🔄 Rolling back to v{last_success.previous_version}...")
        service.status = ServiceStatus.ROLLING_BACK

        # Simulate rollback time
        time.sleep(0.5)

        # Restore previous version
        service.set_version(last_success.previous_version)
        service.status = ServiceStatus.HEALTHY
        service.stop_chaos()

        # Mark last deployment as rolled back
        if self._history:
            self._history[-1].status = DeploymentStatus.ROLLED_BACK
            self._history[-1].rollback_reason = reason

        print(f"  ✅ Rollback complete — running v{last_success.previous_version}")

        return {
            "rolled_back_to": last_success.previous_version,
            "reason": reason,
            "duration_seconds": 2.1
        }

    def get_history(self, limit: int = 10) -> list[dict]:
        return [d.to_dict() for d in reversed(self._history[:limit])]


# Global pipeline instance
pipeline = DeploymentPipeline()