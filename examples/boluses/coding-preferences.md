---
id: coding-preferences
title: Coding Preferences
active: true
render: reference
priority: 30
summary: Stack choices, tooling conventions, and style preferences for this project.
tags:
  - technical
  - preferences
created: '2024-01-01'
updated: '2024-01-01'
---

**Language and runtime:** Python 3.12+ with uv for package management. Type annotations required. No walrus operator — prefer explicit assignments for readability.

**Web framework:** FastAPI for REST APIs. Pydantic v2 for request/response models. No Django.

**Testing:** pytest only. No unittest. Test files mirror source structure. Fixtures in conftest.py.

**Database:** SQLite for local/embedded storage. PostgreSQL for production multi-tenant. No ORM — raw SQL with parameterized queries.

**Frontend:** SvelteKit for dashboards. Plain TypeScript, no React.

**Formatting:** ruff for linting and formatting. Line length 100. No black.
