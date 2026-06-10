# Schema Validation — FastAPI + Pydantic v2

## Overview and scope

The purpose of this document is to establish the standards and guidelines for schema validation in FastAPI applications using Pydantic v2 within the Xentic platform. This standard aims to ensure consistency, maintainability, and security across all services developed in Python.

### Audience
This document is intended for:
- Backend engineers working on FastAPI applications.
- Technical leads overseeing architecture and design.
- Quality assurance teams responsible for validating API behavior.

### Scope
This standard covers:
- Request validation for incoming data using Pydantic models.
- Response schema definitions for outgoing data.
- Best practices for implementing custom validators.
- Configuration examples for schema validation.

### Non-goals
This document does not cover:
- General FastAPI application development practices.
- Database schema design or ORM integration.
- Frontend validation or user interface considerations.

### Glossary
| Term               | Definition                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| Pydantic           | A data validation and settings management library for Python.              |
| FastAPI            | A modern web framework for building APIs with Python 3.7+ based on standard Python type hints. |
| Schema             | A structured representation of data, often defined as a model in Pydantic. |
| Validator          | A function that checks the validity of data against defined rules.         |
| Request Schema     | The structure defining the expected format of incoming requests.           |
| Response Schema    | The structure defining the format of outgoing responses.                   |

### How This Standard Fits the Xentic Platform
The Xentic platform emphasizes the importance of robust and secure API design. By adhering to these schema validation standards, we ensure that:
- All incoming data is validated against strict criteria, reducing the risk of malformed or malicious data.
- Response data is structured and predictable, enhancing the consumer experience.
- Consistency is maintained across different services, facilitating easier integration and collaboration among teams.

### Example Implementation

#### Request Validation
```python
from pydantic import BaseModel, EmailStr, field_validator
import re

class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "USER"

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        return v
```

#### Response Schemas
```python
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
```

### Rules
- **Request schemas**: MUST enforce strict validation and MUST NOT expose internal fields.
- **Response schemas**: MUST NOT include password hashes or sensitive information.
- **Email fields**: MUST use `EmailStr` for all email-related data.
- **Validators**: MUST be pure functions without side effects or I/O operations.

## Standards and policies

1. **Schema Definition**: 
   - All request and response schemas MUST be defined using Pydantic models. This ensures type safety and validation consistency across the application.

2. **Naming Conventions**:
   - Schema classes MUST follow the naming convention of `<Action><Resource>Request` for request schemas (e.g., `CreateUserRequest`) and `<Resource>Response` for response schemas (e.g., `UserResponse`).

3. **Field Types**:
   - All fields in Pydantic models MUST use the appropriate Pydantic types (e.g., `EmailStr`, `conint`, `constr`) to enforce validation rules.

4. **Custom Validators**:
   - Custom validators MUST be implemented using the `@field_validator` decorator and MUST NOT include side effects or I/O operations.

5. **Error Handling**:
   - Validation errors MUST return clear and descriptive messages to the client. The error format MUST be consistent across all APIs.

6. **Sensitive Information**:
   - Response schemas MUST NOT include sensitive information such as passwords, password hashes, or personal identification numbers.

7. **Default Values**:
   - Default values for fields MUST be defined in the schema where applicable, ensuring that the API behaves predictably.

8. **Optional Fields**:
   - Optional fields MUST be explicitly marked with `Optional` from the `typing` module and MUST have a clear default value if applicable.

9. **Documentation**:
   - All Pydantic models MUST include docstrings that describe the purpose of the model and its fields, following the format defined in the Xentic documentation guidelines.

10. **Testing**:
    - All schemas MUST be covered by unit tests that validate both expected and edge case inputs, ensuring robustness.

11. **Versioning**:
    - Schemas MUST be versioned when breaking changes are introduced, following the semantic versioning principles outlined in the Xentic API standards.

12. **Shared Libraries**:
    - Common validation logic MUST be extracted into shared libraries under `com.xentic.common` to promote code reuse and reduce duplication.

13. **Configuration**:
    - Configuration settings related to validation MUST be defined in a centralized configuration file (e.g., `config.yaml`) and MUST NOT be hardcoded within the schema classes.

    Example of a configuration file:
    ```yaml
    validation:
      max_full_name_length: 50
      min_password_length: 8
    ```

14. **Logging**:
    - All validation failures MUST be logged at the appropriate log level, ensuring that issues can be tracked and resolved efficiently.

