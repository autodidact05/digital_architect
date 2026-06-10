# MongoDB Indexing Strategy

## Overview and scope

The purpose of this document is to establish a comprehensive MongoDB Indexing Strategy for Xentic's engineering teams. This strategy aims to optimize query performance and ensure efficient data retrieval across various services that utilize MongoDB as their database solution. 

### Audience
This document is intended for:
- Software Engineers
- Database Administrators
- Technical Leads
- Architects

### Scope
This standard covers:
- Guidelines for creating and managing indexes in MongoDB.
- Best practices for compound indexes, standard indexes, and Mongoose schema indexes.
- Performance evaluation techniques for queries and indexes.
- Recommendations for index management in production environments.

### Non-goals
This document does NOT cover:
- Detailed MongoDB installation and configuration.
- General database design principles outside of indexing strategies.
- Specific use cases for every service within Xentic.

### Glossary
| Term               | Definition                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| Index              | A data structure that improves the speed of data retrieval operations on a database. |
| Compound Index     | An index that consists of multiple fields from a document.                 |
| Partial Index      | An index that only includes documents that meet a specified filter condition. |
| Mongoose           | An ODM (Object Data Modeling) library for MongoDB and Node.js.            |
| Execution Stats    | Metrics that provide insight into the performance of a query execution plan. |

### Relationship to Xentic Platform
The MongoDB Indexing Strategy is a critical component of Xentic's overall data management framework. By adhering to these standards, teams will ensure that data retrieval is optimized, leading to improved application performance and user experience. This strategy aligns with Xentic's commitment to operational excellence and scalability, ensuring that our services can handle increasing data loads efficiently.

### Key Indexing Principles
- **Compound Indexing**: Order compound index fields as follows: 
  - **Equality** → **Sort** → **Range**.
  
  Example:
  ```javascript
  // Query: active users for tenant, sorted by createdAt in a date range
  db.users.find({
      tenantId: ObjectId("..."),    // E - equality
      isActive: true,               // E - equality
      createdAt: { $gte: startDate} // R - range
  }).sort({ createdAt: -1 });       // S - sort

  // CORRECT index
  db.users.createIndex({ tenantId: 1, isActive: 1, createdAt: -1 });
  ```

- **Standard Indexes**: Create necessary indexes to support application queries.
  ```javascript
  db.users.createIndex({ tenantId: 1, email: 1 }, { unique: true });
  db.sessions.createIndex({ createdAt: 1 }, { expireAfterSeconds: 86400 });

  // Partial index
  db.orders.createIndex(
    { userId: 1, createdAt: -1 },
    { partialFilterExpression: { status: "ACTIVE" } }
  );

  // Text search index
  db.products.createIndex({ name: "text", description: "text" });
  ```

- **Mongoose Schema Indexes**: Define indexes directly in Mongoose schemas.
  ```typescript
  userSchema.index({ tenantId: 1, email: 1 }, { unique: true });
  userSchema.index({ tenantId: 1, isActive: 1, createdAt: -1 });
  ```

### Index Management Rules
- Run `explain("executionStats")` on any new query before deploying to ensure optimal performance.
- Limit the number of indexes to a maximum of **8 indexes per collection** to avoid performance degradation.
- Use rolling index builds in MongoDB Atlas for production to minimize downtime during index creation.

## Standards and policies

1. **MUST** create indexes for all fields that are frequently queried or used in sorting. This includes fields that are used in `WHERE`, `ORDER BY`, and `JOIN` operations.

2. **MUST NOT** create unnecessary indexes. Each index consumes additional disk space and can slow down write operations. Evaluate the necessity of each index based on query patterns.

3. **SHOULD** use compound indexes when queries involve multiple fields. Ensure the order of fields in the index aligns with the query's filter and sort order.

4. **MUST** define unique indexes for fields that require uniqueness, such as email addresses or user IDs, to maintain data integrity.

5. **MUST NOT** use wildcard indexes unless absolutely necessary. These can lead to performance issues and should be avoided unless the use case justifies their inclusion.

6. **SHOULD** utilize partial indexes when applicable. This can significantly reduce index size and improve performance for queries that only need to access a subset of documents.

   Example:
   ```javascript
   db.orders.createIndex(
     { userId: 1, createdAt: -1 },
     { partialFilterExpression: { status: "ACTIVE" } }
   );
   ```

