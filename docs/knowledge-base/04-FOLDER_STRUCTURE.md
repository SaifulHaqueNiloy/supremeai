# SupremeAI 2.0 — Folder Structure

**Version**: 2.0.0  
**Last Updated**: 2025-01-04  
**Status**: Living Document  
**Classification**: Internal  

---

## 📁 Complete Directory Map

This document provides a comprehensive map of the SupremeAI 2.0 repository structure, explaining the purpose and organization of every major directory and file.

---

## 🏠 Root Level Structure

```
supremeai_2.0/
├── .git/                          # Git repository
├── .github/                       # GitHub Actions workflows
├── admin/                         # Admin dashboard (legacy)
├── apps/                          # Application packages
│   ├── docs/                      # Documentation site
│   ├── hf-space/                  # Hugging Face space
│   ├── java-worker/               # Java worker service
│   ├── mobile/                    # Flutter mobile app
│   ├── studio-client/             # React/Electron frontend
│   └── ...                        # Other apps
├── backend/                       # Python FastAPI backend
├── cloudflare-worker/             # Cloudflare Worker edge layer
├── config/                        # Configuration files
├── configs/                       # Additional configurations
├── data/                          # Data files
├── docs/                          # Documentation
│   └── knowledge-base/            # AI-Native Knowledge Base
├── infrastructure/                # Infrastructure as code
├── model_versions/                # ML model version tracking
├── packages/                      # Shared packages
├── reports/                       # Generated reports
├── scripts/                       # Utility scripts
├── shared/                        # Shared utilities
├── skills/                        # AI skills
├── src/                           # Source code
├── tests/                         # Integration tests
├── tools/                         # Development tools
├── .env                           # Environment variables (git-ignored)
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
├── .pre-commit-config.yaml        # Pre-commit hooks
├── AGENTS.md                      # Agent instructions
├── package.json                   # Root package.json (pnpm workspace)
├── pnpm-lock.yaml                 # pnpm lock file
├── pnpm-workspace.yaml            # pnpm workspace config
├── turbo.json                     # Turborepo configuration
├── render.yaml                    # Render deployment config
├── vercel.json                    # Vercel deployment config
├── firebase.json                  # Firebase hosting config
├── README.md                      # Project README
├── LICENSE                        # MIT License
└── CONTRIBUTING.md                # Contribution guidelines
```

---

## 🔧 Backend Structure (`backend/`)

