# Revised MVP diagrams

Each diagram has an editable `.drawio` source and a matching `.svg` export. PNG
exports are included in the downloadable revision pack. The original diagrams
were preserved; these revisions describe the current local learning MVP.

| Diagram | View | Editable source |
| --- | --- | --- |
| Database ERD | [SVG](01_Database_ERD.svg) | [draw.io](01_Database_ERD.drawio) |
| Level 1 data flow | [SVG](02_Level_1_Data_Flow_Diagram.svg) | [draw.io](02_Level_1_Data_Flow_Diagram.drawio) |
| Current architecture | [SVG](03_System_Architecture.svg) | [draw.io](03_System_Architecture.drawio) |
| Employee submission | [SVG](04_Ticket_Creation_Workflow.svg) | [draw.io](04_Ticket_Creation_Workflow.drawio) |
| Ticket status model | [SVG](05_Ticket_State_Diagram.svg) | [draw.io](05_Ticket_State_Diagram.drawio) |
| Creation sequence | [SVG](06_UML_Sequence_Diagram.svg) | [draw.io](06_UML_Sequence_Diagram.drawio) |

## What changed

- Added `ticket_history.notes` and corrected `tickets.first_responded_at`.
- Checked columns, nullability, foreign keys, unique constraints, and allowed values
  through the existing PostgreSQL reader connection. No ticket contents are included.
- Added the read-only FastAPI dashboard and its separate reader account.
- Represented the three supplied n8n workflows and implemented Gmail integration.
- Removed speculative critical-only alerts, Teams/Slack integrations, and retry queues.
- Replaced the earlier prescribed state-transition chart with a verified status-value
  model plus an explicitly illustrative Open → In Progress → Resolved lifecycle.
- Showed Gmail success/error outputs leading to the form confirmation, as visible
  in the supplied creation canvas. A confirmation page is not proof of delivery.

These are documentation models, not workflow exports, migrations, or guarantees
of transaction atomicity, visitor identity, delivery reliability, or concurrency.
