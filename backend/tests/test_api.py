"""Automated tests for FastAPI REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.store import repository_store


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "RepoMind AI API"
    assert data["docs"] == "/docs"


def test_analyze_empty_url(client: TestClient) -> None:
    response = client.post("/api/repositories/analyze", json={"url": "   "})
    assert response.status_code == 400


def test_analyze_invalid_github_url(client: TestClient) -> None:
    response = client.post("/api/repositories/analyze", json={"url": "https://gitlab.com/invalid/repo"})
    assert response.status_code == 400
    assert "Only github.com" in response.json()["detail"]


def test_analyze_with_repo_url_key(client: TestClient) -> None:
    response = client.post("/api/repositories/analyze", json={"repo_url": "https://github.com/prince-builds/ai-study-copilot"})
    assert response.status_code == 200
    assert response.json()["repo_id"] == "prince-builds-ai-study-copilot"


def test_get_nonexistent_repo_endpoints(client: TestClient) -> None:
    non_existent = "non-existent-repo"
    
    assert client.get(f"/api/repositories/{non_existent}/overview").status_code == 404
    assert client.get(f"/api/repositories/{non_existent}/architecture").status_code == 404
    assert client.get(f"/api/repositories/{non_existent}/files").status_code == 404
    assert client.post(f"/api/repositories/{non_existent}/files/analyze", json={"file_path": "test.py"}).status_code == 404
    assert client.post(f"/api/repositories/{non_existent}/qa", json={"question": "hello"}).status_code == 404
    assert client.post(f"/api/repositories/{non_existent}/interview", json={"prompt": "hello"}).status_code == 404
    assert client.post(f"/api/repositories/{non_existent}/clear").status_code == 404


def test_analyze_and_query_repository(client: TestClient) -> None:
    # Uses already-cached prince-builds/ai-study-copilot in repomind/data/repos
    response = client.post("/api/repositories/analyze", json={"url": "https://github.com/prince-builds/ai-study-copilot"})
    assert response.status_code == 200
    data = response.json()
    assert data["repo_id"] == "prince-builds-ai-study-copilot"
    assert data["repo_name"] == "prince-builds/ai-study-copilot"
    assert data["owner"] == "prince-builds"
    assert data["repo"] == "ai-study-copilot"
    assert data["status"] == "ready"
    assert data["parsed_files_count"] > 0
    assert data["chunks_count"] > 0
    assert data["vectors_indexed"] > 0

    # Test GET Overview
    overview_resp = client.get("/api/repositories/prince-builds-ai-study-copilot/overview")
    assert overview_resp.status_code == 200
    overview_data = overview_resp.json()
    assert overview_data["repo_id"] == "prince-builds-ai-study-copilot"
    assert "metrics" in overview_data
    assert overview_data["metrics"]["files_indexed"] > 0
    assert overview_data["metrics"]["chunks_created"] > 0
    assert len(overview_data["chunk_previews"]) > 0

    # Test GET Architecture
    arch_resp = client.get("/api/repositories/prince-builds-ai-study-copilot/architecture")
    assert arch_resp.status_code == 200
    arch_data = arch_resp.json()
    assert arch_data["repo_id"] == "prince-builds-ai-study-copilot"
    assert "dot_graph" in arch_data
    assert arch_data["files_analyzed"] > 0

    # Test GET Files
    files_resp = client.get("/api/repositories/prince-builds-ai-study-copilot/files")
    assert files_resp.status_code == 200
    files_data = files_resp.json()
    assert files_data["repo_id"] == "prince-builds-ai-study-copilot"
    assert files_data["total_files"] > 0
    assert "tree" in files_data

    # Test GET Files with query filter
    filtered_resp = client.get("/api/repositories/prince-builds-ai-study-copilot/files?query=app.py")
    assert filtered_resp.status_code == 200
    filtered_data = filtered_resp.json()
    assert filtered_data["filtered_count"] >= 1
    assert any("app.py" in p for p in filtered_data["paths"])

    # Test POST Clear (in-memory only)
    clear_resp = client.post("/api/repositories/prince-builds-ai-study-copilot/clear", json={"delete_disk_cache": False})
    assert clear_resp.status_code == 200
    assert clear_resp.json()["status"] == "cleared"

    # Verify repo is now evicted from active memory
    assert client.get("/api/repositories/prince-builds-ai-study-copilot/overview").status_code == 404
