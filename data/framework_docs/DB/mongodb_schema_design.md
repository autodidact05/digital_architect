# MongoDB Schema Design Standards

## Overview and scope

The purpose of this document is to establish comprehensive MongoDB schema design standards for Xentic's engineering teams. It serves as a guideline to ensure consistency, maintainability, and performance across all services utilizing MongoDB as a data store. This document is intended for software architects, developers, and database administrators who are involved in the design, implementation, and maintenance of MongoDB schemas within Xentic's ecosystem.

### Audience

- Software Architects
- Backend Developers
- Database Administrators
- Quality Assurance Engineers

### Scope

This standard applies to all MongoDB schema designs implemented within Xentic services, including but not limited to:

- User management systems
- Transactional systems
- Reporting and analytics solutions

### Non-goals

This document does NOT aim to cover:

- General MongoDB usage or administration outside of schema design.
- Application-level logic or business rules.
- Performance tuning or indexing strategies, which are addressed in separate documents.

### Glossary

| Term         | Definition                                                                 |
|--------------|-----------------------------------------------------------------------------|
| Schema       | The structure that defines the organization of data in a MongoDB database. |
| Document     | A record in MongoDB, typically represented in BSON format.                  |
| Collection   | A grouping of MongoDB documents, analogous to a table in relational databases.|
| UUID         | Universally Unique Identifier, a 128-bit number used to uniquely identify information.|
| Tenant       | A distinct entity that uses the application, often representing a customer or client. |

### How This Standard Fits the Xentic Platform

This schema design standard is integral to Xentic's platform as it ensures that all services adhere to a unified approach to data modeling. By following these standards, teams can achieve:

- **Consistency**: All services will have a recognizable structure, making it easier to onboard new developers and maintain existing codebases.
- **Scalability**: Proper schema design will facilitate the growth of data without compromising performance.
- **Interoperability**: Services can share and interact with data seamlessly, leveraging shared libraries and adhering to common practices.

### Embedding vs Referencing

| Criterion       | Embed               | Reference            |
|------------------|--------------------|----------------------|
| Cardinality      | One-to-few         | One-to-many          |
| Access pattern    | Always together     | Independently        |
| Document size    | Stays < 16MB       | Could grow unbounded  |

### Standard Document Example

```javascript
{
  _id: ObjectId(),
  externalId: UUID,          // Expose this to API consumers, not _id
  email: String,
  profile: {                 // Embedded — always accessed with user
    firstName: String,
    lastName: String,
  },
  roles: [String],           // Bounded embedded array
  tenantId: ObjectId,        // Reference
  createdAt: Date,
  updatedAt: Date,
}
```

### Anti-Patterns

```javascript
// BAD: Unbounded array
{ userId: ..., messages: [...allMessagesEver] }
// GOOD: Separate collection for messages

// BAD: Exposing ObjectId in API
GET /api/users/64f4b2c8e1234567890abcde
// GOOD: Use externalId (UUID)
GET /api/users/550e8400-e29b-41d4-a716-446655440000
```

### Rules

- **MUST** use `timestamps: true` in Mongoose schemas to automatically manage createdAt and updatedAt fields.
- **MUST** include a `tenantId` field in every tenant-scoped collection to ensure data isolation.
- **SHOULD** prefer embedding for data that is always fetched together and referencing for independent data to optimize performance and maintainability.

## Standards and policies

1. **MUST** use the `com.xentic.<service>` package structure for all MongoDB-related classes and schemas to maintain consistency across services.

2. **MUST NOT** include sensitive information such as passwords or personal identification numbers directly in the database documents. Use secure mechanisms for storing sensitive data.

3. **MUST** define indexes on fields that are frequently queried to enhance performance. The index definitions should be included in the schema definition.

   ```javascript
   const userSchema = new mongoose.Schema({
       email: { type: String, required: true, unique: true },
       // other fields...
   });
   userSchema.index({ email: 1 });
   ```

4. **SHOULD** use UUIDs for external identifiers instead of MongoDB's ObjectId to ensure consistency and ease of integration with external systems.

5. **MUST** ensure that all collections have a clear and descriptive naming convention that reflects the data they store. Use plural nouns for collection names.

   | Collection Name   | Description                     |
   |-------------------|---------------------------------|
   | `users`           | Stores user information         |
   | `transactions`    | Stores transaction records      |
   | `products`        | Stores product details          |

