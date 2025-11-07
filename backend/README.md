# Backend Structure

## Directory Layout

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config/              # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py      # Pydantic BaseSettings
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic models
│   ├── routes/              # API routes
│   │   ├── __init__.py
│   │   ├── investigation.py # Investigation endpoints
│   │   ├── proposals.py     # Proposal management endpoints
│   │   ├── chat.py          # Chat interface endpoints
│   │   └── audit.py         # Audit log endpoints
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── detective.py     # Revenue leakage detection logic
│   │   ├── agent.py         # PydanticAI agent
│   │   └── sandbox_manager.py # Sandbox management
│   └── tools/               # Utilities and tools
│       ├── __init__.py
│       ├── data_loader.py   # Data loading utilities
│       └── tools.py         # Tool functions for the agent
├── Dockerfile
└── pyproject.toml           # Python dependencies (UV)
```

## Module Descriptions

### Config (`src/config/`)
Centralized configuration management using Pydantic BaseSettings:
- Environment variable loading
- Type validation and defaults
- OpenAI model configuration
- API and CORS settings
- Investigation parameters

### Models (`src/models/`)
Contains Pydantic models for data validation and serialization:
- BillingPlan, Invoice, CreditMemo, ExchangeRate
- Finding, Proposal, AuditLogEntry
- MakeGoodInvoice, AppliedCreditMemo, PlanAmendment

### Routes (`src/routes/`)
FastAPI route handlers organized by feature:
- `investigation.py`: Investigation and finding explanation endpoints
- `proposals.py`: Proposal management (get, apply, rollback)
- `chat.py`: Chat interface with AI agent
- `audit.py`: Audit log and sandbox management

### Services (`src/services/`)
Core business logic:
- `detective.py`: Revenue leakage detection algorithms
- `agent.py`: PydanticAI agent wrapper for AI-powered analysis
- `sandbox_manager.py`: Manages proposal application and audit logging

### Tools (`src/tools/`)
Utilities and helper functions:
- `data_loader.py`: JSON file loading and validation
- `tools.py`: Agent tool functions (query, convert, propose, apply)

## Configuration

### Environment Variables

Create a `.env` file in the project root with:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...


# API Configuration
API_TITLE=Revenue Leakage Detection Agent API
API_VERSION=1.0.0

# CORS Configuration
CORS_ORIGINS=*

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true

# Investigation Settings
INVOICE_DATE_TOLERANCE_DAYS=5
MIN_AMOUNT_THRESHOLD=0.01

# Logging
LOG_LEVEL=INFO
```

### Configurable Parameters

- `OPENAI_MODEL`: Which GPT model to use (default: gpt-5)
- `OPENAI_MAX_RETRIES`: Number of retries for failed API calls
- `INVOICE_DATE_TOLERANCE_DAYS`: Days of tolerance when matching invoice dates
- `MIN_AMOUNT_THRESHOLD`: Minimum amount difference to flag as discrepancy

### Using Settings in Code

```python
from src.config import get_settings

settings = get_settings()

# Access configuration
model_name = settings.openai_model
api_key = settings.openai_api_key
tolerance = settings.invoice_date_tolerance_days
```

## Running the Backend

### With UV (local development)
```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -e .

# Make sure .env file exists with OPENAI_API_KEY
uvicorn src.main:app --reload
```

### With Docker
```bash
docker build -t revenue-agent-backend .
docker run -p 8000:8000 --env-file ../.env revenue-agent-backend
```

### With Docker Compose
```bash
cd ..
docker-compose up backend
```

### With Makefile
```bash
# From project root
make dev-backend    # Local development
make up            # Docker Compose
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/api/health

## Architecture Benefits

1. **Centralized Configuration**: All settings in one place using Pydantic BaseSettings
2. **Type Safety**: Full type checking with Pydantic models
3. **Environment Validation**: Settings are validated on startup
4. **Separation of Concerns**: Clear distinction between routes, business logic, and data models
5. **Testability**: Each module can be tested independently
6. **Maintainability**: Easy to locate and modify specific features
7. **Scalability**: Can add new routes/services without touching existing code
8. **Dependency Injection**: Settings can be overridden for testing
