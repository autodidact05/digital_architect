# Dependency Injection Patterns — FastAPI

## Overview and scope

The purpose of this document is to establish a set of engineering standards for implementing Dependency Injection (DI) patterns within FastAPI applications at Xentic. This standard aims to promote best practices that enhance code maintainability, testability, and scalability across our projects. 

### Audience
This document is intended for:
- Software Engineers
- Technical Leads
- Architects
- Quality Assurance Engineers

### Scope
This standard covers:
- Best practices for implementing DI in FastAPI applications.
- Patterns for service layer injection, pagination, and other common use cases.
- Configuration examples and code snippets to illustrate proper usage.
- Guidelines for testing and overriding dependencies.

### Non-goals
This document does NOT aim to:
- Provide a comprehensive tutorial on FastAPI or Python.
- Cover every possible use case for dependency injection.
- Replace existing architectural documentation.

### Glossary
| Term               | Definition                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| Dependency Injection| A design pattern that allows a class to receive its dependencies from an external source rather than creating them internally. |
| FastAPI            | A modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints. |
| Service Layer      | A design pattern that encapsulates the business logic of an application.    |
| Pagination         | The process of dividing a large dataset into smaller chunks for efficient retrieval. |

### How this standard fits the Xentic platform
This standard aligns with Xentic's commitment to maintain high-quality software development practices. By adhering to these guidelines, teams can ensure that their FastAPI applications are consistent, easy to test, and maintainable. The use of DI patterns allows for better separation of concerns, enabling developers to focus on business logic without being tightly coupled to specific implementations.

### Example Patterns

#### Service Layer DI
```python
async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

async def get_user_service(
    repo: UserRepository = Depends(get_user_repository)
) -> UserService:
    return UserService(repo)
```

#### Pagination Dependency
```python
@dataclass
class PaginationParams:
    page: int = 0
    size: int = 20

    def __post_init__(self):
        self.size = min(self.size, 100)

def get_pagination(page: int = 0, size: int = 20) -> PaginationParams:
    return PaginationParams(page=page, size=size)
```

#### Usage Example
```python
@router.get("/users")
async def list_users(
    pagination: PaginationParams = Depends(get_pagination),
    current_user: TokenData = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return await service.find_all(pagination.page, pagination.size)
```

### Rules
- **MUST** prefer `Depends()` over global singletons for testability.
- **MUST NOT** create tight coupling between components; dependencies should be injected.
- **MUST** ensure that dependencies forming a chain are transparent for test overrides.
- **MUST** always override dependencies in tests via `app.dependency_overrides`.

## Standards and policies

1. **MUST** use the `Depends` utility provided by FastAPI for all dependency injections to ensure proper lifecycle management and better testability.
   
2. **MUST NOT** use global variables or singletons for managing dependencies, as this leads to tight coupling and makes unit testing difficult.

3. **SHOULD** define all dependencies in a dedicated module (e.g., `dependencies.py`) within the service package to maintain organization and clarity.

4. **MUST** document all dependencies in the respective modules using docstrings to provide clear context for future developers.

5. **MUST** ensure that all service classes and their dependencies are defined within the `com.xentic.<service>` package structure to adhere to Xentic conventions.

6. **MUST NOT** hardcode configuration values directly in the code. Instead, use environment variables or configuration files (YAML, HCL, or properties) to manage settings.

   Example configuration in `config.yaml`:
   ```yaml
   database:
     url: "postgresql://user:password@localhost/dbname"
   ```

7. **SHOULD** use a configuration management library (e.g., `Pydantic` or `Dynaconf`) to load and validate configuration settings.

8. **MUST** implement error handling within dependency functions to ensure that any issues are logged and handled gracefully.

9. **SHOULD** utilize FastAPI's built-in dependency injection for middleware and background tasks to maintain consistency across the application.

10. **MUST** write unit tests for all dependencies using FastAPI's testing utilities to ensure that they function correctly in isolation.

11. **SHOULD** use type hints consistently for all dependencies to leverage FastAPI's automatic validation and documentation generation.

12. **MUST NOT** create circular dependencies between services. If a circular dependency is detected, refactor the code to break the cycle.

13. **MUST** use `async` functions for any dependency that interacts with I/O operations, such as database calls, to ensure non-blocking behavior.

14. **SHOULD** consider using dependency injection for third-party services (e.g., external APIs) to allow for easier mocking and testing.