6. **MUST NOT** use unbounded arrays within documents. Instead, create separate collections for items that can grow indefinitely.

   ```javascript
   // BAD: Unbounded array
   { userId: ..., messages: [...allMessagesEver] }
   // GOOD: Separate collection for messages
   ```

7. **SHOULD** use embedded documents for data that is accessed together to optimize read performance, but only if the embedded document size remains under 16MB.

8. **MUST** include a `createdAt` and `updatedAt` field in every schema to track the lifecycle of documents.

   ```javascript
   const productSchema = new mongoose.Schema({
       name: String,
       price: Number,
       createdAt: { type: Date, default: Date.now },
       updatedAt: { type: Date, default: Date.now }
   });
   ```

9. **MUST NOT** expose internal MongoDB identifiers (e.g., ObjectId) in API responses. Always use external identifiers like UUIDs.

10. **SHOULD** document the schema design rationale and any decisions made during the design process to facilitate future maintenance and onboarding.

11. **MUST** validate all incoming data against the schema to prevent invalid data from being stored in the database.

12. **SHOULD** use MongoDB's aggregation framework for complex queries and reporting, rather than relying on multiple queries to achieve the same result.

13. **MUST** ensure that all schema changes are versioned and documented to maintain a clear history of changes and facilitate rollbacks if necessary.

14. **SHOULD** regularly review and refactor schemas to eliminate deprecated fields and optimize the structure as the application evolves.

15. **MUST** use environment-specific configurations for database connections, ensuring that development, testing, and production environments are properly isolated.

   ```yaml
   database:
     uri: ${DB_URI}
     options:
       useNewUrlParser: true
       useUnifiedTopology: true
   ```

16. **MUST NOT** include business logic within the schema definitions. Keep schemas focused solely on data structure.

17. **SHOULD** implement soft deletes by adding a `deletedAt` field instead of removing documents from collections, allowing for data recovery if necessary.

   ```javascript
   const userSchema = new mongoose.Schema({
       name: String,
       deletedAt: { type: Date, default: null }
   });
   ```

18. **MUST** ensure that all database interactions are performed using a consistent data access layer, abstracting the database operations from the business logic.

19. **SHOULD** use transactions for operations that involve multiple collections to maintain data integrity and consistency.

20. **MUST** ensure that all MongoDB schemas are reviewed and approved by a senior architect before deployment to production environments.

## Architecture and design

The architecture of MongoDB schemas at Xentic is designed to ensure scalability, performance, and maintainability. Below is a component diagram and description of data flows, integration points, and failure domains.

```mermaid
graph TD;
    A[Client Application] -->|REST API| B[API Gateway]
    B -->|Service Calls| C[User Service]
    B -->|Service Calls| D[Transaction Service]
    B -->|Service Calls| E[Product Service]
    C -->|MongoDB Queries| F[User Database]
    D -->|MongoDB Queries| G[Transaction Database]
    E -->|MongoDB Queries| H[Product Database]
    C -->|Event| I[Notification Service]
    D -->|Event| I
    E -->|Event| I
    I -->|Push Notifications| J[Client Application]
```

### Data Flows

1. **Client Application** interacts with the **API Gateway** to perform CRUD operations.
2. The **API Gateway** routes requests to the appropriate service (e.g., User, Transaction, Product).
3. Each service interacts with its dedicated MongoDB database for data retrieval and storage.
4. Services emit events to the **Notification Service** for asynchronous processing (e.g., sending notifications).

### Integration Points

- **API Gateway**: Central entry point for all client requests, routing them to the appropriate service.
- **User Service**: Manages user-related data and operations, including authentication and authorization.
- **Transaction Service**: Handles all transactional data, ensuring data integrity through the use of transactions.
- **Product Service**: Manages product-related data, including inventory and pricing.
- **Notification Service**: Listens for events from other services to send notifications to clients.

### Failure Domains

- **Service Failures**: If one service fails (e.g., User Service), the API Gateway should return an appropriate error response without affecting other services.
- **Database Failures**: Each service has its own database; therefore, a failure in one database does not impact others. Implement retries and circuit breakers to handle transient failures.
- **Network Failures**: Use timeouts and fallback mechanisms to ensure that network issues do not cause cascading failures across services.

### Configuration Example

To ensure proper connectivity and configuration for each service, the following YAML configuration should be used:

```yaml
services:
  user:
    database:
      uri: ${USER_DB_URI}
      options:
        useNewUrlParser: true
        useUnifiedTopology: true
  transaction:
    database:
      uri: ${TRANSACTION_DB_URI}
      options:
        useNewUrlParser: true
        useUnifiedTopology: true
  product:
    database:
      uri: ${PRODUCT_DB_URI}
      options:
        useNewUrlParser: true
        useUnifiedTopology: true
```

### Best Practices

- **MUST** ensure that each service has a dedicated database to isolate failure domains and improve maintainability.
- **SHOULD** implement health checks for services and databases to monitor their status and enable quick recovery.
- **MUST NOT** allow direct access to the databases from the client applications; all interactions must go through the API Gateway.
- **SHOULD** utilize logging and monitoring tools to track the performance and health of services and databases.

By adhering to these architecture and design standards, Xentic can ensure a robust and scalable MongoDB implementation that meets the needs of its applications and users.

## Configuration reference

### application.yml

The following configuration outlines the necessary settings for connecting to MongoDB in a typical Xentic application. Ensure that environment variables are set for production values.

```yaml
database:
  uri: ${DB_URI} # Set this in your environment variables
  options:
    useNewUrlParser: true
    useUnifiedTopology: true
    auth:
      username: ${DB_USERNAME} # Set this in your environment variables
      password: ${DB_PASSWORD} # Set this in your environment variables
    replicaSet: ${DB_REPLICA_SET} # Optional for replica sets
    ssl: true # Set to true if using SSL
```

### Terraform Configuration

When provisioning MongoDB resources using Terraform, ensure that the following configurations are included. Replace placeholders with actual values.

```hcl
resource "mongodb_database" "example" {
  name = "example_db"
  provider = mongodb

  settings {
    storage_engine = "wiredTiger"
    version = "4.4"
  }
}

resource "mongodb_user" "example_user" {
  username = var.db_username
  password = var.db_password
  database = mongodb_database.example.name
  roles = ["readWrite"]
}
```

### Environment Variables

The following table outlines the required environment variables for MongoDB configuration, including default and production values.

| Variable Name         | Default Value           | Production Value         | Description                                |
|-----------------------|-------------------------|---------------------------|--------------------------------------------|
| `DB_URI`              | `mongodb://localhost:27017` | `mongodb://prod-db:27017` | Connection URI for MongoDB                 |
| `DB_USERNAME`         | `admin`                 | `prod_user`               | Username for MongoDB authentication        |
| `DB_PASSWORD`         | `password`              | `secure_password`         | Password for MongoDB authentication        |
| `DB_REPLICA_SET`      | `null`                  | `prod-replica-set`       | Replica set name if applicable             |
| `DB_SSL`              | `false`                 | `true`                    | Enable SSL for connections                 |

### Example MongoDB Schema Configuration

Here is an example of a MongoDB schema configuration that adheres to the standards outlined in this document. This schema includes timestamps and a tenantId.

```javascript
const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
    email: { type: String, required: true, unique: true },
    name: { type: String, required: true },
    tenantId: { type: String, required: true },
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now }
}, { timestamps: true });

userSchema.index({ email: 1 });

module.exports = mongoose.model('User', userSchema);
```

### SQL Equivalent for Reference

While MongoDB is a NoSQL database, understanding the SQL equivalent can be helpful for those transitioning from relational databases. Below is an SQL equivalent for creating a similar table structure.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Additional Configuration Considerations

- **MUST** ensure that all configurations are stored securely, especially sensitive information such as database credentials.
- **SHOULD** utilize a secrets management tool (e.g., HashiCorp Vault) for managing sensitive environment variables.
- **MUST** validate that the database connection settings are correctly configured in all environments (development, testing, production).

By following these configuration standards, Xentic can ensure a secure, efficient, and maintainable MongoDB setup across its services.

## Implementation guide

To implement MongoDB schemas effectively at Xentic, follow these step-by-step guidelines, ensuring adherence to the established standards.

### Step 1: Define the Schema

Define a schema using Mongoose, ensuring that all required fields are included and that appropriate data types are specified. For example, consider a `Product` schema:

```javascript
const mongoose = require('mongoose');

const productSchema = new mongoose.Schema({
    name: { type: String, required: true },
    description: { type: String, required: true },
    price: { type: Number, required: true, min: 0 },
    tenantId: { type: String, required: true },
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now }
}, { timestamps: true });

productSchema.index({ name: 1, tenantId: 1 }); // Composite index for efficient queries

module.exports = mongoose.model('Product', productSchema);
```

### Step 2: Create Data Access Layer

