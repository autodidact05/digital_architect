# Standard FastAPI Project Structure

## Overview and scope

The purpose of this document is to define the standard project structure for FastAPI applications within Xentic. This standard aims to ensure consistency, maintainability, and scalability across all backend services developed using FastAPI. It is intended for software engineers, architects, and team leads involved in the development and deployment of FastAPI applications at Xentic.

### Audience
- Software Engineers
- Technical Architects
- Development Team Leads
- Quality Assurance Engineers

### Scope
This standard applies to all new FastAPI projects initiated within Xentic. It encompasses:
- Directory structure
- Configuration management
- Code organization
- Dependency management
- Best practices for development and deployment

### Non-goals
This document does NOT cover:
- Frontend development standards
- Non-FastAPI backend frameworks
- Specific deployment strategies or tools outside the scope of FastAPI

### Glossary
| Term               | Definition                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| FastAPI            | A modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints. |
| Dependency Injection| A design pattern that allows for the removal of hard-coded dependencies, making code more modular and testable. |
| Pydantic           | A data validation and settings management library for Python, used for defining data models. |

### How this standard fits the Xentic platform
This standard aligns with Xentic's broader architectural principles of modularity, reusability, and maintainability. By adhering to this structure, teams can ensure that their FastAPI applications integrate seamlessly with existing services, libraries, and infrastructure components within the Xentic ecosystem. 

### Project Structure Layout
The following directory structure is recommended for all FastAPI projects at Xentic:

```plaintext
app/
├── api/v1/
│   ├── router.py
│   └── endpoints/
│       ├── users.py
│       └── orders.py
├── core/
│   ├── config.py
│   ├── security.py
│   └── dependencies.py
├── db/
│   ├── session.py
│   └── base.py
├── models/
├── schemas/
├── services/
├── repositories/
└── main.py
```

### App Factory Example
To create a FastAPI application, use the following app factory pattern:

```python
from fastapi import FastAPI
from app.api.v1.router import api_router
from app.core.config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    )
    app.include_router(api_router, prefix="/api/v1")
    return app

app = create_app()
```

