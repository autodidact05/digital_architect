# Soft Delete Patterns — MongoDB

## Overview and scope

The purpose of this document is to outline the standards and best practices for implementing soft delete patterns in MongoDB within the Xentic platform. Soft deletes are a crucial design pattern that allows for the logical deletion of records while preserving the data for potential future retrieval or auditing purposes. This document will serve as a guide for engineers and developers working on services that utilize MongoDB as their primary data store.

### Audience

This document is intended for:
- Software Engineers
- Database Administrators
- Technical Architects
- Quality Assurance Engineers

### Scope

This standard applies to all services within Xentic that utilize MongoDB for data storage. The following aspects will be covered:
- Implementation of soft delete patterns
- Querying soft-deleted records
- Configuration examples
- Best practices for data integrity and performance

### Non-goals

This document does NOT cover:
- Hard delete patterns
- General MongoDB usage and configuration
- Data migration strategies unrelated to soft deletes

### Glossary

| Term               | Definition                                                                                   |
|--------------------|----------------------------------------------------------------------------------------------|
| Soft Delete        | A method of marking a record as deleted without actually removing it from the database.     |
| MongoDB            | A NoSQL database that uses a document-oriented data model.                                   |
| Logical Deletion    | The process of marking a record as deleted while keeping it in the database for future use. |

### How This Standard Fits the Xentic Platform

The implementation of soft delete patterns aligns with Xentic's commitment to data integrity, auditability, and compliance. By adhering to these standards, services can ensure that:
- Deleted records can be restored if necessary.
- Historical data can be preserved for reporting and auditing.
- Compliance with data retention policies is maintained.

### Implementation Example

To implement a soft delete in MongoDB, you MUST include a `deleted` field in your document schema. This field should be a boolean indicating whether the record is deleted.

```yaml
# Example MongoDB document schema with soft delete
{
  "_id": "ObjectId",
  "name": "Sample Record",
  "createdAt": "ISODate",
  "updatedAt": "ISODate",
  "deleted": false  # Soft delete flag
}
```

### Querying Soft Deleted Records

When querying for records, you MUST ensure that soft-deleted records are excluded from results by filtering on the `deleted` field.

```javascript
// Example MongoDB query to find non-deleted records
db.collection.find({ deleted: false });
```

### Best Practices

- **Indexing**: You SHOULD create an index on the `deleted` field to improve query performance.
- **Data Retention**: You MUST define a data retention policy to determine how long soft-deleted records will be retained.
- **Audit Logs**: You SHOULD maintain an audit log for soft-deleted records to track changes and deletions.

By following these guidelines, Xentic services can effectively manage data while ensuring compliance and integrity across the platform.

## Standards and policies

1. **Soft Delete Field**: You MUST include a `deleted` field in every document schema where soft deletes are applicable. This field MUST be a boolean type, defaulting to `false`.

   ```yaml
   # Document schema example
   {
     "_id": "ObjectId",
     "name": "Sample Record",
     "createdAt": "ISODate",
     "updatedAt": "ISODate",
     "deleted": false  # Soft delete flag
   }
   ```

2. **Querying Records**: You MUST filter out soft-deleted records in all read queries by including a condition on the `deleted` field.

   ```javascript
   // Query to find all non-deleted records
   db.collection.find({ deleted: false });
   ```

3. **Indexing**: You SHOULD create an index on the `deleted` field to enhance query performance. This index MUST be a sparse index to avoid unnecessary overhead.

   ```javascript
   // Create a sparse index on the deleted field
   db.collection.createIndex({ deleted: 1 }, { sparse: true });
   ```

4. **Data Retention Policy**: You MUST define a data retention policy for soft-deleted records, specifying how long these records will be retained before permanent deletion. This policy MUST be documented and communicated to all relevant stakeholders.

5. **Audit Logging**: You SHOULD maintain an audit log for all soft delete operations. The log MUST include the record ID, timestamp, and user who performed the deletion.

   ```javascript
   // Example audit log entry for a soft delete
   {
     "recordId": "ObjectId",
     "action": "soft_delete",
     "timestamp": "ISODate",
     "user": "username"
   }
   ```

