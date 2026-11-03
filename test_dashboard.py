import asyncio

import httpx
import psycopg

import main


def request(path):
    async def run():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            return await client.get(path)
    return asyncio.run(run())


def test_empty_dashboard(monkeypatch):
    monkeypatch.setattr(main, "get_overview", lambda: {
        "total": 0, "open": 0, "in_progress": 0, "resolved": 0,
        "statuses": [], "priorities": [], "recent": [],
    })
    response = request("/")
    assert response.status_code == 200
    assert "No tickets yet" in response.text
    assert response.headers["cache-control"] == "no-store"


def test_database_errors_do_not_expose_details(monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("SECRET connection details")
    monkeypatch.setattr(main, "get_overview", unavailable)
    for path in ("/", "/api/overview"):
        response = request(path)
        assert response.status_code == 503
        assert "SECRET" not in response.text


def test_ticket_titles_are_escaped(monkeypatch):
    monkeypatch.setattr(main, "get_overview", lambda: {
        "total": 1, "open": 1, "in_progress": 0, "resolved": 0,
        "statuses": [{"label": "Open", "count": 1}],
        "priorities": [{"label": "High", "count": 1}],
        "recent": [{"ticket_id": 1, "title": "<script>alert(1)</script>",
                    "status": "Open", "priority": "High", "created_at": None,
                    "category_name": None, "technician": None}],
    })
    response = request("/")
    assert response.status_code == 200
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;" in response.text
