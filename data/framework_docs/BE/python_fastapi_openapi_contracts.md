# OpenAPI and API Contract Standards — FastAPI

## Overview and scope

The purpose of this document is to establish standards and guidelines for using OpenAPI specifications within FastAPI applications at Xentic. This standard aims to ensure consistency, maintainability, and interoperability across all API services developed within the organization.

### Audience

This document is intended for:
- Software Engineers
- API Developers
- Technical Leads
- Quality Assurance Engineers
- DevOps Engineers

### Scope

This standard covers:
- Definition and structure of OpenAPI specifications
- Best practices for API design and documentation
- Versioning and backward compatibility
- Security considerations for APIs
- Integration with CI/CD pipelines

### Non-goals

This document does NOT cover:
- Detailed implementation of FastAPI itself
- Non-API related development practices
- Frameworks outside of FastAPI
- Client-side API consumption patterns

### Glossary

| Term              | Definition                                                                 |
|-------------------|----------------------------------------------------------------------------|
| OpenAPI           | A specification for defining RESTful APIs, allowing for machine-readable documentation. |
| FastAPI           | A modern web framework for building APIs with Python based on standard Python type hints. |
| API Contract      | A formal agreement on how an API behaves, including endpoints, request/response formats, and error handling. |
| CI/CD             | Continuous Integration and Continuous Deployment, a method to frequently deliver apps to customers. |
| Swagger           | A tool for auto-generating documentation from OpenAPI specifications. |

### How this standard fits the Xentic platform

The OpenAPI and API Contract Standards are integral to the Xentic platform as they ensure that all APIs are designed with a consistent approach, allowing for seamless integration with other services and libraries within the ecosystem. By adhering to these standards, Xentic aims to:

- Enhance collaboration among teams by providing clear documentation.
- Facilitate automated testing and validation of APIs.
- Improve the onboarding process for new developers by providing a clear framework.
- Ensure compliance with security standards and best practices.

### Example OpenAPI Specification

Below is a basic example of an OpenAPI specification for a FastAPI application:

```yaml
openapi: 3.0.0
info:
  title: Example API
  version: 1.0.0
paths:
  /items:
    get:
      summary: Retrieve a list of items
      responses:
        '200':
          description: A list of items
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    id:
                      type: integer
                    name:
                      type: string
```

By following these guidelines, Xentic aims to maintain high-quality APIs that are easy to understand, use, and maintain, ultimately leading to a more efficient development process and a better product for our users.

## Standards and policies

1. **MUST** define all APIs using OpenAPI specifications. All endpoints, request/response formats, and error handling MUST be documented in the OpenAPI format to ensure clarity and consistency across services.

2. **MUST NOT** use any package names outside the `com.xentic.<service>` namespace for your FastAPI applications. This aligns with Xentic's Java base package conventions and ensures a consistent structure across all services.

3. **SHOULD** use versioning in the OpenAPI specification to manage backward compatibility. Each API version MUST have its own dedicated OpenAPI document. For example:

   ```yaml
   info:
     title: Example API
     version: 1.0.0
   ```

4. **MUST** include detailed descriptions for each endpoint, parameter, and response in the OpenAPI specification. This enhances the usability of the API and aids in client integration.

5. **MUST NOT** expose sensitive information in API responses. All responses MUST be sanitized to remove any sensitive data such as user credentials or internal identifiers.

6. **SHOULD** implement authentication and authorization for all endpoints. Use OAuth2 or API keys as specified in the OpenAPI documentation to secure your APIs.

7. **MUST** validate all incoming requests against the defined OpenAPI schema. FastAPI provides built-in validation features that MUST be utilized to ensure data integrity.

8. **SHOULD** use descriptive HTTP status codes in responses. Each endpoint MUST clearly define the expected status codes and their meanings in the OpenAPI specification.

9. **MUST NOT** create endpoints that are not documented in the OpenAPI specification. All publicly accessible endpoints MUST have corresponding documentation to ensure transparency and ease of use.

10. **SHOULD** provide example requests and responses in the OpenAPI documentation. This helps consumers of the API understand how to interact with it effectively.

11. **MUST** maintain a changelog for each version of the API. This changelog MUST be included in the OpenAPI documentation to inform users of any breaking changes or new features.