6. **Restoration of Records**: You MUST provide a mechanism to restore soft-deleted records. This mechanism MUST update the `deleted` field back to `false`.

   ```javascript
   // Example of restoring a soft-deleted record
   db.collection.updateOne({ _id: "ObjectId" }, { $set: { deleted: false } });
   ```

7. **Service Layer Enforcement**: You MUST enforce soft delete logic at the service layer to prevent direct database operations that could bypass the soft delete mechanism.

8. **Testing**: You MUST write unit tests to validate that soft delete functionality works as intended, including tests for querying, restoring, and auditing.

9. **Documentation**: You MUST document all soft delete implementations in the service's README file and include examples of how to use the soft delete functionality.

10. **Performance Monitoring**: You SHOULD monitor the performance of queries involving the `deleted` field and adjust indexing strategies as necessary to maintain optimal performance.

11. **Data Integrity**: You MUST ensure that foreign key relationships are handled appropriately when implementing soft deletes. If a record is soft-deleted, related records MUST be updated to reflect this state if necessary.

12. **Configuration Management**: You SHOULD use configuration management tools to manage settings related to soft delete policies, such as retention periods and audit logging configurations.

By adhering to these standards and policies, Xentic services can effectively implement soft delete patterns in MongoDB, ensuring data integrity, compliance, and performance across the platform.

## Architecture and design

### Component Diagram

```mermaid
graph TD;
    A[Service Layer] -->|CRUD Operations| B[MongoDB Database]
    B -->|Audit Logs| C[Audit Log Service]
    B -->|Indexing| D[Index Management]
    A -->|Soft Delete| E[Soft Delete Logic]
    E -->|Restore Records| B
    E -->|Query Non-deleted Records| B
    F[User Interface] -->|User Actions| A
```

### Data Flows

1. **User Actions**: Users interact with the User Interface (UI) to perform CRUD operations.
2. **Service Layer**: The Service Layer processes these actions and applies soft delete logic where necessary.
3. **MongoDB Database**: The Service Layer communicates with the MongoDB database to store, retrieve, or update records.
4. **Audit Log Service**: Any soft delete actions are logged in the Audit Log Service for compliance and tracking.
5. **Index Management**: The database maintains indexes to optimize query performance, especially for the `deleted` field.

### Integration Points

- **MongoDB**: This is the primary data store where all records are kept, whether active or soft-deleted.
- **Audit Log Service**: This service captures all soft delete actions, ensuring that there is a record of who deleted what and when.
- **User Interface**: The UI provides a front-end for users to interact with the system, triggering soft delete actions through the Service Layer.

### Failure Domains

1. **Database Failures**: If MongoDB becomes unavailable, all CRUD operations will fail, including soft deletes and retrieval of records.
2. **Service Layer Failures**: Issues in the Service Layer could prevent the correct application of soft delete logic, leading to potential data integrity issues.
3. **Audit Log Service Failures**: If the Audit Log Service fails, soft delete actions may not be recorded, compromising compliance.
4. **Network Issues**: Any network problems between the UI and the Service Layer or between the Service Layer and MongoDB can disrupt operations.

### Best Practices for Architecture

- **Separation of Concerns**: The architecture MUST separate the concerns of data management, business logic, and user interface to enhance maintainability and scalability.
- **Error Handling**: You MUST implement robust error handling throughout the Service Layer to gracefully manage failures and ensure data integrity.
- **Load Balancing**: Consider using load balancers for the Service Layer to manage traffic and ensure high availability.
- **Monitoring and Alerts**: You SHOULD set up monitoring and alerting for all critical components, including MongoDB, the Service Layer, and the Audit Log Service, to quickly identify and resolve issues.
- **Backup Strategies**: You MUST implement regular backup strategies for MongoDB to prevent data loss, especially for soft-deleted records that may need to be restored.

By adhering to these architectural guidelines, Xentic services can effectively manage soft delete patterns in MongoDB while ensuring reliability, maintainability, and compliance.

## Configuration reference