7. **MUST** regularly monitor index performance using the `db.collection.getIndexes()` and `db.collection.stats()` commands to ensure that indexes are being utilized effectively.

8. **SHOULD** remove unused indexes periodically. Use the `explain()` method to identify indexes that are not being used by queries, and drop them to improve performance.

9. **MUST** document all indexes created in the project repository. This documentation should include the purpose of the index, the fields included, and the expected query patterns.

10. **SHOULD** use Mongoose schema definitions to manage indexes for Node.js applications. This ensures that indexes are consistently applied across different environments.

    Example:
    ```typescript
    const userSchema = new mongoose.Schema({
      email: { type: String, required: true, unique: true },
      tenantId: { type: mongoose.Schema.Types.ObjectId, required: true },
      isActive: { type: Boolean, default: true },
    });
    
    userSchema.index({ tenantId: 1, email: 1 }, { unique: true });
    ```

11. **MUST** run `db.collection.reIndex()` during maintenance windows if there are significant changes to the data or if index fragmentation is suspected.

12. **SHOULD** utilize the `explain("executionStats")` command on queries before deploying them to production to ensure that the indexes are being used optimally.

13. **MUST NOT** exceed **8 indexes per collection**. Having too many indexes can lead to increased overhead during write operations and can degrade performance.

14. **SHOULD** utilize the MongoDB Atlas rolling index builds for production environments to minimize downtime and maintain service availability during index creation.

15. **MUST** ensure that any changes to indexes are tested in a staging environment that mirrors production before being applied to live systems.

16. **SHOULD** prioritize the creation of indexes based on the most common and performance-critical queries identified through application profiling and analytics.

17. **MUST** keep the index definitions in sync with the application codebase. Any changes to the schema should be reflected in the index definitions to avoid discrepancies.

18. **SHOULD** consider using TTL (Time-To-Live) indexes for collections that store temporary data, such as session information, to automatically remove outdated documents.

    Example:
    ```javascript
    db.sessions.createIndex({ createdAt: 1 }, { expireAfterSeconds: 86400 });
    ```

By adhering to these standards and policies, Xentic's engineering teams will ensure efficient data retrieval and optimal performance of MongoDB databases across all services.

## Architecture and design

The architecture for MongoDB indexing at Xentic is designed to ensure efficient data retrieval and optimal query performance across various services. Below is a component diagram that illustrates the key components involved in the MongoDB indexing strategy.

```mermaid
graph TD;
    A[Client Application] -->|Query| B[API Gateway]
    B -->|Request| C[Service Layer]
    C -->|Database Operation| D[MongoDB Database]
    D -->|Index Usage| E[Indexes]
    E -->|Performance Metrics| F[Monitoring Tools]
    F -->|Feedback| C
```

### Data Flows
1. **Client Application to API Gateway**: The client application sends a query request to the API Gateway.
2. **API Gateway to Service Layer**: The API Gateway forwards the request to the appropriate service layer for processing.
3. **Service Layer to MongoDB Database**: The service layer interacts with the MongoDB database to perform CRUD operations.
4. **Index Usage**: The database utilizes indexes to optimize query execution and improve performance.
5. **Monitoring Tools**: Performance metrics are collected by monitoring tools to provide feedback to the service layer for optimization.

### Integration Points
- **API Gateway**: Acts as the entry point for all client requests and routes them to the appropriate services.
- **Service Layer**: Contains business logic and interacts with the MongoDB database for data operations.
- **Monitoring Tools**: Integrates with MongoDB to collect execution statistics and performance metrics, which are essential for evaluating index effectiveness.

### Failure Domains
- **Client Application**: If the client application fails, users cannot send requests, impacting the overall user experience.
- **API Gateway**: A failure here can prevent any requests from reaching the service layer, resulting in downtime for all services.
- **Service Layer**: If the service layer encounters issues, it may lead to incorrect data retrieval or application errors.
- **MongoDB Database**: Any failure in the database will directly affect data availability and integrity.
- **Indexes**: If indexes become corrupted or are not used correctly, it can lead to degraded query performance and increased latency.

### Indexing Strategy Summary Table