Implement a data access layer to abstract database operations. This layer should include functions for CRUD operations. Here’s an example for the `Product` service:

```javascript
const Product = require('./models/product');

class ProductService {
    async createProduct(productData) {
        const product = new Product(productData);
        return await product.save();
    }

    async getProductById(productId) {
        return await Product.findById(productId).exec();
    }

    async updateProduct(productId, updateData) {
        return await Product.findByIdAndUpdate(productId, updateData, { new: true }).exec();
    }

    async deleteProduct(productId) {
        return await Product.findByIdAndDelete(productId).exec();
    }

    async getAllProducts(tenantId) {
        return await Product.find({ tenantId }).exec();
    }
}

module.exports = new ProductService();
```

### Step 3: Implement Transaction Logic

For operations involving multiple collections, implement transaction logic to ensure data integrity. Here’s an example using Mongoose transactions:

```javascript
const mongoose = require('mongoose');
const ProductService = require('./productService');

async function createProductWithTransaction(productData) {
    const session = await mongoose.startSession();
    session.startTransaction();

    try {
        const product = await ProductService.createProduct(productData);
        // Additional operations can be added here
        await session.commitTransaction();
        return product;
    } catch (error) {
        await session.abortTransaction();
        throw error; // Handle error appropriately
    } finally {
        session.endSession();
    }
}
```

### Step 4: Configure Environment Variables

Ensure that all necessary environment variables are set in your `.env` file or through your deployment pipeline. Here’s an example:

```plaintext
DB_URI=mongodb://localhost:27017/xentic
DB_USERNAME=admin
DB_PASSWORD=secure_password
DB_REPLICA_SET=null
DB_SSL=false
```

### Step 5: Set Up Indexes

Indexes are crucial for optimizing query performance. Ensure that you create indexes on fields that are frequently queried. For example, in the `Product` schema, we created a composite index on `name` and `tenantId`.

### Step 6: Implement Validation

Incorporate validation logic to ensure data integrity before saving to the database. You can use Mongoose's built-in validation or implement custom validation logic in your service layer.

### Step 7: Logging and Monitoring

Implement logging for all database operations to track performance and identify issues. Use a logging library such as Winston or Bunyan:

```javascript
const winston = require('winston');

const logger = winston.createLogger({
    level: 'info',
    format: winston.format.json(),
    transports: [
        new winston.transports.File({ filename: 'error.log', level: 'error' }),
        new winston.transports.Console()
    ]
});

// Example of logging a product creation
async function createProduct(productData) {
    logger.info('Creating product', { productData });
    return await ProductService.createProduct(productData);
}
```

### Step 8: Testing

Ensure that you implement unit tests for your data access layer and service methods. Use a testing framework like Jest or Mocha to validate functionality.

```javascript
const ProductService = require('./productService');

describe('ProductService', () => {
    it('should create a product', async () => {
        const productData = { name: 'Test Product', description: 'Test Description', price: 100, tenantId: 'tenant123' };
        const product = await ProductService.createProduct(productData);
        expect(product).toHaveProperty('_id');
        expect(product.name).toBe('Test Product');
    });
});
```

### Step 9: Review and Approval

Before deploying any schema changes to production, ensure that all schemas and related code are reviewed and approved by a senior architect.

### Summary of Steps

- Define the schema using Mongoose.
- Create a data access layer for CRUD operations.
- Implement transaction logic for multi-collection operations.
- Configure environment variables securely.
- Set up appropriate indexes for performance.
- Implement validation logic.
- Incorporate logging and monitoring.
- Write unit tests for all service methods.
- Seek review and approval before production deployment.

By following this implementation guide, Xentic can maintain high standards in MongoDB schema design and ensure robust, scalable applications.

## Security requirements

To ensure the security of MongoDB databases within Xentic, the following security requirements must be adhered to:

### Threat Model Summary

- **Data Breach**: Unauthorized access to sensitive data.
- **Data Corruption**: Malicious or accidental modification of data.
- **Denial of Service (DoS)**: Disruption of database availability.
- **Insider Threats**: Malicious actions by employees or contractors.

### Authentication and Authorization

- **MUST** use MongoDB's built-in authentication mechanisms. 
- **MUST NOT** use default usernames and passwords. Always configure unique credentials for each environment.
- **SHOULD** implement role-based access control (RBAC) to restrict user permissions based on the principle of least privilege.
  
Example of creating a user with specific roles:

```javascript
db.createUser({
    user: "appUser",
    pwd: "securePassword123",
    roles: [
        { role: "readWrite", db: "appDatabase" },
        { role: "dbAdmin", db: "appDatabase" }
    ]
});
```

### Secrets Management

- **MUST** store sensitive information, such as database credentials, in a secure secrets management tool (e.g., HashiCorp Vault, AWS Secrets Manager).
- **SHOULD** use environment variables to inject secrets into applications at runtime.
  
Example of using environment variables in a `.env` file:

```plaintext
DB_URI=mongodb://appUser:securePassword123@localhost:27017/appDatabase
```

### Input Validation

- **MUST** validate all user inputs to prevent injection attacks and ensure data integrity.
- **SHOULD** use libraries like Joi or express-validator for server-side validation.
  
Example of input validation using Joi:

```javascript
const Joi = require('joi');

const userSchema = Joi.object({
    email: Joi.string().email().required(),
    name: Joi.string().min(3).required(),
    tenantId: Joi.string().required()
});

// Validate input
const { error } = userSchema.validate(userInput);
if (error) {
    throw new Error(error.details[0].message);
}
```

### Audit Logging

- **MUST** implement audit logging for all database operations, including create, read, update, and delete actions.
- **SHOULD** log the following information:
  - User ID
  - Timestamp
  - Operation type
  - Affected resource
  - Result of the operation (success/failure)

Example of logging a database operation:

```javascript
const logger = require('winston');

async function logDatabaseOperation(userId, operation, resource, success) {
    const logEntry = {
        userId,
        operation,
        resource,
        success,
        timestamp: new Date()
    };
    logger.info('Database Operation', logEntry);
}

// Usage
await logDatabaseOperation('user123', 'create', 'User', true);
```

### Summary of Security Practices

| Security Aspect           | Requirement                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| Authentication            | Use MongoDB authentication; avoid defaults.                               |
| Authorization             | Implement RBAC; restrict permissions.                                      |
| Secrets Management        | Use secure tools for storing credentials; utilize environment variables.   |
| Input Validation          | Validate all inputs to prevent injection attacks.                          |
| Audit Logging             | Log all database operations with relevant details.                        |

By adhering to these security requirements, Xentic can significantly reduce the risk of security breaches and ensure the integrity and confidentiality of its MongoDB databases.

## Testing strategy

To ensure the quality and reliability of MongoDB schema designs and their associated services, Xentic MUST implement a comprehensive testing strategy that includes unit tests, integration tests, and contract tests. The following outlines the necessary components of this strategy, including coverage targets and example test classes.

### 1. Unit Tests

Unit tests are essential for validating individual functions and methods within your service layer. Each function should have a corresponding unit test that verifies its expected behavior.

**Coverage Target:** 
- A minimum of 80% code coverage for all service methods.

**Example Test Class:**

```javascript
const ProductService = require('./productService');
const mongoose = require('mongoose');

describe('ProductService Unit Tests', () => {
    beforeAll(async () => {
        await mongoose.connect('mongodb://localhost:27017/test', { useNewUrlParser: true, useUnifiedTopology: true });
    });

    afterAll(async () => {
        await mongoose.connection.dropDatabase();
        await mongoose.connection.close();
    });

    it('should create a product', async () => {
        const productData = { name: 'Test Product', description: 'Test Description', price: 100, tenantId: 'tenant123' };
        const product = await ProductService.createProduct(productData);
        expect(product).toHaveProperty('_id');
        expect(product.name).toBe('Test Product');
    });

    it('should retrieve a product by ID', async () => {
        const productData = { name: 'Another Product', description: 'Another Description', price: 150, tenantId: 'tenant123' };
        const createdProduct = await ProductService.createProduct(productData);
        const retrievedProduct = await ProductService.getProductById(createdProduct._id);
        expect(retrievedProduct.name).toBe('Another Product');
    });
});
```

### 2. Integration Tests

Integration tests validate the interaction between different components, such as the service layer and the database. These tests ensure that the entire flow works as expected.

**Coverage Target:** 
- At least 75% coverage for integration tests.

**Example Test Class:**