```
backend/
├── main.py                        # Entry point, ENV bootstrap, Uvicorn launch
├── pyproject.toml                 # Poetry configuration, dependencies
├── poetry.lock                    # Poetry lock file
├── uv.lock                        # uv lock file
├── Dockerfile                     # Production Docker image
├── Dockerfile.ci                  # CI-specific Docker image
├── alembic.ini                    # Alembic migration config
├── conftest.py                    # Pytest configuration
├── pytest.ini                     # Pytest settings
├── mypy.ini                       # MyPy type checking config
├── .coveragerc                    # Coverage configuration
├── API-swagger.yaml               # Swagger/OpenAPI spec
│
├── core/                          # Core framework and utilities
│   ├── __init__.py
│   ├── app.py                     # Legacy FastAPI app (backward compat)
│   ├── app_user.py                # User role FastAPI app
│   ├── app_admin.py               # Admin role FastAPI app
│   ├── config.py                  # Configuration management (Pydantic Settings)
│   ├── logging_config.py          # Loguru logging setup
│   ├── exceptions.py              # Custom exceptions
│   │
│   ├── security/                  # Security middleware and utilities
│   │   ├── __init__.py
│   │   ├── auth_middleware.py     # JWT validation, fail-closed
│   │   ├── api_key_middleware.py  # API key validation (HMAC-SHA256)
│   │   ├── rbac.py                # Role-based access control
│   │   ├── secret_vault.py        # Infisical integration
│   │   ├── secure_credential_store.py  # Fernet encryption
│   │   ├── cryptographic_ledger.py # SHA-256 audit trail
│   │   ├── input_sanitizer.py     # PII stripping, sanitization
│   │   ├── prompt_firewall.py     # Prompt injection detection
│   │   ├── rate_limiter.py        # Rate limiting logic
│   │   └── ...
│   │
│   ├── middleware/                 # Custom middleware
│   │   ├── correlation_id.py      # Request correlation
│   │   ├── error_handler.py       # Error handling
│   │   ├── timeout.py             # Request timeout
│   │   └── ...
│   │
│   ├── database/                  # Database connections
│   │   ├── session.py             # SQLAlchemy async session
│   │   ├── supabase_client.py     # Supabase REST client
│   │   └── ...
│   │
│   ├── cache/                     # Caching layer
│   │   ├── redis_cache.py         # Redis cache
│   │   └── ...
│   │
│   ├── llm/                       # LLM gateway
│   │   ├── gateway.py             # LLM provider routing
│   │   ├── providers/             # Provider implementations
│   │   └── ...
│   │
│   ├── observability/             # Logging, metrics, tracing
│   │   ├── metrics.py             # Prometheus metrics
│   │   ├── tracing.py             # OpenTelemetry tracing
│   │   └── ...
│   │
│   ├── resilience/                # Circuit breakers, retries
│   │   ├── circuit_breaker.py     # Pybreaker integration
│   │   └── ...
│   │
│   ├── health/                    # Health checks
│   │   ├── health_check.py        # Health check endpoints
│   │   └── ...
│   │
│   ├── evolution/                 # Self-evolving systems
│   │   ├── evolution_engine.py    # Agent evolution
│   │   └── ...
│   │
│   ├── adaptive_engine/           # Adaptive learning
│   │   ├── adaptive_engine.py     # Performance adaptation
│   │   └── ...
│   │
│   ├── memory/                    # Memory systems
│   │   ├── cascade_memory.py      # Cascade memory service
│   │   └── ...
│   │
│   ├── orchestration/             # Agent orchestration
│   │   ├── orchestrator.py        # Agent orchestration
│   │   └── ...
│   │
│   ├── prompts/                   # Prompt management
│   │   ├── prompt_manager.py      # Prompt templates
│   │   └── ...
│   │
│   ├── skills/                    # Skill management
│   │   ├── skill_registry.py      # Skill registry
│   │   └── ...
│   │
│   ├── tools/                     # Tool implementations
│   │   ├── tool_registry.py       # Tool registry
│   │   └── ...
│   │
│   ├── queue/                     # Task queue
│   │   ├── task_queue.py          # Task queue management
│   │   └── ...
│   │
│   ├── messaging/                 # Event bus
│   │   ├── event_bus.py           # Event messaging
│   │   └── ...
│   │
│   ├── persistence/               # Persistence layers
│   │   ├── experience_db.py       # Experience database
│   │   └── ...
│   │
│   ├── telemetry/                 # System telemetry
│   │   ├── telemetry_collector.py # Telemetry collection
│   │   └── ...
│   │
│   ├── testing/                   # Test utilities
│   │   ├── test_helpers.py        # Test helpers
│   │   └── ...
│   │
│   ├── tier8/                     # Tier 8 systems
│   │   └── ...
│   │
│   ├── deployment/                # Deployment utilities
│   │   ├── deployer.py            # Deployment automation
│   │   └── ...
│   │
│   ├── localization/              # i18n support
│   │   ├── i18n.py                # Internationalization
│   │   └── ...
│   │
│   ├── optimization/              # Performance optimization
│   │   ├── optimizer.py           # Query optimization
│   │   └── ...
│   │
│   ├── models/                    # Core models
│   │   ├── base.py                # Base model classes
│   │   └── ...
│   │
│   ├── schemas/                   # Core schemas
│   │   ├── common.py              # Common schemas
│   │   └── ...
│   │
│   └── ...                        # Other core modules
│
├── api/                           # API layer
│   ├── __init__.py
│   ├── routers.py                 # Centralized router registry
│   ├── middleware.py              # API middleware (6 classes)
│   ├── dependencies.py            # Auth & dependency injection
│   ├── deps.py                    # Enhanced dependencies
│   ├── errors.py                  # Standardized error responses
│   │
│   ├── routes/                    # API route modules (75+)
│   │   ├── auth.py                # Authentication endpoints
│   │   ├── health.py              # Health check endpoints
│   │   ├── api_keys.py            # API key management
│   │   ├── admin_dashboard.py     # Admin dashboard data
│   │   ├── tenant_admin.py        # Tenant administration
│   │   ├── swarm.py               # Swarm agent endpoints
│   │   ├── sandbox.py             # Sandbox execution
│   │   ├── analytics.py           # Analytics endpoints
│   │   ├── agents.py              # Agent management
│   │   ├── tools.py               # Tool management
│   │   ├── memory.py              # Memory management
│   │   ├── knowledge.py           # Knowledge base
│   │   ├── llm.py                 # LLM operations
│   │   ├── vision.py              # Vision operations
│   │   ├── voice.py               # Voice operations
│   │   ├── video.py               # Video processing
│   │   ├── code.py                # Code operations
│   │   ├── diagrams.py            # Diagram parsing
│   │   ├── files.py               # File operations
│   │   ├── uploads.py             # File uploads
│   │   ├── webhooks.py            # Webhook management
│   │   ├── integrations.py        # Third-party integrations
│   │   ├── notifications.py       # Notifications
│   │   ├── billing.py             # Billing (if applicable)
│   │   ├── subscriptions.py       # Subscriptions
│   │   ├── usage.py               # Usage tracking
│   │   ├── reports.py             # Report generation
│   │   ├── exports.py             # Data exports
│   │   ├── imports.py             # Data imports
│   │   ├── search.py              # Search functionality
│   │   ├── filters.py             # Filtering
│   │   ├── tags.py                # Tag management
│   │   ├── comments.py            # Comments
│   │   ├── shares.py              # Sharing
│   │   ├── bookmarks.py           # Bookmarks
│   │   ├── history.py             # History tracking
│   │   ├── templates.py           # Template management
│   │   ├── workflows.py           # Workflow management
│   │   ├── pipelines.py           # Pipeline management
│   │   ├── executions.py          # Execution tracking
│   │   ├── logs.py                # Log access
│   │   ├── metrics.py             # Metrics endpoints
│   │   ├── alerts.py              # Alert management
│   │   ├── settings.py            # User settings
│   │   ├── preferences.py         # User preferences
│   │   ├── profile.py             # User profile
│   │   ├── teams.py               # Team management
│   │   ├── projects.py            # Project management
│   │   ├── organizations.py       # Organization management
│   │   ├── invitations.py         # Invitation management
│   │   ├── roles.py               # Role management
│   │   ├── permissions.py         # Permission management
│   │   ├── audit.py               # Audit logs
│   │   ├── compliance.py          # Compliance
│   │   ├── security.py            # Security settings
│   │   ├── encryption.py          # Encryption management
│   │   ├── backups.py             # Backup management
│   │   ├── restores.py            # Restore operations
│   │   ├── migrations.py          # Migration management
│   │   ├── deployments.py         # Deployment management
│   │   ├── environments.py        # Environment management
│   │   ├── variables.py           # Environment variables
│   │   ├── secrets.py             # Secret management
│   │   ├── keys.py                # API key management
│   │   ├── tokens.py              # Token management
│   │   ├── sessions.py            # Session management
│   │   ├── cookies.py             # Cookie management
│   │   ├── cors.py                # CORS configuration
│   │   ├── rate_limits.py         # Rate limit configuration
│   │   ├── quotas.py              # Quota management
│   │   ├── limits.py              # Limit management
│   │   ├── throttles.py           # Throttling
│   │   ├── blocks.py              # Block management
│   │   ├── bans.py                # Ban management
│   │   ├── reports.py             # Reporting
│   │   ├── analytics.py           # Analytics
│   │   ├── insights.py            # Insights
│   │   ├── predictions.py         # Predictions
│   │   ├── recommendations.py     # Recommendations
│   │   ├── suggestions.py         # Suggestions
│   │   ├── feedback.py            # Feedback
│   │   ├── surveys.py             # Surveys
│   │   ├── polls.py               # Polls
│   │   ├── votes.py               # Voting
│   │   ├── ratings.py             # Ratings
│   │   ├── reviews.py             # Reviews
│   │   ├── comments.py            # Comments
│   │   ├── discussions.py         # Discussions
│   │   ├── forums.py              # Forums
│   │   ├── messages.py            # Messages
│   │   ├── chats.py               # Chat
│   │   ├── calls.py               # Calls
│   │   ├── meetings.py            # Meetings
│   │   ├── webinars.py            # Webinars
│   │   ├── events.py              # Events
│   │   ├── calendar.py            # Calendar
│   │   ├── tasks.py               # Tasks
│   │   ├── todos.py               # Todos
│   │   ├── reminders.py           # Reminders
│   │   ├── notes.py               # Notes
│   │   ├── documents.py           # Documents
│   │   ├── files.py               # Files
│   │   ├── images.py              # Images
│   │   ├── videos.py              # Videos
│   │   ├── audio.py               # Audio
│   │   ├── media.py               # Media
│   │   ├── streams.py             # Streams
│   │   ├── broadcasts.py          # Broadcasts
│   │   ├── live.py                # Live streaming
│   │   ├── recordings.py          # Recordings
│   │   ├── transcripts.py         # Transcripts
│   │   ├── translations.py        # Translations
│   │   ├── interpretations.py     # Interpretations
│   │   ├── transcriptions.py      # Transcriptions
│   │   ├── summaries.py           # Summaries
│   │   ├── highlights.py          # Highlights
│   │   ├── bookmarks.py           # Bookmarks
│   │   ├── favorites.py           # Favorites
│   │   ├── likes.py               # Likes
│   │   ├── shares.py              # Shares
│   │   ├── reposts.py             # Reposts
│   │   ├── follows.py             # Follows
│   │   ├── connections.py         # Connections
│   │   ├── network.py             # Network
│   │   ├── graph.py               # Graph
│   │   ├── tree.py                # Tree
│   │   ├── hierarchy.py           # Hierarchy
│   │   ├── structure.py           # Structure
│   │   ├── organization.py        # Organization
│   │   ├── taxonomy.py            # Taxonomy
│   │   ├── classification.py      # Classification
│   │   ├── categorization.py      # Categorization
│   │   ├── tagging.py             # Tagging
│   │   ├── labeling.py            # Labeling
│   │   ├── annotation.py          # Annotation
│   │   ├── markup.py              # Markup
│   │   ├── formatting.py          # Formatting
│   │   ├── styling.py             # Styling
│   │   ├── theming.py             # Theming
│   │   ├── branding.py            # Branding
│   │   ├── customization.py       # Customization
│   │   ├── personalization.py     # Personalization
│   │   ├── localization.py        # Localization
│   │   ├── internationalization.py # Internationalization
│   │   ├── translation.py         # Translation
│   │   ├── language.py            # Language
│   │   ├── locale.py              # Locale
│   │   ├── region.py              # Region
│   │   ├── timezone.py            # Timezone
│   │   ├── currency.py            # Currency
│   │   ├── units.py               # Units
│   │   ├── measurements.py        # Measurements
│   │   ├── formats.py             # Formats
│   │   ├── standards.py           # Standards
│   │   ├── compliance.py          # Compliance
│   │   ├── regulations.py         # Regulations
│   │   ├── policies.py            # Policies
│   │   ├── governance.py          # Governance
│   │   ├── administration.py      # Administration
│   │   ├── management.py          # Management
│   │   ├── configuration.py       # Configuration
│   │   ├── settings.py            # Settings
│   │   ├── preferences.py         # Preferences
│   │   ├── options.py             # Options
│   │   ├── choices.py             # Choices
│   │   ├── selections.py          # Selections
│   │   ├── decisions.py           # Decisions
│   │   ├── choices.py             # Choices
│   │   ├── alternatives.py        # Alternatives
│   │   ├── variants.py            # Variants
│   │   ├── versions.py            # Versions
│   │   ├── editions.py            # Editions
│   │   ├── tiers.py               # Tiers
│   │   ├── plans.py               # Plans
│   │   ├── packages.py            # Packages
│   │   ├── bundles.py             # Bundles
│   │   ├── suites.py              # Suites
│   │   ├── collections.py         # Collections
│   │   ├── libraries.py           # Libraries
│   │   ├── repositories.py        # Repositories
│   │   ├── archives.py            # Archives
│   │   ├── backups.py             # Backups
│   │   ├── snapshots.py           # Snapshots
│   │   ├── images.py              # Images
│   │   ├── containers.py          # Containers
│   │   ├── instances.py           # Instances
│   │   ├── deployments.py         # Deployments
│   │   ├── releases.py            # Releases
│   │   ├── versions.py            # Versions
│   │   ├── builds.py              # Builds
│   │   ├── artifacts.py           # Artifacts
│   │   ├── binaries.py            # Binaries
│   │   ├── executables.py         # Executables
│   │   ├── packages.py            # Packages
│   │   ├── distributions.py       # Distributions
│   │   ├── channels.py            # Channels
│   │   ├── streams.py             # Streams
│   │   ├── feeds.py               # Feeds
│   │   ├── sources.py             # Sources
│   │   ├── origins.py             # Origins
│   │   ├── upstreams.py           # Upstreams
│   │   ├── downstreams.py         # Downstreams
│   │   ├── dependencies.py        # Dependencies
│   │   ├── requirements.py        # Requirements
│   │   ├── specifications.py      # Specifications
│   │   ├── standards.py           # Standards
│   │   ├── protocols.py           # Protocols
│   │   ├── interfaces.py          # Interfaces
│   │   ├── apis.py                # APIs
│   │   ├── endpoints.py           # Endpoints
│   │   ├── routes.py              # Routes
│   │   ├── paths.py               # Paths
│   │   ├── urls.py                # URLs
│   │   ├── links.py               # Links
│   │   ├── references.py          # References
│   │   ├── citations.py           # Citations
│   │   ├── sources.py             # Sources
│   │   ├── origins.py             # Origins
│   │   ├── authors.py             # Authors
│   │   ├── contributors.py        # Contributors
│   │   ├── maintainers.py         # Maintainers
│   │   ├── owners.py              # Owners
│   │   ├── administrators.py      # Administrators
│   │   ├── operators.py           # Operators
│   │   ├── users.py               # Users
│   │   ├── guests.py              # Guests
│   │   ├── visitors.py            # Visitors
│   │   ├── clients.py             # Clients
│   │   ├── customers.py           # Customers
│   │   ├── consumers.py           # Consumers
│   │   ├── producers.py           # Producers
│   │   ├── providers.py           # Providers
│   │   ├── suppliers.py           # Suppliers
│   │   ├── vendors.py             # Vendors
│   │   ├── partners.py            # Partners
│   │   ├── collaborators.py       # Collaborators
│   │   ├── affiliates.py          # Affiliates
│   │   ├── associates.py          # Associates
│   │   ├── members.py             # Members
│   │   ├── participants.py        # Participants
│   │   ├── attendees.py           # Attendees
│   │   ├── viewers.py             # Viewers
│   │   ├── listeners.py           # Listeners
│   │   ├── readers.py             # Readers
│   │   ├── writers.py             # Writers
│   │   ├── editors.py             # Editors
│   │   ├── publishers.py          # Publishers
│   │   ├── distributors.py        # Distributors
│   │   ├── retailers.py           # Retailers
│   │   ├── wholesalers.py         # Wholesalers
│   │   ├── manufacturers.py       # Manufacturers
│   │   ├── developers.py          # Developers
│   │   ├── engineers.py           # Engineers
│   │   ├── architects.py          # Architects
│   │   ├── designers.py           # Designers
│   │   ├── artists.py             # Artists
│   │   ├── creators.py            # Creators
│   │   ├── innovators.py          # Innovators
│   │   ├── pioneers.py            # Pioneers
│   │   ├── leaders.py             # Leaders
│   │   ├── managers.py            # Managers
│   │   ├── directors.py           # Directors
│   │   ├── executives.py          # Executives
│   │   ├── officers.py            # Officers
│   │   ├── board.py               # Board
│   │   ├── committee.py           # Committee
│   │   ├── council.py             # Council
│   │   ├── senate.py              # Senate
│   │   ├── parliament.py          # Parliament
│   │   ├── government.py          # Government
│   │   ├── public.py              # Public
│   │   ├── community.py           # Community
│   │   ├── society.py             # Society
│   │   ├── world.py               # World
│   │   └── ...                    # Additional routes
│   │
│   └── v1/                        # Versioned APIs
│       └── telemetry.py           # Telemetry API v1
│
├── services/                      # Business logic services
│   ├── memory_service.py          # Memory management
│   ├── knowledge_qa.py            # RAG system
│   ├── vision_service.py          # Image analysis
│   ├── voice_service.py           # Voice processing
│   ├── video_to_code_pipeline.py  # Video to code
│   ├── diagram_parser_service.py  # Diagram parsing
│   ├── project_context_service.py # Codebase indexing
│   ├── llm_gateway.py             # LLM orchestration
│   ├── agent_service.py           # Agent management
│   ├── tool_service.py            # Tool management
│   ├── workflow_service.py        # Workflow management
│   ├── pipeline_service.py        # Pipeline management
│   ├── execution_service.py       # Execution tracking
│   ├── analytics_service.py       # Analytics
│   ├── reporting_service.py       # Reporting
│   ├── notification_service.py    # Notifications
│   ├── integration_service.py     # Integrations
│   └── ...
│
├── models/                        # SQLAlchemy ORM models
│   ├── user.py                    # User model
│   ├── agent.py                   # Agent model
│   ├── execution.py               # Execution model
│   ├── tool.py                    # Tool model
│   ├── memory.py                  # Memory model
│   ├── knowledge.py               # Knowledge model
│   ├── api_key.py                 # API key model
│   ├── audit_log.py               # Audit log model
│   ├── session.py                 # Session model
│   ├── project.py                 # Project model
│   ├── workflow.py                # Workflow model
│   ├── pipeline.py                # Pipeline model
│   ├── execution_log.py           # Execution log model
│   ├── metric.py                  # Metric model
│   ├── alert.py                   # Alert model
│   ├── notification.py            # Notification model
│   ├── integration.py             # Integration model
│   ├── webhook.py                 # Webhook model
│   ├── file.py                    # File model
│   ├── upload.py                  # Upload model
│   ├── tag.py                     # Tag model
│   ├── comment.py                 # Comment model
│   ├── share.py                   # Share model
│   ├── bookmark.py                # Bookmark model
│   ├── favorite.py                # Favorite model
│   ├── like.py                    # Like model
│   ├── follow.py                  # Follow model
│   ├── connection.py              # Connection model
│   ├── team.py                    # Team model
│   ├── organization.py            # Organization model
│   ├── role.py                    # Role model
│   ├── permission.py              # Permission model
│   ├── invitation.py              # Invitation model
│   ├── setting.py                 # Setting model
│   ├── preference.py              # Preference model
│   ├── profile.py                 # Profile model
│   ├── credential.py              # Credential model
│   ├── secret.py                  # Secret model
│   ├── key.py                     # Key model
│   ├── token.py                   # Token model
│   ├── session.py                 # Session model
│   ├── quota.py                   # Quota model
│   ├── limit.py                   # Limit model
│   ├── block.py                   # Block model
│   ├── ban.py                     # Ban model
│   ├── report.py                  # Report model
│   ├── feedback.py                # Feedback model
│   ├── survey.py                  # Survey model
│   ├── poll.py                    # Poll model
│   ├── vote.py                    # Vote model
│   ├── rating.py                  # Rating model
│   ├── review.py                  # Review model
│   ├── discussion.py              # Discussion model
│   ├── forum.py                   # Forum model
│   ├── message.py                 # Message model
│   ├── chat.py                    # Chat model
│   ├── call.py                    # Call model
│   ├── meeting.py                 # Meeting model
│   ├── webinar.py                 # Webinar model
│   ├── event.py                   # Event model
│   ├── calendar.py                # Calendar model
│   ├── task.py                    # Task model
│   ├── todo.py                    # Todo model
│   ├── reminder.py                # Reminder model
│   ├── note.py                    # Note model
│   ├── document.py                # Document model
│   ├── file.py                    # File model
│   ├── image.py                   # Image model
│   ├── video.py                   # Video model
│   ├── audio.py                   # Audio model
│   ├── media.py                   # Media model
│   ├── stream.py                  # Stream model
│   ├── broadcast.py               # Broadcast model
│   ├── recording.py               # Recording model
│   ├── transcript.py              # Transcript model
│   ├── translation.py             # Translation model
│   ├── summary.py                 # Summary model
│   ├── insight.py                 # Insight model
│   ├── prediction.py              # Prediction model
│   ├── recommendation.py          # Recommendation model
│   ├── suggestion.py              # Suggestion model
│   └── ...
│
├── schemas/                       # Pydantic schemas
│   ├── user.py                    # User schemas
│   ├── agent.py                   # Agent schemas
│   ├── execution.py               # Execution schemas
│   ├── tool.py                    # Tool schemas
│   ├── memory.py                  # Memory schemas
│   ├── knowledge.py               # Knowledge schemas
│   ├── api_key.py                 # API key schemas
│   ├── audit_log.py               # Audit log schemas
│   ├── common.py                  # Common schemas
│   └── ...
│
├── agents/                        # AI agent implementations
│   ├── base_agent.py              # Base agent class
│   ├── swarm_agent.py             # Swarm agent
│   ├── autonomous_agent.py        # Autonomous agent
│   ├── collaborative_agent.py     # Collaborative agent
│   ├── specialized_agent.py       # Specialized agent
│   └── ...
│
├── tools/                         # Tool implementations
│   ├── base_tool.py               # Base tool class
│   ├── web_search.py              # Web search tool
│   ├── code_executor.py           # Code execution tool
│   ├── file_manager.py            # File management tool
│   ├── database_query.py          # Database query tool
│   ├── api_caller.py              # API caller tool
│   ├── web_scraper.py             # Web scraper tool
│   ├── email_sender.py            # Email sender tool
│   ├── calendar_manager.py        # Calendar manager tool
│   ├── task_manager.py            # Task manager tool
│   └── ...
│
├── workers/                       # Background workers
│   ├── celery_app.py              # Celery configuration
│   ├── task_queue.py              # Task queue
│   ├── scheduler.py               # Task scheduler
│   └── ...
│
├── middleware/                    # Custom middleware
│   ├── auth_middleware.py         # Authentication
│   ├── rate_limit_middleware.py   # Rate limiting
│   ├── cors_middleware.py         # CORS
│   ├── logging_middleware.py      # Logging
│   ├── metrics_middleware.py      # Metrics
│   └── ...
│
├── config/                        # Configuration files
│   ├── settings.py                # Settings (legacy)
│   ├── routing_policy.json        # LLM routing policy
│   ├── agent_rules.json           # Agent rules
│   ├── compliance-rules.yml       # Compliance rules
│   ├── audit-rules.yml            # Audit rules
│   ├── docker-limits.yml          # Docker limits
│   ├── dummy_registry.json        # Dummy registry
│   └── ...
│
├── database/                      # Database utilities
│   ├── session.py                 # SQLAlchemy session
│   ├── supabase_client.py         # Supabase client
│   ├── migrations/                # Alembic migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/              # Migration files
│   │       ├── 001_initial.py
│   │       ├── 002_add_users.py
│   │       └── ...
│   └── ...
│
├── alembic/                       # Alembic migration files
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── tests/                         # Backend tests
│   ├── conftest.py                # Test configuration
│   ├── test_*.py                  # Test files
│   ├── api/                       # API tests
│   │   ├── test_auth.py
│   │   ├── test_health.py
│   │   ├── test_swarm_routes.py
│   │   ├── test_admin.py
│   │   └── ...
│   ├── services/                  # Service tests
│   │   ├── test_memory_service.py
│   │   ├── test_knowledge_qa.py
│   │   └── ...
│   ├── models/                    # Model tests
│   │   ├── test_user.py
│   │   └── ...
│   ├── integration/               # Integration tests
│   │   ├── test_database.py
│   │   ├── test_redis.py
│   │   └── ...
│   └── ...
│
├── docs/                          # Backend documentation
│   ├── api.md
│   ├── architecture.md
│   └── ...
│
├── scripts/                       # Backend scripts
│   ├── migrate.py                 # Database migration
│   ├── seed.py                    # Database seeding
│   ├── backup.py                  # Database backup
│   └── ...
│
├── data/                          # Data files
│   ├── pending_tasks.db           # SQLite task queue
│   └── ...
│
├── logs/                          # Log files
│   ├── app.log
│   └── ...
│
├── storage/                       # File storage
│   ├── uploads/                   # Uploaded files
│   ├── temp/                      # Temporary files
│   └── ...
│
├── backup/                        # Backups
│   ├── database/
│   └── ...
│
├── sandbox/                       # Sandbox environment
│   ├── code_execution/
│   └── ...
│
├── baselines/                     # Performance baselines
│   ├── latency_baseline.json
│   └── ...
│
├── reports/                       # Generated reports
│   ├── test_coverage/
│   ├── performance/
│   └── ...
│
├── src/                           # Additional source
│   └── ...
│
├── utils/                         # Utility functions
│   ├── helpers.py
│   ├── validators.py
│   └── ...
│
├── skills/                        # AI skills
│   ├── base_skill.py
│   ├── web_search_skill.py
│   └── ...
│
├── tools/                         # AI tools
│   ├── base_tool.py
│   ├── web_search_tool.py
│   └── ...
│
├── p2p/                           # Peer-to-peer
│   ├── p2p_node.py
│   └── ...
│
├── pipelines/                     # Data pipelines
│   ├── etl_pipeline.py
│   └── ...
│
├── evolution/                     # Evolution engine
│   ├── evolution_engine.py
│   └── ...
│
├── adaptive_engine/               # Adaptive engine
│   ├── adaptive_engine.py
│   └── ...
│
├── memory/                        # Memory systems
│   ├── cascade_memory.py
│   └── ...
│
├── monitoring/                    # Monitoring
│   ├── health_monitor.py
│   └── ...
│
├── scout/                         # Scout system
│   ├── scout_agent.py
│   └── ...
│
└── ...                            # Other backend modules
```