| Index Type       | Description                                              | Use Case Example                                      |
|------------------|----------------------------------------------------------|------------------------------------------------------|
| Standard Index   | Basic index for single fields.                           | `db.users.createIndex({ email: 1 })`                |
| Compound Index   | Index on multiple fields for complex queries.           | `db.orders.createIndex({ userId: 1, createdAt: -1 })` |
| Partial Index    | Index that includes only a subset of documents.         | `db.products.createIndex({ price: 1 }, { partialFilterExpression: { inStock: true } })` |
| TTL Index        | Automatically removes documents after a specified time. | `db.sessions.createIndex({ createdAt: 1 }, { expireAfterSeconds: 3600 })` |
| Text Index       | Supports text search capabilities.                       | `db.articles.createIndex({ content: "text" })`      |

### Best Practices for Indexing
- **Analyze Query Patterns**: Regularly review the most frequent queries to determine which fields require indexing.
- **Use Explain Plans**: Always utilize the `explain()` method to analyze how queries are executed and ensure indexes are being utilized effectively.
- **Monitor Index Performance**: Use MongoDB's built-in tools to monitor index performance and adjust as necessary.
- **Limit Index Count**: Adhere to the maximum of **8 indexes per collection** to avoid performance degradation during write operations.

By following this architecture and design strategy, Xentic's engineering teams will be able to implement a robust and efficient MongoDB indexing strategy that enhances data retrieval and application performance.

## Configuration reference

### application.yml

The following configuration settings should be included in your `application.yml` file to define MongoDB connection parameters and indexing strategies.

```yaml
spring:
  data:
    mongodb:
      uri: mongodb://<username>:<password>@mongo.internal.xentic.io:27017/<database>
      database: <database>
      authentication-database: admin
      connection-timeout: 3000
      socket-timeout: 5000
      indexes:
        - name: email_index
          fields:
            email: 1
          unique: true
        - name: userId_createdAt_index
          fields:
            userId: 1
            createdAt: -1
        - name: ttl_session_index
          fields:
            createdAt: 1
          expireAfterSeconds: 86400
```

### Terraform Configuration

The following Terraform configuration can be used to provision MongoDB resources, including the necessary indexes.

```hcl
resource "mongodbatlas_cluster" "example" {
  project_id   = "<project_id>"
  name         = "example-cluster"
  provider_name = "AWS"
  region       = "US_EAST_1"
  // Other cluster settings...

  backup_enabled = true
}

resource "mongodbatlas_index" "email_index" {
  project_id   = "<project_id>"
  cluster_name = mongodbatlas_cluster.example.name
  database     = "<database>"
  collection   = "users"

  keys {
    email = 1
  }

  options {
    unique = true
  }
}

resource "mongodbatlas_index" "userId_createdAt_index" {
  project_id   = "<project_id>"
  cluster_name = mongodbatlas_cluster.example.name
  database     = "<database>"
  collection   = "orders"

  keys {
    userId    = 1
    createdAt = -1
  }
}

resource "mongodbatlas_index" "ttl_session_index" {
  project_id   = "<project_id>"
  cluster_name = mongodbatlas_cluster.example.name
  database     = "<database>"
  collection   = "sessions"

  keys {
    createdAt = 1
  }

  options {
    expire_after_seconds = 86400
  }
}
```

### Environment Variables

The following environment variables should be set for MongoDB configuration:

| Variable Name                      | Default Value                     | Production Value                   |
|------------------------------------|-----------------------------------|------------------------------------|
| `MONGODB_URI`                      | `mongodb://localhost:27017`      | `mongodb://<username>:<password>@mongo.internal.xentic.io:27017/<database>` |
| `MONGODB_DATABASE`                 | `test`                            | `<database>`                       |
| `MONGODB_AUTH_DATABASE`            | `admin`                           | `admin`                            |
| `MONGODB_CONNECTION_TIMEOUT`       | `3000`                            | `3000`                            |
| `MONGODB_SOCKET_TIMEOUT`           | `5000`                            | `5000`                            |

### Index Configuration Table

| Index Name              | Collection  | Fields                               | Unique | Expiration (seconds) |
|------------------------|-------------|--------------------------------------|--------|-----------------------|
| email_index            | users       | email                                | Yes    | N/A                   |
| userId_createdAt_index | orders      | userId, createdAt                    | No     | N/A                   |
| ttl_session_index      | sessions    | createdAt                            | No     | 86400                 |