12. **SHOULD** leverage FastAPI's built-in support for generating interactive API documentation using Swagger UI. This documentation MUST be accessible at `/docs` by default.

13. **MUST NOT** hard-code configuration values in the FastAPI application. Instead, use environment variables or configuration files (e.g., YAML, HCL) to manage settings. For example:

    ```yaml
    database:
      url: ${DATABASE_URL}
      username: ${DATABASE_USERNAME}
      password: ${DATABASE_PASSWORD}
    ```

14. **MUST** include error handling in the API to provide meaningful error messages. All errors MUST be returned in a consistent format as defined in the OpenAPI specification. For example:

    ```json
    {
      "error": {
        "code": 400,
        "message": "Invalid request"
      }
    }
    ```

15. **SHOULD** regularly review and update the OpenAPI documentation to reflect any changes in the API. This ensures that the documentation remains accurate and useful for developers.

16. **MUST** ensure that all APIs are tested using automated testing frameworks. Tests MUST cover both functional and performance aspects of the API to ensure reliability.

By adhering to these standards and policies, Xentic aims to create robust, secure, and user-friendly APIs that facilitate seamless interactions and integrations across its services.

## Architecture and design

The architecture of FastAPI applications at Xentic follows a microservices approach, allowing for modular development and deployment. The following component diagram illustrates the key components and their interactions within the system.

```mermaid
graph TD;
    A[Client] -->|HTTP Requests| B[FastAPI Service]
    B -->|Database Queries| C[Database]
    B -->|Authentication| D[Auth Service]
    B -->|External API Calls| E[External Service]
    B -->|Logging| F[Logging Service]
    B -->|Monitoring| G[Monitoring Service]
```

### Data Flows

1. **Client to FastAPI Service**: Clients initiate requests to the FastAPI service via HTTP, which handles incoming requests and routes them to the appropriate endpoints.
2. **FastAPI Service to Database**: The FastAPI service communicates with the database to perform CRUD operations based on the requests received.
3. **FastAPI Service to Auth Service**: Authentication and authorization are handled by a dedicated Auth service, which verifies user credentials and issues tokens.
4. **FastAPI Service to External Services**: The FastAPI service may call external APIs for additional data or functionality, ensuring that the necessary data is fetched and processed.
5. **FastAPI Service to Logging and Monitoring Services**: All interactions and errors are logged, and metrics are sent to monitoring services for performance tracking and alerting.

### Integration Points

- **Database**: All FastAPI applications MUST connect to a centralized database using a defined schema. The connection string should be defined in a configuration file or environment variable.
  
  Example configuration (YAML):
  ```yaml
  database:
    url: ${DATABASE_URL}
    username: ${DATABASE_USERNAME}
    password: ${DATABASE_PASSWORD}
  ```

- **Authentication**: The FastAPI service MUST integrate with the Xentic Auth service for user authentication. OAuth2 or API keys MUST be utilized as per the OpenAPI specifications.

- **External APIs**: When integrating with external services, the FastAPI service MUST handle errors gracefully and provide fallback mechanisms where applicable.

### Failure Domains

1. **Client Failures**: Clients may encounter network issues or invalid requests. The FastAPI service MUST return appropriate HTTP status codes (e.g., 400 for bad requests).
  
2. **Service Failures**: If the FastAPI service fails, it should return a 500 Internal Server Error and log the error for further investigation.

3. **Database Failures**: If the database is unreachable, the FastAPI service MUST handle the error and return a 503 Service Unavailable status. Retry mechanisms should be implemented where appropriate.

4. **Authentication Failures**: If authentication fails, the FastAPI service MUST return a 401 Unauthorized status and provide a clear error message.

5. **External API Failures**: The service should implement circuit breaker patterns to handle failures from external APIs gracefully, ensuring that the overall system remains responsive.

By adhering to these architectural and design principles, Xentic ensures that its FastAPI applications are resilient, maintainable, and scalable, fostering a robust API ecosystem.

## Configuration reference

### Application Configuration (application.yml)

The application configuration should be defined in a YAML file, which allows for clear and structured settings management. Below is an example of a configuration file with default and production values.

