from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["dataset_rows"] == 500
    assert data["llm_model"] == "qwen3:4b-instruct"


def test_anomaly_endpoint():
    response = client.get("/anomalies")

    assert response.status_code == 200

    data = response.json()

    assert data["resolution_time_anomalies"]["anomaly_count"] == 21
    assert data["weekly_resolution_time_anomalies"]["anomaly_count"] == 3
    assert data["stale_priority_tickets"]["anomaly_count"] == 80
    assert data["total_anomalies"] == 101


def test_query_endpoint(monkeypatch):
    fake_response = {
        "question": "How many tickets are currently open?",
        "sql": (
            "SELECT COUNT(*) AS open_ticket_count "
            "FROM tickets WHERE status = 'Open';"
        ),
        "explanation": "Counts tickets with status Open.",
        "answer": "There are 111 currently open tickets.",
        "results": [
            {
                "open_ticket_count": 111,
            }
        ],
    }

    monkeypatch.setattr(
        "app.api.routes_query.answer_question",
        lambda question: fake_response,
    )

    response = client.post(
        "/query",
        json={
            "question": "How many tickets are currently open?",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == "There are 111 currently open tickets."
    assert data["results"][0]["open_ticket_count"] == 111