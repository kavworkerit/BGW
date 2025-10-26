# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BGW (Board Games Watcher) is a local monitoring system for board game releases, pre-orders, and discounts from Russian online stores. It's a full-stack application with a FastAPI backend, React frontend, and comprehensive monitoring infrastructure.

## Technology Stack

- **Backend**: FastAPI (Python 3.11+) with SQLAlchemy 2.0
- **Frontend**: React 18 + TypeScript with Ant Design
- **Database**: PostgreSQL 15 + TimescaleDB for time-series data
- **Task Queue**: Celery with Redis broker
- **Storage**: MinIO (S3-compatible)
- **Monitoring**: Prometheus + Grafana
- **Containerization**: Docker + Docker Compose

## Development Commands

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev  # Development server on :3000
npm run build  # Production build
npm run lint  # ESLint check
npm run lint:fix  # Auto-fix linting issues
```

### Task Workers
```bash
# Start Celery worker (for background tasks)
celery -A app.celery_app worker -l INFO

# Start Celery beat scheduler (for periodic tasks)
celery -A app.celery_app beat -l INFO
```

### Testing
```bash
cd backend
pytest  # Run all tests
pytest --cov=app  # With coverage
pytest tests/test_agents.py  # Specific module
pytest -m "unit"  # Only unit tests
pytest -m "integration"  # Only integration tests
```

### Docker Development
```bash
# Full stack development
docker-compose up -d

# Rebuild specific service
docker-compose up -d --build api

# View logs
docker-compose logs -f api
docker-compose logs -f worker
```

## Architecture Overview

### Backend Structure
```
backend/app/
├── agents/           # Web scraping agents platform
│   ├── base.py       # Base agent classes (HTMLAgent, RuntimeContext)
│   ├── builtin/      # Store-specific agents (hobbygames, lavkaigr, etc.)
│   └── registry.py   # Agent registry and discovery
├── api/              # FastAPI routers (games, agents, events, etc.)
├── core/             # Configuration, database, security
├── models/           # SQLAlchemy models (Game, Agent, Event, etc.)
├── schemas/          # Pydantic schemas for API
├── services/         # Business logic layer
└── tasks/            # Celery tasks (agents, notifications, cleanup)
```

### Frontend Structure
```
frontend/src/
├── components/       # Reusable components
│   ├── Layout/       # Header, Sidebar navigation
│   ├── RuleBuilder/  # Notification rule builder
│   └── PriceChart/   # Price history visualization
├── pages/            # Route components (Dashboard, Games, etc.)
├── services/         # API service layers
└── store/            # Zustand state management
```

## Key Concepts

### Agent System
The application uses an extensible agent system for web scraping:
- **HTMLAgent**: Base class for HTML parsing agents
- **RuntimeContext**: Provides HTTP session and configuration
- **Built-in agents**: Store-specific implementations in `backend/app/agents/builtin/`
- **Agent Registry**: Dynamic agent discovery and loading

### Event System
- **ListingEvent**: Core data model for game listings (price, availability, etc.)
- **Event kinds**: `release`, `preorder`, `restock`, `sale`
- **Deduplication**: Content hashing to avoid duplicate events

### Notification System
- **Web Push**: VAPID-based browser notifications
- **Telegram**: Bot integration for mobile notifications
- **Rule Engine**: Complex conditional rules for when to trigger notifications

### Data Models
Key SQLAlchemy models in `backend/app/models/`:
- **Game**: Board game information (BGG integration)
- **Agent**: Scraping agent configurations
- **ListingEvent**: Price and availability events
- **NotificationRule**: Notification trigger rules
- **PriceHistory**: Time-series price data (TimescaleDB)

## Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection for Celery
- `S3_*`: MinIO storage configuration
- `OLLAMA_URL`: Optional LLM integration
- `TELEGRAM_*`: Optional Telegram bot integration

### Agent Configuration
Agents are configured via manifests in the `agents/` directory. Each agent specifies:
- Store metadata and URL patterns
- Parsing selectors and extraction rules
- Rate limiting and scheduling

## Common Development Tasks

### Adding a New Store Agent
1. Create new agent file in `backend/app/agents/builtin/newstore.py`
2. Inherit from `HTMLAgent` and implement `parse()` method
3. Add agent to registry
4. Create manifest file in `agents/newstore.yml`
5. Test with `pytest tests/test_agents.py::test_newstore_agent`

### Adding API Endpoints
1. Create Pydantic schemas in `backend/app/schemas/`
2. Add business logic in `backend/app/services/`
3. Create router in `backend/app/api/`
4. Include router in `backend/app/main.py`

### Frontend Component Development
- Use Ant Design components for consistency
- Follow existing file structure in `frontend/src/components/`
- Use Zustand for state management (see `frontend/src/store/`)
- API calls through service layer in `frontend/src/services/`

## Database Management

### Migrations
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Database Reset
```bash
docker-compose down -v
docker-compose up -d postgres
# Wait for postgres to be ready, then:
alembic upgrade head
```

## Monitoring and Debugging

### Application Logs
```bash
docker-compose logs -f api      # API logs
docker-compose logs -f worker   # Background task logs
docker-compose logs -f beat     # Scheduler logs
```

### Prometheus Metrics
- Metrics endpoint: `http://localhost:8000/metrics`
- Grafana dashboard: `http://localhost:3001` (admin/admin)
- Key metrics: `agent_runs_total`, `events_created_total`, `notifications_sent_total`

### Common Issues
- **Agent failures**: Check logs for parsing errors, network issues
- **Database connection**: Ensure postgres is healthy and migrations are applied
- **Redis connection**: Required for Celery task queue
- **MinIO storage**: Check S3 configuration and bucket permissions

## Testing Strategy

### Test Categories
- **Unit tests**: Individual component testing (`@pytest.mark.unit`)
- **Integration tests**: API and database testing (`@pytest.mark.integration`)
- **Agent tests**: Web scraping functionality (`@pytest.mark.agents`)
- **Slow tests**: Full system tests (`@pytest.mark.slow`)

### Test Coverage
Target 80%+ coverage as configured in `pytest.ini`. Coverage reports generated in `htmlcov/`.

## Deployment Notes

### Production Build
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Backup and Restore
- Automated daily backups via Celery beat
- Backups stored in MinIO S3 bucket
- Manual backup through API endpoints in `backend/app/api/export.py`

## Security Considerations

- Local single-user application by design
- API keys and secrets stored in environment variables
- Web scraping respects robots.txt and rate limits
- Data automatically cleaned after 2 years
- VAPID keys auto-generated for Web Push