### Configuration Management
Utilize Pydantic for configuration management as shown below:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "My Service"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
```

### Development Rules
- All endpoints MUST be asynchronous to leverage FastAPI's performance capabilities.
- Dependency injection MUST be used for database sessions, authentication, and pagination.
- The `/docs` endpoint MUST NOT be exposed in production environments to enhance security.

## Standards and policies

1. **Project Structure**  
   All FastAPI projects MUST adhere to the prescribed directory structure outlined in the Project Structure Layout section. This ensures uniformity across all services.

2. **Package Naming**  
   All Python packages MUST follow the naming convention `com.xentic.<service>`. For example, a user service should be named `com.xentic.user`. This aligns with Xentic's Java base package standards.

3. **Configuration Management**  
   Configuration files MUST be managed using Pydantic and MUST include an `.env` file for environment-specific variables. The configuration class MUST extend `BaseSettings` to facilitate loading from the environment.

4. **Environment Variables**  
   All sensitive information, such as database URLs and secret keys, MUST be stored in environment variables and MUST NOT be hard-coded in the application code.

5. **Asynchronous Endpoints**  
   All endpoints MUST be defined as asynchronous functions to take full advantage of FastAPI's performance capabilities. This is critical for handling concurrent requests efficiently.

6. **Dependency Injection**  
   Dependency injection MUST be utilized for managing database sessions, authentication, and any shared services. This promotes modularity and testability of the code.

7. **Documentation**  
   API documentation MUST be automatically generated using FastAPI's built-in documentation features. The `/docs` endpoint MUST NOT be exposed in production environments.

8. **Testing**  
   Unit and integration tests MUST be written for all services. Tests MUST use the `pytest` framework, and a dedicated `tests/` directory MUST be created at the root level of the project.

9. **Error Handling**  
   Global error handling MUST be implemented using FastAPI's exception handlers. Custom exceptions MUST be defined for application-specific errors.

10. **Logging**  
    Logging MUST be configured to capture application logs at various levels (INFO, WARNING, ERROR). A logging configuration file (e.g., `logging.yaml`) MUST be included in the `core/` directory.

11. **Code Style**  
    Code MUST adhere to PEP 8 style guidelines. A linter (e.g., flake8) MUST be used to enforce code quality.

12. **Version Control**  
    All code MUST be version-controlled using Git. Each project MUST have a `.gitignore` file to exclude unnecessary files and directories.

13. **Database Migrations**  
    Database migrations MUST be managed using Alembic. A `migrations/` directory MUST be created at the root level of the project to store migration scripts.

14. **Service Dependencies**  
    External service dependencies MUST be documented in a `requirements.txt` file. This file MUST be kept up-to-date with the required packages and their versions.

15. **Code Reviews**  
    All code changes MUST undergo peer review before being merged into the main branch. This ensures code quality and adherence to Xentic standards.

16. **Security Practices**  
    Security best practices MUST be followed, including input validation, output encoding, and proper authentication mechanisms. The use of OAuth2 with JWT tokens is recommended for securing endpoints.

17. **Performance Monitoring**  
    Performance monitoring tools MUST be integrated into the application to track response times and error rates. This data MUST be reviewed regularly to identify potential bottlenecks.

18. **Continuous Integration/Continuous Deployment (CI/CD)**  
    A CI/CD pipeline MUST be established for automated testing and deployment of FastAPI applications. This pipeline MUST include steps for building, testing, and deploying the application to production.

19. **Static Code Analysis**  
    Static code analysis tools (e.g., mypy, pylint) MUST be integrated into the development workflow to catch potential issues early in the development process.

20. **Service Documentation**  
    Each service MUST include a `README.md` file at the root level, providing an overview of the service, setup instructions, and usage examples. This documentation MUST be kept up-to-date.

By adhering to these standards and policies, Xentic aims to maintain high-quality, scalable, and secure FastAPI applications across all teams.

## Architecture and design

The architecture of a FastAPI application at Xentic is designed to be modular, scalable, and maintainable. The following sections outline the component diagram, data flows, integration points, and failure domains.

### Component Diagram

The following diagram illustrates the key components of a FastAPI application and their interactions:

```mermaid
graph TD;
    A[Client] -->|HTTP Requests| B[FastAPI Application]
    B -->|CRUD Operations| C[Database]
    B -->|Authentication| D[Auth Service]
    B -->|External API Calls| E[External Services]
    B -->|Logging| F[Logging Service]
    B -->|Monitoring| G[Monitoring Service]
```

### Data Flows

- **Client to FastAPI Application**: Clients send HTTP requests to the FastAPI application, which processes these requests and returns responses.
- **FastAPI Application to Database**: The application interacts with the database to perform Create, Read, Update, and Delete (CRUD) operations.
- **FastAPI Application to Auth Service**: For authentication, the application communicates with the Auth Service to validate user credentials and issue tokens.
- **FastAPI Application to External Services**: The application may need to call external APIs for additional data or services.
- **FastAPI Application to Logging and Monitoring Services**: The application logs important events and metrics to facilitate monitoring and debugging.

### Integration Points

- **Database Integration**: The FastAPI application MUST connect to a relational database (e.g., PostgreSQL) using an ORM like SQLAlchemy. The database connection string should be stored in environment variables.
  
  Example of a database connection configuration in `db/session.py`:

  ```python
  from sqlalchemy import create_engine
  from sqlalchemy.ext.declarative import declarative_base
  from sqlalchemy.orm import sessionmaker
  from app.core.config import settings

  DATABASE_URL = settings.DATABASE_URL
  engine = create_engine(DATABASE_URL)
  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  Base = declarative_base()
  ```

- **Authentication Service**: Integration with an authentication service (e.g., OAuth2) MUST be implemented to manage user sessions and secure endpoints.

- **External APIs**: Any integration with external APIs MUST be handled through dedicated service classes to encapsulate the logic and manage errors effectively.

### Failure Domains

- **Database Failures**: If the database becomes unavailable, the application MUST handle exceptions gracefully and return appropriate error messages to clients. A retry mechanism SHOULD be implemented for transient failures.

- **Authentication Failures**: If the authentication service fails, the application MUST return a 401 Unauthorized response to the client. Proper logging of authentication errors MUST be ensured.

- **External API Failures**: The application MUST handle failures when calling external APIs by implementing timeouts and retries. Fallback mechanisms SHOULD be considered to provide alternative responses when external services are down.

- **Application Errors**: Global error handling MUST be implemented to catch unhandled exceptions and return standardized error responses. This can be done using FastAPI's exception handlers.

### Summary

By adhering to the architecture and design principles outlined above, FastAPI applications at Xentic will be robust, maintainable, and capable of handling various failure scenarios effectively. This ensures a high-quality experience for clients and a streamlined development process for engineers.

## Configuration reference

Configuration management is critical for the successful deployment and operation of FastAPI applications at Xentic. Below are the standards for configuration files, environment variables, and Terraform settings, along with their default and production values.

### application.yml

The `application.yml` file MUST be structured as follows:

```yaml
app:
  name: "Xentic FastAPI Service"
  version: "1.0.0"
  debug: false
  host: "0.0.0.0"
  port: 8000
  log_level: "INFO"