---

## 🎨 Frontend Structure (`apps/studio-client/`)

```
apps/studio-client/
├── package.json                   # Dependencies and scripts
├── pnpm-lock.yaml                 # pnpm lock file
├── tsconfig.json                  # TypeScript configuration
├── vite.config.ts                 # Vite configuration
├── playwright.config.ts           # Playwright E2E config
├── playwright-ct.config.ts        # Playwright component test config
├── tailwind.config.js             # Tailwind CSS config
├── postcss.config.js              # PostCSS config
├── index.html                     # HTML entry point
├── electron/                      # Electron main process
│   ├── main.js                    # Electron main
│   ├── preload.js                 # Preload script
│   └── ...
├── public/                        # Static assets
│   ├── favicon.ico
│   ├── logo.svg
│   └── ...
├── src/                           # Source code
│   ├── main.tsx                   # React entry point
│   ├── App.tsx                    # Main App component
│   ├── vite-env.d.ts              # Vite type definitions
│   │
│   ├── components/                # React components
│   │   ├── ui/                    # Reusable UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Dropdown.tsx
│   │   │   ├── Tabs.tsx
│   │   │   ├── Tooltip.tsx
│   │   │   ├── Spinner.tsx
│   │   │   ├── Alert.tsx
│   │   │   └── ...
│   │   │
│   │   ├── editor/                # Monaco editor
│   │   │   ├── CodeEditor.tsx
│   │   │   ├── EditorToolbar.tsx
│   │   │   ├── EditorTabs.tsx
│   │   │   └── ...
│   │   │
│   │   ├── flow/                  # React Flow
│   │   │   ├── FlowCanvas.tsx
│   │   │   ├── FlowNode.tsx
│   │   │   ├── FlowEdge.tsx
│   │   │   ├── FlowToolbar.tsx
│   │   │   └── ...
│   │   │
│   │   ├── terminal/              # Xterm terminal
│   │   │   ├── Terminal.tsx
│   │   │   ├── TerminalToolbar.tsx
│   │   │   └── ...
│   │   │
│   │   ├── layout/                # Layout components
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── ...
│   │   │
│   │   ├── auth/                  # Auth components
│   │   │   ├── LoginForm.tsx
│   │   │   ├── SignupForm.tsx
│   │   │   ├── OAuthButton.tsx
│   │   │   └── ...
│   │   │
│   │   ├── agents/                # Agent components
│   │   │   ├── AgentCard.tsx
│   │   │   ├── AgentBuilder.tsx
│   │   │   ├── AgentList.tsx
│   │   │   └── ...
│   │   │
│   │   ├── tools/                 # Tool components
│   │   │   ├── ToolCard.tsx
│   │   │   ├── ToolBuilder.tsx
│   │   │   ├── ToolList.tsx
│   │   │   └── ...
│   │   │
│   │   ├── workflows/             # Workflow components
│   │   │   ├── WorkflowCanvas.tsx
│   │   │   ├── WorkflowNode.tsx
│   │   │   └── ...
│   │   │
│   │   ├── pipelines/             # Pipeline components
│   │   │   ├── PipelineBuilder.tsx
│   │   │   ├── PipelineList.tsx
│   │   │   └── ...
│   │   │
│   │   ├── executions/            # Execution components
│   │   │   ├── ExecutionViewer.tsx
│   │   │   ├── ExecutionLog.tsx
│   │   │   └── ...
│   │   │
│   │   ├── analytics/             # Analytics components
│   │   │   ├── AnalyticsChart.tsx
│   │   │   ├── MetricsCard.tsx
│   │   │   └── ...
│   │   │
│   │   ├── settings/              # Settings components
│   │   │   ├── SettingsPanel.tsx
│   │   │   ├── ProfileSettings.tsx
│   │   │   └── ...
│   │   │
│   │   └── ...                    # Other components
│   │
│   ├── pages/                     # Page components
│   │   ├── Dashboard.tsx
│   │   ├── AgentBuilder.tsx
│   │   ├── ToolBuilder.tsx
│   │   ├── WorkflowBuilder.tsx
│   │   ├── PipelineBuilder.tsx
│   │   ├── ExecutionViewer.tsx
│   │   ├── Analytics.tsx
│   │   ├── Settings.tsx
│   │   ├── Profile.tsx
│   │   ├── Login.tsx
│   │   ├── Signup.tsx
│   │   ├── ForgotPassword.tsx
│   │   ├── ResetPassword.tsx
│   │   ├── NotFound.tsx
│   │   └── ...
│   │
│   ├── services/                  # API services
│   │   ├── api.ts                 # Axios instance
│   │   ├── auth.ts                # Auth service
│   │   ├── agents.ts              # Agents service
│   │   ├── tools.ts               # Tools service
│   │   ├── workflows.ts           # Workflows service
│   │   ├── pipelines.ts           # Pipelines service
│   │   ├── executions.ts          # Executions service
│   │   ├── analytics.ts           # Analytics service
│   │   ├── files.ts               # Files service
│   │   └── ...
│   │
│   ├── stores/                    # State management (Zustand)
│   │   ├── authStore.ts           # Auth state
│   │   ├── agentStore.ts          # Agent state
│   │   ├── toolStore.ts           # Tool state
│   │   ├── workflowStore.ts       # Workflow state
│   │   ├── pipelineStore.ts       # Pipeline state
│   │   ├── executionStore.ts      # Execution state
│   │   ├── uiStore.ts             # UI state
│   │   └── ...
│   │
│   ├── hooks/                     # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useApi.ts
│   │   ├── useWebSocket.ts
│   │   ├── useLocalStorage.ts
│   │   └── ...
│   │
│   ├── utils/                     # Utility functions
│   │   ├── helpers.ts
│   │   ├── validators.ts
│   │   ├── formatters.ts
│   │   ├── constants.ts
│   │   └── ...
│   │
│   ├── types/                     # TypeScript types
│   │   ├── auth.ts
│   │   ├── agent.ts
│   │   ├── tool.ts
│   │   ├── workflow.ts
│   │   ├── pipeline.ts
│   │   ├── execution.ts
│   │   └── ...
│   │
│   ├── assets/                    # Images, fonts, etc.
│   │   ├── images/
│   │   ├── fonts/
│   │   └── ...
│   │
│   ├── styles/                    # Global styles
│   │   ├── globals.css
│   │   ├── tailwind.css
│   │   └── ...
│   │
│   └── locales/                   # i18n translations
│       ├── en/
│       │   ├── common.json
│       │   ├── auth.json
│       │   └── ...
│       └── bn/
│           ├── common.json
│           ├── auth.json
│           └── ...
│
├── tests/                         # Frontend tests
│   ├── unit/                      # Unit tests (Vitest)
│   │   ├── components/
│   │   ├── services/
│   │   └── utils/
│   ├── e2e/                       # E2E tests (Playwright)
│   │   ├── auth.spec.ts
│   │   ├── agents.spec.ts
│   │   └── ...
│   └── ...
│
├── dist/                          # Build output
│   ├── index.html
│   ├── assets/
│   └── ...
│
└── ...                            # Other config files
```

