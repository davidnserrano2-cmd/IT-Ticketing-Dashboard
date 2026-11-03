import pytest

import database


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch):
    # Tests never read a real .env or connect to PostgreSQL.
    monkeypatch.setattr(database, "load_dotenv", lambda *args, **kwargs: None)
    for name in ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"):
        monkeypatch.delenv(name, raising=False)


def test_missing_password_stops_before_connection():
    with pytest.raises(ValueError, match="DB_PASSWORD"):
        database.connection_settings()


@pytest.mark.parametrize("port", ["abc", "0", "65536"])
def test_invalid_port(monkeypatch, port):
    monkeypatch.setenv("DB_PASSWORD", "test-only")
    monkeypatch.setenv("DB_PORT", port)
    with pytest.raises(ValueError, match="DB_PORT"):
        database.connection_settings()


def test_password_is_passed_literally_and_reads_are_bounded(monkeypatch):
    password = "test:@/$?literal"
    monkeypatch.setenv("DB_PASSWORD", password)
    settings = database.connection_settings()
    assert settings["password"] == password
    assert settings["user"] == "ticket_dashboard_reader"
    assert settings["connect_timeout"] == 5
    assert "default_transaction_read_only=on" in settings["options"]
    assert "statement_timeout=5000" in settings["options"]