15. **Performance**:
    - Schema validation MUST be optimized for performance, and any heavy computations should be handled outside of the validation process.

16. **Security**:
    - All schemas MUST be reviewed for security vulnerabilities, including injection attacks and data leakage, before deployment.

17. **Compliance**:
    - Schemas MUST comply with applicable regulations and standards (e.g., GDPR, HIPAA) regarding data handling and validation.

18. **Inter-Service Communication**:
    - When defining schemas for inter-service communication, the schemas MUST be documented and versioned to ensure compatibility across services.

By adhering to these standards and policies, Xentic ensures that all FastAPI applications maintain high quality, security, and consistency in schema validation practices.

## Architecture and design

### Component Diagram

```mermaid
graph TD;
    A[Client] -->|HTTP Request| B[FastAPI Service];
    B -->|Schema Validation| C[Pydantic Models];
    C -->|Validates| D[Database];
    B -->|Response| A;
    B -->|Logs| E[Logging Service];
    B -->|Metrics| F[Monitoring Service];
    B -->|Error Handling| G[Error Handler];
    D -->|Data Retrieval| H[External API];
```

### Data Flows

1. **Client Request**: The client sends an HTTP request to the FastAPI service.
2. **Schema Validation**: The FastAPI service uses Pydantic models to validate incoming data against defined schemas.
3. **Database Interaction**: Once validated, the service interacts with the database to perform CRUD operations.
4. **Response Generation**: After processing, the service generates a response based on the defined response schema.
5. **Logging**: All interactions, including validation errors and successful requests, are logged for audit and debugging purposes.
6. **Monitoring**: Metrics are collected to monitor the service performance and health.
7. **Error Handling**: Any validation errors or exceptions are handled gracefully, providing clear feedback to the client.

### Integration Points

- **Database**: The FastAPI service integrates with a database for data persistence. The schema validation ensures that only valid data is sent to the database.
- **External APIs**: The service may interact with external APIs for additional data or functionality, with validation ensuring that the data conforms to expected formats.
- **Logging Service**: All validation errors and significant events are logged to a centralized logging service for monitoring and troubleshooting.
- **Monitoring Service**: Integration with a monitoring service allows for tracking of performance metrics and alerting on anomalies.

### Failure Domains

- **Validation Failures**: If incoming data does not conform to the defined Pydantic models, the request is rejected, and an appropriate error response is returned to the client.
- **Database Failures**: Any failures during database interactions (e.g., connection issues, constraint violations) should be handled gracefully, with clear error messages logged and returned.
- **External API Failures**: If the service relies on external APIs, failures in these APIs can affect the overall functionality. The service should implement fallback mechanisms where possible.
- **Logging and Monitoring**: If the logging or monitoring services are unavailable, the application should continue to function, but it may lose the ability to track events and performance metrics.

### Summary

The architecture of the FastAPI application with Pydantic v2 emphasizes a clear separation of concerns, robust validation, and effective error handling. By defining clear data flows and integration points, Xentic ensures that the application is resilient, maintainable, and scalable, while also adhering to the established standards and policies for schema validation.

## Configuration reference

### application.yml

The `application.yml` file defines various configuration parameters for the FastAPI application. Below is an example of how to structure this file, including defaults and production values.

```yaml
app:
  name: "Xentic FastAPI Service"
  version: "1.0.0"

validation:
  max_full_name_length: 50  # Maximum length for full name
  min_password_length: 8     # Minimum length for password
  email_domain_whitelist:
    - "xentic.io"
    - "example.com"

database:
  url: "postgresql://user:password@db.internal.xentic.io:5432/xentic_db"
  pool_size: 10
  timeout: 30

logging:
  level: "INFO"  # Log level can be DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "/var/log/xentic/app.log"

security:
  jwt_secret: "your_jwt_secret_key"
  algorithm: "HS256"
  token_expiration_minutes: 60

cors:
  origins:
    - "https://app.internal.xentic.io"
    - "https://api.internal.xentic.io"
```

### Terraform Configuration

The following Terraform configuration sets up resources necessary for the FastAPI application, including the database and environment variables.