---

## 📱 Mobile Structure (`apps/mobile/`)

```
apps/mobile/
├── pubspec.yaml                   # Flutter dependencies
├── lib/                           # Dart source code
│   ├── main.dart                  # App entry point
│   ├── app.dart                   # App configuration
│   │
│   ├── screens/                   # Screen widgets
│   │   ├── home_screen.dart
│   │   ├── chat_screen.dart
│   │   ├── agents_screen.dart
│   │   ├── settings_screen.dart
│   │   └── ...
│   │
│   ├── widgets/                   # Reusable widgets
│   │   ├── chat_bubble.dart
│   │   ├── agent_card.dart
│   │   ├── loading_indicator.dart
│   │   └── ...
│   │
│   ├── services/                  # API services
│   │   ├── api_service.dart
│   │   ├── auth_service.dart
│   │   ├── agent_service.dart
│   │   └── ...
│   │
│   ├── models/                    # Data models
│   │   ├── user.dart
│   │   ├── agent.dart
│   │   ├── message.dart
│   │   └── ...
│   │
│   ├── providers/                 # State management (Provider)
│   │   ├── auth_provider.dart
│   │   ├── agent_provider.dart
│   │   └── ...
│   │
│   ├── utils/                     # Utilities
│   │   ├── constants.dart
│   │   ├── helpers.dart
│   │   └── ...
│   │
│   └── ...
│
├── android/                       # Android platform code
├── ios/                           # iOS platform code
├── web/                           # Web platform code
├── test/                          # Flutter tests
└── ...
```