By following this configuration reference, Xentic's engineering teams will ensure that the MongoDB setup is consistent and adheres to the defined indexing strategies across all environments.

## Implementation guide

To effectively implement MongoDB indexing strategies at Xentic, follow the steps outlined below. This guide includes code examples for creating indexes in both Java and MongoDB shell commands, ensuring a comprehensive understanding of the process.

### Step 1: Define Indexes in MongoDB

Begin by defining the necessary indexes directly in MongoDB. Use the MongoDB shell or a database management tool to create the indexes as specified in the configuration reference.

#### Example MongoDB Shell Commands

```javascript
// Create a unique index on the email field in the users collection
db.users.createIndex({ email: 1 }, { unique: true });

// Create a compound index on userId and createdAt fields in the orders collection
db.orders.createIndex({ userId: 1, createdAt: -1 });

// Create a TTL index on createdAt field in the sessions collection
db.sessions.createIndex({ createdAt: 1 }, { expireAfterSeconds: 86400 });
```

### Step 2: Configure Spring Data MongoDB

In your Spring Boot application, configure the `application.yml` file to include the MongoDB connection settings and the indexing strategies you defined.

#### Example application.yml Configuration

```yaml
spring:
  data:
    mongodb:
      uri: mongodb://<username>:<password>@mongo.internal.xentic.io:27017/<database>
      database: <database>
      authentication-database: admin
      connection-timeout: 3000
      socket-timeout: 5000
      indexes:
        - name: email_index
          fields:
            email: 1
          unique: true
        - name: userId_createdAt_index
          fields:
            userId: 1
            createdAt: -1
        - name: ttl_session_index
          fields:
            createdAt: 1
          expireAfterSeconds: 86400
```

### Step 3: Implement Repository Interfaces

Create repository interfaces for your collections using Spring Data MongoDB. This will allow you to interact with your collections and utilize the indexes effectively.

#### Example User Repository

```java
package com.xentic.user;

import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface UserRepository extends MongoRepository<User, String> {
    User findByEmail(String email);
}
```

#### Example Order Repository

```java
package com.xentic.order;

import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface OrderRepository extends MongoRepository<Order, String> {
    List<Order> findByUserId(String userId);
}
```

### Step 4: Test Indexes with Query Performance

To ensure that your indexes are being utilized correctly, use the `explain()` method in MongoDB to analyze query performance.

#### Example Query with Explain

```javascript
db.orders.find({ userId: "12345" }).explain("executionStats");
```

This command will provide detailed statistics about the query execution, showing whether the index was used and how it affected performance.

### Step 5: Monitor Index Performance

Utilize MongoDB monitoring tools to keep track of index performance. This includes reviewing slow queries and adjusting indexes as necessary.

#### Example Monitoring Command

```javascript
db.currentOp({ "active": true, "secs_running": { "$gt": 5 } });
```

This command will display currently running operations that have been active for more than 5 seconds, helping you identify potential performance issues.

### Step 6: Regularly Review and Optimize Indexes

Establish a routine to review your indexes based on query patterns and performance metrics. Adjust or remove indexes that are not being utilized effectively.

#### Index Review Checklist

- [ ] Analyze query patterns monthly.
- [ ] Use `db.collection.getIndexes()` to list current indexes.
- [ ] Remove unused indexes to optimize write performance.

By following these implementation steps, Xentic's engineering teams will create a robust MongoDB indexing strategy that enhances data retrieval and application performance across all services.

## Security requirements

To ensure the security of MongoDB deployments at Xentic, the following security requirements must be adhered to:

### Threat Model Summary

The primary threats to MongoDB databases include:

- **Unauthorized Access**: Attackers may attempt to gain access to the database without proper credentials.
- **Data Breaches**: Sensitive data could be exposed due to misconfigurations or vulnerabilities.
- **Data Manipulation**: Malicious actors may attempt to alter or delete data.
- **Denial of Service**: Attackers may try to overwhelm the database with excessive requests.

### Authentication and Authorization

- **Authentication**: MongoDB MUST be configured to use SCRAM-SHA-256 for user authentication. Ensure that all database users have strong, unique passwords.
  
  Example user creation command:
  ```javascript
  db.createUser({
    user: "appUser",
    pwd: "StrongPassword123!",
    roles: [{ role: "readWrite", db: "<database>" }]
  });
  ```