```yaml
# application.yml
app:
  name: xentic-api
  version: 1.0.0
  environment: development # Change to 'production' for production settings

server:
  host: 0.0.0.0
  port: 8000

database:
  url: ${DATABASE_URL} # Default: postgresql://user:password@localhost/dbname
  username: ${DATABASE_USERNAME} # Default: user
  password: ${DATABASE_PASSWORD} # Default: password
  pool_size: 10

logging:
  level: INFO # Change to DEBUG for more verbose logging
  format: "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"

auth:
  oauth2:
    client_id: ${OAUTH2_CLIENT_ID}
    client_secret: ${OAUTH2_CLIENT_SECRET}
    token_url: https://auth.internal.xentic.io/token

features:
  enable_feature_x: true
  enable_feature_y: false
```

### Environment Variables

The following environment variables are required for the application to function correctly. Ensure these are set in the production environment.

| Variable                | Default Value                        | Production Value                        |
|-------------------------|-------------------------------------|-----------------------------------------|
| DATABASE_URL            | postgresql://user:password@localhost/dbname | postgresql://prod_user:prod_password@prod_host/prod_db |
| DATABASE_USERNAME       | user                                | prod_user                               |
| DATABASE_PASSWORD       | password                            | prod_password                           |
| OAUTH2_CLIENT_ID       | test_client_id                      | prod_client_id                          |
| OAUTH2_CLIENT_SECRET    | test_client_secret                  | prod_client_secret                      |

### Terraform Configuration

When deploying the FastAPI application using Terraform, ensure the following configuration is included to manage environment variables and other settings.

```hcl
resource "aws_lambda_function" "fastapi_function" {
  function_name = "xentic_fastapi"
  handler       = "app.main:app"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_exec.arn
  source_code_hash = filebase64sha256("path/to/your/package.zip")

  environment {
    DATABASE_URL            = var.database_url
    DATABASE_USERNAME       = var.database_username
    DATABASE_PASSWORD       = var.database_password
    OAUTH2_CLIENT_ID       = var.oauth2_client_id
    OAUTH2_CLIENT_SECRET    = var.oauth2_client_secret
  }
}

variable "database_url" {
  description = "Database connection string"
  type        = string
}

variable "database_username" {
  description = "Database username"
  type        = string
}

variable "database_password" {
  description = "Database password"
  type        = string
}

variable "oauth2_client_id" {
  description = "OAuth2 client ID"
  type        = string
}

variable "oauth2_client_secret" {
  description = "OAuth2 client secret"
  type        = string
}
```

### Summary of Configuration Practices

- **MUST** use environment variables for sensitive information such as database credentials and OAuth2 secrets.
- **SHOULD** keep the application configuration in a structured format (YAML) for clarity and maintainability.
- **MUST NOT** hard-code any sensitive configuration values directly into the source code.
- **SHOULD** utilize Terraform for infrastructure management to maintain consistency across environments.

## Implementation guide

To implement a FastAPI application at Xentic, follow these step-by-step instructions, which include creating a simple user management API as an example.

### Step 1: Set Up the FastAPI Project

1. **Create a new directory for your project**:
   ```bash
   mkdir xentic-fastapi
   cd xentic-fastapi
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install FastAPI and an ASGI server (e.g., uvicorn)**:
   ```bash
   pip install fastapi uvicorn
   ```

### Step 2: Define the Project Structure

Organize your project as follows:

```
xentic-fastapi/
│
├── app/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   └── routes/
│       └── user.py
│
├── config.yaml
└── requirements.txt
```

### Step 3: Create Configuration File

Create a `config.yaml` file to manage application settings:

```yaml
app:
  title: "Xentic User Management API"
  version: "1.0.0"

database:
  url: ${DATABASE_URL}
```

### Step 4: Define Database Connection

Create `database.py` to handle database connections:

```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import yaml
import os

# Load configuration
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

### Step 5: Define Models

Create `models.py` for database models:

```python
# app/models.py
from sqlalchemy import Column, Integer, String
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
```

### Step 6: Create Schemas

Define data validation schemas in `schemas.py`:

```python
# app/schemas.py
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str

class User(UserCreate):
    id: int

    class Config:
        orm_mode = True
```

### Step 7: Implement User Routes

Create user routes in `routes/user.py`:

```python
# app/routes/user.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
```

### Step 8: Create the Main Application

Create `main.py` to initialize the FastAPI application:

