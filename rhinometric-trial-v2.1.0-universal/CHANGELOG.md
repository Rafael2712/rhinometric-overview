# Changelog

All notable changes to Rhinometric will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-10-29

### 🎉 Major Features

#### License Management System
- **New License Management UI** (port 8092) - Vue.js web interface for generating and managing licenses
- **Unlimited License Generation** - Trial (30 days), Annual (365 days), Permanent (100 years)
- **Real Admin Endpoints** (`/api/admin/licenses`) - No trial mode restrictions
- **Email Integration** - Automatic license delivery via Zoho SMTP with HTML templates
- **License Statistics Dashboard** - Real-time metrics on active, expired, and total licenses

#### Security & Infrastructure
- **Apache 2.0 LICENSE** - Open source with commercial support clarification
- **Credentials Removed** - All hardcoded passwords eliminated from documentation
- **Enhanced .env.example** - Comprehensive configuration template with SMTP settings
- **Security Warnings** - Best practices documentation for production deployments

#### One-Command Installers
- **install.sh** (Linux/macOS) - 400-line automated installer with prerequisite checks
- **install.ps1** (Windows) - PowerShell native installer with health monitoring
- **Auto-configuration** - Generates secure random passwords, creates .env automatically
- **Health Checks** - Waits 30-60s for all services to become healthy before completion

#### CI/CD Pipeline
- **GitHub Actions Workflow** - 8 automated jobs on every push/PR
  - Config validation (docker-compose syntax)
  - Terraform validation (fmt, init, validate)
  - Security scan (credential exposure detection)
  - Docker image builds (License Server, License UI)
  - Integration tests (PostgreSQL, Redis)
  - Documentation checks (markdown link validation)
  - Build reports with job summaries

#### Terraform Infrastructure as Code
- **Multi-Cloud README** - Strategy overview for Oracle, AWS, Azure, GCP
- **Oracle Cloud Deployment** - Production-ready Terraform modules
  - E4.Flex instances with configurable OCPU/RAM
  - VCN with security lists for all required ports
  - Cost estimates (Free Tier vs Production)
  - terraform.tfvars.example with detailed configuration

#### Automatic Email System (NEW v2.1.0)
- **Email Module** (`utils/email_sender.py`) - 345 lines with GDPR compliance
  - HTML email template with gradient header, license box, installation steps
  - Plain text alternative for clients without HTML support
  - GDPR compliance banner (RGPD 2016/679) with user rights notice
  - PDF attachments: Manual de Usuario (20 pages), Guía de Instalación (15 pages)
  - Dual SMTP method: SSL (port 465) primary, STARTTLS (587) fallback
  - Retry mechanism: 1 attempt after 30 seconds on failure
  - Comprehensive logging to `/app/logs/license_mail.log`
- **Zoho Mail Integration** (smtp.zoho.eu) - European zone global SMTP
- **Integration** - Automatic email sending when licenses are created via `/api/admin/licenses`
- **Documentation** - `docs/EMAIL_SYSTEM_STATUS.md` with complete testing guide
- **User Manuals** - Professional documentation (600+ lines manual, 450+ lines installation guide)

### 🔧 Improvements

#### API Enhancements
- License key generation format: `RHINO-{TYPE}-{YEAR}-{12_RANDOM_CHARS}`
- Database persistence with PostgreSQL (licenses table)
- License type validation (trial, annual, permanent)
- Customer email validation with pydantic EmailStr
- Expiration date calculation with timezone awareness

#### Docker Compose
- All services on `rhinometric_network_v21` bridge network
- Health checks for critical services (Postgres, Redis, Grafana)
- Environment variable interpolation from .env
- Volume mounts for persistent data

#### Documentation
- README updates with credential security warnings
- Installation guides for Linux, macOS, Windows
- Terraform deployment documentation
- API documentation via FastAPI Swagger UI (http://localhost:5000/api/docs)

### 🐛 Bug Fixes
- Fixed 404 errors on license creation (was calling `/api/demo/*`, now uses `/api/admin/*`)
- Corrected trial license duration (was 17 days, now 30 days as specified)
- Removed trial mode restrictions on admin endpoints
- Fixed email validator import (added `email-validator==2.1.0` dependency)
- PostgreSQL authentication issues resolved with proper credentials

### 📦 Dependencies
- Added `email-validator==2.1.0` for pydantic EmailStr support
- Updated FastAPI dependencies for async email sending
- Docker images use official latest stable versions

### 🗑️ Deprecated
- Legacy `/api/demo/licenses` endpoints (replaced by `/api/admin/licenses`)
- Hardcoded credentials in documentation files

### 🔒 Security
- All passwords now referenced via environment variables
- .env file added to .gitignore (never committed)
- LICENSE file created (Apache 2.0) for legal clarity
- Security scan integrated in CI/CD pipeline
- SMTP passwords use app-specific tokens (not main account password)

### 📊 Metrics
- 16 containers in production stack
- 400+ lines of installer automation
- 8 CI/CD jobs validating every commit
- 1670+ lines of code added in professionalization update
- 11 files modified in security & infrastructure improvements

### 🌐 Services
All services accessible after installation:
- **Grafana**: http://localhost:3000 (Observability dashboards)
- **Prometheus**: http://localhost:9090 (Metrics collection)
- **License Server API**: http://localhost:5000/api/docs (FastAPI Swagger)
- **API Connector UI**: http://localhost:8091 (External API monitoring)
- **License Management UI**: http://localhost:8092 (License generation)
- **Alertmanager**: http://localhost:9093 (Alert management)
- **PostgreSQL**: localhost:5432 (Database)
- **Redis**: localhost:6379 (Cache)

### 🙏 Acknowledgments
- ChatGPT-5 audit for GitHub repository improvement recommendations
- Community feedback on installation complexity
- Security best practices from OWASP guidelines

---

## [2.0.0] - 2025-XX-XX

### Added
- Initial Rhinometric observability platform
- Three-pillar monitoring (Metrics, Logs, Traces)
- Prometheus + Grafana + Loki + Tempo stack
- PostgreSQL + Redis data layer
- OTEL Collector for distributed tracing
- 8 pre-configured Grafana dashboards
- API Proxy for external service monitoring
- Nginx reverse proxy with SSL/TLS support

### Infrastructure
- Docker Compose orchestration
- Oracle Cloud Terraform deployment
- Network isolation with docker bridge
- Health checks for all critical services

---

## [Unreleased]

### Planned Features
- High Availability (HA) cluster configuration
- Automatic updates with rollback mechanism
- Multi-tenant federation support
- Screenshots and demo GIFs for documentation
- GitHub Issues roadmap and PROJECT board
- GDPR-compliant privacy policy (legal review pending)

---

**Full Changelog**: https://github.com/Rafael2712/mi-proyecto/compare/v2.0.0...v2.1.0