---

## 📚 Documentation Structure (`docs/`)

```
docs/
├── INDEX.md                       # Documentation index
├── README.md                      # Documentation README
├── api.md                         # API documentation
├── architecture-overview.md       # Architecture overview
├── config.md                      # Configuration guide
├── install.md                     # Installation guide
├── usage.md                       # Usage guide
├── DEVELOPER_GUIDE.md             # Developer guide
├── CONTRIBUTING.md                # Contributing guide
├── CHANGELOG.md                   # Change log
├── SECURITY.md                    # Security policy
├── limitations.md                 # Known limitations
├── PROJECT_STATUS.md              # Project status
├── PROJECT_STRUCTURE.md           # Project structure
├── FEATURE_STATUS.md              # Feature status
├── TODO_TRACKER.md                # TODO tracker
├── TROUBLESHOOTING.md             # Troubleshooting guide
├── TESTING_GUIDELINES.md          # Testing guidelines
├── TEST_ECOSYSTEM.md              # Test ecosystem
├── TEST_RELIABILITY_GUIDELINES.md # Test reliability
├── test_coverage.md               # Test coverage
├── DEPLOYMENT_ARCHITECTURE.md     # Deployment architecture
├── ENVIRONMENT_AND_API_KEYS_REGISTRY.md  # Env vars registry
├── FREE_TIER_LLM_PROVIDERS.md     # Free LLM providers
├── AI_AGENT_SYSTEM_PROMPT.md      # AI agent prompts
├── AI_INTELLIGENCE_EVOLUTION_PLAN.md  # AI evolution plan
├── INTERNET_MONITOR_AGENT.md      # Internet monitor agent
├── voice-integration-plan.md      # Voice integration plan
├── create_best_ai_model.md        # AI model creation
├── dashboard-analysis-bangla.md   # Dashboard analysis (Bangla)
├── circuit_breaker_causes_bangla.md  # Circuit breaker (Bangla)
├── CONFIGURATION_SYSTEM_DOCUMENTATION_BANGLA.md  # Config docs (Bangla)
├── CONFIGURATION_MANAGEMENT_IMPLEMENTATION_PLAN_BANGLA.md  # Config plan (Bangla)
├── CONFIGURATION_IMPROVEMENT_SUMMARY_BANGLA.md  # Config summary (Bangla)
├── SUPREMEAI_2_0_COMPLETE_SYSTEM_DOCUMENT.md  # Complete system doc
├── SUPREMEAI_2_0_COMPLETE_SYSTEM_DOCUMENT_BANGLA.md  # Complete system doc (Bangla)
├── SUPREMEAI_MASTER_BLUEPRINT.md  # Master blueprint
├── SUPREMEAI_SYSTEM_MODULES_EXPLAINED.md  # System modules
├── SYSTEM_IMPROVEMENT_ANALYSIS_BANGLA.md  # System analysis (Bangla)
├── PHASE2_SECURITY_AUDIT_IMPLEMENTATION.md  # Phase 2 security
├── PHASE3_LLM_ORCHESTRATION_AUDIT.md  # Phase 3 LLM
├── PHASE4_DATABASE_PERSISTENCE_AUDIT.md  # Phase 4 database
├── PHASE5_CACHING_PERFORMANCE_AUDIT.md  # Phase 5 caching
├── PHASE6_API_MIDDLEWARE_AUDIT.md  # Phase 6 API
├── GITHUB_CI_1269_COMMIT_ANALYSIS_REPORT.md  # CI analysis
├── ci-backend-test-failure-rootcause.md  # CI failure analysis
├── auto_fix_in_github_implementation_plan.md  # Auto-fix plan
├── pre-merge-vs-pre-commit.md      # Pre-merge vs pre-commit
├── README-CI-PARITY-HOOKS.md      # CI parity hooks
├── local-changes.md                # Local changes
├── session-summary.md              # Session summary
├── evolution_log.md                # Evolution log
├── checks.md                       # Checks
├── reference.md                    # Reference
├── quality/                        # Quality docs
├── reports/                        # Reports
├── operations/                     # Operations docs
├── developer-guide/                # Developer guides
├── guidelines/                     # Guidelines
├── api/                            # API docs
├── context_modules/                # Context modules
├── archived_reports/               # Archived reports
├── antigravity_brain_backup/       # Brain backups
├── 01-admin's plan/                # Admin plans
├── 01-project/                     # Project docs
├── 02-admin/                       # Admin docs
├── 02-governance/                  # Governance docs
├── 03-architecture/                # Architecture docs
├── 04-ci-logs/                     # CI logs
├── 04-development/                 # Development docs
├── 05-operations/                  # Operations docs
├── 06-api/                         # API docs
├── 06-devops/                      # DevOps docs
└── 08-roadmap/                     # Roadmap docs
    └── 09-security/                # Security docs
```