- **Authorization**: Role-Based Access Control (RBAC) MUST be implemented. Users should only have the permissions necessary for their roles. Avoid using the `root` role for application users.

| Role              | Permissions                       |
|-------------------|-----------------------------------|
| read              | Read access to the database       |
| readWrite         | Read and write access             |
| dbAdmin           | Database management                |
| userAdmin         | User management                    |

### Secrets Management

- **Environment Variables**: Sensitive information such as database credentials MUST NOT be hard-coded in application code. Instead, use environment variables or a secrets management tool (e.g., HashiCorp Vault, AWS Secrets Manager).

Example environment variable configuration:
```bash
export MONGODB_URI="mongodb://appUser:StrongPassword123!@mongo.internal.xentic.io:27017/<database>"
```

- **Configuration Files**: Ensure that configuration files containing sensitive information are secured and not included in version control systems.

### Input Validation

- **Sanitize Inputs**: All user inputs MUST be validated and sanitized to prevent injection attacks. Use libraries such as `mongo-java-driver` that automatically handle input sanitization.

Example validation in Java:
```java
public User findUserByEmail(String email) {
    if (!isValidEmail(email)) {
        throw new IllegalArgumentException("Invalid email format");
    }
    return userRepository.findByEmail(email);
}

private boolean isValidEmail(String email) {
    return email != null && email.matches("^[A-Za-z0-9+_.-]+@(.+)$");
}
```

### Audit Logging

- **Enable Audit Logging**: MongoDB audit logging MUST be enabled to track access and changes to the database. This helps in identifying unauthorized access and understanding data manipulation.

Example configuration in `mongod.conf`:
```yaml
auditLog:
  destination: file
  format: JSON
  path: /var/log/mongodb/audit.log
  filter: '{ atype: { $in: ["create", "update", "remove"] } }'
```

- **Log Review**: Logs MUST be reviewed regularly to identify suspicious activities. Automate log analysis where possible.

### Summary

By implementing these security requirements, Xentic will ensure that its MongoDB deployments are secure against potential threats. All teams MUST adhere to these guidelines to maintain the integrity and confidentiality of sensitive data.

## Testing strategy

To ensure the quality and reliability of MongoDB implementations at Xentic, a comprehensive testing strategy must be employed. This strategy includes unit tests, integration tests, and contract tests, each serving a specific purpose in the development lifecycle.

### Unit Tests

Unit tests are essential for verifying the correctness of individual components in isolation. For MongoDB-related functionalities, unit tests should focus on repository methods and any custom queries.

- **Coverage Target**: Aim for at least 80% code coverage for all repository methods.
- **Testing Framework**: Use JUnit and Mockito for writing unit tests.

#### Example Unit Test Class

```java
package com.xentic.user;

import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

public class UserRepositoryTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @BeforeEach
    public void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    public void testFindByEmail() {
        User user = new User("test@example.com");
        when(userRepository.findByEmail("test@example.com")).thenReturn(user);

        User foundUser = userService.findUserByEmail("test@example.com");
        assertEquals("test@example.com", foundUser.getEmail());
        verify(userRepository).findByEmail("test@example.com");
    }
}
```

### Integration Tests

Integration tests validate the interaction between different components, such as the application and the MongoDB database. These tests should ensure that the application can correctly perform CRUD operations on the database.

- **Coverage Target**: Aim for at least 70% coverage for integration tests.
- **Testing Framework**: Use Spring Boot Test with embedded MongoDB for integration tests.

#### Example Integration Test Class

```java
package com.xentic.order;

import static org.assertj.core.api.Assertions.*;

import com.xentic.Application;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.mongodb.core.MongoTemplate;

@SpringBootTest(classes = Application.class)
public class OrderIntegrationTest {

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private MongoTemplate mongoTemplate;

    @Test
    public void testCreateAndFindOrder() {
        Order order = new Order("userId123", "item123");
        orderRepository.save(order);

        Order foundOrder = orderRepository.findById(order.getId()).orElse(null);
        assertThat(foundOrder).isNotNull();
        assertThat(foundOrder.getUserId()).isEqualTo("userId123");
    }
}
```

### Contract Tests

