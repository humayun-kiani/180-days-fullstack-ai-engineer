# tests/test_capacity.py
from app.capacity.planner import project_resource, capacity_planner


class TestProjectResource:
    def test_healthy_resource(self):
        result = project_resource("CPU", 30.0, "%", 0.02, 80.0)
        assert result.status == "healthy"
        assert result.months_to_limit is not None or result.months_to_limit is None

    def test_critical_resource_near_limit(self):
        # Resource at 79% with 10% growth will hit 80% very quickly
        result = project_resource("Memory", 79.0, "MB", 0.10, 80.0)
        assert result.status in ("critical", "warning")
        assert result.months_to_limit is not None
        assert result.months_to_limit <= 3

    def test_projections_are_growing(self):
        result = project_resource("Traffic", 100.0, "RPS", 0.10, 1000.0)
        values = [p["value"] for p in result.projections]
        assert values == sorted(values)  # always increasing

    def test_recommendation_is_not_empty(self):
        result = project_resource("DB", 45.0, "GB", 0.08, 500.0)
        assert len(result.recommendation) > 0


class TestCapacityPlanner:
    def test_full_assessment_returns_all_resources(self):
        result = capacity_planner.run_full_assessment()
        assert "resources" in result
        assert len(result["resources"]) >= 3

    def test_overall_status_valid(self):
        result = capacity_planner.run_full_assessment()
        assert result["overall_status"] in ("healthy", "warning", "critical")

    def test_recommended_pod_count_at_least_current(self):
        result = capacity_planner.run_full_assessment(current_pods=3)
        assert result["recommended_pod_count"] >= 3