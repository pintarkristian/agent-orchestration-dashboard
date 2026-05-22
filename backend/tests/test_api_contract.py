from app.main import app
from fastapi.testclient import TestClient


def test_openapi_schema_documents_core_portfolio_endpoints() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    paths = schema["paths"]

    assert "/health" in paths
    assert "/api/agents/planner/run" in paths
    assert "/api/workflows/run" in paths
    assert "/api/workflows" in paths
    assert "/api/workflows/{workflow_id}" in paths
    assert "/api/workflows/{workflow_id}/events" in paths

    assert "post" in paths["/api/workflows/run"]
    assert "get" in paths["/api/workflows/{workflow_id}/events"]
