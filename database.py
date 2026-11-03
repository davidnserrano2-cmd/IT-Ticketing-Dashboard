"""Load local configuration and open short-lived, read-only connections."""

import os
from contextlib import contextmanager
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


def connection_settings():
    # Use this project's .env even when launched from another directory.
    # Explicit environment variables take precedence over the file.
    load_dotenv(Path(__file__).with_name(".env"), interpolate=False)
    password = os.getenv("DB_PASSWORD", "")
    if not password:
        raise ValueError("Set DB_PASSWORD in the dashboard's local .env file.")
    try:
        port = int(os.getenv("DB_PORT", "5432"))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        raise ValueError("DB_PORT must be between 1 and 65535.") from None
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": port,
        "dbname": os.getenv("DB_NAME", "n8n_it_ticketing_system"),
        "user": os.getenv("DB_USER", "ticket_dashboard_reader"),
        "password": password,
        "connect_timeout": 5,
        "application_name": "it_ticket_dashboard",
        "options": "-c default_transaction_read_only=on -c statement_timeout=5000",
        "row_factory": dict_row,
    }


@contextmanager
def read_connection():
    # Separate keyword arguments avoid putting passwords into a URL.
    with psycopg.connect(**connection_settings()) as connection:
        connection.read_only = True
        yield connection


def database_summary():
    """Only metadata and aggregate counts; no personal ticket data."""
    with read_connection() as connection:
        metadata = connection.execute(
            "SELECT current_database() AS database, current_user AS username, "
            "current_setting('transaction_read_only') AS read_only"
        ).fetchone()
        counts = connection.execute(
            "SELECT status, count(*) AS ticket_count FROM public.tickets "
            "GROUP BY status ORDER BY status"
        ).fetchall()
        # Verify SELECT access to the remaining tables without returning records.
        for query in (
            "SELECT user_id FROM public.users LIMIT 0",
            "SELECT category_id FROM public.categories LIMIT 0",
            "SELECT history_id FROM public.ticket_history LIMIT 0",
        ):
            connection.execute(query)
        return {**metadata, "tickets_by_status": counts}