To facilitate the implementation of soft delete patterns in MongoDB, the following configuration references are provided. This includes settings for `application.yml`, Terraform, and environment variables.

### application.yml

The `application.yml` file should include configurations for MongoDB connection settings, soft delete policies, and audit logging.

```yaml
spring:
  data:
    mongodb:
      uri: mongodb://username:password@mongo.internal.xentic.io:27017/xentic_db
      database: xentic_db

soft-delete:
  enabled: true
  retention-period: 30d  # Retain soft-deleted records for 30 days
  audit-log:
    enabled: true
    log-level: INFO
```

### Terraform Configuration

Use Terraform to manage the infrastructure related to MongoDB and its configurations. Below is an example of how to set up a MongoDB instance with soft delete configurations.

```hcl
resource "mongodb_database" "xentic_db" {
  name = "xentic_db"
}

resource "mongodb_collection" "records" {
  database = mongodb_database.xentic_db.name
  name     = "records"

  schema = <<EOF
{
  "bsonType": "object",
  "required": ["name", "createdAt", "updatedAt", "deleted"],
  "properties": {
    "name": {
      "bsonType": "string"
    },
    "createdAt": {
      "bsonType": "date"
    },
    "updatedAt": {
      "bsonType": "date"
    },
    "deleted": {
      "bsonType": "bool",
      "description": "Soft delete flag, defaults to false"
    }
  }
}
EOF

  lifecycle {
    ignore_changes = [schema]
  }
}

resource "mongodb_index" "deleted_index" {
  collection = mongodb_collection.records.name
  keys       = ["deleted"]
  options    = {
    "sparse" = true
  }
}
```

### Environment Variables

Environment variables can be used to configure critical settings for soft delete functionality. Below are examples of environment variables that should be set in production.

| Environment Variable           | Default Value                   | Production Value                      |
|--------------------------------|----------------------------------|---------------------------------------|
| `MONGODB_URI`                  | `mongodb://localhost:27017`     | `mongodb://username:password@mongo.internal.xentic.io:27017/xentic_db` |
| `SOFT_DELETE_ENABLED`          | `false`                         | `true`                                |
| `SOFT_DELETE_RETENTION_PERIOD` | `7d`                            | `30d`                                 |
| `AUDIT_LOG_ENABLED`            | `false`                         | `true`                                |
| `AUDIT_LOG_LEVEL`              | `WARN`                          | `INFO`                                |

### Summary

By adhering to the configuration references outlined above, Xentic services can effectively implement soft delete patterns in MongoDB. These configurations ensure proper data management, retention policies, and audit logging, thereby maintaining compliance and data integrity across the platform.

## Implementation guide

To implement soft delete patterns in MongoDB effectively, follow this step-by-step guide. This implementation will involve creating a model, a repository, a service layer, and an audit logging mechanism.

### Step 1: Define the Model

Create a model class that represents the data structure in MongoDB. This class will include a `deleted` field to indicate whether a record is soft-deleted.

```java
package com.xentic.records.model;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.LocalDateTime;

@Document(collection = "records")
public class Record {
    @Id
    private String id;
    private String name;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private boolean deleted;

    // Getters and Setters
}
```

### Step 2: Create the Repository

Define a repository interface that extends `MongoRepository`. This interface will include methods for soft deletion and restoration.

```java
package com.xentic.records.repository;

import com.xentic.records.model.Record;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface RecordRepository extends MongoRepository<Record, String> {
    List<Record> findByDeletedFalse();
    
    // Custom query to find soft-deleted records if needed
    List<Record> findByDeletedTrue();
}
```

### Step 3: Implement the Service Layer

Create a service class that handles the business logic for soft deleting and restoring records. This class will also handle audit logging.

