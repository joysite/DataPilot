# Changelog

All notable changes to DataPilot will be documented in this file.

This project follows Semantic Versioning.

## [0.1.0] - 2026-11-22

### Added

- E-commerce user, product, and order data ingestion from CSV.
- Data validation, integrity checks, and import history.
- Business analytics tools for order summaries, trends, and category comparisons.
- Five types of business anomaly detection.
- LangGraph-based Agent workflow with controlled tool execution.
- Agent memory, conversation context handling, and SQLite checkpoint persistence.
- Agent evaluation metrics and execution tracing.
- MCP Server for exposing selected data analysis capabilities.
- FastAPI backend and Vue 3 frontend.
- Dockerfiles, Docker Compose configuration, and environment example.
- Automated backend tests covering Agent parsing, ingestion, database constraints, and import transactions.
- MIT License.

### Verified

- 90 automated backend tests passed.
- Backend Ruff checks passed.
- Backend formatting checks passed.
- Core frontend and backend business workflows passed browser acceptance.

### Known Limitations

- Real Agent conversation has not completed end-to-end browser acceptance.
- Docker image build, container startup, and deployment have not been performed.
- Docker configuration has only undergone static validation.
