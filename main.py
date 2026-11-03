"""First milestone: a local API, independent of database availability."""

from pathlib import Path
from typing import Annotated
from urllib.parse import urlencode

import psycopg
from fastapi import FastAPI, Request, Query, Path as PathParameter
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from queries import get_overview, get_tickets, get_ticket

app = FastAPI(title="IT Ticket Dashboard", version="0.1.0")
BASE = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

Search = Annotated[str, Query(max_length=200)]
Filter = Annotated[str, Query(max_length=20)]
Page = Annotated[int, Query(ge=1, le=100000)]
TicketID = Annotated[int, PathParameter(ge=1, le=2147483647)]


def pagination_url(q, status, priority, page):
    return "/tickets?" + urlencode({"q": q, "status": status, "priority": priority, "page": page})


def page_error(request, message, status_code):
    return templates.TemplateResponse(request=request, name="error.html",
                                      context={"message": message}, status_code=status_code)


@app.get("/tickets", response_class=HTMLResponse)
def ticket_list(request: Request, q: Search = "", status: Filter = "", priority: Filter = "", page: Page = 1):
    try:
        data = get_tickets(q, status, priority, page)
    except (psycopg.Error, ValueError):
        return page_error(request, "Database unavailable. Try again after checking your local connection.", 503)
    return templates.TemplateResponse(request=request, name="tickets.html", context={
        **data, "q": q, "status": status, "priority": priority,
        "previous_url": pagination_url(q, status, priority, page - 1),
        "next_url": pagination_url(q, status, priority, page + 1),
    })


@app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
def ticket_detail(request: Request, ticket_id: TicketID, history_page: Page = 1):
    try:
        data = get_ticket(ticket_id, history_page)
    except (psycopg.Error, ValueError):
        return page_error(request, "Database unavailable. Try again after checking your local connection.", 503)
    if data is None:
        return page_error(request, "Ticket not found.", 404)
    return templates.TemplateResponse(request=request, name="ticket.html", context=data)


@app.get("/api/tickets")
def tickets_api(q: Search = "", status: Filter = "", priority: Filter = "", page: Page = 1):
    try:
        return get_tickets(q, status, priority, page)
    except (psycopg.Error, ValueError):
        return JSONResponse({"detail": "Database unavailable."}, status_code=503)


@app.get("/api/tickets/{ticket_id}")
def ticket_api(ticket_id: TicketID, history_page: Page = 1):
    try:
        data = get_ticket(ticket_id, history_page)
    except (psycopg.Error, ValueError):
        return JSONResponse({"detail": "Database unavailable."}, status_code=503)
    if data is None:
        return JSONResponse({"detail": "Ticket not found."}, status_code=404)
    return data


@app.middleware("http")
async def private_responses(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    try:
        overview = get_overview()
    except (psycopg.Error, ValueError):
        return templates.TemplateResponse(
            request=request, name="dashboard.html",
            context={"error": "Database unavailable. Check your local connection settings and restart the app."},
            status_code=503,
        )
    return templates.TemplateResponse(
        request=request, name="dashboard.html", context={"overview": overview}
    )


@app.get("/api/overview")
def overview_api():
    try:
        return get_overview()
    except (psycopg.Error, ValueError):
        return JSONResponse({"detail": "Database unavailable."}, status_code=503)


@app.get("/health")
def health():
    """Application health only; this does not test database connectivity."""
    return {"status": "ok", "database": "not_checked"}