15. **MUST** follow the naming conventions for dependencies, using clear and descriptive names that reflect their purpose (e.g., `get_user_service`, `get_db_connection`).

16. **MUST** provide default values for optional dependencies to ensure that the application remains functional even when certain dependencies are not provided.

17. **SHOULD** review and refactor dependencies periodically to ensure that they remain relevant and efficient as the application evolves.

18. **MUST** avoid using mutable default arguments in dependency functions to prevent unexpected behavior.

19. **MUST** ensure that all dependencies are thread-safe if they are shared across multiple threads or processes.

20. **SHOULD** use FastAPI's dependency injection system to manage authentication and authorization logic, promoting a clean separation of concerns.

21. **MUST** ensure that all injected services are instantiated only once per request to optimize resource usage.

22. **MUST NOT** expose internal service dependencies directly to the API layer; instead, use service interfaces to encapsulate business logic.

23. **SHOULD** leverage FastAPI's dependency injection for managing application state, such as user sessions or request-specific data.

24. **MUST** maintain a clear separation between application logic and dependency management to facilitate easier testing and maintenance.

By adhering to these standards and policies, Xentic aims to create robust, maintainable, and testable FastAPI applications that align with our organizational goals and practices.

## Architecture and design

The architecture of FastAPI applications at Xentic is designed to leverage Dependency Injection (DI) patterns effectively, promoting modularity and testability. Below is a component diagram that illustrates the primary components and their interactions.

```mermaid
graph TD;
    A[API Layer] -->|Depends on| B[Service Layer]
    B -->|Depends on| C[Repository Layer]
    B -->|Uses| D[External API]
    C -->|Interacts with| E[Database]
    A -->|Injects| F[Authentication Middleware]
    A -->|Injects| G[Logging Middleware]
```

### Data Flows

1. **API Layer**: Receives HTTP requests and delegates processing to the Service Layer.
2. **Service Layer**: Contains business logic and interacts with the Repository Layer for data access.
3. **Repository Layer**: Handles CRUD operations and communicates with the Database.
4. **External API**: Services that the application may call for additional data or functionality.
5. **Middleware**: Authentication and logging middleware are injected into the API layer to manage cross-cutting concerns.

### Integration Points

- **Database**: The application integrates with a relational database (e.g., PostgreSQL) for persistent data storage.
- **External Services**: APIs for third-party services can be injected into the service layer, allowing for flexible integration.
- **Authentication**: Middleware for handling authentication is injected into the API layer to ensure secure access.

### Failure Domains

- **Database Failures**: If the database is unavailable, the application should handle this gracefully, returning appropriate error responses to the client.
- **External API Failures**: When calling external APIs, the application should implement retries and fallbacks to maintain resilience.
- **Service Layer Failures**: Any failures in the service layer must be logged, and the API should return a user-friendly error message.

### Example Configuration

The following example demonstrates how to configure the database connection and external API settings in `config.yaml`:

```yaml
database:
  url: "postgresql://user:password@localhost/dbname"
  max_connections: 20

external_api:
  url: "https://api.example.com"
  timeout: 5
```

### Code Example

Here is an example of how to structure the application with DI:

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .dependencies import get_user_service, get_db
from .models import User

app = FastAPI()

@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: int, service: UserService = Depends(get_user_service)):
    return await service.get_user(user_id)
```

### Summary of Best Practices

- **MUST** maintain clear and well-defined boundaries between layers (API, Service, Repository).
- **MUST** handle errors gracefully at each layer, providing meaningful feedback to the client.
- **SHOULD** use environment variables for sensitive configuration data (e.g., database credentials).
- **MUST** ensure that all components are testable in isolation, following DI principles.
- **SHOULD** document data flows and integration points to facilitate onboarding and maintenance.

By adhering to these architectural principles and patterns, Xentic aims to build robust, scalable, and maintainable FastAPI applications that effectively utilize Dependency Injection.

## Configuration reference

### Configuration File (`application.yml`)

The following is an example of the `application.yml` configuration file, which defines various application settings, including database connections and external service configurations.

```yaml
app:
  name: "Xentic FastAPI Application"
  environment: "production"

database:
  url: "postgresql://user:password@localhost/dbname"
  max_connections: 20
  timeout: 5

external_api:
  url: "https://api.example.com"
  timeout: 5
  retries: 3

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Environment Variables

