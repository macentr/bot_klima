# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Basic telegram bot functionality with aiogram 3.x
- PostgreSQL database with SQLAlchemy 2.0 ORM
- Room management (create, join, delete)
- Event creation and participation tracking
- User vacation status management
- Role-based access control (OWNER, ADMIN, MEMBER)
- Background worker for event auto-closing
- Docker Compose setup for local development and deployment
- Alembic database migrations
- Unit of Work pattern for transaction management
- Comprehensive documentation (README, CONTRIBUTING, DEVELOPMENT)

### Changed

### Fixed

### Deprecated

### Removed

### Security

---

## [0.1.0] - 2026-01-24

### Added
- Initial project setup
- Core domain models (User, Room, Event, Participation)
- Database schema with PostgreSQL
- Bot and Worker entry points
- Handler layers for commands and callbacks
- Service layer for business logic
- Repository layer for data access
- Docker and Docker Compose configuration
- Project documentation

[Unreleased]: https://github.com/yourusername/bot_klima/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/bot_klima/releases/tag/v0.1.0