```javascript
const request = require('supertest');
const app = require('../app'); // Your Express app
const mongoose = require('mongoose');

describe('Product API Integration Tests', () => {
    beforeAll(async () => {
        await mongoose.connect('mongodb://localhost:27017/test', { useNewUrlParser: true, useUnifiedTopology: true });
    });

    afterAll(async () => {
        await mongoose.connection.dropDatabase();
        await mongoose.connection.close();
    });

    it('should create a product via API', async () => {
        const response = await request(app)
            .post('/api/products')
            .send({ name: 'API Product', description: 'API Description', price: 200, tenantId: 'tenant123' });
        expect(response.status).toBe(201);
        expect(response.body).toHaveProperty('_id');
        expect(response.body.name).toBe('API Product');
    });

    it('should retrieve all products', async () => {
        const response = await request(app).get('/api/products?tenantId=tenant123');
        expect(response.status).toBe(200);
        expect(response.body).toBeInstanceOf(Array);
    });
});
```

### 3. Contract Tests

Contract tests ensure that the services adhere to the expected API contracts, particularly when integrating with external services or APIs. These tests validate that the service's input and output conform to predefined schemas.

**Coverage Target:** 
- 100% adherence to defined contracts.

**Example Test Class:**

```javascript
const { validate } = require('jsonschema');
const productSchema = require('../schemas/productSchema'); // JSON Schema for product
const ProductService = require('./productService');

describe('Product Service Contract Tests', () => {
    it('should adhere to product schema', async () => {
        const productData = { name: 'Contract Product', description: 'Contract Description', price: 250, tenantId: 'tenant123' };
        const createdProduct = await ProductService.createProduct(productData);
        const validationResult = validate(createdProduct, productSchema);
        expect(validationResult.valid).toBe(true);
    });
});
```

### Summary of Testing Strategy

| Test Type        | Purpose                                        | Coverage Target |
|------------------|------------------------------------------------|------------------|
| Unit Tests       | Validate individual functions and methods      | 80%               |
| Integration Tests| Validate interaction between components        | 75%               |
| Contract Tests   | Ensure adherence to API contracts              | 100%              |

By implementing this testing strategy, Xentic will ensure that its MongoDB schema designs and related services are robust, maintainable, and aligned with quality standards.

## Observability and operations

To ensure optimal performance and reliability of MongoDB databases, Xentic MUST implement a robust observability and operations strategy that encompasses metrics, logs, traces, dashboards, alerts, and service level objectives (SLOs). The following outlines the necessary components of this strategy.

### 1. Metrics

Metrics provide insights into the performance and health of MongoDB instances. Xentic MUST collect the following key metrics:

- **Operation Counts**: Count of CRUD operations (create, read, update, delete).
- **Latency**: Time taken for operations to complete.
- **Memory Usage**: Amount of memory used by MongoDB.
- **Connections**: Number of active connections to the database.
- **Disk I/O**: Read and write operations on the disk.

**Example of Prometheus metrics configuration:**

```yaml
mongodb_exporter:
  enabled: true
  config:
    mongodb_uri: "mongodb://appUser:securePassword123@localhost:27017/appDatabase"
    metrics:
      - operation_counts
      - latency
      - memory_usage
      - connections
      - disk_io
```

### 2. Logs

Xentic MUST implement structured logging for all database interactions. Logs should include:

- Timestamp
- User ID
- Operation type
- Affected resource
- Success or failure status

**Example of logging configuration in Winston:**

```javascript
const winston = require('winston');

const logger = winston.createLogger({
    level: 'info',
    format: winston.format.json(),
    transports: [
        new winston.transports.File({ filename: 'database.log' })
    ]
});

// Example log entry
logger.info('Database Operation', {
    userId: 'user123',
    operation: 'create',
    resource: 'User',
    success: true,
    timestamp: new Date()
});
```

### 3. Traces

Distributed tracing MUST be implemented to track requests as they flow through the system. This helps identify bottlenecks and performance issues.

- **MUST** use tools like OpenTelemetry or Jaeger for tracing.
- **SHOULD** instrument all database calls to capture trace data.

**Example of tracing with OpenTelemetry:**

```javascript
const { trace } = require('@opentelemetry/api');

async function createUser(userData) {
    const span = trace.getTracer('mongodb-tracer').startSpan('createUser');
    try {
        const user = await UserModel.create(userData);
        span.setAttribute('user.id', user._id);
        return user;
    } finally {
        span.end();
    }
}
```

### 4. Dashboards

Dashboards MUST be created to visualize metrics and logs. Xentic SHOULD use Grafana or similar tools to create dashboards that display:

- Database performance metrics
- Error rates
- Latency trends
- Resource utilization

**Example of Grafana dashboard configuration:**

