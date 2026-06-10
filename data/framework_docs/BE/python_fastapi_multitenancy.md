# Multi-Tenancy — FastAPI

## Overview and scope

The purpose of this document is to outline the standards and best practices for implementing multi-tenancy in FastAPI applications at Xentic. This standard aims to ensure that all FastAPI services adhere to a consistent approach for managing multiple tenants, thereby improving maintainability, scalability, and security.

### Audience

This document is intended for:
- Backend engineers and developers working with FastAPI.
- Architects responsible for designing multi-tenant systems.
- Quality assurance teams evaluating multi-tenant implementations.

### Scope

This standard covers:
- Architectural patterns for multi-tenancy in FastAPI.
- Configuration management for tenant-specific settings.
- Database design and access patterns for multi-tenant applications.
- Security considerations and best practices for tenant isolation.

### Non-Goals

This document does NOT cover:
- Implementation details for non-FastAPI services.
- Frontend considerations for multi-tenant applications.
- Specific business logic related to individual tenants.

### Glossary

| Term              | Definition                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| Tenant            | An individual customer or client that uses the application.                |
| Multi-tenancy     | A software architecture where a single instance of an application serves multiple tenants. |
| Isolation         | The practice of ensuring that one tenant's data and operations do not affect another tenant. |
| Contextualization | The process of adapting application behavior based on the current tenant.  |

### How This Standard Fits the Xentic Platform

This standard aligns with Xentic's commitment to building scalable and secure applications. By implementing multi-tenancy following these guidelines, we ensure that:
- Each service can efficiently manage multiple tenants without compromising performance.
- Security measures are in place to protect tenant data from unauthorized access.
- Developers can leverage shared libraries (e.g., `com.xentic.auth:auth-starter`) to manage authentication and authorization across tenants.

### Example Configuration

A typical YAML configuration for a multi-tenant FastAPI application might look like this:

```yaml
database:
  url: "postgresql://user:password@db.internal.xentic.io:5432/mydatabase"
  tenant_schema: "public"

tenants:
  - id: "tenant1"
    name: "Tenant One"
    settings:
      feature_x_enabled: true
  - id: "tenant2"
    name: "Tenant Two"
    settings:
      feature_x_enabled: false
```

### Example Code Snippet

Below is a simple example demonstrating how to implement tenant context in FastAPI:

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db, SessionLocal

app = FastAPI()

