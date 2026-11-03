-- Run in pgAdmin connected to n8n_it_ticketing_system as its administrator.
-- Creates a new account; does not modify ticket data or existing n8n roles.
-- If the role already exists, stop and inspect it before proceeding.
BEGIN;
CREATE ROLE ticket_dashboard_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION;
GRANT CONNECT ON DATABASE n8n_it_ticketing_system TO ticket_dashboard_reader;
GRANT USAGE ON SCHEMA public TO ticket_dashboard_reader;
GRANT SELECT ON TABLE public.users, public.categories, public.tickets, public.ticket_history TO ticket_dashboard_reader;
ALTER ROLE ticket_dashboard_reader SET default_transaction_read_only = on;
ALTER ROLE ticket_dashboard_reader SET statement_timeout = '5s';
COMMIT;
-- Set this account's password locally using pgAdmin's role Properties > Definition.
-- No password is stored in this script. No grants are made on future tables.