```json
{
  "title": "MongoDB Performance Dashboard",
  "panels": [
    {
      "type": "graph",
      "title": "Operation Latency",
      "targets": [
        {
          "target": "mongodb_operation_latency"
        }
      ]
    },
    {
      "type": "graph",
      "title": "Active Connections",
      "targets": [
        {
          "target": "mongodb_active_connections"
        }
      ]
    }
  ]
}
```

### 5. Alerts

Xentic MUST implement alerting mechanisms to notify the team of critical issues. Alerts should be based on defined thresholds for key metrics, such as:

- High latency (e.g., > 200ms)
- Increased error rates (e.g., > 5% of requests)
- Memory usage exceeding 80%

**Example of alert configuration in Prometheus:**

```yaml
groups:
  - name: mongodb-alerts
    rules:
      - alert: HighLatency
        expr: mongodb_operation_latency > 0.2
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High latency detected in MongoDB operations"
          description: "Latency is above 200ms for more than 5 minutes."
```

### 6. Service Level Objectives (SLOs)

Xentic MUST define SLOs for MongoDB operations to ensure reliability and performance. SLOs should include:

- **Availability**: 99.9% uptime
- **Latency**: 95th percentile latency < 200ms
- **Error Rate**: < 1% of requests result in errors

**Example of SLO documentation:**

| SLO Metric        | Target Value  | Measurement Period |
|-------------------|---------------|---------------------|
| Availability       | 99.9%         | Monthly             |
| Latency (95th %)  | < 200ms       | Monthly             |
| Error Rate         | < 1%          | Monthly             |

### 7. On-call Runbook Steps

In the event of an incident, the on-call engineer MUST follow these steps:

1. **Identify** the issue using dashboards and alerts.
2. **Assess** the impact on users and services.
3. **Gather logs** and traces related to the incident.
4. **Communicate** with stakeholders about the issue and expected resolution time.
5. **Implement** a fix or workaround as necessary.
6. **Monitor** the system post-resolution to ensure stability.
7. **Document** the incident and resolution steps for future reference.

By adhering to these observability and operations standards, Xentic will ensure that its MongoDB databases are reliable, performant, and maintainable, leading to a better experience for users and stakeholders alike.

## Migration and versioning

Xentic MUST establish a robust migration and versioning strategy for MongoDB schemas to ensure smooth upgrades, maintain backward compatibility, and facilitate rollback procedures when necessary. This section outlines the guidelines for managing schema migrations, deprecation policies, and versioning practices.

### 1. Migration Strategy