Contract tests ensure that the interactions between services adhere to predefined contracts. This is particularly important in microservices architectures where different services may depend on each other.

- **Coverage Target**: Ensure all service interactions are covered by contract tests.
- **Testing Framework**: Use Pact for contract testing.

#### Example Contract Test Class

```java
package com.xentic.contract;

import au.com.dius.pact.consumer.junit5.PactConsumerTestExt;
import au.com.dius.pact.consumer.junit5.PactTestFor;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;

@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "OrderService", port = "8080")
public class OrderServiceContractTest {

    @Test
    public void testOrderCreation() {
        // Define the expected interaction
        // Set up the mock server and verify the contract
    }
}
```

### Summary of Testing Strategy

| Test Type       | Purpose                                      | Coverage Target |
|------------------|----------------------------------------------|------------------|
| Unit Tests       | Verify individual components                  | 80%              |
| Integration Tests| Validate interactions with MongoDB           | 70%              |
| Contract Tests   | Ensure service interactions adhere to contracts| 100%             |

By adhering to this testing strategy, Xentic's engineering teams will ensure that the MongoDB implementations are robust, reliable, and maintainable, ultimately leading to a higher quality of software delivery.

## Observability and operations

To maintain effective observability and operations for MongoDB deployments at Xentic, the following practices MUST be implemented. These practices encompass metrics collection, logging, tracing, dashboard creation, alerting, and defining Service Level Objectives (SLOs). 

### Metrics

Metrics provide insights into the performance and health of MongoDB instances. The following key metrics MUST be collected:

- **Operation Counts**: Track the number of read and write operations.
- **Latency**: Measure the time taken for read and write operations.
- **Memory Usage**: Monitor the memory consumption of MongoDB.
- **Connections**: Keep track of the number of active connections to the database.
- **Disk I/O**: Measure the read and write throughput on disk.

Example Prometheus metrics configuration:
```yaml
mongodb_exporter:
  enabled: true
  config:
    uri: mongodb://appUser:StrongPassword123!@mongo.internal.xentic.io:27017/<database>
    metrics:
      - name: mongodb_operation_counts
        type: counter
        help: "Count of operations performed on MongoDB"
      - name: mongodb_operation_latency
        type: histogram
        help: "Latency of operations in seconds"
```

### Logs

Logging is essential for diagnosing issues and understanding application behavior. MongoDB logs MUST be configured to capture the following:

- **Query Execution**: Log slow queries to identify performance bottlenecks.
- **Connection Events**: Track connection establishment and termination.
- **Error Messages**: Capture any errors that occur during database operations.

Example configuration in `mongod.conf`:
```yaml
systemLog:
  destination: file
  path: /var/log/mongodb/mongod.log
  logAppend: true
  verbosity: 0 # Adjust as needed for more detailed logs
```

### Traces

Distributed tracing MUST be implemented to understand the flow of requests through the application and identify performance issues. Use OpenTelemetry or similar tools to trace requests from the application to the database.

Example trace configuration:
```yaml
opentelemetry:
  service:
    name: xentic-service
  exporter:
    otlp:
      endpoint: otel-collector.internal.xentic.io:4317
```

### Dashboards

Dashboards MUST be created to visualize key metrics and logs. Use Grafana or similar tools to create dashboards that include:

- **Database Health**: Display metrics like connections, memory usage, and disk I/O.
- **Query Performance**: Show slow queries and their execution times.
- **Operational Metrics**: Visualize read/write operation counts and latency.

Example Grafana dashboard JSON snippet:
```json
{
  "title": "MongoDB Overview",
  "panels": [
    {
      "type": "graph",
      "title": "Operation Counts",
      "targets": [
        {
          "target": "mongodb_operation_counts"
        }
      ]
    },
    {
      "type": "graph",
      "title": "Operation Latency",
      "targets": [
        {
          "target": "mongodb_operation_latency"
        }
      ]
    }
  ]
}
```

### Alerts

Alerts MUST be configured to notify the on-call team of critical issues. Set up alerts for the following conditions:

- **High Latency**: Alert if the average latency exceeds a predefined threshold.
- **High Memory Usage**: Alert if memory usage exceeds 80% of available resources.
- **Connection Limits**: Alert if the number of active connections approaches the maximum limit.