```java
package com.xentic.records.service;

import com.xentic.records.model.Record;
import com.xentic.records.repository.RecordRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class RecordService {
    @Autowired
    private RecordRepository recordRepository;

    public Record softDelete(String id) {
        Record record = recordRepository.findById(id).orElseThrow(() -> new RuntimeException("Record not found"));
        record.setDeleted(true);
        record.setUpdatedAt(LocalDateTime.now());
        // Log the soft delete action
        logAudit(record.getId(), "soft_delete");
        return recordRepository.save(record);
    }

    public Record restore(String id) {
        Record record = recordRepository.findById(id).orElseThrow(() -> new RuntimeException("Record not found"));
        record.setDeleted(false);
        record.setUpdatedAt(LocalDateTime.now());
        // Log the restore action
        logAudit(record.getId(), "restore");
        return recordRepository.save(record);
    }

    private void logAudit(String recordId, String action) {
        // Implement audit logging logic here
        System.out.println("Audit Log: Record ID: " + recordId + ", Action: " + action + ", Timestamp: " + LocalDateTime.now());
    }
}
```

### Step 4: Create the Controller

Implement a REST controller to expose the soft delete and restore endpoints.

```java
package com.xentic.records.controller;

import com.xentic.records.model.Record;
import com.xentic.records.service.RecordService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/records")
public class RecordController {
    @Autowired
    private RecordService recordService;

    @DeleteMapping("/{id}")
    public ResponseEntity<Record> softDelete(@PathVariable String id) {
        Record deletedRecord = recordService.softDelete(id);
        return ResponseEntity.ok(deletedRecord);
    }

    @PostMapping("/{id}/restore")
    public ResponseEntity<Record> restore(@PathVariable String id) {
        Record restoredRecord = recordService.restore(id);
        return ResponseEntity.ok(restoredRecord);
    }

    @GetMapping
    public ResponseEntity<List<Record>> getActiveRecords() {
        return ResponseEntity.ok(recordService.findActiveRecords());
    }
}
```

### Step 5: Testing the Implementation

You MUST write unit tests to validate the soft delete and restore functionality.

```java
package com.xentic.records.service;

import com.xentic.records.model.Record;
import com.xentic.records.repository.RecordRepository;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import static org.mockito.Mockito.*;

class RecordServiceTest {
    private final RecordRepository recordRepository = Mockito.mock(RecordRepository.class);
    private final RecordService recordService = new RecordService(recordRepository);

    @Test
    void testSoftDelete() {
        Record record = new Record();
        record.setId("1");
        record.setDeleted(false);
        when(recordRepository.findById("1")).thenReturn(Optional.of(record));

        Record deletedRecord = recordService.softDelete("1");

        assertTrue(deletedRecord.isDeleted());
        verify(recordRepository).save(deletedRecord);
    }

    @Test
    void testRestore() {
        Record record = new Record();
        record.setId("1");
        record.setDeleted(true);
        when(recordRepository.findById("1")).thenReturn(Optional.of(record));

        Record restoredRecord = recordService.restore("1");

        assertFalse(restoredRecord.isDeleted());
        verify(recordRepository).save(restoredRecord);
    }
}
```

### Summary

By following this implementation guide, Xentic services can effectively manage soft delete patterns in MongoDB. The provided code examples illustrate how to define the model, repository, service layer, and controller, ensuring a robust and maintainable implementation.

## Security requirements

To ensure the security of the soft delete implementation in MongoDB, the following security requirements must be adhered to:

### Threat Model Summary

The following threats must be considered when designing and implementing soft delete functionality:

| Threat                         | Description                                                                 |
|--------------------------------|-----------------------------------------------------------------------------|
| Unauthorized Access            | Attackers may attempt to access or manipulate soft-deleted records.        |
| Data Leakage                   | Sensitive information may be exposed if soft-deleted records are not properly handled. |
| Injection Attacks              | Input validation must be robust to prevent injection attacks (e.g., NoSQL injection). |
| Insecure Audit Logs            | Audit logs must be protected to ensure integrity and confidentiality.       |

### Authentication and Authorization

- **Authentication**: All API endpoints must enforce authentication using OAuth2 or JWT. Access tokens must be validated for each request.
- **Authorization**: Role-based access control (RBAC) MUST be implemented to restrict access to soft delete and restore operations. Only authorized roles should be able to perform these actions.

```yaml
security:
  oauth2:
    tokenUrl: https://auth.internal.xentic.io/oauth/token
    scopes:
      records:read: Grants read access to records.
      records:write: Grants write access to records.
```

