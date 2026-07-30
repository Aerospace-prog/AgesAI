# ages_common

Shared Python library for AgesAI microservices. Provides reusable cross-cutting concerns:

- **Auth**: Clerk JWT verification middleware for FastAPI
- **Database**: Async PostgreSQL (asyncpg) and Redis clients
- **Vector**: Qdrant client wrapper
- **Events**: Kafka producer/consumer base classes
- **Observability**: Structured logging (structlog), OpenTelemetry tracing, Prometheus metrics
- **Models**: Shared Pydantic base models
- **Exceptions**: Domain exception hierarchy
- **Config**: Base settings via pydantic-settings

## Installation

```bash
pip install -e .          # Install in editable mode
pip install -e ".[dev]"   # With development dependencies
```

## Usage

```python
from ages_common.config import BaseServiceSettings
from ages_common.database.postgres import PostgresClient
from ages_common.auth.dependencies import require_auth
```