database:
  url: "${DATABASE_URL}"
  max_connections: 20
  min_connections: 5

auth:
  jwt_secret: "${JWT_SECRET}"
  algorithm: "HS256"
  token_expiration: "3600"  # in seconds

service:
  external_api_url: "${EXTERNAL_API_URL}"
```

### Terraform Configuration

The following Terraform configuration MUST be used for deploying resources related to the FastAPI application. This includes setting up environment variables in a secure manner.

```hcl
resource "aws_lambda_function" "fastapi_service" {
  function_name = "xentic_fastapi_service"
  handler       = "app.main:app"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_exec.arn
  source_code_hash = filebase64sha256("path/to/package.zip")

  environment {
    DATABASE_URL     = var.database_url
    JWT_SECRET       = var.jwt_secret
    EXTERNAL_API_URL = var.external_api_url
  }
}

variable "database_url" {
  description = "Database connection string"
  type        = string
}

variable "jwt_secret" {
  description = "Secret key for JWT"
  type        = string
}

variable "external_api_url" {
  description = "Base URL for external API"
  type        = string
}
```

### Environment Variables

The following table outlines the required environment variables, their default values, and production values:

| Variable             | Default Value                     | Production Value                        |
|----------------------|-----------------------------------|----------------------------------------|
| DATABASE_URL         | "postgresql://user:pass@localhost/db" | "postgresql://user:pass@prod-db:5432/db" |
| JWT_SECRET           | "defaultsecret"                  | "supersecretproductionkey"             |
| EXTERNAL_API_URL     | "https://api.internal.xentic.io" | "https://api.prod.xentic.io"          |
| LOG_LEVEL            | "DEBUG"                          | "ERROR"                                |
| APP_PORT             | 8000                             | 80                                     |

### Important Notes

- The `DATABASE_URL` MUST point to a secure database instance in production.
- The `JWT_SECRET` MUST be a strong, randomly generated string and MUST NOT be shared.
- The `EXTERNAL_API_URL` MUST be configured to point to the correct environment-specific API endpoint.
- The `LOG_LEVEL` MUST be adjusted according to the environment; DEBUG should only be used in development.
- The application MUST read these environment variables at runtime, ensuring sensitive data is not hard-coded in the source code.

By following these configuration guidelines, Xentic ensures that FastAPI applications are secure, maintainable, and adaptable to various environments.

## Implementation guide

To implement a FastAPI project at Xentic, follow the step-by-step guide below. This guide covers the project structure, essential components, and provides code examples for each module.

### 1. Project Structure

The FastAPI project structure MUST be organized as follows:

```
/xentic-fastapi-service
│
├── app
│   ├── __init__.py
│   ├── main.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── v1
│   │   │   ├── __init__.py
│   │   │   ├── endpoints.py
│   │   │   └── models.py
│   ├── core
│   │   ├── __init__.py
│   │   └── config.py
│   ├── db
│   │   ├── __init__.py
│   │   └── session.py
│   ├── services
│   │   ├── __init__.py
│   │   └── auth.py
│   └── utils
│       ├── __init__.py
│       └── logger.py
│
├── requirements.txt
└── application.yml
```

### 2. Main Application File

The `main.py` file MUST serve as the entry point for the FastAPI application. Below is an example:

```python
from fastapi import FastAPI
from app.api.v1.endpoints import router as api_router
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.include_router(api_router, prefix="/api/v1")
```

### 3. Configuration Management

The `config.py` file MUST manage application settings:

```python
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Xentic FastAPI Service"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    EXTERNAL_API_URL: str = os.getenv("EXTERNAL_API_URL")

