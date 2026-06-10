# Async Database Patterns — FastAPI + SQLAlchemy

## Overview and scope

The purpose of this document is to establish a comprehensive set of standards and best practices for implementing asynchronous database patterns using FastAPI and SQLAlchemy within the Xentic platform. This document aims to guide developers in creating efficient, maintainable, and scalable applications that leverage asynchronous programming paradigms to improve performance and responsiveness.

### Audience

This document is intended for:
- Software Engineers and Developers working on backend services at Xentic.
- Technical Architects and Team Leads responsible for code reviews and architecture decisions.
- Quality Assurance Engineers involved in testing and validating backend services.

### Scope

This document covers:
- Configuration and setup of asynchronous database connections using SQLAlchemy.
- Implementation of the Repository Pattern for data access.
- Guidelines for error handling and transaction management in an asynchronous context.
- Best practices for using FastAPI in conjunction with SQLAlchemy to ensure optimal performance.

### Non-goals

This document does NOT cover:
- General FastAPI usage beyond database interactions.
- Synchronous database patterns or configurations.
- Specific use cases outside of the Xentic platform's standard practices.

### Glossary

| Term             | Definition                                                                                       |
|------------------|--------------------------------------------------------------------------------------------------|
| AsyncSession      | An asynchronous session for database operations in SQLAlchemy.                                   |
| Repository Pattern| A design pattern that encapsulates data access logic and provides a clean API for data operations.|
| FastAPI          | A modern web framework for building APIs with Python 3.6+ based on standard Python type hints.  |
| SQLAlchemy       | A SQL toolkit and Object-Relational Mapping (ORM) system for Python.                            |
| UUID             | A universally unique identifier, a 128-bit number used to uniquely identify information.         |

### How this standard fits the Xentic platform

The standards outlined in this document align with Xentic's commitment to building high-quality, scalable, and maintainable software solutions. By adopting these guidelines, teams can ensure that their implementations of asynchronous database patterns are consistent across services, facilitating easier collaboration and reducing technical debt. Furthermore, these practices support Xentic's architectural principles of modularity and reusability, allowing for the seamless integration of shared libraries and components.

### Session Setup

To establish a connection to the database, the following code snippet demonstrates how to set up an asynchronous SQLAlchemy engine and session:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost/dbname",  # Replace with actual credentials
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

### Repository Pattern