```python
# app/main.py
from fastapi import FastAPI
from .database import engine, Base
from .routes import user

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Xentic User Management API")

app.include_router(user.router)
```

### Step 9: Run the Application

To run the FastAPI application, use the following command:

```bash
uvicorn app.main:app --reload
```

### Step 10: Test the API

You can test the API using tools like Postman or curl. For example, to create a user, send a POST request to `http://127.0.0.1:8000/users/` with the following JSON body:

```json
{
  "username": "johndoe",
  "email": "john@example.com"
}
```

### Summary of Implementation Steps

- **MUST** follow the directory structure to ensure maintainability.
- **MUST** use environment variables for sensitive configurations.
- **SHOULD** implement error handling and validation using Pydantic schemas.
- **MUST** include database models and routes in separate modules for clarity.
- **SHOULD** document the API endpoints using OpenAPI specifications automatically generated by FastAPI. 

By following these steps, you will create a robust and maintainable FastAPI application that adheres to Xentic's internal standards.

## Security requirements

### Threat Model Summary

The FastAPI application must be designed with a comprehensive threat model to mitigate risks associated with unauthorized access, data breaches, and other vulnerabilities. Key threats include:

- **Unauthorized Access**: Attackers may attempt to access endpoints without proper authentication.
- **Data Exposure**: Sensitive data may be exposed through improper handling or logging.
- **Injection Attacks**: SQL injection or other forms of injection could compromise the database.
- **Denial of Service (DoS)**: Attackers may overload the application with requests.

### Authentication and Authorization

The application MUST implement OAuth2 for authentication and authorization. The following practices should be adhered to:

- **MUST** use the `Bearer` token scheme for API access.
- **MUST NOT** expose any sensitive endpoints without proper authentication.
- **SHOULD** validate tokens on every request to ensure they are still valid and not expired.

Example of token validation in a FastAPI dependency:

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

Sensitive information such as database credentials and OAuth2 secrets MUST be stored securely. The following practices are recommended:

- **MUST** use environment variables to store sensitive information.
- **MUST NOT** hard-code secrets in the application code or configuration files.
- **SHOULD** utilize secret management tools such as AWS Secrets Manager or HashiCorp Vault.

Example of loading secrets from environment variables:

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL")
OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET")
```

### Input Validation

All incoming data MUST be validated to prevent injection attacks and ensure data integrity. Use Pydantic models for validation:

- **MUST** define schemas for all incoming requests.
- **SHOULD** implement additional validation logic as necessary.

Example of a Pydantic model for user creation:

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr  # Validates that the email is in the correct format
```

### Audit Logging

The application MUST implement audit logging to track access and changes to sensitive data. Key requirements include:

- **MUST** log all authentication attempts, successful or failed.
- **MUST** log changes to user data and other sensitive operations.
- **SHOULD** use a structured logging format (e.g., JSON) for easier analysis.

Example of logging an authentication attempt:

```python
import logging

logger = logging.getLogger("audit")

def log_authentication_attempt(username: str, success: bool):
    logger.info(f"Authentication attempt for user '{username}': {'Success' if success else 'Failure'}")
```

### Summary of Security Requirements

- **MUST** implement OAuth2 for securing API endpoints.
- **MUST NOT** expose sensitive data through logs or error messages.
- **SHOULD** validate all incoming requests to safeguard against injection attacks.
- **MUST** manage secrets securely using environment variables or secret management tools.
- **MUST** implement comprehensive audit logging for security monitoring.

By adhering to these security requirements, the FastAPI application will be more resilient against common threats and vulnerabilities, ensuring a secure environment for users and data.

## Testing strategy

A comprehensive testing strategy is essential for maintaining the quality and reliability of the FastAPI application. The testing strategy MUST include unit tests, integration tests, and contract tests. Each type of test serves a distinct purpose and collectively ensures that the application operates as expected.

### 1. Unit Tests

Unit tests focus on testing individual components or functions in isolation. They MUST be written for all critical functions and methods to ensure correctness.

- **Coverage Target**: A minimum of 80% coverage for all business logic.
- **Testing Framework**: Use `pytest` for writing and executing tests.

Example of a unit test for the `create_user` function:

```python
# tests/test_user.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import User
from app.schemas import UserCreate

client = TestClient(app)

@pytest.fixture
def user_data():
    return {"username": "testuser", "email": "test@example.com"}

def test_create_user(user_data):
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    assert response.json()["username"] == user_data["username"]
```

### 2. Integration Tests

Integration tests validate the interaction between different components of the application, such as the database and the API routes.

- **Coverage Target**: A minimum of 70% coverage for integration points.
- **Testing Framework**: Continue using `pytest` with the `pytest-asyncio` plugin for asynchronous testing.

Example of an integration test for user creation:

```python
# tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import User
from app.database import SessionLocal, engine
from sqlalchemy.orm import sessionmaker

client = TestClient(app)

@pytest.fixture(scope="module")
def test_db():
    # Setup database
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session  # This will be the test database session

    session.close()
    transaction.rollback()
    connection.close()

def test_create_user_integration(test_db):
    response = client.post("/users/", json={"username": "integrationuser", "email": "integration@example.com"})
    assert response.status_code == 200
    assert response.json()["username"] == "integrationuser"
```

### 3. Contract Tests

Contract tests ensure that the API adheres to the defined specifications and that changes do not break existing contracts. This is particularly important when multiple teams are consuming the API.

- **Coverage Target**: 100% adherence to the OpenAPI specifications.
- **Testing Framework**: Use `pact-python` for contract testing.

Example of a contract test:

```python
# tests/test_contract.py
from pact import Consumer, Provider

pact = Consumer('UserService').has_pact_with(Provider('UserAPI'))

def test_user_api_contract():
    with pact:
        pact.given('a user exists').upon_receiving('a request for user creation').with_request(
            'POST', '/users/',
            body={"username": "contractuser", "email": "contract@example.com"},
            headers={"Content-Type": "application/json"}
        ).will_respond_with(
            200,
            body={"username": "contractuser", "email": "contract@example.com"}
        )

        response = client.post("/users/", json={"username": "contractuser", "email": "contract@example.com"})
        assert response.status_code == 200
```

### Summary of Testing Strategy

| Test Type         | Purpose                                           | Coverage Target |
|-------------------|---------------------------------------------------|------------------|
| Unit Tests        | Validate individual functions and methods         | 80%               |
| Integration Tests  | Validate interaction between components           | 70%               |
| Contract Tests    | Ensure adherence to API specifications            | 100%              |

### Best Practices

- **MUST** run tests automatically as part of the CI/CD pipeline.
- **SHOULD** use fixtures to manage test data and resources efficiently.
- **MUST NOT** write tests that are dependent on external services; use mocks or stubs instead.
- **SHOULD** document all tests and their expected outcomes for clarity.

By implementing this testing strategy, the FastAPI application will maintain high quality and reliability, ensuring that it meets the needs of users and stakeholders effectively.

## Observability and operations

To ensure the FastAPI application is reliable and performant, observability practices MUST be implemented. This includes metrics collection, logging, tracing, dashboards, alerts, and defining Service Level Objectives (SLOs). 

### Metrics

Metrics provide insights into the application's performance and health. The following metrics MUST be collected:

- **Request Latency**: Measure the time taken to process requests.
- **Error Rates**: Track the percentage of failed requests.
- **Throughput**: Monitor the number of requests handled per second.
- **Resource Usage**: Collect CPU and memory usage statistics.

Example of configuring Prometheus for metrics collection:

```python
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

Instrumentator().instrument(app).expose(app)
```

### Logging

Logging is crucial for diagnosing issues and understanding application behavior. The application MUST implement structured logging and adhere to the following guidelines:

- **MUST** log at least the following levels: INFO, WARNING, ERROR, and CRITICAL.
- **MUST NOT** log sensitive information such as passwords or personal data.
- **SHOULD** use a logging framework that supports structured logging, such as `loguru` or `structlog`.

Example of structured logging with `loguru`:

```python
from loguru import logger

logger.add("app.log", rotation="1 MB")  # Rotate logs after reaching 1 MB

logger.info("Application started")
logger.error("An error occurred", exc_info=True)
```

### Tracing

Distributed tracing allows tracking requests as they flow through various services. The application MUST implement tracing using a tool like OpenTelemetry.

- **MUST** propagate trace context across service boundaries.
- **SHOULD** instrument all major functions and endpoints.