```hcl
resource "aws_db_instance" "xentic_db" {
  allocated_storage    = 20
  engine             = "postgres"
  engine_version     = "13.3"
  instance_class     = "db.t3.micro"
  name               = "xentic_db"
  username           = "user"
  password           = "password"
  db_subnet_group_name = aws_db_subnet_group.xentic_subnet_group.name
  vpc_security_group_ids = [aws_security_group.xentic_sg.id]

  tags = {
    Name = "Xentic Database"
  }
}

resource "aws_lambda_function" "xentic_fastapi" {
  function_name = "xentic_fastapi"
  handler       = "app.handler"
  runtime       = "python3.8"
  s3_bucket     = "xentic-bucket"
  s3_key        = "fastapi.zip"
  
  environment = {
    DATABASE_URL = "postgresql://user:password@db.internal.xentic.io:5432/xentic_db"
    JWT_SECRET   = "your_jwt_secret_key"
    LOG_LEVEL    = "INFO"
  }
}
```

### Environment Variables

The following table outlines the environment variables that should be set for the FastAPI application, including their default and production values.

| Variable                  | Default Value                                          | Production Value                                   |
|---------------------------|-------------------------------------------------------|---------------------------------------------------|
| `DATABASE_URL`            | `postgresql://user:password@localhost:5432/xentic_db` | `postgresql://user:password@db.internal.xentic.io:5432/xentic_db` |
| `JWT_SECRET`              | `default_jwt_secret`                                 | `your_jwt_secret_key`                             |
| `LOG_LEVEL`               | `INFO`                                               | `ERROR`                                           |
| `CORS_ORIGINS`            | `http://localhost:3000`                              | `https://app.internal.xentic.io`                 |
| `VALIDATION_MAX_FULL_NAME_LENGTH` | `50`                                      | `50`                                             |
| `VALIDATION_MIN_PASSWORD_LENGTH` | `8`                                       | `8`                                              |

### Notes

- All configuration values MUST be managed through environment variables in production to avoid hardcoding sensitive information.
- The `application.yml` file MUST be included in the source control but should not contain sensitive information such as passwords or secrets.
- Terraform configurations MUST be versioned and stored in a secure repository to ensure reproducibility and traceability.
- Environment variables MUST be documented and shared among team members to maintain consistency across development and production environments.

## Implementation guide

To implement schema validation in a FastAPI application using Pydantic v2, follow these steps:

### Step 1: Install Required Packages

Ensure you have FastAPI and Pydantic installed. You can install them using pip:

```bash
pip install fastapi[all] pydantic
```

### Step 2: Define Your Pydantic Models

Create a file named `models.py` in your application directory. This file will contain your Pydantic models for validation.

```python
# models.py
from pydantic import BaseModel, EmailStr, constr, Field

class User(BaseModel):
    id: int
    full_name: constr(max_length=50) = Field(..., description="Full name of the user")
    email: EmailStr
    password: constr(min_length=8)

class Item(BaseModel):
    name: constr(max_length=100) = Field(..., description="Name of the item")
    description: str = Field(None, description="Description of the item")
    price: float = Field(..., gt=0, description="Price of the item")
```

### Step 3: Create FastAPI Application

Create a file named `main.py` for your FastAPI application.

```python
# main.py
from fastapi import FastAPI, HTTPException
from models import User, Item

app = FastAPI()

@app.post("/users/", response_model=User)
async def create_user(user: User):
    # Here you would typically save the user to a database
    return user

@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    # Here you would typically save the item to a database
    return item
```

### Step 4: Run Your Application

Run your FastAPI application using the command below:

```bash
uvicorn main:app --reload
```

### Step 5: Test Your Endpoints

You can test your endpoints using a tool like Postman or cURL. Here are examples of how to test the endpoints:

#### Create User

```bash
curl -X POST "http://127.0.0.1:8000/users/" -H "Content-Type: application/json" -d '{
  "id": 1,
  "full_name": "John Doe",
  "email": "john.doe@example.com",
  "password": "securepassword"
}'
```

#### Create Item

```bash
curl -X POST "http://127.0.0.1:8000/items/" -H "Content-Type: application/json" -d '{
  "name": "Sample Item",
  "description": "This is a sample item.",
  "price": 19.99
}'
```

### Step 6: Handle Validation Errors

FastAPI automatically handles validation errors and returns a structured response. Here’s an example of a validation error response when the `full_name` exceeds the maximum length:

```json
{
  "detail": [
    {
      "loc": ["body", "full_name"],
      "msg": "ensure this value has at most 50 characters",
      "type": "value_error.str.max_length"
    }
  ]
}
```

### Step 7: Logging Validation Errors