The application can also be configured using environment variables. Below is a table outlining the environment variables, their default values, and production values.

| Environment Variable        | Default Value                       | Production Value                       |
|-----------------------------|-------------------------------------|----------------------------------------|
| `APP_NAME`                  | `Xentic FastAPI Application`        | `Xentic FastAPI Production`            |
| `DATABASE_URL`              | `postgresql://user:password@localhost/dbname` | `postgresql://prod_user:prod_password@prod_host/prod_dbname` |
| `DATABASE_MAX_CONNECTIONS`  | `20`                                | `50`                                   |
| `EXTERNAL_API_URL`          | `https://api.example.com`          | `https://api.prod.example.com`        |
| `EXTERNAL_API_TIMEOUT`      | `5`                                 | `10`                                   |
| `LOGGING_LEVEL`             | `INFO`                              | `ERROR`                                |

### Terraform Configuration

For infrastructure management, Terraform can be used to provision the necessary resources. Below is an example of a Terraform configuration snippet that defines the environment variables for the application.

```hcl
resource "aws_lambda_function" "xentic_fastapi" {
  function_name = "xentic_fastapi"
  handler       = "app.handler"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_exec.arn
  environment {
    APP_NAME                  = "Xentic FastAPI Application"
    DATABASE_URL              = "postgresql://user:password@localhost/dbname"
    DATABASE_MAX_CONNECTIONS   = "20"
    EXTERNAL_API_URL          = "https://api.example.com"
    EXTERNAL_API_TIMEOUT      = "5"
    LOGGING_LEVEL             = "INFO"
  }
}
```

### Summary of Configuration Management

- **MUST** use environment variables or configuration files to manage sensitive information and settings.
- **SHOULD** validate configuration settings at application startup to ensure that all necessary values are provided.
- **MUST NOT** hardcode sensitive information such as passwords or API keys in the source code.
- **SHOULD** utilize a configuration management library (e.g., `Pydantic` or `Dynaconf`) to facilitate loading and validating configurations.
- **MUST** document all configuration options in the repository to provide clarity for developers and operators.

## Implementation guide

To implement Dependency Injection (DI) patterns in a FastAPI application, follow the steps outlined below. This guide provides a comprehensive overview of creating a modular application structure, defining services, and managing dependencies effectively.

### Step 1: Create Project Structure

Organize your FastAPI application with a clear directory structure:

```
/my_fastapi_app
|-- app/
|   |-- __init__.py
|   |-- main.py
|   |-- dependencies.py
|   |-- services/
|   |   |-- __init__.py
|   |   |-- user_service.py
|   |-- models/
|   |   |-- __init__.py
|   |   |-- user.py
|   |-- repositories/
|   |   |-- __init__.py
|   |   |-- user_repository.py
|-- requirements.txt
|-- config.yaml
```

### Step 2: Define Models

Create models that represent your data structures. For example, a User model can be defined as follows:

```python
# app/models/user.py
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str
```

### Step 3: Create Repository Layer

Define a repository that interacts with the database. This layer abstracts data access logic:

```python
# app/repositories/user_repository.py
from typing import List
from .models import User

class UserRepository:
    def __init__(self):
        self.users = []

    def get_user(self, user_id: int) -> User:
        return next((user for user in self.users if user.id == user_id), None)

    def create_user(self, user: User) -> User:
        self.users.append(user)
        return user
```

### Step 4: Implement Service Layer

Create a service that uses the repository to implement business logic:

```python
# app/services/user_service.py
from .repositories.user_repository import UserRepository
from .models import User

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def get_user(self, user_id: int) -> User:
        return self.user_repository.get_user(user_id)

    def create_user(self, user: User) -> User:
        return self.user_repository.create_user(user)
```

### Step 5: Define Dependencies

Create a module for managing dependencies. This module will provide instances of services and repositories:

```python
# app/dependencies.py
from fastapi import Depends
from .repositories.user_repository import UserRepository
from .services.user_service import UserService

def get_user_repository() -> UserRepository:
    return UserRepository()

def get_user_service(user_repository: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(user_repository)
```

### Step 6: Create API Endpoints

Define the API endpoints in the main application file. Use FastAPI's dependency injection to inject services into the route handlers:

```python
# app/main.py
from fastapi import FastAPI, Depends
from .dependencies import get_user_service
from .services.user_service import UserService
from .models.user import User

app = FastAPI()

@app.post("/users/", response_model=User)
async def create_user(user: User, service: UserService = Depends(get_user_service)):
    return service.create_user(user)

@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: int, service: UserService = Depends(get_user_service)):
    return service.get_user(user_id)
```

### Step 7: Configuration Management

Use a configuration file to manage application settings. Below is an example of a `config.yaml`:

```yaml
app:
  name: "Xentic FastAPI Application"
  environment: "production"

database:
  url: "postgresql://user:password@localhost/dbname"
```

### Step 8: Run the Application

To run the FastAPI application, use the following command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Summary of Implementation Steps

- **MUST** define a clear project structure to separate concerns effectively.
- **MUST** create models, repositories, and services to encapsulate data and business logic.
- **MUST** use FastAPI's dependency injection to manage dependencies in route handlers.
- **SHOULD** utilize configuration files for managing application settings securely.
- **MUST** ensure that all components are testable in isolation by following DI principles.

By following this implementation guide, Xentic developers can create scalable and maintainable FastAPI applications that adhere to best practices in Dependency Injection.

## Security requirements

To ensure the security of FastAPI applications at Xentic, the following security requirements must be adhered to:

### Threat Model Summary

- **MUST** identify and assess potential threats such as:
  - Unauthorized access to sensitive data.
  - Injection attacks (SQL, XSS).
  - Denial of Service (DoS) attacks.
  - Data leakage through misconfigured endpoints.
- **SHOULD** conduct regular security assessments and penetration testing to identify vulnerabilities.
- **MUST NOT** expose sensitive endpoints without proper authentication and authorization checks.

### Authentication and Authorization (Authn/z)

- **MUST** implement OAuth2 or JWT for user authentication.
- **SHOULD** use role-based access control (RBAC) to manage user permissions.
- **MUST** ensure that all endpoints requiring authentication are protected using FastAPI's security utilities.

Example of OAuth2 implementation:

```python
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Validate user credentials
    pass

@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    # Decode token and return user information
    pass
```

### Secrets Management

- **MUST** utilize a secrets management tool (e.g., AWS Secrets Manager, HashiCorp Vault) to store sensitive information.
- **SHOULD** rotate secrets regularly and update application configurations accordingly.
- **MUST NOT** hardcode secrets directly in the source code or configuration files.

Example of loading secrets from environment variables:

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
```

### Input Validation

- **MUST** validate all incoming data using Pydantic models to ensure data integrity and prevent injection attacks.
- **SHOULD** implement rate limiting to mitigate brute force attacks on endpoints.
- **MUST NOT** trust user input; always sanitize and validate before processing.

Example of input validation using Pydantic:

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

@app.post("/users/")
async def create_user(user: UserCreate):
    # Create user logic
    pass
```

### Audit Logging

- **MUST** implement logging for all authentication attempts, including successful and failed logins.
- **SHOULD** log all critical actions performed by users, especially those that modify data.
- **MUST NOT** log sensitive information such as passwords or personal data.

Example of audit logging implementation:

```python
import logging

logging.basicConfig(level=logging.INFO)

def log_authentication_attempt(username: str, success: bool):
    if success:
        logging.info(f"User '{username}' logged in successfully.")
    else:
        logging.warning(f"Failed login attempt for user '{username}'.")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Validate user credentials
    log_authentication_attempt(form_data.username, success=True)
```

### Summary of Security Requirements

- **MUST** identify potential threats and implement appropriate security measures.
- **MUST** utilize robust authentication and authorization mechanisms.
- **MUST** manage secrets securely and avoid hardcoding sensitive information.
- **MUST** validate all user inputs to protect against injection attacks.
- **MUST** implement comprehensive audit logging for security monitoring.

By adhering to these security requirements, Xentic ensures that its FastAPI applications are resilient against common threats and vulnerabilities, thereby protecting both the application and its users.

## Testing strategy

To ensure the quality and reliability of FastAPI applications at Xentic, a comprehensive testing strategy must be implemented. This strategy should encompass unit tests, integration tests, and contract tests, with clearly defined coverage targets.

### Testing Types

1. **Unit Tests**
   - **MUST** test individual units of code (e.g., functions, methods) in isolation.
   - **SHOULD** use mocking to isolate dependencies.
   - **MUST NOT** involve external systems (e.g., databases, APIs).