Example Prometheus alerting rule:
```yaml
groups:
  - name: mongodb-alerts
    rules:
      - alert: HighLatency
        expr: avg(mongodb_operation_latency) > 0.5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High MongoDB Latency"
          description: "Latency is above 500ms for more than 5 minutes."
```

### Service Level Objectives (SLOs)

SLOs MUST be defined to measure the reliability and performance of MongoDB services. Consider the following SLOs:

- **Availability**: 99.9% uptime over a rolling 30-day period.
- **Latency**: 95% of queries should complete within 200ms.
- **Error Rate**: Less than 1% of requests should result in errors.

### On-Call Runbook Steps

In the event of an incident, the on-call engineer MUST follow these steps:

1. **Identify the Issue**: Review logs and metrics to understand the nature of the problem.
2. **Check Alerts**: Determine if any alerts have been triggered and their severity.
3. **Investigate**: Use tracing tools to identify slow queries or bottlenecks.
4. **Mitigate**: Apply quick fixes, such as optimizing queries or scaling resources.
5. **Document**: Record the incident details, actions taken, and resolution in the incident management system.
6. **Review**: Conduct a post-mortem to analyze the incident and improve processes.

By implementing these observability and operations practices, Xentic will ensure that MongoDB deployments are monitored effectively, enabling quick responses to incidents and maintaining high service reliability.

## Migration and versioning

To ensure smooth transitions and maintain system integrity during MongoDB updates at Xentic, the following migration and versioning strategies MUST be adhered to:

### Upgrade Paths

- **Major Version Upgrades**: These MUST be carefully planned and executed. A detailed migration plan should be created, including:
  - Compatibility checks with existing data.
  - Testing in a staging environment before production rollout.
  - A rollback plan in case of failure.

- **Minor Version Upgrades**: These SHOULD be applied regularly to leverage improvements and security patches. The following steps are recommended:
  - Review release notes for breaking changes.
  - Perform testing in a controlled environment.
  - Schedule upgrades during low-traffic periods.

### Deprecation Policy

- **Deprecation Notices**: Any deprecated features MUST be communicated clearly through release notes and internal documentation. Teams MUST be given at least one full release cycle to adapt to changes.

- **Grace Period**: Deprecated features MUST remain functional for at least two minor releases before being removed. This allows teams adequate time to refactor their code.

### Backward Compatibility

- **Data Model Changes**: Any changes to the MongoDB schema MUST be backward compatible. Use techniques such as:
  - Adding new fields instead of removing existing ones.
  - Using default values for new fields to ensure old records remain valid.

- **Application Compatibility**: The application MUST be able to handle both old and new versions of the database schema. Implement feature toggles or versioning in APIs to manage different client versions.

### Rollback Procedures

In the event of a failed migration or upgrade, the following rollback procedures MUST be established:

1. **Backup**: Always take a full backup of the database before performing any upgrades. Use the following command to create a backup:
   ```bash
   mongodump --uri="mongodb://appUser:StrongPassword123!@mongo.internal.xentic.io:27017/<database>" --out=/path/to/backup/
   ```

2. **Restore**: If an upgrade fails, restore the database using the backup:
   ```bash
   mongorestore --uri="mongodb://appUser:StrongPassword123!@mongo.internal.xentic.io:27017/<database>" /path/to/backup/<database>
   ```

3. **Validation**: After restoration, validate the integrity of the data and ensure that the application is functioning as expected.

### Versioning Strategy

- **MongoDB Versioning**: Maintain a versioning strategy for MongoDB schemas. Use semantic versioning (MAJOR.MINOR.PATCH) to indicate changes:
  - **MAJOR**: Incompatible API changes.
  - **MINOR**: Backward-compatible functionality.
  - **PATCH**: Backward-compatible bug fixes.

- **Schema Versioning**: Store the current schema version in a dedicated collection to track migrations:
  ```json
  {
    "schemaVersion": "1.0.0",
    "lastUpdated": "2023-10-01T12:00:00Z"
  }
  ```

### Migration Scripts

- **Migration Scripts**: All schema changes MUST be accompanied by migration scripts. These scripts should be idempotent, meaning they can be run multiple times without adverse effects. Example migration script in Java:
  ```java
  public void migrateToVersion1_1() {
      MongoCollection<Document> collection = mongoDatabase.getCollection("users");
      collection.updateMany(
          new Document("status", "active"),
          new Document("$set", new Document("lastLogin", new Date()))
      );
  }
  ```