---

## ⚙️ Configuration Structure (`config/`)

```
config/
├── .pre-commit-config.yaml         # Pre-commit hooks
├── agent_rules.json                # Agent rules
├── audit-rules.yml                 # Audit rules
├── compliance-rules.yml            # Compliance rules
├── docker-limits.yml               # Docker limits
├── dummy_registry.json             # Dummy registry
├── firestore.indexes.json          # Firestore indexes
├── firestore.rules                 # Firestore rules
├── kilo.json                       # Kilo configuration
├── promptfooconfig.yaml            # Promptfoo config
├── proxy_list.json                 # Proxy list
├── routing_policy.json             # LLM routing policy
└── vercel.json                     # Vercel config
```

---

## 🚀 Deployment Configuration

### Render (`render.yaml`)
```yaml
services:
  - type: web
    name: supremeai-backend
    runtime: docker
    plan: free
    region: singapore
    branch: main
    dockerfile: backend/Dockerfile
    envVars:
      - key: SERVICE_ROLE
        value: user
      - key: ENV
        value: production
    healthCheckPath: /health
    autoDeploy: true

  - type: web
    name: supremeai-admin
    runtime: docker
    plan: free
    region: singapore
    branch: main
    dockerfile: backend/Dockerfile
    envVars:
      - key: SERVICE_ROLE
        value: admin
      - key: ENV
        value: production
    healthCheckPath: /health
    autoDeploy: true
```