Example of setting up OpenTelemetry:

```python
from opentelemetry import trace
from opentelemetry.ext.fastapi import FastAPIInstrumentor

tracer = trace.get_tracer(__name__)
FastAPIInstrumentor.instrument_app(app)
```

### Dashboards

Dashboards provide visual representations of metrics and logs. The following practices MUST be followed:

- **MUST** use a tool like Grafana to create dashboards for monitoring key metrics.
- **SHOULD** include visualizations for request latency, error rates, and throughput.

Example of a Grafana dashboard panel configuration for request latency:

```json
{
  "type": "graph",
  "title": "Request Latency",
  "targets": [
    {
      "target": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
      "refId": "A"
    }
  ]
}
```

### Alerts

Alerts are essential for proactive incident management. The application MUST define alerting rules based on metrics thresholds:

- **MUST** set up alerts for high error rates (e.g., > 5%).
- **MUST** alert on increased latency (e.g., 95th percentile > 500ms).
- **SHOULD** use a tool like Prometheus Alertmanager for managing alerts.

Example of an alerting rule in Prometheus:

```yaml
groups:
  - name: alerting_rules
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status="500"}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "More than 5% of requests are failing."
```

### Service Level Objectives (SLOs)

Defining SLOs helps in measuring service reliability. The following SLOs MUST be established:

- **Availability SLO**: 99.9% uptime.
- **Performance SLO**: 95th percentile latency under 500ms.
- **Error Rate SLO**: Less than 1% error rate.

### On-Call Runbook Steps

In the event of an incident, the following on-call steps MUST be followed:

1. **Acknowledge the Alert**: Confirm receipt of the alert.
2. **Investigate**: Check logs and metrics for anomalies.
3. **Diagnose**: Identify the root cause of the issue.
4. **Mitigate**: Apply a temporary fix if possible.
5. **Resolve**: Implement a permanent fix and verify resolution.
6. **Document**: Record the incident details and resolution steps in the incident management system.
7. **Review**: Conduct a post-mortem to analyze the incident and improve processes.

By adhering to these observability and operations standards, the FastAPI application will maintain high reliability and performance, ensuring a seamless experience for users and stakeholders.

## Migration and versioning

Managing migration and versioning of APIs is critical to ensure backward compatibility and a smooth transition for consumers of the API. The following guidelines MUST be adhered to:

### Upgrade Paths

- **MUST** provide clear upgrade paths for each version of the API.
- **MUST** document breaking changes and new features in a CHANGELOG.
- **SHOULD** support multiple versions of the API simultaneously to allow clients time to migrate.

Example of a CHANGELOG entry:

```markdown
## [1.1.0] - 2023-10-01
### Added
- New endpoint for user profile retrieval: `GET /users/{id}/profile`

### Changed
- Updated response format for `GET /users/` to include `last_login` timestamp.

### Deprecated
- `GET /users/{id}/details` will be removed in version 2.0.0.
```

### Deprecation Policy

- **MUST** establish a deprecation policy that clearly communicates when features or endpoints will be removed.
- **MUST NOT** remove deprecated features without a minimum notice period of 3 months.
- **SHOULD** provide alternative solutions or endpoints when deprecating features.

Example of a deprecation notice in the API documentation:

```markdown
### Deprecation Notice
The endpoint `GET /users/{id}/details` is deprecated and will be removed in version 2.0.0. Please use `GET /users/{id}/profile` instead.
```

### Backward Compatibility

- **MUST** ensure that new versions of the API are backward compatible with previous versions whenever possible.
- **SHOULD** use versioning in the URL (e.g., `/api/v1/users`) to clearly distinguish between versions.
- **MUST NOT** introduce breaking changes without a clear migration path.

Example of versioned endpoint usage:

```python
@app.get("/api/v1/users/")
async def get_users_v1():
    # Logic for v1
    return [{"id": 1, "username": "user1"}]

@app.get("/api/v2/users/")
async def get_users_v2():
    # Logic for v2 with additional fields
    return [{"id": 1, "username": "user1", "last_login": "2023-10-01T12:00:00Z"}]
```

### Rollback Procedures

- **MUST** have a rollback procedure in place for each deployment to revert to the previous stable version if issues arise.
- **SHOULD** automate the rollback process to minimize downtime.
- **MUST NOT** deploy breaking changes without testing in a staging environment first.