To log validation errors, you can implement a custom exception handler in `main.py`.

```python
# main.py (continued)
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logging.error(f"Validation Error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
```

### Summary

By following these steps, you have implemented schema validation in a FastAPI application using Pydantic v2. The application now validates incoming requests against defined schemas, handles errors gracefully, and logs validation failures for further analysis. This approach ensures data integrity and enhances the reliability of your FastAPI services.

## Security requirements

To ensure the security of the FastAPI application, Xentic must implement a comprehensive security model that addresses various threats and vulnerabilities. Below is a summary of the security requirements that must be adhered to:

### Threat Model Summary

- **Data Breaches**: Unauthorized access to sensitive user data, including personally identifiable information (PII) and authentication credentials.
- **Injection Attacks**: Risks associated with SQL injection, command injection, and other forms of injection attacks that can compromise the application.
- **Denial of Service (DoS)**: Attacks that aim to overwhelm the application, rendering it unavailable to legitimate users.
- **Insecure Direct Object References (IDOR)**: Risks associated with exposing internal object references that can be exploited by attackers.

### Authentication and Authorization

- **Authentication**: The application MUST use JWT (JSON Web Tokens) for user authentication. Tokens MUST be signed and verified using a secure algorithm (e.g., HS256).
  
  Example configuration for JWT:
  ```yaml
  security:
    jwt_secret: "your_jwt_secret_key"  # MUST be kept secret
    algorithm: "HS256"
    token_expiration_minutes: 60
  ```

- **Authorization**: All endpoints MUST enforce authorization checks to ensure that users have the appropriate permissions to access resources. Role-based access control (RBAC) SHOULD be implemented to manage user roles and permissions effectively.

### Secrets Management

- **Secrets Storage**: Sensitive information such as database credentials and JWT secrets MUST NOT be hardcoded in the source code. Instead, they MUST be stored in environment variables or a secure secrets management system (e.g., HashiCorp Vault).
  
  Example of environment variable usage:
  ```bash
  export JWT_SECRET="your_jwt_secret_key"
  export DATABASE_URL="postgresql://user:password@db.internal.xentic.io:5432/xentic_db"
  ```

- **Access Control**: Access to secrets management systems MUST be restricted to authorized personnel only, and audit logs MUST be maintained to track access and modifications.

### Input Validation

- **Schema Validation**: All incoming requests MUST be validated against Pydantic models to ensure that the data conforms to expected formats. This helps prevent injection attacks and ensures data integrity.

- **Rate Limiting**: Implement rate limiting on API endpoints to mitigate the risk of DoS attacks. FastAPI can be integrated with middleware such as `slowapi` to enforce rate limits.

  Example of rate limiting configuration:
  ```python
  from slowapi import Limiter
  limiter = Limiter(key_func=get_remote_address)

  @app.route("/items/")
  @limiter.limit("5/minute")  # Limit to 5 requests per minute
  async def create_item(item: Item):
      ...
  ```

### Audit Logging

- **Logging Configuration**: The application MUST have a robust logging mechanism to capture security-related events, including authentication attempts, authorization failures, and input validation errors.

  Example logging configuration:
  ```yaml
  logging:
    level: "INFO"  # Log level can be DEBUG, INFO, WARNING, ERROR, CRITICAL
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: "/var/log/xentic/app.log"
  ```

- **Sensitive Data Redaction**: Logs MUST NOT contain sensitive information (e.g., passwords, JWT tokens). Implement mechanisms to redact or obfuscate sensitive data in logs.

- **Regular Audits**: Security logs MUST be reviewed regularly to identify suspicious activities and ensure compliance with security policies. Automated tools SHOULD be used to analyze logs for anomalies.

### Summary

By implementing the above security requirements, Xentic can significantly reduce the risk of security breaches and ensure that the FastAPI application is resilient against various threats. The focus on authentication, authorization, secrets management, input validation, and audit logging will help maintain the integrity and confidentiality of the application and its data.

## Testing strategy

To ensure the reliability and correctness of the FastAPI application, Xentic MUST implement a comprehensive testing strategy that includes unit tests, integration tests, and contract tests. The testing strategy should adhere to the following guidelines:

### Testing Types

- **Unit Tests**: Validate individual components in isolation, ensuring that each function or method behaves as expected. Unit tests MUST cover at least 80% of the codebase.
  
- **Integration Tests**: Test the interaction between different components and external systems (e.g., databases, third-party APIs). Integration tests SHOULD cover at least 70% of the integration points.