An example implementation of the Repository Pattern for user data access is shown below:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_id(self, user_id: UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def save(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
```

### Rules

To ensure adherence to best practices, the following rules MUST be followed:

- **Always use the `asyncpg` driver**: The connection string must be in the format `postgresql+asyncpg://`.
- **Never use synchronous SQLAlchemy calls** in an async context: All database interactions must be performed using asynchronous methods.
- **Set `expire_on_commit=False`**: This configuration prevents lazy-load errors when accessing related objects after a commit.
- **Use `flush()` within unit-of-work flows**: This ensures that changes are sent to the database without committing the transaction.
- **Use `commit()` at session boundaries**: Commit only when the entire transaction is complete to maintain data integrity.

By adhering to these guidelines, developers at Xentic can create robust and efficient asynchronous applications that leverage the full capabilities of FastAPI and SQLAlchemy.

## Standards and policies

1. **MUST use the `com.xentic` package structure**: All code must reside in the `com.xentic.<service>` namespace to maintain consistency across services.

2. **MUST employ the Repository Pattern**: Each database entity should have a corresponding repository class to encapsulate data access logic and promote separation of concerns.

3. **MUST NOT perform blocking I/O operations**: All database calls must be non-blocking and utilize asynchronous methods provided by SQLAlchemy.

4. **MUST define database models using SQLAlchemy's ORM**: Models should extend from `Base` and include appropriate data types and relationships.

   ```python
   from sqlalchemy import Column, String, Integer
   from sqlalchemy.ext.declarative import declarative_base

   Base = declarative_base()

   class User(Base):
       __tablename__ = 'users'
       id = Column(Integer, primary_key=True, index=True)
       username = Column(String, unique=True, index=True)
       email = Column(String, unique=True, index=True)
   ```

5. **MUST implement error handling**: Use try-except blocks around database operations to handle exceptions gracefully and log errors appropriately.

   ```python
   from sqlalchemy.exc import SQLAlchemyError

   async def save_user(user: User, db: AsyncSession):
       try:
           db.add(user)
           await db.commit()
       except SQLAlchemyError as e:
           await db.rollback()
           raise e
   ```

6. **SHOULD use type hints for all function signatures**: Type hints improve code readability and facilitate better tooling support.

7. **MUST configure connection pooling appropriately**: Ensure that the database connection pool is configured to handle the expected load.

   ```yaml
   database:
     url: postgresql+asyncpg://user:password@localhost/dbname
     pool_size: 10
     max_overflow: 20
   ```

8. **MUST NOT expose sensitive information in logs**: Ensure that database credentials and sensitive user data are not logged.

9. **SHOULD use dependency injection for database sessions**: Use FastAPI's dependency injection to manage database session lifecycles.

   ```python
   from fastapi import Depends

   @app.get("/users/{user_id}")
   async def read_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
       return await user_repository.find_by_id(user_id, db)
   ```

10. **MUST ensure all migrations are version-controlled**: Use a migration tool (e.g., Alembic) to manage database schema changes and ensure migrations are applied in a controlled manner.

11. **SHOULD document all repository methods**: Provide docstrings for all repository methods to describe their purpose, parameters, and return types.

12. **MUST NOT use global session instances**: Always create a new session for each request to avoid potential data corruption and race conditions.

13. **MUST implement transaction management**: Use context managers to handle transactions effectively, ensuring that commits and rollbacks are managed properly.

   ```python
   async def create_user(user_data: UserCreate, db: AsyncSession):
       async with db.begin():
           user = User(**user_data.dict())
           db.add(user)
           await db.flush()
           return user
   ```

14. **SHOULD use UUIDs for primary keys**: When applicable, use UUIDs instead of integers for primary keys to enhance scalability and uniqueness.

15. **MUST ensure all async functions are awaited**: Always use the `await` keyword when calling asynchronous functions to prevent unhandled exceptions and ensure proper execution flow.

By adhering to these standards and policies, Xentic developers can ensure that their implementations of asynchronous database patterns are robust, maintainable, and aligned with the company's architectural principles.

## Architecture and design

The architecture of the FastAPI application using SQLAlchemy for asynchronous database operations is designed to ensure scalability, maintainability, and resilience. Below is a detailed description of the component diagram, data flows, integration points, and failure domains.

### Component Diagram

```mermaid
graph TD;
    A[FastAPI Application] -->|HTTP Requests| B[API Endpoints]
    B -->|Dependency Injection| C[User Repository]
    C -->|Async Calls| D[AsyncSession]
    D -->|Database Operations| E[PostgreSQL Database]
    B -->|Error Handling| F[Error Logging Service]
    F -->|Alerts| G[Monitoring System]
```

### Data Flows

1. **Client Request Flow**:
   - The client sends an HTTP request to the FastAPI application.
   - FastAPI routes the request to the appropriate API endpoint.
   - The endpoint handler uses dependency injection to obtain an `AsyncSession`.

2. **Database Interaction Flow**:
   - The endpoint handler calls methods on the User Repository.
   - The repository interacts with the database using the `AsyncSession`.
   - Data is fetched or modified asynchronously, ensuring non-blocking operations.

3. **Error Handling Flow**:
   - If any error occurs during database operations, it is caught by the error handling mechanism.
   - Errors are logged and may trigger alerts to the monitoring system.

### Integration Points

- **FastAPI and SQLAlchemy**: FastAPI integrates seamlessly with SQLAlchemy through dependency injection, allowing for easy management of database sessions.
- **Monitoring System**: Integrate with external monitoring tools (e.g., Prometheus, Grafana) to track application performance and error rates.
- **Error Logging Service**: Use a centralized logging service (e.g., ELK Stack) to capture and analyze error logs for better debugging and alerting.

### Failure Domains

1. **Database Connectivity**:
   - If the PostgreSQL database is unreachable, the application should handle the connection error gracefully and return a suitable response to the client.

2. **Data Integrity**:
   - Implement transaction management to ensure that data remains consistent even in the event of failures. Use rollback mechanisms to revert changes in case of errors.

3. **Asynchronous Execution**:
   - Ensure that all asynchronous functions are awaited to prevent unhandled exceptions that could lead to application crashes.

4. **Error Handling**:
   - Centralize error handling to capture all exceptions and log them appropriately. This helps in identifying and addressing issues proactively.

### Summary

By following these architectural guidelines, the FastAPI application can achieve high performance and reliability while managing asynchronous database interactions with SQLAlchemy. The integration of various components and adherence to failure domains ensures that the application remains robust and maintainable in the face of challenges.

## Configuration reference

### Application Configuration (application.yml)

The following is a sample configuration for the FastAPI application using SQLAlchemy. This configuration should be placed in `application.yml`.

```yaml
database:
  url: postgresql+asyncpg://user:password@localhost/dbname
  pool_size: 10
  max_overflow: 20
  expire_on_commit: false

logging:
  level: INFO
  format: "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
  handlers:
    - console
    - file
  file:
    filename: app.log
    max_bytes: 10485760  # 10 MB
    backup_count: 5

app:
  host: 0.0.0.0
  port: 8000
  debug: false
```

### Terraform Configuration

The following is a sample Terraform configuration for provisioning the PostgreSQL database. This configuration should be placed in your Terraform files.

```hcl
resource "postgresql_database" "my_database" {
  name     = "dbname"
  owner    = "db_user"
  provider = postgresql
}

resource "postgresql_role" "db_user" {
  name     = "user"
  password = "password"
  login    = true
}

resource "postgresql_role" "db_admin" {
  name     = "admin"
  password = "admin_password"
  login    = true
  superuser = true
}

resource "postgresql_grant" "db_user_grant" {
  database = postgresql_database.my_database.name
  role     = postgresql_role.db_user.name
  privileges = ["CONNECT", "SELECT", "INSERT", "UPDATE", "DELETE"]
}
```

### Environment Variables

The following environment variables should be set for the application to run correctly. Default values are provided for development, while production values should be set in the production environment.

| Variable                | Default Value                       | Production Value               |
|-------------------------|------------------------------------|--------------------------------|
| `DATABASE_URL`          | `postgresql+asyncpg://user:password@localhost/dbname` | `postgresql+asyncpg://prod_user:prod_password@prod_host/prod_dbname` |
| `LOG_LEVEL`             | `INFO`                             | `ERROR`                        |
| `APP_HOST`              | `0.0.0.0`                          | `0.0.0.0`                     |
| `APP_PORT`              | `8000`                             | `80`                           |
| `DEBUG`                 | `False`                           | `False`                       |

### Summary

By following the above configuration guidelines, developers at Xentic can ensure that the FastAPI application is correctly set up for both development and production environments. Proper configuration management is essential for maintaining application performance and security.

## Implementation guide

To implement asynchronous database patterns in a FastAPI application using SQLAlchemy, follow the steps outlined below. This guide includes full code examples and best practices for structuring your application.

### Step 1: Install Required Packages

Ensure you have the necessary packages installed. You can use pip to install FastAPI, SQLAlchemy, and asyncpg:

```bash
pip install fastapi[all] sqlalchemy asyncpg
```

### Step 2: Create Database Models

Define your database models using SQLAlchemy's ORM. Below is an example of a `User` model.

```python
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String, index=True)

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"
```

### Step 3: Configure Database Connection

Create a database connection using SQLAlchemy's `create_async_engine` and `AsyncSession`.

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

### Step 4: Create Dependency for Database Session

Define a dependency to get the database session for each request. This ensures that sessions are created and closed properly.

```python
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
```

### Step 5: Implement Repository Pattern

Create a repository class to handle database operations. This encapsulates the logic for interacting with the `User` model.

```python
from sqlalchemy.future import select

class UserRepository:
    @staticmethod
    async def create_user(user_data: User, db: AsyncSession) -> User:
        db.add(user_data)
        await db.commit()
        await db.refresh(user_data)
        return user_data

    @staticmethod
    async def get_user_by_id(user_id: str, db: AsyncSession) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()
```

### Step 6: Define API Endpoints

Create API endpoints to interact with the `User` model using FastAPI.

```python
from fastapi import HTTPException
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str

@app.post("/users/", response_model=User)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = User(**user_data.dict())
    return await UserRepository.create_user(user, db)

@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await UserRepository.get_user_by_id(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### Step 7: Run the FastAPI Application

Finally, run your FastAPI application using Uvicorn.

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Summary of Implementation Steps

1. **Install Required Packages**: Use pip to install FastAPI, SQLAlchemy, and asyncpg.
2. **Create Database Models**: Define your models using SQLAlchemy's ORM.
3. **Configure Database Connection**: Set up the async engine and session.
4. **Create Dependency for Database Session**: Implement a dependency for managing session lifecycles.
5. **Implement Repository Pattern**: Encapsulate database logic in repository classes.
6. **Define API Endpoints**: Create endpoints for user creation and retrieval.
7. **Run the FastAPI Application**: Use Uvicorn to serve your application.

By following this implementation guide, Xentic developers can effectively utilize asynchronous database patterns in their FastAPI applications, ensuring scalability and maintainability.

## Security requirements

### Threat Model Summary

The following threat model outlines potential security risks associated with the FastAPI application using SQLAlchemy. Each identified threat should be addressed through appropriate security measures.

| Threat                     | Description                                                                 | Mitigation Strategy                                |
|---------------------------|-----------------------------------------------------------------------------|---------------------------------------------------|
| Unauthorized Access       | Attackers may attempt to access restricted resources without proper credentials. | Implement strong authentication and authorization mechanisms. |
| Data Breach               | Sensitive user data may be exposed due to vulnerabilities in the application.  | Use encryption for data at rest and in transit.   |
| SQL Injection             | Malicious users may attempt to manipulate SQL queries to gain unauthorized access or alter data. | Use parameterized queries and ORM to prevent injection attacks. |
| Denial of Service (DoS)   | Attackers may overload the application with excessive requests, causing service disruption. | Implement rate limiting and monitoring to detect and block abusive behavior. |
| Insecure Dependencies     | Vulnerabilities in third-party libraries may compromise application security. | Regularly update dependencies and use tools to scan for vulnerabilities. |

### Authentication and Authorization

The application MUST implement authentication and authorization using OAuth2 with JWT tokens. The following steps outline the necessary implementation:

1. **User Registration**: Users MUST register with a unique username and password.
2. **Token Generation**: Upon successful login, the application MUST generate a JWT token that includes user roles and permissions.
3. **Protected Routes**: All API endpoints that require authentication MUST be protected by a dependency that checks for a valid JWT token.

Example of token generation:

```python
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### Secrets Management

Secrets such as database credentials and API keys MUST NOT be hardcoded in the application code. Instead, they MUST be stored in environment variables or a secure secrets management tool.

Example of using environment variables in `application.yml`:

```yaml
database:
  url: ${DATABASE_URL}
```

### Input Validation

All user inputs MUST be validated to prevent injection attacks and ensure data integrity. FastAPI provides built-in data validation using Pydantic models.

Example of input validation using Pydantic:

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str

    @validator('username')
    def username_must_not_contain_special_chars(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v
```

### Audit Logging

The application MUST implement audit logging to track user actions and system events. This helps in monitoring for suspicious activities and compliance with regulatory requirements.

Example of logging configuration in `application.yml`:

```yaml
logging:
  level: INFO
  format: "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
  handlers:
    - console
    - file
  file:
    filename: audit.log
    max_bytes: 10485760  # 10 MB
    backup_count: 5
```

To log user actions, use the logging module in your application:

```python
import logging

logger = logging.getLogger(__name__)

@app.post("/users/")
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Creating user: {user_data.username}")
    # User creation logic here
```

### Summary

By adhering to the outlined security requirements, the FastAPI application can significantly reduce the risk of security breaches and ensure the confidentiality, integrity, and availability of user data. Implementing robust authentication, input validation, secrets management, and audit logging are essential practices for maintaining a secure application environment.

## Testing strategy

A comprehensive testing strategy is essential for ensuring the reliability and maintainability of the FastAPI application. This strategy includes unit tests, integration tests, and contract tests, each serving a distinct purpose. The following outlines the testing strategy, coverage targets, and example test classes.

### Types of Tests

1. **Unit Tests**
   - Focus on individual components (e.g., functions, classes).
   - Must isolate dependencies using mocking.
   - Coverage target: 80% or higher.

2. **Integration Tests**
   - Validate the interaction between components and external systems (e.g., database).
   - Must use a test database to avoid affecting production data.
   - Coverage target: 70% or higher.

3. **Contract Tests**
   - Ensure that the API adheres to the defined contracts (e.g., request/response formats).
   - Must verify that changes in the API do not break existing clients.
   - Coverage target: 100% for critical endpoints.

### Example Test Frameworks

- **Unit Testing**: `pytest`
- **Mocking**: `unittest.mock`
- **Integration Testing**: `httpx` for making requests to the FastAPI app
- **Contract Testing**: `pact-python` for consumer-driven contracts

### Example Test Classes

#### Unit Tests

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.repositories import UserRepository
from app.models import User

@pytest.mark.asyncio
async def test_create_user():
    user_data = User(username="testuser", email="test@example.com", full_name="Test User")
    mock_session = AsyncMock()
    
    with patch('app.repositories.AsyncSession', return_value=mock_session):
        result = await UserRepository.create_user(user_data, mock_session)
        
    assert result.username == "testuser"
    mock_session.add.assert_called_once_with(user_data)
    mock_session.commit.assert_awaited_once()
```

#### Integration Tests

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_user_integration():
    response = client.post("/users/", json={"username": "testuser", "email": "test@example.com", "full_name": "Test User"})
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"

def test_read_user_integration():
    response = client.get("/users/testuser")
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
```

#### Contract Tests

```python
from pact import Consumer, Provider

pact = Consumer('UserService').has_pact_with(Provider('UserAPI'))

@pact.given('a user exists')
def given_user_exists():
    # Setup code to create a user in the test database

@pact.when('a request is made to create a user')
def when_request_is_made():
    # Code to make a request to the FastAPI application

@pact.then('the response should match the contract')
def then_response_should_match():
    # Validate the response against the expected contract
    pact.verify()
```

### Coverage Targets

| Test Type         | Coverage Target |
|-------------------|-----------------|
| Unit Tests        | 80% or higher    |
| Integration Tests | 70% or higher    |
| Contract Tests    | 100% for critical endpoints |

### Running Tests

To run the tests, use the following command:

```bash
pytest --cov=app tests/
```

### Conclusion

By implementing a robust testing strategy that includes unit, integration, and contract tests, Xentic developers can ensure the quality and reliability of the FastAPI application. Adhering to the specified coverage targets will help maintain high standards and facilitate continuous improvement in the codebase.

## Observability and operations

To ensure the reliability and performance of the FastAPI application, observability practices MUST be implemented. This includes metrics, logs, traces, dashboards, alerts, and service-level objectives (SLOs). The following sections outline the necessary components for effective observability.

### Metrics

Metrics MUST be collected to monitor the application's performance and health. Key metrics to track include:

- **Request Latency**: Measure the time taken to process requests.
- **Error Rates**: Track the number of failed requests.
- **Throughput**: Monitor the number of requests processed per second.
- **Database Query Performance**: Measure the time taken for database operations.

Example of Prometheus metrics configuration in `application.yml`:

```yaml
prometheus:
  enabled: true
  port: 8000
  path: /metrics
```

### Logs

Logging MUST be comprehensive and structured to facilitate easy searching and analysis. Logs should include:

- Timestamp
- Log level (INFO, DEBUG, ERROR)
- Service name
- Request ID
- User ID (if applicable)
- Error messages and stack traces

Example logging configuration in `application.yml`:

```yaml
logging:
  level: DEBUG
  format: "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
  handlers:
    - console
    - file
  file:
    filename: app.log
    max_bytes: 10485760  # 10 MB
    backup_count: 5
```

### Traces

Distributed tracing MUST be implemented to track requests across microservices. This helps in identifying bottlenecks and understanding the flow of requests. Use tools like OpenTelemetry or Jaeger for tracing.

Example of initializing tracing in your FastAPI application:

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI()

FastAPIInstrumentor.instrument_app(app)
```

### Dashboards

Dashboards MUST be created to visualize metrics and logs. Use tools like Grafana to create dashboards that include:

- Request latency over time
- Error rates by endpoint
- Database query performance
- System resource utilization (CPU, memory)

### Alerts

Alerts MUST be configured to notify the team of critical issues. Set up alerts for:

- High error rates (e.g., > 5% of requests failing)
- Increased latency (e.g., > 500ms for 95th percentile)
- Resource exhaustion (e.g., CPU or memory usage > 80%)

Example alert configuration in Prometheus:

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

SLOs MUST be defined to establish performance targets for the application. Common SLOs include:

- **Availability**: 99.9% uptime
- **Latency**: 95th percentile response time < 200ms
- **Error Rate**: < 1% of requests result in an error

### On-Call Runbook Steps

In the event of an incident, the following on-call runbook steps MUST be followed:

1. **Acknowledge the Alert**: Confirm receipt of the alert and begin investigation.
2. **Check Metrics**: Review relevant metrics on the dashboard to identify anomalies.
3. **Inspect Logs**: Look for error messages and stack traces in the logs.
4. **Trace Requests**: Use distributed tracing to identify bottlenecks or failures in the request flow.
5. **Communicate**: Update stakeholders on the status of the incident and any findings.
6. **Mitigate**: Implement a temporary fix if possible (e.g., scaling the service, rolling back a deployment).
7. **Document**: Record the incident details, actions taken, and resolution steps in the incident management system.
8. **Post-Mortem**: Conduct a post-mortem analysis to identify root causes and prevent recurrence.

By adhering to these observability practices, the FastAPI application at Xentic will be better equipped to handle incidents, maintain performance, and ensure a high-quality user experience.

## Migration and versioning

Effective migration and versioning strategies are essential for maintaining the integrity and performance of the FastAPI application as it evolves. This section outlines the upgrade paths, deprecation policies, backward compatibility requirements, and rollback procedures that MUST be followed.

### Upgrade Paths

When upgrading the application or its dependencies, the following paths MUST be adhered to:

- **Semantic Versioning**: All versions MUST follow [Semantic Versioning](https://semver.org/) principles (MAJOR.MINOR.PATCH).
- **Incremental Upgrades**: Upgrades MUST be performed incrementally. For example, do not skip from version 1.0.0 to 2.0.0 directly; instead, upgrade to 1.1.0, then to 1.2.0, and finally to 2.0.0.
- **Changelog**: A changelog MUST be maintained and updated with each release, detailing changes, new features, and bug fixes.

### Deprecation Policy

To ensure smooth transitions, the following deprecation policy MUST be implemented:

- **Deprecation Notices**: Features that are deprecated MUST be marked with clear notices in the documentation and code comments.
- **Grace Period**: A grace period of at least one major version MUST be provided before deprecated features are removed. During this time, users MUST be encouraged to migrate to the new alternatives.
- **Documentation**: Deprecated features MUST have corresponding migration guides in the documentation, detailing how to transition to newer implementations.

### Backward Compatibility

Backward compatibility MUST be a priority during development:

- **API Changes**: Changes to API endpoints MUST maintain backward compatibility whenever possible. If breaking changes are necessary, they MUST be introduced in a new major version.
- **Database Migrations**: Database schema changes MUST be designed to be backward compatible. Use techniques such as adding new columns instead of dropping existing ones.

### Rollback Procedures

In the event of a failed deployment or migration, rollback procedures MUST be in place:

1. **Backup**: Always create a backup of the database and application state before performing migrations. Use tools like `pg_dump` for PostgreSQL.
   
   Example command:
   ```bash
   pg_dump -U username -h localhost dbname > backup.sql
   ```

2. **Rollback Script**: Maintain rollback scripts for database migrations. Each migration MUST have a corresponding rollback script to revert the changes.

   Example SQL rollback script:
   ```sql
   -- Rollback script for adding a new column
   ALTER TABLE users DROP COLUMN new_column;
   ```

3. **Version Control**: Use version control (e.g., Git) for application code and database migration scripts. This allows for easy reversion to a previous stable state.

4. **Monitoring Post-Rollback**: After rolling back, monitor the application closely for any issues. Ensure that logging and monitoring tools are configured to detect anomalies.

### Migration Example

Here is an example of a database migration using Alembic, a lightweight database migration tool for SQLAlchemy:

```python
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1234567890ab'
down_revision = '0987654321ba'
branch_labels = None
depends_on = None

def upgrade():
    # Add new column
    op.add_column('users', sa.Column('new_column', sa.String(length=50), nullable=True))

def downgrade():
    # Remove new column
    op.drop_column('users', 'new_column')
```

### Conclusion

By adhering to these migration and versioning practices, Xentic ensures that the FastAPI application remains robust, maintainable, and user-friendly. The focus on backward compatibility, clear deprecation policies, and well-defined rollback procedures will facilitate a smoother development lifecycle and enhance overall application stability.

## FAQ, anti-patterns, and checklists

### FAQ

1. **What is FastAPI?**
   FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints.

2. **Why use SQLAlchemy with FastAPI?**
   SQLAlchemy is a powerful ORM that allows for easy database interactions and management, making it a suitable choice for FastAPI applications that require database access.

3. **How do I handle asynchronous database calls in FastAPI?**
   Use `async` and `await` keywords with SQLAlchemy's asynchronous features, such as `AsyncSession`, to handle database operations without blocking the event loop.

4. **What is the recommended way to manage database sessions?**
   Use dependency injection to manage database sessions in FastAPI. This allows for clean session management and ensures that sessions are properly closed after use.

5. **Can I use synchronous SQLAlchemy with FastAPI?**
   Yes, but it is recommended to use the asynchronous version of SQLAlchemy (`asyncpg` for PostgreSQL) to take full advantage of FastAPI's asynchronous capabilities.

6. **What are the best practices for error handling in FastAPI?**
   Implement global exception handlers and use HTTPException to return meaningful error responses. Ensure to log errors for further analysis.

7. **How should I structure my FastAPI application?**
   Organize your application into modules based on functionality, such as routes, models, and services. This promotes maintainability and scalability.

8. **Is it necessary to validate request data?**
   Yes, data validation is crucial. Use Pydantic models to validate incoming request data and ensure it meets the expected structure.

9. **What should I do if I encounter a performance issue?**
   Profile your application using tools like `cProfile` or `py-spy` to identify bottlenecks. Optimize database queries and consider caching strategies.

10. **How do I deploy a FastAPI application?**
    Deploy using a WSGI server like Uvicorn or Gunicorn, and consider using Docker for containerization. Ensure to configure environment variables and secrets properly.

### Anti-Patterns

| Anti-Pattern                      | Description                                                                                   | Recommendation                                       |
|-----------------------------------|-----------------------------------------------------------------------------------------------|-----------------------------------------------------|
| Blocking Database Calls           | Using synchronous database calls in an async context.                                        | Always use async database calls with FastAPI.       |
| Global State Management           | Using global variables to manage application state.                                          | Use dependency injection for state management.      |
| Hardcoding Configuration          | Hardcoding database URLs or API keys in the codebase.                                       | Use environment variables or configuration files.    |
| Lack of Input Validation          | Not validating user input leading to potential security vulnerabilities.                     | Always validate input using Pydantic models.        |
| Ignoring Error Handling           | Failing to handle exceptions properly, leading to unhandled errors.                          | Implement global exception handlers.                 |
| Overcomplicating Routes           | Creating overly complex route structures that are hard to maintain.                         | Keep routes simple and modular.                      |
| Not Using Dependency Injection    | Relying on manual instantiation of services and database connections.                        | Utilize FastAPI's dependency injection system.      |

### Pre-Merge Checklist

- [ ] Code adheres to PEP 8 style guidelines.
- [ ] All tests are passing, including unit and integration tests.
- [ ] Code is reviewed by at least one other developer.
- [ ] Documentation is updated to reflect any changes.
- [ ] Configuration files are validated and follow the prescribed structure.
- [ ] No hardcoded values are present in the codebase.

### Production Checklist

- [ ] Application is containerized using Docker.
- [ ] Environment variables are configured for production.
- [ ] Database migrations are applied and verified.
- [ ] Monitoring and alerting are set up and tested.
- [ ] Load testing has been performed to ensure performance.
- [ ] Backup procedures are in place for data recovery.
- [ ] Security measures (e.g., HTTPS, CORS) are implemented.
