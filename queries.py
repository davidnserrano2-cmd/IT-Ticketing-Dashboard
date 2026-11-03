"""Dashboard reads, kept separate from HTTP routes and presentation."""

from database import read_connection


TICKET_COLUMNS = """
    SELECT t.ticket_id, t.title, t.description, t.status, t.priority,
           t.created_at, t.resolved_at, t.closed_at,
           c.category_name, r.full_name AS requester,
           a.full_name AS technician
    FROM public.tickets t
    LEFT JOIN public.categories c ON c.category_id = t.category_id
    LEFT JOIN public.users r ON r.user_id = t.requester_id
    LEFT JOIN public.users a ON a.user_id = t.assigned_to
"""


def ticket_filters(q="", status="", priority=""):
    """User input is always bound as a value, never interpolated into SQL."""
    clauses, values = [], []
    q = q.strip()
    if q:
        # Treat percent and underscore as literal characters, not wildcards.
        term = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        clauses.append("(t.title ILIKE %s OR t.description ILIKE %s OR t.ticket_id::text = %s)")
        values.extend((term, term, q.removeprefix("#")))
    if status:
        clauses.append("t.status = %s")
        values.append(status)
    if priority:
        clauses.append("t.priority = %s")
        values.append(priority)
    return (" WHERE " + " AND ".join(clauses) if clauses else ""), values


def get_tickets(q="", status="", priority="", page=1, page_size=25):
    where, values = ticket_filters(q, status, priority)
    with read_connection() as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        total = connection.execute(
            "SELECT count(*) AS count FROM public.tickets t" + where, values
        ).fetchone()["count"]
        tickets = connection.execute(
            TICKET_COLUMNS + where + " ORDER BY t.created_at DESC, t.ticket_id DESC LIMIT %s OFFSET %s",
            [*values, page_size, (page - 1) * page_size],
        ).fetchall()
        statuses = connection.execute("SELECT DISTINCT status FROM public.tickets ORDER BY status").fetchall()
        priorities = connection.execute("SELECT DISTINCT priority FROM public.tickets ORDER BY priority").fetchall()
    return {"tickets": tickets, "total": total, "page": page, "page_size": page_size,
            "pages": max(1, (total + page_size - 1) // page_size),
            "statuses": [row["status"] for row in statuses],
            "priorities": [row["priority"] for row in priorities]}


def get_ticket(ticket_id, history_page=1):
    with read_connection() as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        ticket = connection.execute(TICKET_COLUMNS + " WHERE t.ticket_id = %s", (ticket_id,)).fetchone()
        if ticket is None:
            return None
        count = connection.execute(
            "SELECT count(*) AS count FROM public.ticket_history WHERE ticket_id = %s", (ticket_id,)
        ).fetchone()["count"]
        history = connection.execute(
            "SELECT h.history_id, h.action, h.old_value, h.new_value, h.notes, h.changed_at, "
            "u.full_name AS changed_by FROM public.ticket_history h "
            "LEFT JOIN public.users u ON u.user_id = h.changed_by "
            "WHERE h.ticket_id = %s ORDER BY h.changed_at DESC, h.history_id DESC LIMIT 50 OFFSET %s",
            (ticket_id, (history_page - 1) * 50),
        ).fetchall()
    return {"ticket": ticket, "history": history, "history_total": count,
            "history_page": history_page, "history_pages": max(1, (count + 49) // 50)}


def get_overview():
    with read_connection() as connection:
        # A consistent snapshot keeps cards and charts aligned during n8n updates.
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        statuses = connection.execute(
            "SELECT status AS label, count(*) AS count FROM public.tickets "
            "GROUP BY status ORDER BY status"
        ).fetchall()
        priorities = connection.execute(
            "SELECT priority AS label, count(*) AS count FROM public.tickets "
            "GROUP BY priority ORDER BY priority"
        ).fetchall()
        recent = connection.execute(
            "SELECT t.ticket_id, t.title, t.status, t.priority, t.created_at, "
            "c.category_name, u.full_name AS technician "
            "FROM public.tickets t "
            "LEFT JOIN public.categories c ON c.category_id = t.category_id "
            "LEFT JOIN public.users u ON u.user_id = t.assigned_to "
            "ORDER BY t.created_at DESC, t.ticket_id DESC LIMIT 10"
        ).fetchall()
    by_status = {row["label"]: row["count"] for row in statuses}
    return {
        "total": sum(by_status.values()),
        "open": by_status.get("Open", 0),
        "in_progress": by_status.get("In Progress", 0),
        "resolved": by_status.get("Resolved", 0),
        "statuses": statuses,
        "priorities": priorities,
        "recent": recent,
    }
