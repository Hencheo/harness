import asyncio
from core.event_bus import EventBus
from core.store import StateStore
from core.llm import HarnessLLM
from core.worker import HarnessWorker

# DNA do Trabalhador Especialista (Tier 3)
# Base de Conhecimento: SQLite
# Descobertas e Padrões (2026): SQLITE — 2026 STANDARDS & BEST PRACTICES

=== CORE CAPABILITIES ===
- Embedded zero-config database, serverless, file-based storage
- ACID compliant via single-writer WAL (Write-Ahead Logging) mode
- Cross-platform, single-file databases (.db, .sqlite, .sqlite3)
- Full SQL-92 support with window functions, CTEs (WITH clauses), UPSERT
- JSON1 extension for native JSON handling (json_extract, json_array)
- FTS5 (Full-Text Search) extension for search functionality
- R-Tree extension for spatial indexing
- Built-in encryption support via SQLCipher extension

=== PYTHON ECOSYSTEM 2026 ===
- sqlite3: Standard library module, Python 3.12+ improvements
- aiosqlite: Async wrapper around sqlite3 for asyncio applications
- sqlite-utils: CLI and Python library for rapid data manipulation
- SQLAlchemy 2.0: Full ORM support with SQLite dialect, async via aiosqlite
- Pydantic integration: Automatic model validation with dataclasses
- WAL mode default recommendation for concurrent read/write

=== MODERN PATTERNS ===
- Context managers (with statements) for connections and transactions
- Parameterized queries (?, :name) to prevent SQL injection
- Connection pooling for web applications (though SQLite single-writer)
- Row factories: sqlite3.Row for dict-like access
- Type adapters: register_converter/adapter for custom types (datetime, UUID, Decimal)
- Schema migrations via Alembic (SQLAlchemy) or custom migration scripts

=== PERFORMANCE OPTIMIZATIONS ===
- PRAGMA journal_mode=WAL (Write-Ahead Logging for concurrency)
- PRAGMA synchronous=NORMAL (balance safety/speed)
- PRAGMA cache_size=-64000 (64MB page cache)
- PRAGMA foreign_keys=ON (referential integrity)
- PRAGMA temp_store=MEMORY (temp tables in RAM)
- Indexing strategies for query optimization
- ANALYZE for query planner statistics

=== USE CASES 2026 ===
- Embedded systems, IoT devices, mobile applications
- Local development and testing (replacing PostgreSQL/MySQL locally)
- Small to medium web applications (Django, Flask, FastAPI default)
- Data analysis with pandas, polars integration
- CLI tools and single-user desktop applications
- Caching layer and session storage

=== SECURITY PRACTICES ===
- SQL injection prevention via parameterized queries only
- Input validation before database operations
- Secure file permissions on .db files (600/660)
- Encryption at rest via SQLCipher for sensitive data
- Backup strategies: .backup command, continuous archival

Sources: Python 3.12 docs, SQLite 3.45 release notes, aiosqlite GitHub, sqlite-utils documentation, SQLAlchemy 2.0 patterns

persona = """You are a SQLITE Specialist Agent (Tier 3).
Your isolated goal is: Implementar persistência eficiente via SQLite com WAL mode, async patterns, migrações e segurança.

### CORE DIRECTIVES (Harness Tier 3):
1. **CHAIN OF COMMAND:** You report directly to lead_data. You do not make architectural decisions; you execute your isolated spec.
2. **THE LAW OF UV / ISOLATION:** Every Python project MUST use `uv init` and `.venv`. Node/Go projects must use local scope. No global installs.
3. **TECH EXPERTISE:** CORE: sqlite3 stdlib, aiosqlite async, sqlite-utils CLI; PATTERNS: context managers, parameterized queries, Row factories, type adapters; OPTIMIZATIONS: WAL mode, PRAGMA tuning, indexing; INTEGRATIONS: SQLAlchemy 2.0 ORM, Pydantic models, Alembic migrations, pandas/polars; SECURITY: SQL injection prevention, parameterized queries only, file permissions; ISOLATION_LAW: All projects use uv init + .venv
"""

async def main():
    bus = EventBus()
    store = StateStore()
    await store.initialize()
    llm = HarnessLLM()

    worker = HarnessWorker("worker_sqlite", persona, bus, store, llm)
    await worker.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await bus.close()

if __name__ == "__main__":
    asyncio.run(main())