- **MUST** use a migration tool such as [Migrate](https://github.com/golang-migrate/migrate) or [MongoDB Migrations](https://github.com/mongodb/mongo-migrate) to manage schema changes.
- **MUST** maintain a version history of migrations in a dedicated collection (e.g., `migrations`).
- **MUST NOT** apply migrations directly to production without testing in a staging environment.

**Example Migration Document:**

```json
{
  "version": 20231001,
  "description": "Add new field 'category' to products collection",
  "applied_at": "2023-10-01T12:00:00Z"
}
```

### 2. Upgrade Paths

- **MUST** define clear upgrade paths for each version of the schema.
- **SHOULD** provide detailed documentation outlining changes, including new fields, data types, and any deprecated fields.

**Example Upgrade Path Documentation:**

| Version | Changes                                      | Notes                          |
|---------|----------------------------------------------|--------------------------------|
| 1.0     | Initial schema creation                      |                                |
| 1.1     | Added `category` field to `products`        | Required for product categorization |
| 1.2     | Deprecated `description` field              | Use `details` instead         |

### 3. Deprecation Policy

- **MUST** deprecate fields gradually to avoid breaking changes.
- **SHOULD** provide a deprecation notice in the schema documentation and through API responses.
- **MUST NOT** remove deprecated fields until at least two major version releases have occurred.

**Example Deprecation Notice:**

```json
{
  "field": "description",
  "status": "deprecated",
  "replacement": "details",
  "deprecation_since": "1.1",
  "removal_target": "2.0"
}
```

### 4. Backward Compatibility

- **MUST** ensure that new schema changes do not break existing functionality.
- **SHOULD** use default values for new fields to maintain compatibility with existing documents.
- **MUST NOT** change the data type of existing fields in a way that breaks compatibility.

**Example of Adding a New Field with Default Value:**

```javascript
db.products.updateMany(
  {},
  { $set: { category: "general" } }
);
```

### 5. Rollback Procedures

In case of a failed migration or issues arising from schema changes, Xentic MUST have a rollback strategy in place:

- **MUST** create a rollback migration for every upgrade migration.
- **MUST** test rollback procedures in a staging environment before applying to production.
- **SHOULD** maintain a backup of the database before applying any migrations.

**Example Rollback Migration:**

```json
{
  "version": 20231001,
  "description": "Rollback - Remove 'category' field from products collection",
  "rollback": [
    {
      "operation": "remove",
      "field": "category"
    }
  ]
}
```

### 6. Versioning Best Practices

- **MUST** use Semantic Versioning (SemVer) for schema versions (e.g., MAJOR.MINOR.PATCH).
- **SHOULD** increment the MAJOR version for incompatible changes, MINOR for backward-compatible changes, and PATCH for bug fixes.
- **MUST** document all changes in a CHANGELOG file.

**Example CHANGELOG Entry:**

```markdown
# Changelog

## [1.1.0] - 2023-10-01
### Added
- New field `category` to `products` collection.

### Deprecated
- Field `description` in `products` collection, use `details` instead.
```

By adhering to these migration and versioning standards, Xentic will ensure that its MongoDB schemas remain maintainable, backward-compatible, and resilient to changes, thus providing a seamless experience for developers and users alike.

## FAQ, anti-patterns, and checklists

### FAQ

1. **What is the maximum document size in MongoDB?**
   - The maximum BSON document size is 16 MB.

2. **How should I handle relationships between collections?**
   - Use references for one-to-many relationships and embedding for one-to-few relationships. 

3. **What indexing strategies should I use?**
   - Index fields that are frequently queried, especially those used in filters, sorts, or joins.

4. **How can I ensure data consistency?**
   - Use transactions for multi-document operations, and ensure proper validation rules are in place.

5. **What is the best way to handle schema changes?**
   - Use migration tools and follow the migration and versioning standards outlined in this document.

6. **How do I handle large datasets?**
   - Consider sharding your collections and using pagination for queries.

7. **What is the recommended way to query documents?**
   - Use the most efficient query operators and avoid using `$where` for performance reasons.

8. **How can I improve query performance?**
   - Analyze slow queries using the MongoDB profiler and optimize indexes accordingly.

9. **Should I use the aggregation framework?**
   - Yes, the aggregation framework is powerful for data transformation and analysis but should be used judiciously to avoid performance hits.

10. **What should I do if I experience performance issues?**
    - Monitor your database performance metrics, check for slow queries, and optimize indexes or sharding strategies as necessary.

### Anti-patterns

| Anti-pattern                     | Description                                                                                     | Recommendation                                   |
|----------------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------|
| Storing large binary files       | Storing large files directly in MongoDB can lead to performance degradation.                  | Use GridFS for large files.                      |
| Over-indexing                    | Creating too many indexes can slow down write operations.                                     | Index only what is necessary.                    |
| Not using transactions            | Performing multi-document operations without transactions can lead to data inconsistency.     | Always use transactions for critical operations. |
| Using `$where` for queries      | `$where` can lead to performance issues as it evaluates JavaScript code.                      | Use native query operators instead.              |
| Ignoring schema validation       | Not enforcing schema validation can lead to inconsistent data.                                 | Always define validation rules.                   |
| Hardcoding connection strings     | Hardcoding database connection strings can lead to security vulnerabilities.                   | Use environment variables for configuration.     |
| Not monitoring performance        | Failing to monitor performance can result in unnoticed slowdowns and outages.                  | Implement monitoring and alerting solutions.     |
| Using unbounded `$limit`        | Using unbounded `$limit` can lead to excessive memory usage.                                   | Always set a reasonable limit.                   |

### Pre-Merge Checklist

- [ ] Code adheres to Xentic's Java package structure (`com.xentic.<service>`).
- [ ] All new features are covered by unit tests.
- [ ] Documentation is updated to reflect changes.
- [ ] Migration scripts are created and tested.
- [ ] Schema validation rules are defined and implemented.
- [ ] Performance tests are conducted for critical queries.
- [ ] Code review completed by at least one other engineer.

### Production Checklist

- [ ] Backup of the current database is taken before deployment.
- [ ] All migrations are tested in a staging environment.
- [ ] Monitoring and alerting systems are in place and configured.
- [ ] Rollback procedures are documented and ready.
- [ ] Deployment is scheduled during low-traffic periods.
- [ ] Post-deployment verification plan is established.
- [ ] Notify stakeholders about the deployment and expected changes.