Example of a rollback command in a CI/CD pipeline:

```yaml
# rollback.yml
steps:
  - name: Rollback to Previous Version
    run: |
      kubectl rollout undo deployment/my-api-deployment
```

### Summary Table

| Aspect                 | Requirement                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| Upgrade Paths         | MUST provide clear upgrade paths and document changes in CHANGELOG         |
| Deprecation Policy    | MUST NOT remove features without a 3-month notice; MUST provide alternatives |
| Backward Compatibility | MUST ensure new versions are backward compatible; MUST NOT introduce breaking changes |
| Rollback Procedures    | MUST have automated rollback procedures in place; MUST test in staging     |

By adhering to these migration and versioning standards, the FastAPI application will maintain stability and reliability, ensuring a seamless experience for API consumers.

## FAQ, anti-patterns, and checklists

### Frequently Asked Questions (FAQ)

1. **What is FastAPI?**
   - FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.6+ based on standard Python type hints.

2. **How do I install FastAPI?**
   - You can install FastAPI using pip:
     ```bash
     pip install fastapi
     ```

3. **What is the recommended way to run a FastAPI application?**
   - Use an ASGI server like Uvicorn:
     ```bash
     uvicorn main:app --reload
     ```

4. **How do I define an API endpoint in FastAPI?**
   - You can define an endpoint using decorators:
     ```python
     @app.get("/items/{item_id}")
     async def read_item(item_id: int):
         return {"item_id": item_id}
     ```

5. **What is dependency injection in FastAPI?**
   - Dependency injection allows you to define reusable components that can be injected into your endpoints, improving modularity and testability.

6. **How can I handle CORS in FastAPI?**
   - Use the `fastapi.middleware.cors` middleware:
     ```python
     from fastapi.middleware.cors import CORSMiddleware

     app.add_middleware(
         CORSMiddleware,
         allow_origins=["*"],
         allow_credentials=True,
         allow_methods=["*"],
         allow_headers=["*"],
     )
     ```

7. **How can I validate request bodies in FastAPI?**
   - Use Pydantic models for request body validation:
     ```python
     from pydantic import BaseModel

     class Item(BaseModel):
         name: str
         price: float

     @app.post("/items/")
     async def create_item(item: Item):
         return item
     ```

8. **What are the best practices for error handling in FastAPI?**
   - Use exception handlers to manage errors gracefully:
     ```python
     from fastapi import HTTPException

     @app.exception_handler(HTTPException)
     async def http_exception_handler(request, exc):
         return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
     ```

9. **How do I document my API with FastAPI?**
   - FastAPI automatically generates interactive API documentation using Swagger UI and ReDoc. Access it at `/docs` and `/redoc`.

10. **What is the recommended way to test FastAPI applications?**
    - Use the `httpx` library for testing:
      ```python
      from fastapi.testclient import TestClient

      client = TestClient(app)

      def test_read_item():
          response = client.get("/items/1")
          assert response.status_code == 200
          assert response.json() == {"item_id": 1}
      ```

### Anti-Patterns

| Anti-Pattern                      | Description                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|
| Using Global State                | Avoid using global variables for state management; use dependency injection instead. |
| Not Validating Input              | Failing to validate request bodies can lead to unexpected errors; always use Pydantic models. |
| Hardcoding Configuration           | Configuration values should not be hardcoded; use environment variables or config files. |
| Ignoring Asynchronous Features    | Not leveraging FastAPI's asynchronous capabilities can lead to performance bottlenecks. |
| Lack of Documentation              | Failing to document endpoints and their responses can lead to confusion for API consumers. |

### Pre-Merge Checklist

- [ ] Code adheres to PEP 8 style guidelines.
- [ ] All new features are covered by unit tests.
- [ ] API documentation is updated.
- [ ] No sensitive information is logged.
- [ ] Dependency injection is used for all services.

### Production Checklist

- [ ] Ensure all environment variables are set correctly.
- [ ] Run integration tests in a staging environment.
- [ ] Verify that logging and monitoring are configured.
- [ ] Confirm that the application is running behind a reverse proxy (e.g., Nginx).
- [ ] Check that CORS settings are properly configured for production.