2. **Integration Tests**
   - **MUST** test the interaction between different modules and components.
   - **SHOULD** involve actual database connections and external services.
   - **MUST NOT** be run in the same environment as unit tests to avoid side effects.

3. **Contract Tests**
   - **MUST** ensure that the API contracts between services are adhered to.
   - **SHOULD** include tests for request and response formats.
   - **MUST NOT** allow breaking changes without updating corresponding tests.

### Coverage Targets

- **MUST** aim for a minimum of 80% code coverage across all tests.
- **SHOULD** prioritize critical components, aiming for 90% coverage in core business logic.
- **MUST NOT** ignore untested code paths, particularly those handling errors and edge cases.

### Example Test Classes

Here are examples of how to implement unit and integration tests for the `UserService` class:

#### Unit Test Example

```python
# tests/test_user_service.py
import unittest
from unittest.mock import MagicMock
from app.models.user import User
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository

class TestUserService(unittest.TestCase):
    def setUp(self):
        self.user_repository = MagicMock(UserRepository)
        self.user_service = UserService(self.user_repository)

    def test_create_user(self):
        user_data = User(id=1, name="John Doe", email="john@example.com")
        self.user_repository.create_user.return_value = user_data
        
        created_user = self.user_service.create_user(user_data)
        
        self.assertEqual(created_user.name, "John Doe")
        self.user_repository.create_user.assert_called_once_with(user_data)

    def test_get_user(self):
        user_data = User(id=1, name="John Doe", email="john@example.com")
        self.user_repository.get_user.return_value = user_data
        
        retrieved_user = self.user_service.get_user(1)
        
        self.assertEqual(retrieved_user.id, 1)
        self.user_repository.get_user.assert_called_once_with(1)

if __name__ == "__main__":
    unittest.main()
```

#### Integration Test Example

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_user():
    response = client.post("/users/", json={"id": 1, "name": "John Doe", "email": "john@example.com"})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "John Doe", "email": "john@example.com"}

def test_read_user():
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "John Doe", "email": "john@example.com"}
```

### Summary of Testing Strategy

- **MUST** implement unit, integration, and contract tests to ensure application reliability.
- **SHOULD** aim for at least 80% code coverage, focusing on critical components.
- **MUST NOT** neglect testing for edge cases and error handling scenarios.
- **MUST** utilize appropriate testing frameworks (e.g., `unittest`, `pytest`) to facilitate the testing process.

By adhering to this testing strategy, Xentic developers can maintain high-quality FastAPI applications that meet the organization's standards for reliability and performance.

## Observability and operations

To ensure that FastAPI applications at Xentic are observable and maintainable, the following observability and operations practices must be implemented:

### Metrics

- **MUST** collect application metrics to monitor performance and usage.
- **SHOULD** use a metrics collection library such as Prometheus or Grafana.
- **MUST NOT** ignore the importance of tracking key performance indicators (KPIs).

#### Example Metrics Configuration (Prometheus)

```yaml
prometheus:
  scrape_configs:
    - job_name: 'fastapi_app'
      static_configs:
        - targets: ['localhost:8000']
```

### Logs

- **MUST** implement structured logging to facilitate log analysis.
- **SHOULD** use a logging framework like `loguru` or Python's built-in `logging` module.
- **MUST NOT** log sensitive information (e.g., passwords, personal data).

#### Example Logging Configuration

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger("my_fastapi_app")

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    logger.info(f"Fetching item with ID: {item_id}")
    return {"item_id": item_id}
```

### Traces

- **MUST** implement distributed tracing to monitor requests across services.
- **SHOULD** use tools like OpenTelemetry or Jaeger for tracing.
- **MUST NOT** overlook the need for correlation IDs to track requests.

#### Example Tracing Configuration (OpenTelemetry)

```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name='localhost',
    agent_port=6831,
)

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)
```

### Dashboards

- **MUST** create dashboards to visualize metrics and logs.
- **SHOULD** use Grafana or Kibana for dashboarding.
- **MUST NOT** create dashboards that are not actionable or informative.

#### Example Dashboard Setup

| Dashboard Tool | Purpose                             | Key Metrics to Display               |
|----------------|-------------------------------------|--------------------------------------|
| Grafana        | Visualize application metrics        | Request count, error rates, latency  |
| Kibana         | Analyze logs                        | Log volume, error logs, user activity|