### Secrets Management

- Secrets, such as database credentials and API keys, MUST NOT be hardcoded in the application. Use a secrets management tool (e.g., HashiCorp Vault, AWS Secrets Manager) to manage sensitive information.
- Ensure that secrets are encrypted both at rest and in transit.

```hcl
resource "vault_generic_secret" "mongodb_credentials" {
  path = "mongodb/creds"
  data_json = <<EOF
{
  "username": "mongo_user",
  "password": "secure_password"
}
EOF
}
```

### Input Validation

- All inputs to the API MUST be validated against a defined schema to prevent injection attacks and ensure data integrity.
- Use libraries such as `javax.validation` for Java to enforce constraints on incoming data.

```java
import javax.validation.constraints.NotBlank;

public class RecordRequest {
    @NotBlank(message = "Name must not be empty")
    private String name;
    
    // Getters and Setters
}
```

### Audit Logging

- Audit logging MUST be enabled for all operations related to soft delete and restore. Logs should capture the following information:
  - User ID of the requester
  - Action performed (soft delete or restore)
  - Record ID affected
  - Timestamp of the action

- Logs MUST be stored securely and should be immutable to prevent tampering.

```java
private void logAudit(String recordId, String action) {
    AuditLog log = new AuditLog();
    log.setRecordId(recordId);
    log.setAction(action);
    log.setTimestamp(LocalDateTime.now());
    log.setUserId(getCurrentUserId());
    
    // Save log to audit log repository
    auditLogRepository.save(log);
}
```

### Summary

By implementing the outlined security requirements, Xentic can ensure that the soft delete functionality in MongoDB is secure, compliant, and resilient against common threats. This comprehensive approach to security will help maintain data integrity and protect sensitive information across the platform.

## Testing strategy

To ensure the reliability and correctness of the soft delete functionality in MongoDB, a comprehensive testing strategy must be employed. This strategy includes unit tests, integration tests, and contract tests, each serving a specific purpose in the validation process.

### Unit Tests

Unit tests should focus on individual components, such as the service methods responsible for soft deleting and restoring records. The following coverage targets should be established:

| Coverage Target            | Description                                                             |
|----------------------------|-------------------------------------------------------------------------|
| 100% Method Coverage       | Every public method in the service layer MUST be covered by unit tests. |
| 100% Branch Coverage       | All conditional branches in the service methods MUST be tested.         |
| Exception Handling         | All exceptions that can be thrown MUST be tested.                       |

#### Example Unit Test Class

```java
package com.xentic.records.service;

import com.xentic.records.model.Record;
import com.xentic.records.repository.RecordRepository;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import java.time.LocalDateTime;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class RecordServiceTest {
    private final RecordRepository recordRepository = Mockito.mock(RecordRepository.class);
    private final RecordService recordService = new RecordService(recordRepository);

    @Test
    void testSoftDelete() {
        Record record = new Record();
        record.setId("1");
        record.setDeleted(false);
        when(recordRepository.findById("1")).thenReturn(Optional.of(record));

        Record deletedRecord = recordService.softDelete("1");

        assertTrue(deletedRecord.isDeleted());
        assertNotNull(deletedRecord.getUpdatedAt());
        verify(recordRepository).save(deletedRecord);
    }

    @Test
    void testRestore() {
        Record record = new Record();
        record.setId("1");
        record.setDeleted(true);
        when(recordRepository.findById("1")).thenReturn(Optional.of(record));

        Record restoredRecord = recordService.restore("1");

        assertFalse(restoredRecord.isDeleted());
        assertNotNull(restoredRecord.getUpdatedAt());
        verify(recordRepository).save(restoredRecord);
    }

    @Test
    void testSoftDeleteRecordNotFound() {
        when(recordRepository.findById("2")).thenReturn(Optional.empty());

        Exception exception = assertThrows(RuntimeException.class, () -> {
            recordService.softDelete("2");
        });

        assertEquals("Record not found", exception.getMessage());
    }
}
```

### Integration Tests

Integration tests should validate the interaction between components, particularly the service and repository layers. The following aspects should be covered:

- **Database Interaction**: Ensure that soft delete and restore operations correctly update the database.
- **REST API Endpoints**: Validate that the controller correctly handles requests and responses.

#### Example Integration Test Class

```java
package com.xentic.records.controller;

import com.xentic.records.model.Record;
import com.xentic.records.service.RecordService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(RecordController.class)
class RecordControllerTest {
    @Autowired
    private MockMvc mockMvc;

    private RecordService recordService;

    @BeforeEach
    void setUp() {
        recordService = mock(RecordService.class);
    }

    @Test
    void testSoftDelete() throws Exception {
        Record record = new Record();
        record.setId("1");
        record.setDeleted(true);
        when(recordService.softDelete("1")).thenReturn(record);

        mockMvc.perform(delete("/api/records/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value("1"))
                .andExpect(jsonPath("$.deleted").value(true));
    }

    @Test
    void testRestore() throws Exception {
        Record record = new Record();
        record.setId("1");
        record.setDeleted(false);
        when(recordService.restore("1")).thenReturn(record);

        mockMvc.perform(post("/api/records/1/restore"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value("1"))
                .andExpect(jsonPath("$.deleted").value(false));
    }
}
```

### Contract Tests

Contract tests should ensure that the API adheres to the expected contract between services. These tests are critical when multiple services interact with each other.

- **API Specification**: Use tools like Pact to define and verify contracts between the consumer and provider.
- **Versioning**: Ensure that changes to the API do not break existing contracts.

### Summary

By implementing a robust testing strategy that includes unit, integration, and contract tests, Xentic can ensure that the soft delete functionality in MongoDB is thoroughly validated. This comprehensive approach will help maintain high code quality and reliability across the platform.

## Observability and operations

To ensure the smooth operation and observability of the soft delete functionality in MongoDB, Xentic MUST implement a comprehensive monitoring and alerting strategy. This includes metrics collection, logging, tracing, dashboard creation, alerting, and defining Service Level Objectives (SLOs).

### Metrics

The following metrics MUST be collected to monitor the performance and health of the soft delete functionality:

| Metric Name                   | Description                                           |
|-------------------------------|-------------------------------------------------------|
| `soft_delete_requests_total`  | Total number of soft delete requests received.        |
| `soft_delete_success_total`   | Total number of successful soft delete operations.    |
| `soft_delete_failure_total`   | Total number of failed soft delete operations.        |
| `restore_requests_total`      | Total number of restore requests received.            |
| `restore_success_total`       | Total number of successful restore operations.        |
| `restore_failure_total`       | Total number of failed restore operations.            |
| `latency_soft_delete`         | Latency of soft delete operations in milliseconds.    |
| `latency_restore`             | Latency of restore operations in milliseconds.        |

### Logs

All operations related to soft delete and restore MUST be logged. The logs should include:

- Timestamp
- User ID of the requester
- Action performed (soft delete or restore)
- Record ID affected
- Status of the operation (success or failure)
- Error messages (if any)

#### Example Log Entry

```plaintext
2023-10-01T12:00:00Z INFO User 123 performed soft delete on record ID 456. Status: success
```

### Traces

Distributed tracing MUST be implemented to trace the flow of requests through the system. This helps in identifying bottlenecks and performance issues. Use tools like OpenTelemetry or Zipkin to capture traces.

### Dashboards

Dashboards MUST be created to visualize the collected metrics. The following panels should be included:

- Total soft delete requests over time
- Success and failure rates for soft delete and restore operations
- Latency metrics for both operations
- User activity logs for soft delete and restore actions

#### Example Dashboard Layout

| Panel Name                     | Type          | Description                                  |
|--------------------------------|---------------|----------------------------------------------|
| Soft Delete Requests           | Time Series   | Displays total requests over time.          |
| Soft Delete Success Rate       | Pie Chart     | Shows the percentage of successful requests. |
| Restore Operations Latency     | Bar Chart     | Compares latency for restore operations.     |
| User Activity Log              | Table         | Lists recent user actions related to deletes.|

### Alerts

Alerts MUST be configured to notify the operations team of any anomalies or issues. The following alerts should be set up:

