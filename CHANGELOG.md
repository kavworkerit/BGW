# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Board Games Monitor
- Docker-based deployment with one-click setup
- Agent platform for monitoring multiple sources
- Web Push and Telegram notifications
- Price history tracking with TimescaleDB
- React frontend with Russian UI
- FastAPI backend with automatic API documentation

### Features
- **Agent System**
  - HTML, API, Headless, and Telegram agent types
  - Configurable schedules and rate limiting
  - Import/Export functionality for agents
  - Built-in agents for popular Russian board game stores

- **Game Management**
  - Watchlist with game synonyms
  - BGG ID integration
  - Smart title matching with fuzzy search
  - Tag and publisher support

- **Notifications**
  - Rule-based notification system
  - Web Push with VAPID
  - Telegram bot integration
  - Quiet hours and cooldown settings

- **Price Tracking**
  - Historical price data with TimescaleDB
  - Price charts and analytics
  - Discount detection
  - CSV export functionality

- **Monitoring & Analytics**
  - Dashboard with system overview
  - Agent performance metrics
  - Event feed with filtering
  - Prometheus metrics endpoint

### Built-in Agents
- Hobby Games (coming-soon, catalog-new)
- Лавка Игр (shop, projects)
- Nastol.io (publications, specific articles)
- Evrikus (catalog)
- CrowdGames (collection)
- Gaga.ru (catalog)
- Zvezda.org.ru (board games)
- ChooChooGames (shop)

### Technology Stack
- **Backend**: FastAPI, SQLAlchemy, Celery, Redis
- **Frontend**: React, Ant Design, TypeScript
- **Database**: PostgreSQL 15 + TimescaleDB
- **Storage**: MinIO (S3-compatible)
- **Proxy**: Nginx
- **Containerization**: Docker & Docker Compose

### Deployment
- PowerShell script for Windows
- Bash script for Linux/macOS
- Automatic environment configuration
- Health checks and monitoring
- Backup functionality

### Documentation
- Comprehensive README in Russian
- API documentation
- Contributing guidelines
- Deployment guides

## [1.0.0] - 2024-01-20

### Added
- Complete monitoring system for board games
- Support for up to 100 sources
- 2-year data retention
- Local single-user deployment
- Russian language interface
- Docker Compose orchestration
- Automated deployment scripts
- Web-based management interface
- Mobile-responsive design
- Real-time notifications
- Price history visualization
- Export/import capabilities
- Agent development framework
- Extensible architecture

---

**Note:** This is the initial release of the Board Games Monitor project. All features are newly implemented and based on the requirements specified in the technical specification.