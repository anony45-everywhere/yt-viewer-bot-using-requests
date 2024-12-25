import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_create_view_task():
    response = client.post(
        "/view",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "num_views": 1}
    )
    assert response.status_code == 200
    assert "task_id" in response.json()

def test_invalid_view_count():
    response = client.post(
        "/view",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "num_views": 11}
    )
    assert response.status_code == 400

def test_invalid_url():
    response = client.post(
        "/view",
        json={"url": "https://invalid-url.com", "num_views": 1}
    )
    assert response.status_code == 200  # Task is created
    task_id = response.json()["task_id"]
    
    # Check if task status is failed
    response = client.get(f"/status/{task_id}")
    assert response.json()["status"] == "failed"

def test_get_tasks():
    response = client.get("/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), dict) 