### Vercel (`vercel.json`)
```json
{
  "version": 2,
  "builds": [
    {
      "src": "apps/studio-client/package.json",
      "use": "@vercel/static-build"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "https://supremeai-backend-08zd.onrender.com/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "apps/studio-client/dist/$1"
    }
  ]
}
```

### Firebase (`firebase.json`)
```json
{
  "hosting": {
    "site": "supremeai-admin",
    "public": "apps/studio-client/dist-admin",
    "rewrites": [
      {
        "source": "/admin-api/**",
        "destination": "https://supremeai-backend-secondary.onrender.com/admin-api/**"
      }
    ]
  }
}
```

---

## 🔄 CI/CD Structure (`.github/workflows/`)

```
.github/
└── workflows/
    ├── backend-core.yml            # Backend core tests
    ├── backend-api.yml             # Backend API tests
    ├── backend-integration.yml     # Backend integration tests
    ├── frontend-unit.yml           # Frontend unit tests
    ├── frontend-e2e.yml            # Frontend E2E tests
    ├── mobile-test.yml             # Mobile tests
    ├── security-scan.yml           # Security scanning
    ├── dependency-audit.yml        # Dependency audit
    ├── build-docker.yml            # Docker build
    ├── deploy-render.yml           # Deploy to Render
    ├── deploy-vercel.yml           # Deploy to Vercel
    ├── deploy-firebase.yml         # Deploy to Firebase
    └── ...
```

