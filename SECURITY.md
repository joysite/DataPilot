# Security Policy

## Supported Versions

DataPilot is currently under active development.

Security fixes are applied to the latest development version.
No older release series is currently guaranteed to receive security updates.

## Reporting a Vulnerability

Please do not disclose security vulnerabilities in public issues.

Until a dedicated security contact is established, report suspected
vulnerabilities privately to the repository maintainer through the
private contact channel associated with the repository hosting platform.

When reporting a vulnerability, include:

- A description of the potential security issue.
- Steps to reproduce the issue.
- The affected component or version.
- Potential impact and, if available, a suggested mitigation.

Please avoid including real customer data, credentials, API tokens,
or other sensitive information in vulnerability reports.

## Security Considerations

- Do not commit `.env` files, credentials, database files, or real business data.
- Keep local evaluation ground-truth data and generated reports out of public repositories.
- Agent tool execution is restricted to registered tools and validated arguments.
- Do not expose the local Ollama service or application APIs to untrusted networks
  without appropriate access controls.
- Review environment variables and volume mappings before running containerized
  deployments.
- Treat imported CSV files and user-provided content as untrusted input.

## Scope

This policy applies to the DataPilot application, its backend, frontend,
Agent workflow, data ingestion, and deployment configuration.