- **Contract Tests**: Ensure that the API adheres to the defined contract, validating that the API responses match the expected schema. Contract tests MUST be run against both the consumer and provider sides.

### Coverage Targets

| Test Type         | Coverage Target |
|-------------------|-----------------|
| Unit Tests        | 80%             |
| Integration Tests | 70%             |
| Contract Tests    | 100%            |

### Example Test Classes

#### Unit Test Example

Create a file named `test_models.py` to test your Pydantic models.

```python
# test_models.py
import pytest
from models import User, Item
from pydantic import ValidationError

def test_user_model_valid():
    user = User(id=1, full_name="John Doe", email="john.doe@example.com", password="securepassword")
    assert user.id == 1
    assert user.full_name == "John Doe"

def test_user_model_invalid_email():
    with pytest.raises(ValidationError):
        User(id=1, full_name="John Doe", email="invalid-email", password="securepassword")
```

#### Integration Test Example

Create a file named `test_integration.py` to test the API endpoints.

```python
# test_integration.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_user():
    response = client.post("/users/", json={
        "id": 1,
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "password": "securepassword"
    })
    assert response.status_code == 200
    assert response.json()["full_name"] == "John Doe"

def test_create_item():
    response = client.post("/items/", json={
        "name": "Sample Item",
        "description": "This is a sample item.",
        "price": 19.99
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Sample Item"
```

#### Contract Test Example

Create a file named `test_contract.py` to validate the API contract.

```python
# test_contract.py
import requests
import jsonschema
from jsonschema import validate

API_URL = "http://127.0.0.1:8000/users/"

user_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "full_name": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "password": {"type": "string", "minLength": 8}
    },
    "required": ["id", "full_name", "email", "password"]
}

def test_user_contract():
    response = requests.post(API_URL, json={
        "id": 1,
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "password": "securepassword"
    })
    assert response.status_code == 200
    validate(instance=response.json(), schema=user_schema)
```

### Test Execution

To run the tests, ensure that the FastAPI application is running and execute the following command:

```bash
pytest
```

### Summary

By implementing a robust testing strategy that includes unit, integration, and contract tests, Xentic can ensure the quality and reliability of its FastAPI application. Adhering to the specified coverage targets and using the provided examples will help maintain high standards in the development process.

## Observability and operations

To maintain the reliability and performance of the FastAPI application, Xentic MUST implement a comprehensive observability strategy that encompasses metrics, logs, traces, dashboards, alerts, and service level objectives (SLOs). The following guidelines outline the requirements for effective observability and operations.

### Metrics

Xentic MUST collect and expose application metrics to monitor performance and health. Key metrics to track include:

- **Request Latency**: Measure the time taken to process requests.
- **Error Rates**: Track the number of failed requests.
- **Throughput**: Monitor the number of requests processed per second.
- **Resource Utilization**: Monitor CPU and memory usage.

Example Prometheus metrics configuration in `main.py`:

```python
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

Instrumentator().instrument(app).expose(app)
```

### Logging

Xentic MUST implement structured logging to capture relevant application events. Logs MUST include:

- **Timestamp**: When the event occurred.
- **Log Level**: Severity of the log (INFO, ERROR, etc.).
- **Message**: Description of the event.
- **Context**: Additional context (e.g., user ID, request ID).

Example logging configuration in `logging.yaml`:

```yaml
version: 1
disable_existing_loggers: False
formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
handlers:
  file:
    class: logging.FileHandler
    filename: '/var/log/xentic/app.log'
    formatter: standard
loggers:
  myapp:
    level: INFO
    handlers: [file]
    propagate: no
```

### Traces

Distributed tracing MUST be implemented to track requests across microservices. Xentic SHOULD use OpenTelemetry for tracing. Key components include:

- **Trace Context**: Pass trace IDs between services.
- **Span**: Measure the duration of operations.

Example OpenTelemetry setup in `main.py`:

```python
from opentelemetry import trace
from opentelemetry.ext.fastapi import FastAPIInstrumentor

tracer = trace.get_tracer(__name__)
FastAPIInstrumentor.instrument_app(app)
```

### Dashboards

Xentic SHOULD create dashboards to visualize metrics and logs. Dashboards MUST include:

- **Service Health**: Display key metrics and error rates.
- **Performance Trends**: Show latency and throughput over time.
- **Error Tracking**: Highlight the most common errors.