---

## 🐳 Docker Structure

### Production Dockerfile (`backend/Dockerfile`)
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "core.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### CI Dockerfile (`backend/Dockerfile.ci`)
```dockerfile
FROM python:3.11-slim

# Install all dependencies including dev
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

# Install with dev dependencies for testing
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY . .

CMD ["pytest", "tests/", "-v"]
```

---

## 🔗 Related Documents

- [03-ARCHITECTURE.md](03-ARCHITECTURE.md) - System architecture
- [05-MODULE_DOCUMENTATION.md](05-MODULE_DOCUMENTATION.md) - Module details
- [07-DEPENDENCY_DOCUMENTATION.md](07-DEPENDENCY_DOCUMENTATION.md) - Dependencies
- [08-CONFIGURATION_DOCUMENTATION.md](08-CONFIGURATION_DOCUMENTATION.md) - Configuration
- [21-DEPLOYMENT_DOCUMENTATION.md](21-DEPLOYMENT_DOCUMENTATION.md) - Deployment

---

## ✅ Folder Structure Verification

**How to verify this structure**:

1. **Check Directory Exists**:
   ```bash
   ls -la backend/
   ls -la apps/studio-client/
   ls -la docs/
   ```

2. **Verify Key Files**:
   ```bash
   test -f backend/main.py && echo "✓ backend/main.py exists"
   test -f backend/pyproject.toml && echo "✓ backend/pyproject.toml exists"
   test -f apps/studio-client/package.json && echo "✓ package.json exists"
   test -f docs/knowledge-base/INDEX.md && echo "✓ Knowledge base exists"
   ```

3. **Count Files**:
   ```bash
   find backend -name "*.py" | wc -l
   find apps/studio-client/src -name "*.tsx" -o -name "*.ts" | wc -l
   ```

---

**Document Status**: ✅ Complete and Verified  
**Next Review**: 2025-02-04  
**Owner**: Engineering Team