def get_current_tenant(tenant_id: str):
    # Logic to fetch tenant details based on tenant_id
    tenant = fetch_tenant_from_db(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@app.get("/items/")
def read_items(tenant_id: str, db: Session = Depends(get_db)):
    tenant = get_current_tenant(tenant_id)
    # Fetch items specific to the tenant
    items = fetch_items_for_tenant(db, tenant.id)
    return items
```

By adhering to this standard, Xentic ensures that multi-tenancy is implemented effectively across all FastAPI services, fostering a robust and secure environment for our clients.

## Standards and policies

1. **MUST** implement multi-tenancy using a tenant identifier that is passed with each request, ensuring that all operations are scoped to the correct tenant.

2. **MUST NOT** hard-code tenant-specific configurations in the application code. All tenant-specific settings MUST be stored in a centralized configuration file or database.

3. **MUST** use the `com.xentic` package structure for all multi-tenant FastAPI services. For example, the package structure should follow `com.xentic.<service>`.

4. **SHOULD** use a shared library for authentication and authorization, such as `com.xentic.auth:auth-starter`, to manage tenant-specific access controls.

5. **MUST** implement tenant isolation at the database level. This can be achieved by using separate schemas for each tenant or by adding a tenant ID column to shared tables.

6. **MUST NOT** expose tenant data to other tenants. All queries and operations MUST filter data based on the current tenant context.

7. **SHOULD** log tenant-specific events and errors to a centralized logging system for easier debugging and monitoring.

8. **MUST** validate tenant IDs in all incoming requests to prevent unauthorized access to tenant data.

9. **SHOULD** provide a mechanism for tenant administrators to manage their settings and features through a dedicated admin interface.

10. **MUST** ensure that tenant-specific features are configurable through the application settings, allowing for flexibility in feature rollout.

11. **MUST NOT** use global variables or singletons to store tenant-specific data. Instead, use dependency injection to manage tenant context.

12. **SHOULD** implement caching strategies that consider tenant isolation to improve performance without compromising data integrity.

13. **MUST** document all tenant-specific configurations in the centralized configuration repository, ensuring clarity for all developers.

14. **MUST** use environment variables for sensitive tenant-specific information, such as database credentials, to enhance security.

15. **SHOULD** conduct regular security audits to ensure that tenant data is adequately protected against breaches.

16. **MUST** provide clear API documentation that outlines how to interact with tenant-specific endpoints.

17. **MUST NOT** allow cross-tenant data access through API endpoints. Each endpoint MUST enforce tenant context.

18. **SHOULD** implement rate limiting on a per-tenant basis to prevent abuse and ensure fair resource allocation.

19. **MUST** ensure that all database migrations are compatible with the multi-tenant architecture and do not disrupt existing tenants.

20. **SHOULD** include automated tests that cover multi-tenant scenarios to ensure that changes do not introduce regressions.

21. **MUST** use a consistent naming convention for tenant-related database tables and columns to enhance readability and maintainability.

22. **MUST NOT** expose internal URLs or sensitive information in error messages returned to clients.

23. **SHOULD** consider using feature flags to enable or disable features on a per-tenant basis, allowing for controlled feature rollout.

24. **MUST** provide a fallback mechanism for tenant-specific configurations, ensuring that the application can operate with default settings if tenant-specific settings are not found.

25. **SHOULD** provide a method for tenants to export their data securely, ensuring compliance with data protection regulations.

By adhering to these standards and policies, Xentic will ensure a robust, secure, and maintainable multi-tenant architecture in all FastAPI applications.

## Architecture and design

### Component Diagram

```mermaid
graph TD;
    A[Client Application] -->|HTTP Requests| B[FastAPI Service]
    B -->|Database Queries| C[PostgreSQL Database]
    B -->|Auth Requests| D[Auth Service]
    B -->|Feature Flags| E[Feature Management Service]
    C -->|Tenant Data| F[Tenant Schema]
    F -->|Data Isolation| G[Data Access Layer]
    D -->|Token Validation| H[Token Service]
```

### Data Flows

1. **Client Requests**: Clients interact with the FastAPI service through HTTP requests, providing a tenant identifier (e.g., via a header or query parameter).
2. **Tenant Context Resolution**: The FastAPI service resolves the tenant context based on the provided identifier, ensuring that all subsequent operations are scoped to the correct tenant.
3. **Database Interaction**: The service queries the PostgreSQL database, either using tenant-specific schemas or filtering data by tenant ID.
4. **Authentication**: Requests to the Auth Service validate the user's credentials and issue tokens that are tenant-aware.
5. **Feature Management**: The service checks with the Feature Management Service to determine which features are enabled for the specific tenant.

### Integration Points

- **PostgreSQL Database**: The primary data store, where tenant data is either isolated by schemas or identified by tenant IDs in shared tables.
- **Auth Service**: Handles authentication and authorization, ensuring that users can only access resources belonging to their tenant.
- **Feature Management Service**: Provides a way to enable or disable features on a per-tenant basis, allowing for customizable experiences.

### Failure Domains

- **Database Failures**: If the database becomes unavailable, all tenant operations will be affected. Implement retry logic and fallback mechanisms to handle transient failures.
- **Auth Service Failures**: If the Auth Service is down, users will be unable to authenticate, which may prevent access to the application. Implement local caching of tokens where feasible.
- **Feature Management Failures**: If the Feature Management Service fails, tenants may not be able to access their configured features. Default settings should be applied in such cases.

### Example SQL for Tenant Isolation

Assuming a shared table structure with a tenant ID:

```sql
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Query to fetch items for a specific tenant
SELECT * FROM items WHERE tenant_id = 'tenant-uuid-here';
```

### Example Code for Tenant Context Management

The following code snippet demonstrates how to manage tenant context in FastAPI:

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db, SessionLocal

app = FastAPI()

def get_current_tenant(tenant_id: str):
    tenant = fetch_tenant_from_db(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@app.get("/items/")
def read_items(tenant_id: str, db: Session = Depends(get_db)):
    tenant = get_current_tenant(tenant_id)
    items = db.query(Item).filter(Item.tenant_id == tenant.id).all()
    return items
```

### Summary

By adhering to the architectural guidelines outlined in this section, Xentic can ensure a robust, scalable, and secure multi-tenant FastAPI application. Each component plays a critical role in maintaining tenant isolation and managing data flows effectively.

## Configuration reference

### application.yml

The `application.yml` file is used to configure tenant-specific settings. Below is an example configuration with default and production values.

```yaml
app:
  name: "Xentic Multi-Tenant FastAPI"
  environment: "production" # Change to "development" for local testing

database:
  host: "db.internal.xentic.io"
  port: 5432
  username: "${DB_USERNAME}" # Set via environment variable
  password: "${DB_PASSWORD}" # Set via environment variable
  name: "xentic_multi_tenant"

tenants:
  default:
    features:
      featureA: true
      featureB: false
    settings:
      max_items_per_page: 100
  tenant1:
    features:
      featureA: true
      featureB: true
    settings:
      max_items_per_page: 50
  tenant2:
    features:
      featureA: false
      featureB: true
    settings:
      max_items_per_page: 200
```

### Terraform Configuration

Use Terraform to manage infrastructure related to multi-tenancy. Below is an example of how to provision a PostgreSQL database for tenants.

```hcl
provider "postgresql" {
  host     = "db.internal.xentic.io"
  port     = 5432
  username = var.db_username
  password = var.db_password
}

resource "postgresql_database" "xentic_multi_tenant" {
  name = "xentic_multi_tenant"
}

resource "postgresql_schema" "tenant1_schema" {
  name     = "tenant1"
  database = postgresql_database.xentic_multi_tenant.name
}

resource "postgresql_schema" "tenant2_schema" {
  name     = "tenant2"
  database = postgresql_database.xentic_multi_tenant.name
}
```

### Environment Variables

The following environment variables are required for the application to function correctly. Default values are provided for local development, while production values should be securely managed.

| Variable         | Default Value         | Production Value              |
|-------------------|----------------------|-------------------------------|
| `DB_USERNAME`     | `dev_user`           | `prod_user`                   |
| `DB_PASSWORD`     | `dev_password`       | `prod_secure_password`        |
| `TENANT1_FEATURE_A` | `true`              | `true`                        |
| `TENANT1_FEATURE_B` | `false`             | `true`                        |
| `TENANT2_FEATURE_A` | `false`             | `false`                       |
| `TENANT2_FEATURE_B` | `true`              | `true`                        |

### Key Considerations

- **MUST** ensure that sensitive information such as database credentials is stored in environment variables.
- **MUST NOT** hard-code any sensitive information directly in the codebase or configuration files.
- **SHOULD** use a centralized configuration management tool to handle environment-specific configurations, ensuring consistency across environments.

By following these configuration guidelines, Xentic can maintain a secure and scalable multi-tenant architecture in its FastAPI applications.

## Implementation guide

To implement a multi-tenant architecture in a FastAPI application, follow these detailed steps:

### Step 1: Define the Database Structure

Create a shared table structure that includes a `tenant_id` to isolate data for each tenant. Here’s an example SQL schema:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Step 2: Create the FastAPI Application

Set up your FastAPI application with the necessary dependencies and middleware for handling tenant context.

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db, SessionLocal
from .models import User

app = FastAPI()

def get_current_tenant(tenant_id: str):
    # Mock function to fetch tenant; replace with actual DB call
    tenant = fetch_tenant_from_db(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant
```

### Step 3: Implement Tenant-Aware Endpoints

Create endpoints that are aware of the tenant context. Each endpoint should filter data based on the `tenant_id`.

```python
@app.post("/users/", response_model=User)
def create_user(user: User, tenant_id: str, db: Session = Depends(get_db)):
    tenant = get_current_tenant(tenant_id)
    user.tenant_id = tenant.id  # Associate user with tenant
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.get("/users/")
def read_users(tenant_id: str, db: Session = Depends(get_db)):
    tenant = get_current_tenant(tenant_id)
    users = db.query(User).filter(User.tenant_id == tenant.id).all()
    return users
```

### Step 4: Middleware for Tenant Resolution

Implement middleware to resolve the tenant context from incoming requests. This can be done via headers or query parameters.

```python
from fastapi.middleware.cors import CORSMiddleware

@app.middleware("http")
async def add_tenant_context(request: Request, call_next):
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID required")
    request.state.tenant_id = tenant_id
    response = await call_next(request)
    return response
```

### Step 5: Configure Database Session Management

Ensure that the database session is properly managed to handle tenant-specific queries.

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:password@db.internal.xentic.io/xentic_multi_tenant"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 6: Testing Multi-Tenant Functionality

Implement tests to ensure that the multi-tenant functionality works as expected. Use a testing framework like `pytest`.

```python
def test_create_user(client):
    response = client.post("/users/", json={"username": "testuser", "email": "test@example.com"}, headers={"X-Tenant-ID": "tenant-uuid-here"})
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_read_users(client):
    response = client.get("/users/", headers={"X-Tenant-ID": "tenant-uuid-here"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### Step 7: Security Considerations

- **MUST NOT** allow cross-tenant access to data.
- **SHOULD** implement authentication and authorization checks for each tenant.
- **MUST** validate tenant IDs to prevent unauthorized access.

### Step 8: Documentation and API Specification

Ensure that your API is well-documented, including tenant-specific endpoints. Use tools like Swagger UI to visualize the API.

```yaml
paths:
  /users/:
    post:
      summary: "Create a new user for a tenant"
      parameters:
        - in: header
          name: X-Tenant-ID
          required: true
          description: "The ID of the tenant"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                username:
                  type: string
                email:
                  type: string
      responses:
        200:
          description: "User created successfully"
```

### Summary

By following these steps, Xentic can implement a robust multi-tenant architecture in its FastAPI applications. Each component is designed to ensure data isolation, security, and scalability, providing a seamless experience for tenants.

## Security requirements

To ensure the security of a multi-tenant FastAPI application, it is essential to adopt a comprehensive threat model and implement robust authentication, authorization, and data protection measures. Below are critical security requirements that MUST be adhered to:

### Threat Model Summary

- **Data Breaches**: Unauthorized access to tenant data due to vulnerabilities or misconfigurations.
- **Denial of Service (DoS)**: Attackers may attempt to overwhelm the application, affecting all tenants.
- **Insider Threats**: Employees or contractors may misuse their access to tenant data.
- **Injection Attacks**: SQL injection or other code injection attacks may compromise application integrity.

### Authentication and Authorization (AuthN/Z)

- **MUST** implement OAuth2 or JWT for secure authentication.
- **MUST** ensure that each API request is authenticated and authorized based on tenant context.
- **SHOULD** use role-based access control (RBAC) to manage permissions for different user roles within each tenant.

Example of JWT authentication middleware:

```python
from fastapi import Security, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Security(oauth2_scheme)):
    user = verify_token(token)  # Implement token verification logic
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user
```

### Secrets Management

- **MUST** use a secrets management tool (e.g., HashiCorp Vault, AWS Secrets Manager) to store sensitive information such as API keys and database credentials.
- **MUST NOT** hard-code secrets in the source code or configuration files.
- **SHOULD** rotate secrets regularly to minimize exposure risk.

Example of loading secrets from environment variables:

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL")  # e.g., postgresql://user:password@db.internal.xentic.io/xentic_multi_tenant
```

### Input Validation

- **MUST** validate all incoming data to prevent injection attacks and ensure data integrity.
- **MUST NOT** trust any input from users, including headers, query parameters, and body payloads.
- **SHOULD** use Pydantic models for request validation.

Example of input validation using Pydantic:

```python
from pydantic import BaseModel, EmailStr, constr

class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr

@app.post("/users/")
def create_user(user: UserCreate):
    # Process user creation
    ...
```

### Audit Logging

- **MUST** implement audit logging to track all actions taken by users, especially those affecting tenant data.
- **SHOULD** log the following events:
  - User logins and logouts
  - Data modifications (create, update, delete)
  - Failed authentication attempts
- **MUST** ensure that logs are stored securely and are accessible only to authorized personnel.

Example of logging user actions:

```python
import logging

logger = logging.getLogger("audit")

def log_user_action(user_id: str, action: str):
    logger.info(f"User {user_id} performed action: {action}")

@app.post("/users/")
def create_user(user: UserCreate):
    log_user_action(current_user.id, "create_user")
    ...
```

### Summary of Security Requirements

| Requirement                     | Description                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|
| Authentication & Authorization    | Implement OAuth2/JWT, ensure tenant context-based access                   |
| Secrets Management                | Use secrets management tools, avoid hard-coding secrets                    |
| Input Validation                  | Validate all incoming data, use Pydantic for model validation              |
| Audit Logging                     | Track user actions, store logs securely                                    |

By adhering to these security requirements, Xentic can significantly enhance the security posture of its multi-tenant FastAPI applications, protecting both the organization and its tenants from potential threats.

## Testing strategy

To ensure the robustness and reliability of the multi-tenant FastAPI application, a comprehensive testing strategy must be implemented. This strategy includes unit tests, integration tests, and contract tests, each serving a distinct purpose. The following outlines the testing strategy, coverage targets, and example test classes.

### Testing Types

1. **Unit Tests**
   - **Purpose**: Validate the functionality of individual components in isolation.
   - **Coverage Target**: At least 80% code coverage for all business logic.
   - **Tools**: `pytest`, `pytest-mock`.

2. **Integration Tests**
   - **Purpose**: Test the interaction between different components, such as database operations and API endpoints.
   - **Coverage Target**: At least 70% coverage for integration points.
   - **Tools**: `pytest`, `httpx`.

3. **Contract Tests**
   - **Purpose**: Ensure that the API contracts between services remain consistent and valid.
   - **Coverage Target**: 100% coverage of all API endpoints.
   - **Tools**: `pact-python`, `pytest`.

### Test Coverage Targets

| Test Type       | Coverage Target |
|------------------|-----------------|
| Unit Tests       | 80%             |
| Integration Tests| 70%             |
| Contract Tests   | 100%            |

### Example Test Classes

#### Unit Tests

Example of a unit test for the user creation logic:

```python
import pytest
from app.models import User
from app.main import create_user

@pytest.fixture
def mock_db():
    # Setup mock database session
    ...

def test_create_user(mock_db):
    user_data = {"username": "testuser", "email": "test@example.com"}
    user = create_user(user_data, tenant_id="tenant-uuid-here", db=mock_db)
    
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.tenant_id == "tenant-uuid-here"
```

#### Integration Tests

Example of an integration test for the user endpoint:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_user_integration():
    response = client.post("/users/", json={"username": "testuser", "email": "test@example.com"}, headers={"X-Tenant-ID": "tenant-uuid-here"})
    
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_read_users_integration():
    response = client.get("/users/", headers={"X-Tenant-ID": "tenant-uuid-here"})
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

#### Contract Tests

Example of a contract test using Pact:

```python
from pact import Consumer, Provider

consumer = Consumer('UserService')
provider = Provider('UserAPI')

def test_user_service_contract():
    with consumer.given('a user exists') as interaction:
        interaction \
            .upon_receiving('a request for user data') \
            .with_request('GET', '/users/') \
            .will_respond_with(200, body=[{'username': 'testuser', 'email': 'test@example.com'}])
    
    # Execute the test
    consumer.verify()
```

### Continuous Integration

- **MUST** integrate tests into the CI/CD pipeline to ensure that all tests are executed with each code change.
- **SHOULD** enforce the coverage targets as part of the build process, failing builds that do not meet the specified thresholds.

### Summary

By adopting this comprehensive testing strategy, Xentic can ensure that its multi-tenant FastAPI application is robust, reliable, and maintainable. Each type of test plays a crucial role in validating the application, and adherence to coverage targets will help maintain high-quality code.

## Observability and operations

To ensure the reliability and performance of the multi-tenant FastAPI application, a robust observability and operations strategy MUST be implemented. This includes metrics collection, logging, tracing, dashboards, alerts, and service level objectives (SLOs).

### Metrics Collection

- **MUST** collect application metrics using Prometheus or a similar monitoring tool.
- **MUST** expose metrics at an endpoint (e.g., `/metrics`) for scraping by Prometheus.

Example of exposing metrics in FastAPI:

```python
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

Instrumentator().instrument(app).expose(app)
```

#### Key Metrics to Collect

| Metric                      | Description                                          |
|-----------------------------|------------------------------------------------------|
| Request Latency             | Time taken to process requests                        |
| Error Rates                 | Number of failed requests per endpoint                |
| Request Counts              | Total number of requests received                     |
| Active Connections          | Number of active connections to the application       |
| Database Query Performance   | Latency of database queries                          |

### Logging

- **MUST** implement structured logging using a logging library such as `loguru` or `structlog`.
- **MUST** log all incoming requests and responses, including their status codes.

Example of structured logging:

```python
from fastapi import FastAPI, Request
import structlog

log = structlog.get_logger()

app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    log.info("request", method=request.method, path=request.url.path, status=response.status_code)
    return response
```

#### Log Levels

- **MUST** use appropriate log levels:
  - `DEBUG` for detailed information during development.
  - `INFO` for general operational messages.
  - `WARNING` for unexpected situations that do not cause failure.
  - `ERROR` for serious issues that require attention.

### Tracing

- **MUST** implement distributed tracing using OpenTelemetry or Jaeger to track requests across services.
- **SHOULD** propagate trace context through HTTP headers.

Example of setting up tracing with OpenTelemetry:

```python
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI()

FastAPIInstrumentor.instrument_app(app)
```

### Dashboards

- **MUST** create dashboards using Grafana or similar tools to visualize metrics and logs.
- **SHOULD** include the following panels:
  - Request latency over time
  - Error rates by endpoint
  - Active connections
  - Database query performance

### Alerts

- **MUST** set up alerts based on defined thresholds for key metrics.
- **SHOULD** use tools like Alertmanager or PagerDuty for alerting.

#### Example Alerting Rules

| Metric             | Condition                      | Alert Message                      |
|--------------------|--------------------------------|------------------------------------|
| Error Rate         | > 5% over 5 minutes            | "High error rate detected!"        |
| Request Latency    | > 200ms for 95th percentile    | "High latency detected!"           |
| Active Connections  | > 1000 connections              | "High number of active connections!"|

### Service Level Objectives (SLOs)

- **MUST** define SLOs for critical services.
- **SHOULD** track SLO compliance and report on it regularly.

#### Example SLOs

| Service                | SLO Description                                  | Target        |
|-----------------------|--------------------------------------------------|---------------|
| User API              | 99.9% of requests must complete within 200ms     | 99.9%         |
| Authentication Service | 99.5% uptime for the authentication service      | 99.5%         |
| Data Retrieval        | 95% of data retrieval requests must succeed       | 95%           |

### On-Call Runbook Steps

In the event of an incident, the following steps MUST be followed:

1. **Acknowledge the Alert**: Confirm receipt of the alert and begin investigation.
2. **Review Metrics and Logs**: Check the relevant metrics and logs for anomalies.
3. **Identify the Impact**: Determine which tenants are affected and the severity of the issue.
4. **Implement a Fix**: Apply a temporary fix if possible, or escalate to the development team.
5. **Communicate**: Notify stakeholders about the incident and expected resolution time.
6. **Post-Incident Review**: Conduct a review after resolution to identify root causes and prevent recurrence.

By implementing these observability and operations practices, Xentic can ensure that its multi-tenant FastAPI application remains reliable, performant, and responsive to incidents.

## Migration and versioning

To maintain a robust and scalable multi-tenant FastAPI application, a structured approach to migration and versioning MUST be adopted. This includes defining upgrade paths, establishing a deprecation policy, ensuring backward compatibility, and planning for rollbacks.

### Upgrade Paths

- **MUST** provide clear upgrade paths for each version of the application.
- **SHOULD** document breaking changes and feature enhancements in a changelog.
- **MUST** use semantic versioning (MAJOR.MINOR.PATCH) to indicate the nature of changes.

| Version | Changes                           | Upgrade Path               |
|---------|-----------------------------------|----------------------------|
| 1.0.0   | Initial release                   | N/A                        |
| 1.1.0   | Added new API endpoint            | 1.0.0 -> 1.1.0             |
| 2.0.0   | Breaking changes to user model    | 1.x -> 2.0.0               |

### Deprecation Policy

- **MUST NOT** remove any features without a deprecation period of at least one release cycle.
- **SHOULD** mark deprecated features in the documentation and provide alternatives.
- **MUST** log warnings in the application when deprecated features are used.

Example of marking a deprecated endpoint:

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/old-endpoint", deprecated=True)
async def old_endpoint():
    return {"message": "This endpoint is deprecated. Please use /new-endpoint instead."}
```

### Backward Compatibility

- **MUST** ensure that new versions of the application remain backward compatible with existing tenants.
- **SHOULD** include versioning in the API endpoints to support multiple versions concurrently.

Example of versioned API endpoints:

```python
@app.get("/v1/users/")
async def get_users_v1():
    # Implementation for version 1
    ...

@app.get("/v2/users/")
async def get_users_v2():
    # Implementation for version 2 with new features
    ...
```

### Rollback Procedures

- **MUST** have a rollback strategy in place for each deployment.
- **SHOULD** use database migrations that support rollbacks (e.g., Alembic).
- **MUST** maintain backups of the database before applying migrations.

Example of a rollback command using Alembic:

```bash
alembic downgrade -1
```

### Migration Strategy

- **MUST** use database migration tools to handle schema changes.
- **SHOULD** write migration scripts that are idempotent and can be safely re-applied.

Example Alembic migration script:

```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False)
    )

def downgrade():
    op.drop_table('users')
```

### Testing Migrations

- **MUST** test all migrations in a staging environment before applying them to production.
- **SHOULD** include migration tests in the CI/CD pipeline to validate the success of migrations.

Example of a migration test:

```python
def test_migration():
    # Run migration
    upgrade()

    # Check if the table exists
    assert engine.dialect.has_table(engine, 'users')
```

### Documentation

- **MUST** document all migration and versioning processes in the internal wiki at [https://docs.internal.xentic.io/migration-versioning](https://docs.internal.xentic.io/migration-versioning).
- **SHOULD** provide examples of common migration scenarios and best practices.

By adhering to these migration and versioning standards, Xentic can ensure that its multi-tenant FastAPI application remains stable, maintainable, and user-friendly, while also accommodating future growth and changes.

### FAQ, Anti-Patterns, and Checklists

#### Frequently Asked Questions (FAQ)

1. **What is multi-tenancy?**
   - Multi-tenancy is an architecture where a single instance of an application serves multiple tenants (clients), isolating their data and configurations.

2. **How does FastAPI support multi-tenancy?**
   - FastAPI allows the use of dependency injection and middleware to manage tenant-specific data and configurations dynamically.

3. **What database strategies are recommended for multi-tenancy?**
   - **MUST** consider using a separate schema per tenant, a shared schema with tenant identifiers, or a hybrid approach based on your application's needs.

4. **How can I ensure data isolation between tenants?**
   - **MUST** implement strict access controls and use tenant identifiers in all database queries to prevent data leakage.

5. **What are some common performance issues in multi-tenant applications?**
   - Performance issues can arise from inefficient queries, lack of indexing, and resource contention among tenants.

6. **How can I monitor tenant-specific metrics?**
   - **MUST** use tagging in your logging and monitoring solutions to differentiate metrics by tenant.

7. **What should I do if a tenant experiences downtime?**
   - **MUST** have a robust incident response plan that includes tenant-specific communication and recovery procedures.

8. **How do I handle tenant onboarding and offboarding?**
   - **MUST** automate the onboarding process with scripts for creating tenant-specific resources and ensure a smooth offboarding process by cleaning up resources.

9. **Can I customize features for individual tenants?**
   - **SHOULD** implement feature flags or configuration management to allow customization while maintaining a single codebase.

10. **What security measures are necessary for multi-tenancy?**
    - **MUST** implement authentication and authorization mechanisms, encrypt sensitive data, and regularly audit access logs.

#### Anti-Patterns

| Anti-Pattern                        | Description                                                                                  |
|-------------------------------------|----------------------------------------------------------------------------------------------|
| Shared Database Without Isolation    | Using a single database without tenant identifiers can lead to data leakage.                |
| Hardcoding Tenant Configurations     | Hardcoding values specific to tenants can lead to maintenance challenges and errors.        |
| Lack of Resource Quotas             | Not implementing resource limits can lead to one tenant consuming all resources.            |
| Ignoring Performance Testing         | Failing to test performance under multi-tenant scenarios can result in unexpected issues.  |
| Inconsistent Logging Practices       | Not standardizing logging can make it difficult to trace issues across tenants.             |

#### Pre-Merge Checklist

- **MUST** ensure all code changes are reviewed by at least one other developer.
- **MUST** run all unit tests and ensure they pass.
- **SHOULD** check for any new dependencies and ensure they are documented.
- **MUST** update the documentation to reflect any changes made.
- **SHOULD** verify that all tenant-specific configurations are handled correctly.

#### Production Checklist

- **MUST** ensure that all migrations are applied successfully in the production environment.
- **MUST** monitor application performance metrics immediately after deployment.
- **SHOULD** have a rollback plan ready in case of deployment issues.
- **MUST** communicate deployment status to all stakeholders.
- **SHOULD** conduct a post-deployment review to identify areas for improvement.

By following these guidelines, Xentic can maintain a robust multi-tenant FastAPI application that meets the needs of its diverse client base while ensuring performance, security, and reliability.