### Alerts

- **MUST** set up alerts for critical metrics and events.
- **SHOULD** use tools like PagerDuty or Opsgenie for alert management.
- **MUST NOT** configure alerts for non-critical events to avoid alert fatigue.

#### Example Alert Configuration (Prometheus Alertmanager)

```yaml
groups:
  - name: fastapi_alerts
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

- **MUST** define SLOs for key metrics to ensure service reliability.
- **SHOULD** review SLOs regularly and adjust based on business needs.
- **MUST NOT** set unrealistic SLOs that cannot be achieved.

| Metric                | SLO                   | Measurement Period |
|----------------------|----------------------|---------------------|
| HTTP 200 Response Rate| 99.9% of requests    | Monthly             |
| Average Latency      | < 200ms              | Monthly             |
| Error Rate           | < 1%                 | Monthly             |

### On-call Runbook Steps

- **MUST** create an on-call runbook for incident response.
- **SHOULD** include clear escalation paths and contact information.
- **MUST NOT** leave out troubleshooting steps for common issues.

#### Example On-call Runbook Steps

1. **Identify the Issue**
   - Check alerts and logs for anomalies.
   - Confirm if the issue is affecting multiple users.

2. **Assess Impact**
   - Determine the severity of the issue.
   - Notify stakeholders if necessary.

3. **Mitigate**
   - Apply quick fixes if possible (e.g., restart services).
   - Document any temporary workarounds.

4. **Resolve**
   - Investigate the root cause.
   - Implement a permanent fix.

5. **Postmortem**
   - Conduct a postmortem analysis to learn from the incident.
   - Update documentation and runbooks accordingly.

By adhering to these observability and operations practices, Xentic ensures that its FastAPI applications maintain high availability and performance while being responsive to issues as they arise.

## Migration and versioning

To manage the lifecycle of FastAPI applications at Xentic, a structured approach to migration and versioning is essential. This section outlines the policies and practices that MUST be followed to ensure smooth transitions between versions, maintain backward compatibility, and facilitate rollback when necessary.

### Upgrade Paths

- **MUST** define clear upgrade paths for each version of the application.
- **SHOULD** provide a migration guide that outlines breaking changes, new features, and deprecated functionality.
- **MUST NOT** introduce breaking changes without a corresponding major version increment.

#### Example Upgrade Path Table

| Version | Upgrade Path       | Notes                                  |
|---------|--------------------|----------------------------------------|
| 1.0    | 1.0 -> 1.1         | Minor updates, no breaking changes     |
| 1.1    | 1.1 -> 2.0         | Major updates, introduces breaking changes |
| 2.0    | 2.0 -> 2.1         | Minor updates, backward compatible     |

### Deprecation Policy

- **MUST** announce deprecated features in the release notes and provide a timeline for removal.
- **SHOULD** offer alternative solutions or replacements for deprecated features.
- **MUST NOT** remove deprecated features without a grace period of at least one major version.

#### Example Deprecation Notice

```markdown
### Deprecation Notice for `old_feature`

- **Deprecated in**: Version 1.1
- **Removal planned for**: Version 2.0
- **Recommended alternative**: Use `new_feature` instead.
```

### Backward Compatibility

- **MUST** ensure that new versions of the application are backward compatible with the previous stable version.
- **SHOULD** implement feature flags to manage the rollout of new features without affecting existing functionality.
- **MUST NOT** break existing API contracts unless a major version change is issued.

### Rollback Procedures

In the event of a failed deployment or significant issues arising from a new version, a rollback procedure MUST be in place:

1. **Identify the Issue**
   - Monitor logs and metrics to determine the impact of the new version.
   - Gather feedback from users experiencing issues.

2. **Prepare for Rollback**
   - Ensure that the previous stable version is still available in the deployment environment.
   - Backup current configurations and data if necessary.

3. **Execute Rollback**
   - Use the deployment tools to revert to the previous version.
   - Example command for rolling back using Docker:
   ```bash
   docker service update --image myapp:1.0 myapp_service
   ```

4. **Verify Rollback Success**
   - Confirm that the application is functioning as expected.
   - Monitor logs and metrics to ensure stability.

5. **Post-Rollback Review**
   - Conduct a review of the deployment process to identify what went wrong.
   - Document findings and update migration guides as necessary.

### Versioning Strategy

- **MUST** follow semantic versioning (MAJOR.MINOR.PATCH) for all releases.
- **SHOULD** include a changelog that documents all changes, enhancements, and bug fixes.
- **MUST NOT** skip version numbers to avoid confusion in the release history.

#### Example Versioning Format

```markdown
# Changelog