- **High Failure Rate Alert**: Trigger if the failure rate for soft delete or restore exceeds 5% over a 5-minute window.
- **High Latency Alert**: Trigger if the latency for soft delete or restore exceeds 500 milliseconds.
- **Error Rate Alert**: Trigger if the error rate for API responses exceeds 1% over a 5-minute window.

### Service Level Objectives (SLOs)

Xentic MUST define SLOs for the soft delete and restore functionalities. The following SLOs are recommended:

| SLO Description                             | Target                      |
|---------------------------------------------|-----------------------------|
| 99.9% of soft delete requests are successful | Monthly                      |
| 99.9% of restore requests are successful     | Monthly                      |
| Average latency for soft delete < 200ms      | Monthly                      |
| Average latency for restore < 200ms           | Monthly                      |

### On-call Runbook Steps

In case of an incident related to soft delete or restore operations, the following steps MUST be followed:

1. **Identify the Incident**: Use dashboards and alerts to confirm the issue.
2. **Gather Logs**: Collect logs related to the incident timeframe.
3. **Check Metrics**: Review metrics for anomalies in success rates or latencies.
4. **Trace Analysis**: Use tracing tools to identify bottlenecks or failures in the request flow.
5. **Notify Stakeholders**: Inform relevant teams about the incident and the impact.
6. **Implement Fix**: Based on the analysis, implement necessary fixes or rollbacks.
7. **Post-Incident Review**: Conduct a review to identify root causes and preventive measures.

By adhering to these observability and operations standards, Xentic can ensure that the soft delete functionality in MongoDB is monitored effectively, enabling quick responses to issues and maintaining high service reliability.

## Migration and versioning

When implementing soft delete functionality in MongoDB, Xentic MUST establish clear migration and versioning strategies to ensure smooth transitions between versions, maintain backward compatibility, and facilitate rollback procedures. The following guidelines outline the necessary steps and considerations.

### Upgrade Paths

1. **Versioning Strategy**: Each service MUST adopt a semantic versioning strategy (MAJOR.MINOR.PATCH) to indicate the nature of changes:
   - **MAJOR**: Breaking changes (e.g., changing the soft delete implementation).
   - **MINOR**: New features or enhancements (e.g., adding new fields for soft deletes).
   - **PATCH**: Bug fixes or minor improvements.

2. **Backward Compatibility**: New versions of the service MUST be backward compatible with previous versions. This means that existing clients should continue to function without changes. 

3. **Feature Flags**: Introduce feature flags for new functionalities to allow gradual rollout and easy rollback if issues arise.

#### Example Feature Flag Configuration (YAML)

```yaml
featureFlags:
  softDelete:
    enabled: true
  newSoftDeleteLogic:
    enabled: false
```

### Deprecation Policy

1. **Deprecation Notices**: When a feature or API endpoint is deprecated, Xentic MUST provide clear documentation and notifications to all stakeholders at least one release cycle in advance.

2. **Grace Period**: A grace period of at least three months MUST be provided for deprecated features, during which both old and new implementations are supported.

3. **Removal Timeline**: After the grace period, deprecated features MUST be removed in a subsequent major release.

### Rollback Procedures

In the event of a failed deployment or critical issue, Xentic MUST have a rollback procedure in place:

1. **Backup Strategy**: Regular backups of the database MUST be taken before deploying new versions. This allows for restoration in case of failure.

2. **Rollback Steps**:
   - Identify the version that needs to be rolled back.
   - Restore the database from the most recent backup.
   - Redeploy the previous version of the service.

3. **Rollback Testing**: Rollback procedures MUST be tested in staging environments to ensure they function correctly before being relied upon in production.

### Migration Scripts

When changes to the database schema are required (e.g., adding a `deleted` field), Xentic MUST provide migration scripts. These scripts should be idempotent and reversible.

#### Example Migration Script (MongoDB Shell)

```javascript
db.records.updateMany(
  {},
  { $set: { deleted: false } }
);
```

### Versioning in Database

1. **Version Field**: Each document in the MongoDB collection MUST include a `version` field to track the schema version.

