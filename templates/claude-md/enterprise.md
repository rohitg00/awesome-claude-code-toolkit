# Enterprise Portal

Internal enterprise portal for employee management, compliance tracking, and reporting.

## Stack
- **Language**: Java 21 (backend), TypeScript 5.x (frontend)
- **Backend**: Spring Boot 3.3, Spring Security, Spring Data JPA
- **Frontend**: React 19, Vite 6, Ant Design 5, TanStack Query
- **Database**: Oracle 23c (primary), PostgreSQL 16 (analytics)
- **Cache**: Hazelcast (distributed session cache)
- **Queue**: Apache Kafka (event streaming)
- **Auth**: Okta SSO (SAML 2.0) + Spring Security OAuth2
- **CI/CD**: Jenkins, SonarQube, Artifactory, ArgoCD
- **Infrastructure**: Kubernetes on AWS EKS, Terraform
- **Monitoring**: Datadog APM, PagerDuty, Splunk

## Commands
- `./gradlew build` - Build backend
- `./gradlew test` - Run unit tests
- `./gradlew integrationTest` - Run integration tests (requires Docker)
- `./gradlew sonar` - Run SonarQube analysis
- `npm run dev --workspace=frontend` - Start frontend dev server
- `npm run build --workspace=frontend` - Production frontend build
- `npm run test --workspace=frontend` - Frontend unit tests
- `docker compose up -d` - Start local dependencies (Oracle, Kafka, Redis)
- `./gradlew flywayMigrate` - Apply database migrations
- `./scripts/generate-api-client.sh` - Generate TypeScript API client from OpenAPI spec

## Project Structure
```
backend/
  src/main/java/com/acme/portal/
    config/           - Spring configuration, security, Kafka
    controller/       - REST controllers (thin, delegates to services)
    service/          - Business logic layer
    repository/       - JPA repositories and custom queries
    model/            - JPA entities and domain objects
    dto/              - Request/response DTOs with Jakarta validation
    mapper/           - MapStruct mappers (entity <-> DTO)
    event/            - Kafka producers and consumers
    security/         - Custom security filters, authorization
    exception/        - Global exception handler, error codes
  src/main/resources/
    db/migration/     - Flyway migration scripts
    application.yml   - Configuration (profiles: dev, staging, prod)
  src/test/           - Unit and integration tests
frontend/
  src/
    pages/            - Route-level page components
    components/       - Reusable UI components
    hooks/            - Custom React hooks
    api/              - Generated API client (OpenAPI)
    store/            - Zustand state management
    utils/            - Utility functions
```

## Compliance Requirements
- SOC 2 Type II: Audit logging for all data access and mutations.
- GDPR: Data export and deletion endpoints for user data.
- HIPAA: PHI fields encrypted at rest (AES-256) and in transit (TLS 1.3).
- Retain audit logs for 7 years. No hard deletes on regulated data.
- All API endpoints require authentication. No public endpoints.
- Role-based access control (RBAC) with four levels: Viewer, Editor, Admin, SuperAdmin.

## Conventions
- All REST endpoints versioned: `/api/v1/...`.
- DTOs validated with Jakarta Bean Validation annotations.
- MapStruct for all entity-to-DTO conversions. No manual mapping.
- Kafka events follow CloudEvents specification.
- Database migrations must be backward-compatible (no column drops without a 2-release window).
- Feature flags via LaunchDarkly for all new features. No code-level toggles.
- Every service method that modifies data must emit an audit event.

## Security
- Okta SSO for all authentication. No local user/password storage.
- API keys for service-to-service communication (rotated quarterly).
- Secrets stored in AWS Secrets Manager. Never in environment variables or config files.
- Dependency scanning via Snyk. Block PRs with critical vulnerabilities.
- SAST via SonarQube. Quality gate: 0 critical issues, 80% coverage on new code.
- Penetration testing quarterly via external vendor.

## Environment Variables
- `SPRING_DATASOURCE_URL` - Oracle JDBC connection string
- `SPRING_DATASOURCE_USERNAME` / `PASSWORD` - Database credentials
- `OKTA_ISSUER_URI` - Okta OIDC issuer
- `OKTA_CLIENT_ID` / `CLIENT_SECRET` - OAuth2 client credentials
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka broker addresses
- `HAZELCAST_CLUSTER_NAME` - Cache cluster identifier
- `DATADOG_API_KEY` - APM and logging
- `AWS_SECRETS_MANAGER_PREFIX` - Secrets namespace

## Key Decisions
| Date | Decision | Rationale |
|------|----------|-----------|
| 2024-03-01 | Oracle over PostgreSQL | Enterprise licensing agreement, existing DBA team |
| 2024-06-15 | Kafka over RabbitMQ | Event sourcing requirement, compliance audit trail |
| 2024-09-01 | MapStruct over manual mapping | Type safety, compile-time validation |
| 2025-01-10 | Okta over Auth0 | Corporate SSO standardization |
| 2025-04-20 | Hazelcast over Redis | Distributed session replication across AZs |