Tools like Grafana or Kibana MUST be used to create these dashboards.

### Alerts

Xentic MUST configure alerts to notify the team of critical issues. Alerts SHOULD be based on:

- **Error Rate Thresholds**: Alert when error rates exceed a defined threshold.
- **Latency Thresholds**: Alert when request latency exceeds acceptable limits.
- **Resource Utilization**: Alert when CPU or memory usage is critically high.

Example alerting rule in Prometheus:

```yaml
groups:
- name: alerting
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status="500"}[5m]) > 0.05
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "More than 5% of requests are failing."
```

### Service Level Objectives (SLOs)

Xentic MUST define SLOs to measure service reliability. SLOs SHOULD include:

- **Availability**: Percentage of successful requests over a defined period.
- **Latency**: Percentage of requests completed within a specific time frame.

Example SLO definition:

| Objective        | Target       | Measurement Period |
|------------------|--------------|---------------------|
| Availability      | 99.9%        | Monthly             |
| Latency (95th%)  | < 200ms      | Monthly             |

### On-Call Runbook Steps

In the event of an incident, the on-call engineer MUST follow these steps:

1. **Identify the Incident**: Check alerts and logs to identify the issue.
2. **Assess Impact**: Determine the severity and affected services.
3. **Notify Stakeholders**: Inform relevant teams and stakeholders about the incident.
4. **Mitigate the Issue**: Implement temporary fixes or workarounds.
5. **Document the Incident**: Record the incident details, actions taken, and resolution.
6. **Post-Incident Review**: Conduct a review to identify root causes and preventive measures.

### Summary

By implementing a comprehensive observability and operations strategy, Xentic can ensure the FastAPI application remains reliable and performant. Adhering to the outlined metrics, logging, tracing, dashboards, alerts, SLOs, and on-call runbook steps will help maintain high operational standards and quickly address any issues that arise.

## Migration and versioning

To ensure the integrity and stability of Xentic's FastAPI applications, a clear migration and versioning strategy MUST be established. This section outlines the upgrade paths, deprecation policies, backward compatibility considerations, and rollback procedures.

### Upgrade Paths

When upgrading FastAPI or Pydantic versions, the following paths MUST be followed:

1. **Review Release Notes**: Always review the release notes for both FastAPI and Pydantic to understand breaking changes and new features.
2. **Incremental Upgrades**: Upgrades SHOULD be performed incrementally (e.g., from v2.0 to v2.1) rather than jumping multiple versions to minimize risks.
3. **Testing**: Comprehensive testing MUST be conducted after each upgrade to ensure the application behaves as expected.

### Deprecation Policy

Xentic MUST adhere to a strict deprecation policy:

- **Deprecation Notices**: Any deprecated features MUST be documented in the release notes and communicated to the development team.
- **Grace Period**: A grace period of at least one major version MUST be provided before removing deprecated features.
- **Alternative Solutions**: Documentation MUST include recommended alternatives for deprecated features.

### Backward Compatibility

Backward compatibility MUST be prioritized during upgrades:

- **API Versioning**: APIs MUST be versioned to allow clients to continue using older versions while migrating to newer ones. This can be achieved by including the version in the URL, e.g., `/v1/users/`.
- **Feature Flags**: New features SHOULD be implemented behind feature flags to allow gradual rollouts and easy rollback if issues arise.

Example of API versioning in FastAPI:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/v1/users/")
def read_users_v1():
    return [{"username": "user1"}, {"username": "user2"}]

@app.get("/v2/users/")
def read_users_v2():
    return [{"username": "user1", "status": "active"}, {"username": "user2", "status": "inactive"}]