#### Example Document Structure

```json
{
  "_id": "1",
  "name": "Sample Record",
  "deleted": false,
  "version": 1
}
```

2. **Schema Validation**: Use MongoDB schema validation to enforce the structure of documents based on the version.

#### Example Schema Validation (MongoDB)

```json
{
  "$jsonSchema": {
    "bsonType": "object",
    "required": ["name", "deleted", "version"],
    "properties": {
      "name": {
        "bsonType": "string"
      },
      "deleted": {
        "bsonType": "bool"
      },
      "version": {
        "bsonType": "int"
      }
    }
  }
}
```

### Documentation

All migration and versioning processes MUST be documented clearly in the internal wiki at [https://docs.internal.xentic.io](https://docs.internal.xentic.io). This documentation should include:

- Migration scripts and their purpose.
- Instructions for rolling back to previous versions.
- Deprecation timelines and notices.

By adhering to these migration and versioning standards, Xentic can ensure a smooth transition between versions, maintain backward compatibility, and provide a reliable rollback mechanism for the soft delete functionality in MongoDB.

## FAQ, anti-patterns, and checklists

### FAQ

1. **What is a soft delete?**
   - A soft delete is a method of marking a record as deleted without physically removing it from the database. This allows for easy recovery and auditing of deleted records.

2. **How do I implement a soft delete in MongoDB?**
   - You MUST add a boolean field (e.g., `deleted`) to the document schema. When a record is deleted, set this field to `true` instead of removing the document.

3. **Can I restore a soft-deleted record?**
   - Yes, you can restore a soft-deleted record by updating the `deleted` field back to `false`.

4. **What happens to indexes when a record is soft deleted?**
   - The indexes remain intact, but queries MUST be adjusted to filter out soft-deleted records by checking the `deleted` field.

5. **Should I use TTL indexes with soft deletes?**
   - No, TTL indexes MUST NOT be used with soft deletes as they automatically remove documents after a specified time, which conflicts with the purpose of soft deletes.

6. **How do I query for non-deleted records?**
   - Use the following query to filter out soft-deleted records:
   ```javascript
   db.records.find({ deleted: false });
   ```

7. **Is it safe to perform aggregations on soft-deleted records?**
   - You MUST ensure that your aggregation queries account for the `deleted` field to avoid including soft-deleted records in the results.

8. **What logging is required for soft delete operations?**
   - All soft delete and restore operations MUST be logged with details such as user ID, action, record ID, and status.

9. **How do I handle foreign key relationships with soft deletes?**
   - You MUST manage foreign key relationships carefully, ensuring that related records are not affected by the soft delete of a parent record.

10. **What are the performance implications of soft deletes?**
    - Soft deletes can lead to increased data size and potentially slower queries if not managed properly. Regular maintenance and archiving strategies MUST be implemented.

### Anti-Patterns

| Anti-Pattern                          | Description                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------|
| Hard Deleting Records                 | Permanently removing records instead of marking them as deleted.           |
| Ignoring Soft Delete Field in Queries | Failing to filter out soft-deleted records in queries, leading to incorrect results. |
| Using NULL for Soft Delete             | Using NULL values instead of a boolean field to indicate deletion status.  |
| Not Logging Soft Delete Operations     | Failing to log soft delete and restore actions, making auditing difficult.  |
| Overusing Soft Deletes                 | Relying too heavily on soft deletes instead of proper data lifecycle management. |

### Pre-Merge Checklist

- [ ] Ensure all soft delete implementations are covered by unit tests.
- [ ] Validate that the `deleted` field is correctly added to the schema.
- [ ] Confirm that all queries include checks for the `deleted` field.
- [ ] Review logging implementation for soft delete and restore actions.
- [ ] Ensure documentation is updated with new soft delete functionality.

### Production Checklist

- [ ] Monitor metrics for soft delete and restore operations after deployment.
- [ ] Check for any performance degradation in queries post-deployment.
- [ ] Validate that all logging is functioning as expected.
- [ ] Conduct a post-deployment review to assess any issues or anomalies.
- [ ] Ensure that rollback procedures are in place and tested.
