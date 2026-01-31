# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Invite code system for joining rooms (`0003_add_invite_code`)
- Support for custom event types with user descriptions (`0008_add_custom_event_type`)
- Admin management system with grant/revoke commands (`0007_add_user_is_admin`)
- Smart message cleanup (last_menu_message_id, last_invite_message_id) (`0006_add_user_last_messages`)
- Creator message ID tracking for event updates (`0002_add_creator_message_id`)
- Open event ID reference in rooms (`0004_add_open_event_id`)
- Owner role restoration functionality (`0005_restore_owner_roles`)
- `/join_room <invite_code>` command for easy room joining
- `/delete_room <room_id>` command for room owners
- `/admin_grant` and `/admin_revoke` commands
- Event creation cooldown (5 minutes) to prevent spam
- Comprehensive admin service layer
- Enhanced access control with admin middleware
- Detailed architectural documentation updates

### Changed
- Improved README.md with complete feature list and security section
- Updated ARCHITECTURE.md with current state analysis (January 2026)
- Enhanced DEVELOPMENT.md with better troubleshooting and IDE setup
- Refined CONTRIBUTING.md with security and performance guidelines
- Event type enum now includes CUSTOM type
- Database models enhanced with nullable fields for flexibility

### Fixed
- Owner role consistency in rooms
- Message update conflicts with smart cleanup

### Security
- Role-based access control enforcement
- Invite code validation
- Admin-only command isolation
- Event creation rate limiting (cooldown)

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

[Unreleased]: https://github.com/macentr/bot_klima/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/macentr/bot_klima/releases/tag/v0.1.0
