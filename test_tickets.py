from datetime import datetime, timezone
from contextlib import contextmanager

import psycopg
import pytest

import main
import queries
from test_dashboard import request


def test_search_values_are_bound_and_wildcards_literal():
    attack = "x%' OR 1=1 --_"
    sql, values = queries.ticket_filters(attack, "Open", "High")
    assert attack not in sql
    assert "Open" not in sql
    assert values == ["%x\\%' OR 1=1 --\\_%", "%x\\%' OR 1=1 --\\_%", attack, "Open", "High"]
    assert queries.ticket_filters("#14")[1][-1] == "14"


def test_list_filters_and_pagination_are_passed_to_query(monkeypatch):
    calls = []
    def fake(q, status, priority, page):
        calls.append((q, status, priority, page))
        return {"tickets": [], "total": 26, "page": page, "pages": 2,
                "page_size": 25, "statuses": ["Open"], "priorities": ["High"]}
    monkeypatch.setattr(main, "get_tickets", fake)
    response = request("/tickets?q=laptop&status=Open&priority=High&page=2")
    assert response.status_code == 200
    assert calls == [("laptop", "Open", "High", 2)]
    assert "q=laptop&amp;status=Open&amp;priority=High&amp;page=1" in response.text
    assert "26 matching tickets" in response.text
    assert request("/api/tickets?status=Open").json()["total"] == 26


@pytest.mark.parametrize("path", [
    "/tickets?page=0", "/api/tickets?page=-1", "/tickets/0",
    "/api/tickets/2147483648", "/tickets/1?history_page=0",
    "/api/tickets?q=" + "a" * 201,
])
def test_invalid_inputs_never_query_database(monkeypatch, path):
    def unexpected(*args, **kwargs):
        pytest.fail("Invalid request reached the database query")
    monkeypatch.setattr(main, "get_tickets", unexpected)
    monkeypatch.setattr(main, "get_ticket", unexpected)
    assert request(path).status_code == 422


def test_missing_ticket(monkeypatch):
    monkeypatch.setattr(main, "get_ticket", lambda *args: None)
    for path in ("/tickets/999", "/api/tickets/999"):
        response = request(path)
        assert response.status_code == 404
        assert "Ticket not found" in response.text


def test_detail_and_history_escaping_and_nulls(monkeypatch):
    now = datetime(2026, 11, 3, tzinfo=timezone.utc)
    ticket = {"ticket_id": 14, "title": "<script>title</script>", "description": "Issue\nDetails",
              "status": "Open", "priority": "High", "requester": "Example User",
              "technician": None, "category_name": "Hardware", "created_at": now,
              "resolved_at": None, "closed_at": None}
    event = {"history_id": 1, "action": "Status changed", "changed_by": None,
             "changed_at": now, "old_value": None, "new_value": "Open",
             "notes": "<img src=x onerror=alert(1)>"}
    monkeypatch.setattr(main, "get_ticket", lambda *args: {
        "ticket": ticket, "history": [event], "history_total": 51,
        "history_page": 1, "history_pages": 2,
    })
    response = request("/tickets/14")
    assert response.status_code == 200
    assert "Unassigned" in response.text
    assert "&lt;script&gt;title" in response.text
    assert "&lt;img" in response.text
    assert "<img src=x" not in response.text
    assert "history_page=2" in response.text
    result = request("/api/tickets/14").json()
    assert result["history"][0]["old_value"] is None
    assert result["ticket"]["created_at"].startswith("2026-11-03")


def test_ticket_database_failures_are_sanitized(monkeypatch):
    def fail(*args, **kwargs):
        raise psycopg.OperationalError("SECRET password")
    monkeypatch.setattr(main, "get_ticket", fail)
    monkeypatch.setattr(main, "get_tickets", fail)
    for path in ("/tickets", "/tickets/1", "/api/tickets", "/api/tickets/1"):
        response = request(path)
        assert response.status_code == 503
        assert "SECRET" not in response.text


def test_query_pages_are_bounded_and_ids_are_bound(monkeypatch):
    calls = []
    class Result:
        def fetchone(self):
            return {"count": 26}
        def fetchall(self):
            return []
    class Connection:
        def execute(self, sql, values=None):
            calls.append((sql, values))
            return Result()
    @contextmanager
    def fake_connection():
        yield Connection()
    monkeypatch.setattr(queries, "read_connection", fake_connection)
    result = queries.get_tickets("laptop", "Open", "High", page=2)
    assert result["pages"] == 2
    list_sql, values = calls[2]
    assert "LIMIT %s OFFSET %s" in list_sql
    assert values[-2:] == [25, 25]
    assert "laptop" not in list_sql
    calls.clear()
    queries.get_ticket(14, history_page=2)
    assert calls[1][1] == (14,)
    assert calls[3][1] == (14, 50)


def test_only_read_routes_are_registered():
    for route in main.app.routes:
        if route.path.startswith(("/api/", "/tickets")):
            assert route.methods <= {"GET", "HEAD"}
