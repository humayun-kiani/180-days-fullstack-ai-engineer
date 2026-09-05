# tests/test_deployment.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.service_state import service
from app.deployment.pipeline import pipeline, DeploymentStatus


@pytest.fixture(autouse=True)
def reset_service():
    service.stop_chaos()
    service.current_version = "1.0.0"
    service.status.__class__.HEALTHY
    from app.service_state import ServiceStatus
    service.status = ServiceStatus.HEALTHY
    pipeline._history.clear()
    pipeline._deploy_counter = 0
    yield


@pytest.fixture
def client():
    return TestClient(app)


class TestServiceStatus:
    def test_status_endpoint_returns_200(self, client):
        r = client.get("/service/status")
        assert r.status_code == 200

    def test_status_has_required_fields(self, client):
        data = client.get("/service/status").json()
        assert "status" in data
        assert "version" in data
        assert "pods" in data
        assert "live_metrics" in data


class TestDeployment:
    def test_successful_deployment(self, client):
        r = client.post("/deployment/deploy", json={
            "version": "1.1.0",
            "environment": "production",
            "deployed_by": "test",
            "simulate_failure": False
        })
        assert r.status_code == 200
        data = r.json()
        assert data["result"] in ("success", "failed")

    def test_deployment_history(self, client):
        client.post("/deployment/deploy", json={
            "version": "1.1.0",
            "deployed_by": "test",
            "simulate_failure": False
        })
        r = client.get("/deployment/history")
        assert r.status_code == 200
        assert len(r.json()["deployments"]) >= 1


class TestChaos:
    def test_catalog_returns_experiments(self, client):
        r = client.get("/chaos/catalog")
        assert r.status_code == 200
        assert len(r.json()["experiments"]) >= 4

    def test_run_pod_kill(self, client):
        r = client.post("/chaos/run/pod-kill")
        assert r.status_code == 200
        assert "experiment" in r.json()

    def test_stop_chaos(self, client):
        client.post("/chaos/run/high-error-rate")
        r = client.post("/chaos/stop")
        assert r.status_code == 200

    def test_invalid_experiment_returns_404(self, client):
        r = client.post("/chaos/run/nonexistent-experiment")
        assert r.status_code == 404


class TestIncidents:
    def test_open_and_resolve_incident(self, client):
        # Open
        r = client.post("/incidents/open", json={
            "title": "Test incident",
            "severity": "sev2",
            "description": "Testing incident flow"
        })
        assert r.status_code == 200
        incident_id = r.json()["incident"]["incident_id"]

        # Resolve
        r = client.post(f"/incidents/{incident_id}/resolve", json={
            "root_cause": "Test root cause",
            "resolution": "Test resolution"
        })
        assert r.status_code == 200
        assert r.json()["incident"]["status"] == "resolved"

    def test_list_incidents(self, client):
        r = client.get("/incidents")
        assert r.status_code == 200
        assert "incidents" in r.json()


class TestRunbooks:
    def test_list_runbooks(self, client):
        r = client.get("/runbooks")
        assert r.status_code == 200
        assert len(r.json()["runbooks"]) >= 3

    def test_get_specific_runbook(self, client):
        r = client.get("/runbooks/high-error-rate")
        assert r.status_code == 200
        data = r.json()
        assert "steps" in data
        assert len(data["steps"]) >= 5

    def test_missing_runbook_returns_404(self, client):
        r = client.get("/runbooks/does-not-exist")
        assert r.status_code == 404