### Summary Table

| Migration Aspect         | Requirement                                                                 |
|--------------------------|-----------------------------------------------------------------------------|
| Upgrade Paths            | MUST plan major upgrades; SHOULD apply minor upgrades regularly.           |
| Deprecation Policy       | MUST communicate deprecations; MUST provide a grace period.                |
| Backward Compatibility    | MUST ensure schema changes are backward compatible.                        |
| Rollback Procedures      | MUST have a backup and restore strategy in place.                          |
| Versioning Strategy      | MUST use semantic versioning for schemas and APIs.                        |
| Migration Scripts        | MUST create idempotent migration scripts for schema changes.              |

By following these migration and versioning guidelines, Xentic will minimize disruptions and maintain the integrity of its MongoDB deployments during upgrades and changes.

## FAQ, anti-patterns, and checklists

### Frequently Asked Questions (FAQ)

1. **What is the purpose of indexing in MongoDB?**
   - Indexing improves query performance by allowing the database to quickly locate and access data without scanning the entire collection.

2. **How many indexes should I create on a collection?**
   - You SHOULD create indexes based on query patterns, but avoid excessive indexing as it can slow down write operations. A maximum of 5-10 indexes per collection is generally recommended.

3. **What types of indexes are available in MongoDB?**
   - MongoDB supports several types of indexes:
     - Single Field Index
     - Compound Index
     - Multikey Index
     - Text Index
     - Geospatial Index

4. **How do I create an index in MongoDB?**
   - Use the following command to create an index:
   ```javascript
   db.collection.createIndex({ fieldName: 1 }) // 1 for ascending, -1 for descending
   ```

5. **What is the impact of indexing on write operations?**
   - Indexing MUST be balanced with write performance. Each index adds overhead to write operations, so only index fields that are frequently queried.

6. **How can I analyze index usage?**
   - Use the `db.collection.getIndexes()` command to view existing indexes and the `db.collection.aggregate()` method with the `$indexStats` stage to analyze usage.

7. **What is an index build blocking operation?**
   - Index builds can block write operations on the collection. To avoid this, use the `background` option:
   ```javascript
   db.collection.createIndex({ fieldName: 1 }, { background: true })
   ```

8. **How do I drop an index?**
   - Use the following command to drop an index:
   ```javascript
   db.collection.dropIndex("indexName")
   ```

9. **What are the best practices for compound indexes?**
   - The order of fields in a compound index MUST match the order of fields in queries. Always include the most selective fields first.

10. **How can I ensure my indexes are optimized?**
    - Regularly review query performance, use the `explain()` method to analyze query plans, and adjust indexes based on usage patterns.

### Anti-patterns

| Anti-pattern                          | Description                                                                                     |
|---------------------------------------|-------------------------------------------------------------------------------------------------|
| Over-indexing                         | Creating too many indexes can degrade write performance and increase storage requirements.     |
| Not using compound indexes             | Relying solely on single-field indexes can lead to inefficient queries that could be optimized. |
| Ignoring index cardinality            | Failing to consider the uniqueness of indexed fields can lead to inefficient indexing strategies.|
| Indexing fields that are rarely queried| Indexes on infrequently accessed fields waste resources and slow down write operations.         |
| Not monitoring index usage            | Without monitoring, you may have stale or unused indexes that need to be removed.              |

### Pre-Merge Checklist

- [ ] Ensure all new indexes are documented in the database schema documentation.
- [ ] Validate that new indexes do not interfere with existing indexes.
- [ ] Run performance tests to confirm that new indexes improve query times.
- [ ] Review the impact of index changes on write operations.
- [ ] Ensure that the application code is updated to utilize the new indexes effectively.

### Production Checklist

- [ ] Confirm that all indexes are created in a non-blocking manner if applicable.
- [ ] Monitor the performance of queries post-deployment to ensure expected improvements.
- [ ] Check for any alerts related to index usage or performance.
- [ ] Review logs for any unexpected behavior related to indexing.
- [ ] Document any changes to indexing strategy in the internal knowledge base at [https://docs.internal.xentic.io](https://docs.internal.xentic.io).