## [1.1.0] - 2023-10-01
### Added
- New `new_feature` for enhanced functionality.

### Changed
- Updated dependencies to latest versions.

### Deprecated
- `old_feature` will be removed in version 2.0.

## [2.0.0] - 2023-11-01
### Changed
- Breaking changes introduced, see upgrade path for details.
```

By adhering to these migration and versioning standards, Xentic ensures that its FastAPI applications remain stable, maintainable, and user-friendly throughout their lifecycle.

## FAQ, anti-patterns, and checklists

### Frequently Asked Questions (FAQ)

1. **What is Dependency Injection (DI)?**
   - Dependency Injection is a design pattern that allows a class to receive its dependencies from an external source rather than creating them internally.

2. **Why should I use Dependency Injection in FastAPI?**
   - DI promotes loose coupling, enhances testability, and simplifies the management of dependencies across your application.

3. **How do I implement DI in FastAPI?**
   - Use FastAPI's built-in dependency injection system by declaring dependencies as function parameters.

   ```python
   from fastapi import Depends, FastAPI

   app = FastAPI()

   def get_query_param(q: str = None):
       return q

   @app.get("/items/")
   async def read_items(query: str = Depends(get_query_param)):
       return {"query": query}
   ```

4. **Can I use third-party DI frameworks with FastAPI?**
   - Yes, you can integrate third-party DI frameworks like `injector` or `dependency-injector` if you prefer their features.

5. **What are the benefits of using FastAPI's DI system?**
   - FastAPI's DI system is simple, integrates seamlessly with the request lifecycle, and supports asynchronous operations.

6. **What is the difference between constructor injection and method injection?**
   - Constructor injection provides dependencies via the class constructor, while method injection provides them through method parameters.

7. **How can I test my FastAPI application with DI?**
   - You can use FastAPI's `TestClient` along with dependency overrides to test your application in isolation.

   ```python
   from fastapi.testclient import TestClient

   def fake_get_query_param():
       return "fake_query"

   app.dependency_overrides[get_query_param] = fake_get_query_param
   client = TestClient(app)
   response = client.get("/items/")
   ```

8. **What are common anti-patterns in DI?**
   - Common anti-patterns include service locator, over-injection, and circular dependencies.

9. **How do I avoid circular dependencies?**
   - Refactor your code to separate concerns and ensure that dependencies are not interdependent.

10. **When should I use DI?**
    - Use DI when you have complex dependencies, need to manage lifecycles, or want to improve testability.

### Anti-Patterns in Dependency Injection

| Anti-Pattern                | Description                                                                                              | Solution                                  |
|-----------------------------|----------------------------------------------------------------------------------------------------------|-------------------------------------------|
| Service Locator              | Using a global service locator to fetch dependencies instead of injecting them.                         | Use constructor or method injection.      |
| Over-Injection               | Injecting too many dependencies into a single class, making it hard to manage.                          | Break the class into smaller components.  |
| Circular Dependencies        | Dependencies that reference each other, causing issues in instantiation.                                | Refactor to eliminate circular references.|
| Lazy Initialization          | Deferring the creation of dependencies until they are needed, which can lead to unexpected behavior.   | Use eager initialization where possible.  |
| Singleton Misuse             | Using singletons for shared state can lead to issues in testing and concurrency.                       | Prefer dependency injection for shared state. |
| Ignoring Scope               | Not considering the lifecycle of dependencies can lead to memory leaks or stale data.                   | Define appropriate scopes for dependencies. |

### Pre-Merge Checklist

- **MUST** ensure all code follows PEP 8 style guidelines.
- **SHOULD** run unit tests and ensure they pass.
- **MUST NOT** merge code with failing tests.
- **SHOULD** review code for adherence to dependency injection patterns.
- **MUST** document any new dependencies in the README or relevant documentation.

### Production Checklist

- **MUST** ensure all environment variables are set correctly.
- **SHOULD** review logs for errors or warnings before deployment.
- **MUST NOT** deploy untested code to production.
- **MUST** run performance tests to validate application behavior under load.
- **SHOULD** back up the current production environment before deployment.