settings = Settings()
```

### 4. Database Session Management

The `session.py` file MUST handle the database connection using SQLAlchemy:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

### 5. API Endpoints

The `endpoints.py` file MUST define the API routes:

```python
from fastapi import APIRouter, Depends
from app.services.auth import get_current_user
from app.api.v1.models import User

router = APIRouter()

@router.get("/users/", response_model=list[User])
async def read_users(current_user: User = Depends(get_current_user)):
    return [{"username": current_user.username}]
```

### 6. Models

The `models.py` file MUST define the data models:

```python
from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str
```

### 7. Authentication Service

The `auth.py` file MUST implement the authentication logic:

```python
from fastapi import Depends, HTTPException, status
from app.core.config import settings
from app.utils.logger import logger

async def get_current_user(token: str):
    if token != settings.JWT_SECRET:
        logger.error("Invalid token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"username": "test_user", "email": "test@example.com"}
```

### 8. Logger Utility

The `logger.py` file MUST provide logging functionality:

```python
import logging

logger = logging.getLogger("fastapi")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
```

### 9. Requirements File

The `requirements.txt` file MUST list all dependencies:

```
fastapi
uvicorn
sqlalchemy
pydantic
```

### 10. Running the Application

To run the FastAPI application, use the following command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Summary

By following this implementation guide, Xentic developers will create a well-structured, maintainable FastAPI application. Each module serves a specific purpose, ensuring clarity and separation of concerns, which is essential for enterprise-grade applications.

## Security requirements

Ensuring the security of FastAPI applications at Xentic is paramount. The following security requirements outline the necessary measures to protect against various threats, manage authentication and authorization, handle secrets, validate inputs, and maintain audit logging.

### Threat Model Summary

A comprehensive threat model MUST be established to identify potential vulnerabilities. Key threats include:

- **Unauthorized Access**: Attackers may attempt to gain access to sensitive endpoints.
- **Data Exposure**: Sensitive data may be exposed through improper handling or logging.
- **Injection Attacks**: SQL or code injection attacks can compromise the application.
- **Denial of Service (DoS)**: Attackers may attempt to overwhelm the application with requests.

### Authentication and Authorization

Authentication and authorization MUST be implemented using JWT (JSON Web Tokens). The following guidelines apply:

- **JWT Implementation**: All APIs MUST require a valid JWT for access. Tokens MUST be signed using a secure algorithm (e.g., HS256).
- **User Roles**: Role-based access control (RBAC) MUST be enforced to restrict access based on user roles.
- **Token Expiration**: Tokens MUST have an expiration time to minimize the risk of misuse.

Example of JWT validation:

```python
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from app.core.config import settings

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    return username
```

### Secrets Management

Sensitive information MUST NOT be hard-coded in the source code. Instead, secrets MUST be managed through environment variables or secure vaults. 

- **Environment Variables**: Use environment variables for secrets such as JWT keys, database URLs, and API keys.
- **Secret Rotation**: Secrets MUST be rotated regularly to minimize exposure risk.

Example of environment variable usage in configuration:

```python
import os

class Settings(BaseSettings):
    JWT_SECRET: str = os.getenv("JWT_SECRET")
```

### Input Validation

Input validation is critical to prevent injection attacks and ensure data integrity. The following practices MUST be followed:

- **Pydantic Models**: All incoming data MUST be validated using Pydantic models to enforce type checking and constraints.
- **Sanitization**: User inputs MUST be sanitized to remove potentially harmful characters.

Example of a Pydantic model for user input:

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
```

### Audit Logging

Audit logging MUST be implemented to track access and changes to sensitive data. The following requirements apply:

- **Log Sensitive Actions**: Actions such as user logins, data modifications, and permission changes MUST be logged.
- **Log Format**: Logs MUST include timestamps, user identifiers, action types, and affected resources.

Example of logging an action:

```python
import logging

logger = logging.getLogger("fastapi")

def log_user_action(user_id: str, action: str):
    logger.info(f"User {user_id} performed action: {action}")
```

### Summary

By adhering to these security requirements, FastAPI applications at Xentic will be better equipped to mitigate risks associated with unauthorized access, data exposure, and other potential threats. Implementing robust authentication, managing secrets securely, validating inputs thoroughly, and maintaining comprehensive audit logs are essential steps for achieving a secure application environment.

## Testing strategy

A comprehensive testing strategy is essential for ensuring the reliability and quality of FastAPI applications at Xentic. The testing strategy MUST include unit tests, integration tests, and contract tests, along with specific coverage targets. 

### Testing Types

1. **Unit Tests**: 
   - Focus on individual components or functions.
   - Each unit test MUST be isolated and should not depend on external systems.

2. **Integration Tests**: 
   - Validate the interaction between multiple components.
   - Integration tests MUST cover database interactions, API endpoints, and external service calls.

3. **Contract Tests**: 
   - Ensure that services adhere to agreed-upon interfaces.
   - Contract tests MUST verify that the API responses conform to the expected schema.

### Coverage Targets

- **Unit Test Coverage**: MUST achieve at least 80% coverage.
- **Integration Test Coverage**: SHOULD aim for at least 70% coverage.
- **Contract Test Coverage**: MUST cover all public API endpoints.

### Testing Frameworks

- **pytest**: The primary testing framework MUST be `pytest`.
- **httpx**: For making HTTP requests in tests, `httpx` MUST be used.
- **pytest-asyncio**: For testing asynchronous code, `pytest-asyncio` MUST be included.

### Example Test Classes

#### Unit Test Example

```python
import pytest
from app.services.auth import get_current_user

@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    token = "valid_token"
    user = await get_current_user(token)
    assert user["username"] == "test_user"
    assert user["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    token = "invalid_token"
    with pytest.raises(HTTPException):
        await get_current_user(token)
```

#### Integration Test Example

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_users():
    response = client.get("/api/v1/users/", headers={"Authorization": "Bearer valid_token"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

#### Contract Test Example

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_user_endpoint_contract():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/users/")
        assert response.status_code == 200
        assert "username" in response.json()[0]
        assert "email" in response.json()[0]
```

### Running Tests

To run the tests, use the following command:

```bash
pytest --cov=app
```

### Summary

By implementing a robust testing strategy that includes unit, integration, and contract tests, Xentic developers will ensure the reliability and maintainability of FastAPI applications. Adhering to the coverage targets and utilizing the specified frameworks will facilitate a high-quality codebase that meets enterprise standards.

## Observability and operations

To ensure the reliability and performance of FastAPI applications at Xentic, observability practices MUST be implemented, including metrics collection, logging, distributed tracing, dashboards, alerts, and Service Level Objectives (SLOs). These practices will facilitate proactive monitoring and incident response.

### Metrics

Metrics MUST be collected to monitor application performance and health. Key metrics include:

- **Request Latency**: Measure the time taken to process requests.
- **Error Rates**: Track the percentage of failed requests.
- **Throughput**: Monitor the number of requests processed over time.
- **Resource Utilization**: Measure CPU and memory usage.

Example of integrating Prometheus for metrics collection:

```python
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

Instrumentator().instrument(app).expose(app)
```

### Logging

Logging MUST be comprehensive to facilitate troubleshooting and auditing. The following logging practices MUST be followed:

- **Log Levels**: Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
- **Structured Logging**: Logs MUST be structured (e.g., JSON) for easier parsing and analysis.
- **Log Rotation**: Implement log rotation to manage log file sizes.

Example of structured logging:

```python
import logging
import json

class CustomJsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "user_id": getattr(record, 'user_id', None),
        }
        return json.dumps(log_obj)

logger = logging.getLogger("fastapi")
handler = logging.StreamHandler()
handler.setFormatter(CustomJsonFormatter())
logger.addHandler(handler)
```

### Distributed Tracing

Distributed tracing MUST be implemented to track requests across microservices. Xentic recommends using OpenTelemetry for this purpose. Key components include:

- **Trace Context**: Pass trace context through headers.
- **Span Creation**: Create spans for significant operations.

Example of adding tracing:

```python
from opentelemetry import trace

tracer = trace.get_tracer("fastapi")

@app.get("/api/v1/items/")
async def read_items():
    with tracer.start_as_current_span("read_items"):
        # Business logic here
        return {"items": ["item1", "item2"]}
```

### Dashboards

Dashboards MUST be created to visualize key metrics and logs. Xentic recommends using Grafana for this purpose. Key dashboards include:

| Dashboard Name       | Description                          |
|----------------------|--------------------------------------|
| Application Health    | Displays error rates and latencies  |
| Performance Metrics   | Shows throughput and resource usage  |
| User Activity         | Tracks user logins and actions      |

### Alerts

Alerts MUST be configured to notify the on-call team of critical issues. Key alerting strategies include:

- **Error Rate Alerts**: Notify when error rates exceed a threshold.
- **Latency Alerts**: Trigger alerts for high request latencies.
- **Resource Utilization Alerts**: Alert when CPU or memory usage exceeds limits.

Example of alerting configuration in Prometheus:

```yaml
groups:
  - name: application_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status="500"}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "More than 5% of requests are failing."
```

### Service Level Objectives (SLOs)

SLOs MUST be defined to set performance expectations. Key SLOs include:

- **Availability**: 99.9% uptime.
- **Latency**: 95% of requests should be processed in under 200ms.
- **Error Rate**: Less than 1% of requests should result in errors.

### On-Call Runbook Steps

In the event of an incident, the following on-call runbook steps MUST be followed:

1. **Acknowledge Alert**: Confirm receipt of the alert.
2. **Assess Impact**: Determine the scope and impact of the issue.
3. **Investigate Logs**: Review logs for errors or anomalies.
4. **Check Metrics**: Analyze metrics for spikes in error rates or latency.
5. **Communicate**: Update stakeholders on the status of the incident.
6. **Mitigate**: Implement a temporary fix if possible.
7. **Document**: Record the incident details and resolution steps for future reference.
8. **Review**: Conduct a post-mortem to identify root causes and prevent recurrence.

### Summary

By implementing comprehensive observability practices, including metrics, logging, tracing, dashboards, alerts, and SLOs, Xentic can ensure that FastAPI applications are reliable and maintainable. Following the on-call runbook steps will facilitate effective incident response and continuous improvement.

## Migration and versioning

Effective migration and versioning strategies are crucial for maintaining the integrity and reliability of FastAPI applications at Xentic. This section outlines the policies and practices that MUST be followed during upgrades, deprecations, and rollbacks.

### Upgrade Paths

1. **Semantic Versioning**: All services MUST adhere to [Semantic Versioning](https://semver.org/) (e.g., MAJOR.MINOR.PATCH). Breaking changes MUST increment the MAJOR version, new features that are backward compatible MUST increment the MINOR version, and bug fixes MUST increment the PATCH version.

2. **Upgrade Documentation**: Each version release MUST include comprehensive upgrade documentation detailing:
   - Changes made
   - Migration steps
   - Configuration changes
   - Deprecated features

3. **Backward Compatibility**: New versions MUST maintain backward compatibility for at least one full version cycle. This means that any breaking changes MUST be introduced in a major version, allowing clients to upgrade at their convenience.

### Deprecation Policy

1. **Deprecation Notices**: Features that are scheduled for deprecation MUST be clearly documented in the release notes and marked in the codebase using comments. For example:

   ```python
   # Deprecated in v2.0.0: Use `new_function()` instead.
   def old_function():
       pass
   ```

2. **Grace Period**: A grace period of at least one full version cycle MUST be provided after deprecation notices are issued before the feature is removed. 

3. **Deprecation Warnings**: When a deprecated feature is used, a warning MUST be logged to inform developers. Example using Python's `warnings` module:

   ```python
   import warnings

   def old_function():
       warnings.warn("old_function() is deprecated and will be removed in v2.0.0", DeprecationWarning)
   ```

### Rollback Strategy

1. **Version Control**: All changes MUST be version-controlled using Git. Each release MUST have a corresponding Git tag for easy rollback.

2. **Rollback Procedures**: A clear rollback procedure MUST be documented and tested. The rollback process MUST include:
   - Reverting to the previous version in the version control system.
   - Restoring the previous database schema if applicable.
   - Re-deploying the previous application version.

3. **Database Migrations**: Database migrations MUST be reversible. Use tools like Alembic for managing database migrations, ensuring that each migration script can be rolled back. Example Alembic migration script:

   ```python
   from alembic import op
   import sqlalchemy as sa

   def upgrade():
       op.add_column('users', sa.Column('new_column', sa.String(length=50)))

   def downgrade():
       op.drop_column('users', 'new_column')
   ```

### Migration Example

When migrating from version 1.x to 2.x, the following steps MUST be taken:

1. **Review Release Notes**: Developers MUST read the release notes for version 2.x to understand breaking changes and new features.

2. **Update Dependencies**: Update all dependencies in `requirements.txt`:

   ```plaintext
   fastapi==2.0.0
   sqlalchemy==1.4.0
   ```

3. **Run Migrations**: Execute database migrations to ensure the schema is up to date:

   ```bash
   alembic upgrade head
   ```

4. **Test Application**: Thoroughly test the application in a staging environment before deploying to production.

5. **Deploy**: Once testing is complete, deploy the new version to production.

### Summary

By adhering to the outlined migration and versioning policies, Xentic ensures that FastAPI applications remain maintainable, reliable, and user-friendly. Proper documentation, a clear deprecation policy, and a well-defined rollback strategy are essential components of a successful migration process.

## FAQ, anti-patterns, and checklists

### FAQ

1. **What is FastAPI?**
   FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.6+ based on standard Python type hints.

2. **How do I structure a FastAPI project?**
   A typical structure includes directories for `app`, `models`, `routes`, `schemas`, and `tests`. Each service should have its own directory under `com.xentic.<service>`.

3. **What database should I use with FastAPI?**
   Xentic recommends using PostgreSQL for production applications due to its reliability and feature set.

4. **How can I handle authentication?**
   Use Xentic's shared library `com.xentic.auth:auth-starter` for implementing authentication and authorization.

5. **What testing framework should I use?**
   Use `pytest` for unit and integration testing as it is widely supported and integrates well with FastAPI.

6. **How do I manage dependencies?**
   Use `requirements.txt` for Python dependencies and ensure that all dependencies are pinned to specific versions.

7. **What is the recommended way to handle errors?**
   Implement custom exception handlers in FastAPI to manage errors gracefully and return meaningful error responses.

8. **How can I deploy FastAPI applications?**
   FastAPI applications can be deployed using Docker containers, and Xentic recommends using Kubernetes for orchestration.

9. **What should I do if I encounter performance issues?**
   Profile the application using tools like `cProfile` and optimize database queries and response times.

10. **How do I document my API?**
    FastAPI automatically generates interactive API documentation using Swagger UI and ReDoc. Ensure that all endpoints are well-documented with appropriate descriptions.

### Anti-Patterns

| Anti-Pattern                      | Description                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|
| Not Using Type Annotations        | Failing to use type annotations can lead to unclear code and runtime errors.|
| Hardcoding Configuration Values    | Configuration values MUST NOT be hardcoded; use environment variables instead.|
| Ignoring Asynchronous Features    | Blocking calls in async endpoints can lead to performance bottlenecks.     |
| Lack of Input Validation          | Failing to validate input data can lead to security vulnerabilities.       |
| Monolithic Codebase               | Avoid a single large application; split into microservices where applicable.|
| Not Handling Exceptions Properly  | Unhandled exceptions can crash the application; use custom exception handlers.|
| Skipping Tests                    | Not writing tests can lead to undetected bugs and regressions.             |

### Pre-Merge Checklist

- [ ] Code adheres to Xentic's coding standards and style guidelines.
- [ ] All new features are covered by unit tests.
- [ ] Documentation is updated to reflect changes.
- [ ] Code is reviewed by at least one other developer.
- [ ] No hardcoded secrets or sensitive information in the codebase.
- [ ] All dependencies are updated in `requirements.txt`.

### Production Checklist

- [ ] Ensure all migrations are applied to the production database.
- [ ] Verify that logging and monitoring are configured correctly.
- [ ] Confirm that alerts are set up for critical metrics.
- [ ] Conduct a final review of the deployment plan.
- [ ] Backup the current production environment before deployment.
- [ ] Validate that the application is functioning as expected post-deployment.
- [ ] Monitor application performance and error rates closely for the first 24 hours after deployment.
