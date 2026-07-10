# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in AgesAI, please report it responsibly.

### How to Report

1. **Do NOT** open a public GitHub issue for security vulnerabilities.
2. Email your findings to **security@ages-ai.dev** (or use GitHub's private vulnerability reporting).
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment** within 48 hours
- **Assessment** within 5 business days
- **Fix timeline** communicated within 10 business days
- **Credit** given in release notes (unless you prefer to remain anonymous)

### Scope

The following are in scope:
- API Gateway authentication/authorization bypass
- SQL injection, XSS, or CSRF vulnerabilities
- Secrets exposure in logs, API responses, or container images
- Privilege escalation
- Dependency vulnerabilities (critical/high severity)

### Out of Scope

- Social engineering attacks
- Denial of service (DoS) attacks
- Issues in third-party dependencies (report to the upstream project)
- Issues requiring physical access to the server

## Security Best Practices

This project follows these security practices:
- JWT-based authentication via Clerk
- Rate limiting on all API endpoints
- Structured logging with PII redaction
- Container image scanning with Trivy in CI
- Dependency auditing with Dependabot
- Secrets managed via environment variables (never committed)
- Agent code execution in sandboxed containers
