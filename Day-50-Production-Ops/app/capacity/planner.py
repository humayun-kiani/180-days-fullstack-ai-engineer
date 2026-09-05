# app/capacity/planner.py
# Capacity planning and resource projection

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class CapacityProjection:
    resource_name: str
    current_value: float
    unit: str
    growth_rate_monthly: float
    limit: float
    months_to_limit: Optional[int]
    status: str          # healthy, warning, critical
    projections: list[dict]
    recommendation: str

    def to_dict(self) -> dict:
        return {
            "resource": self.resource_name,
            "current": f"{self.current_value:.1f} {self.unit}",
            "limit": f"{self.limit:.1f} {self.unit}",
            "current_pct": round(self.current_value / self.limit * 100, 1),
            "growth_rate_monthly": f"{self.growth_rate_monthly * 100:.1f}%",
            "months_to_limit": self.months_to_limit,
            "status": self.status,
            "recommendation": self.recommendation,
            "projections": self.projections[:6]  # show 6 months
        }


def project_resource(
    resource_name: str,
    current_value: float,
    unit: str,
    growth_rate_monthly: float,
    limit: float,
    months_ahead: int = 12
) -> CapacityProjection:
    """Project resource usage and when it will hit limits."""
    projections = []
    value = current_value
    months_to_limit = None

    for month in range(1, months_ahead + 1):
        value = value * (1 + growth_rate_monthly)
        pct = value / limit * 100

        projections.append({
            "month": month,
            "value": round(value, 2),
            "unit": unit,
            "pct_of_limit": round(pct, 1),
            "status": "critical" if pct > 90 else "warning" if pct > 75 else "ok"
        })

        if value >= limit and months_to_limit is None:
            months_to_limit = month

    current_pct = current_value / limit * 100
    if months_to_limit is None:
        status = "healthy"
        recommendation = f"No action needed — {resource_name} will stay below limit for {months_ahead}+ months"
    elif months_to_limit <= 2:
        status = "critical"
        recommendation = f"URGENT: {resource_name} will hit limit in {months_to_limit} months — provision immediately"
    elif months_to_limit <= 4:
        status = "warning"
        recommendation = f"Plan now: {resource_name} will hit limit in {months_to_limit} months — start procurement"
    else:
        status = "healthy"
        recommendation = f"Monitor: {resource_name} will hit limit in {months_to_limit} months"

    return CapacityProjection(
        resource_name=resource_name,
        current_value=current_value,
        unit=unit,
        growth_rate_monthly=growth_rate_monthly,
        limit=limit,
        months_to_limit=months_to_limit,
        status=status,
        projections=projections,
        recommendation=recommendation
    )


class CapacityPlanner:
    """
    Multi-resource capacity planning for a production service.

    Projects when each resource will hit its limit given current growth.
    """

    def run_full_assessment(
        self,
        traffic_growth_monthly: float = 0.10,
        current_rps: float = 150.0,
        current_db_gb: float = 45.0,
        current_memory_mb: float = 110.0,
        current_pods: int = 3
    ) -> dict:
        """
        Run capacity assessment for all key resources.

        Args:
            traffic_growth_monthly: Expected traffic growth per month (0.10 = 10%)
            current_rps: Current requests per second
            current_db_gb: Current database size in GB
            current_memory_mb: Current pod memory usage in MB
            current_pods: Current pod count
        """
        resources = []

        # API traffic
        resources.append(project_resource(
            "API Traffic",
            current_value=current_rps,
            unit="RPS",
            growth_rate_monthly=traffic_growth_monthly,
            limit=1000.0,    # single node max RPS
            months_ahead=12
        ))

        # Database storage
        db_growth = traffic_growth_monthly * 0.8  # data grows slightly slower than traffic
        resources.append(project_resource(
            "Database Storage",
            current_value=current_db_gb,
            unit="GB",
            growth_rate_monthly=db_growth,
            limit=500.0,      # 500GB limit before sharding needed
            months_ahead=12
        ))

        # Pod memory
        resources.append(project_resource(
            "Pod Memory",
            current_value=current_memory_mb,
            unit="MB",
            growth_rate_monthly=traffic_growth_monthly * 0.5,  # memory grows slower
            limit=512.0,      # current pod memory limit
            months_ahead=12
        ))

        # Compute capacity (pods × capacity per pod)
        pod_capacity = current_pods * (1000 / current_pods)  # current pods handle current traffic
        resources.append(project_resource(
            "Compute Capacity",
            current_value=current_rps,
            unit="RPS",
            growth_rate_monthly=traffic_growth_monthly,
            limit=current_pods * 350.0,   # each pod handles ~350 RPS
            months_ahead=12
        ))

        # Find most critical resource
        critical_resources = [r for r in resources if r.status == "critical"]
        warning_resources = [r for r in resources if r.status == "warning"]

        overall_status = (
            "critical" if critical_resources else
            "warning" if warning_resources else
            "healthy"
        )

        # Determine when to scale
        urgent_actions = []
        if current_rps / (current_pods * 350) > 0.7:
            urgent_actions.append(f"Scale pods: currently at {current_rps / (current_pods * 350) * 100:.0f}% capacity")

        soonest_limit = min(
            (r.months_to_limit for r in resources if r.months_to_limit),
            default=None
        )

        return {
            "overall_status": overall_status,
            "assessment_assumptions": {
                "traffic_growth_monthly": f"{traffic_growth_monthly * 100:.0f}%",
                "current_rps": current_rps,
                "current_pods": current_pods
            },
            "resources": [r.to_dict() for r in resources],
            "urgent_actions": urgent_actions,
            "soonest_limit_months": soonest_limit,
            "recommended_pod_count": max(
                current_pods,
                math.ceil(current_rps * (1 + traffic_growth_monthly * 3) / 350)
            ),
            "summary": (
                f"Most constrained resource hits limit in {soonest_limit} months"
                if soonest_limit else
                "All resources healthy for 12+ months"
            )
        }


# Global planner
capacity_planner = CapacityPlanner()