```

### Rollback Procedures

In the event of a failed upgrade, a rollback procedure MUST be in place:

1. **Backup**: Always create a backup of the current application state and database before performing an upgrade.
2. **Version Control**: Use version control (e.g., Git) to manage changes and allow easy rollback to a previous stable version.
3. **Rollback Steps**:
   - Restore the backup of the application and database.
   - Revert to the previous version in the version control system.
   - Run tests to ensure the application is functioning as expected.

Example rollback command using Git:

```bash
git checkout <previous-stable-commit>
```

### Migration Scripts

If database schema changes are required, migration scripts MUST be created and versioned. Use tools like Alembic for managing database migrations. 

Example Alembic migration script:

```python
"""Add user status column

Revision ID: 123456789abc
Revises: 987654321def
Create Date: 2023-10-01 12:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '123456789abc'
down_revision = '987654321def'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('status', sa.String(length=20), nullable=True))

def downgrade():
    op.drop_column('users', 'status')
```

### Summary

By implementing a structured migration and versioning strategy, Xentic can ensure that its FastAPI applications remain stable and maintainable. Adhering to the outlined upgrade paths, deprecation policies, backward compatibility measures, and rollback procedures will help mitigate risks during transitions and maintain high-quality standards in software development.

## FAQ, anti-patterns, and checklists

### FAQ

1. **What is Pydantic?**
   - Pydantic is a data validation and settings management library for Python, used with FastAPI to validate request and response data.

2. **How do I validate a request body using Pydantic?**
   - Define a Pydantic model and use it as a type hint in your FastAPI route. FastAPI will automatically validate incoming requests against the model.
   ```python
   from pydantic import BaseModel

   class User(BaseModel):
       username: str
       email: str

   @app.post("/users/")
   def create_user(user: User):
       return user
   ```

3. **Can I use custom validation in Pydantic?**
   - Yes, you can use the `@validator` decorator to create custom validation logic within your Pydantic models.
   ```python
   from pydantic import validator

   class User(BaseModel):
       username: str
       email: str

       @validator('email')
       def email_must_be_valid(cls, v):
           if "@" not in v:
               raise ValueError('must be a valid email')
           return v
   ```

4. **What happens if validation fails?**
   - FastAPI will return a 422 Unprocessable Entity response with details about the validation errors.

5. **How do I handle optional fields in Pydantic?**
   - Use `Optional` from the `typing` module to define fields that may or may not be present.
   ```python
   from typing import Optional

   class User(BaseModel):
       username: str
       email: Optional[str] = None
   ```

6. **Can I use Pydantic models for response validation?**
   - Yes, you can return Pydantic models directly from your route functions, and FastAPI will validate the response against the model.

7. **How do I manage environment variables with Pydantic?**
   - Use `BaseSettings` to create a settings class that loads environment variables.
   ```python
   from pydantic import BaseSettings

   class Settings(BaseSettings):
       database_url: str

   settings = Settings()
   ```

8. **What is the difference between `BaseModel` and `BaseSettings`?**
   - `BaseModel` is used for data validation, while `BaseSettings` is specifically designed for managing application settings from environment variables.

9. **How can I enforce strict types in Pydantic?**
   - Use the `strict` parameter in field definitions to enforce strict type checking.
   ```python
   from pydantic import StrictStr

   class User(BaseModel):
       username: StrictStr
   ```

10. **What are the performance implications of using Pydantic?**
    - Pydantic is generally performant, but extensive use of complex models or validations can introduce overhead. Always profile if performance is a concern.

### Anti-Patterns

| Anti-Pattern                           | Description                                                                                 | Solution                                                                                       |
|----------------------------------------|---------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| Using mutable types in models          | Defining lists or dictionaries as default values can lead to unexpected behavior.          | Use `default_factory` for mutable types.                                                     |
| Ignoring validation errors              | Not handling validation errors can lead to unhandled exceptions.                          | Always return meaningful error responses for validation failures.                             |
| Overusing inheritance                   | Excessive inheritance can complicate models and lead to confusion.                         | Prefer composition over inheritance for model definitions.                                    |
| Mixing business logic with validation   | Including business logic inside Pydantic models can make them less reusable.               | Keep validation and business logic separate.                                                  |
| Not using type hints                   | Omitting type hints can lead to unclear code and reduce the benefits of Pydantic.         | Always use type hints for clarity and validation.                                            |
| Hardcoding values in models             | Hardcoding values can lead to inflexible models.                                          | Use constants or enums for fixed values.                                                     |

### Pre-Merge Checklist

- [ ] Ensure all Pydantic models are validated against the expected schema.
- [ ] Review and test custom validators for edge cases.
- [ ] Check for the proper use of optional fields and default values.
- [ ] Ensure all routes return appropriate response models.
- [ ] Verify that environment configurations are loaded correctly.

### Production Checklist

- [ ] Confirm that all models are documented, including fields and validations.
- [ ] Run integration tests to ensure all endpoints behave as expected.
- [ ] Monitor performance metrics to identify any potential bottlenecks.
- [ ] Ensure logging is configured to capture validation errors and warnings.
- [ ] Review security measures to protect against data validation vulnerabilities.
