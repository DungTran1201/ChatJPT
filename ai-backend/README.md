# ChatJPT AI Backend

FastAPI backend for the **ChatJPT Japanese Learning Ecosystem**, structured into a 4-layer SOLID/KISS architecture:

```
HTTP / SSE Routers (src/api/v1/)
        │  Depends(...) via src/dependencies.py
        ▼
Application Services (src/services/) ◄──► LLM Orchestration Engine (llm/)
        │
        ▼
Repositories & Unit of Work (src/repositories/ + src/core/database.py)
        │
        ▼
SQLite WAL Database (database/app.db, schema in database/schema.sql)
```

## Directory Layout

```text
ai-backend/
├── database/
│   └── schema.sql                # Canonical 16-table SQLite schema + FTS5 semantic cache
├── llm/                          # Modular LLM Orchestration Engine
│   ├── circuit_breaker.py        # Per-user scoped 429 cooldown tracker
│   ├── message_builder.py        # 20-message sliding window + multimodal attachment context
│   ├── orchestrator.py           # LangGraph workflow & multi-provider failover streamer
│   └── agent.py                  # Backward-compatible facade exporting chat_agent
├── src/
│   ├── api/v1/                   # Thin HTTP/SSE controllers (0 inline SQL / schemas)
│   ├── core/                     # Config, DatabaseManager/UoW, DomainError, Security, Vault, Storage, Telemetry
│   ├── models/v1/                # Internal domain entities & constants
│   ├── repositories/             # SQLite data-access layer (10 domain repositories)
│   ├── schemas/v1/               # Pydantic v2 API request/response DTO contracts
│   ├── services/                 # Business logic, Strategy registries, Facades, Builders
│   ├── dependencies.py           # Composition Root (FastAPI DI wiring)
│   ├── db.py                     # Backward-compatible thin facade over DatabaseManager
│   └── main.py                   # App factory, CORS, Pure ASGI TelemetryMiddleware, DomainError handler
├── tests/
│   ├── unit/                     # Isolated unit tests per refactored module
│   ├── integration/              # End-to-end cross-service pipeline tests (P1..P6)
│   └── test_*.py                 # Legacy regression & API contract tests
├── requirements.txt
└── README.md
```

## Setup & Verification

```powershell
# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run full test suite (legacy + unit + integration)
pytest -q

# Start development server
uvicorn src.main:app --reload --port 8000
```
