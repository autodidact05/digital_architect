# Bean Validation Standards — Spring Boot

## Overview and scope

The purpose of this document is to establish the standards for implementing Bean Validation in Spring Boot applications at Xentic. This standard aims to ensure that all developers adhere to a consistent approach to validation across various services, enhancing code quality, maintainability, and reliability.

### Audience

This document is intended for:
- Software Engineers
- Technical Leads
- Architects
- Quality Assurance Engineers

### Scope

This standard covers:
- Usage of Bean Validation annotations
- Custom validation logic
- Integration with Spring Boot
- Error handling and response formatting
- Configuration and property management

### Non-goals

This standard does NOT cover:
- General Spring Boot application development practices
- Non-Bean Validation related error handling
- Frontend validation techniques

### Glossary

| Term                | Definition                                                                 |
|---------------------|----------------------------------------------------------------------------|
| Bean Validation      | A specification for validating JavaBeans properties using annotations.     |
| Spring Boot         | A framework that simplifies the development of Java applications.          |
| Annotations         | Metadata added to Java classes, methods, or fields to provide additional information. |
| Constraint          | A rule that defines the conditions under which a JavaBean property is considered valid. |

### How This Standard Fits the Xentic Platform

At Xentic, we prioritize quality and consistency across our services. This Bean Validation standard aligns with our broader engineering principles by ensuring that:
- Validation logic is centralized and reusable.
- Services communicate validation errors in a standardized format.
- Developers can easily understand and implement validation rules.

By adhering to these standards, teams can ensure that their applications are robust and maintainable, reducing the likelihood of defects and improving overall user experience.

### Example Configuration

To enable Bean Validation in a Spring Boot application, ensure the following dependencies are included in your `pom.xml`:

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>
```

### Example Bean Validation Usage

Here is an example of how to use Bean Validation annotations in a Java class:

```java
package com.xentic.user;

import javax.validation.constraints.Email;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Size;

public class UserDTO {

    @NotBlank(message = "Username must not be blank")
    private String username;

    @Email(message = "Email should be valid")
    private String email;

    @Size(min = 6, message = "Password must be at least 6 characters long")
    private String password;

    // Getters and Setters
}
```

### Validation Error Handling Example

To handle validation errors globally, implement a `@ControllerAdvice` class:

```java
package com.xentic.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

import java.util.HashMap;
import java.util.Map;

@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, String>> handleValidationExceptions(MethodArgumentNotValidException ex) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getFieldErrors().forEach(error -> 
            errors.put(error.getField(), error.getDefaultMessage()));
        return new ResponseEntity<>(errors, HttpStatus.BAD_REQUEST);
    }
}
```

By following these standards, Xentic aims to create a consistent and efficient approach to Bean Validation across all services, ensuring high-quality software delivery.

## Standards and policies

1. **MUST** use Java Bean Validation annotations (e.g., `@NotNull`, `@Size`, `@Email`) to enforce validation rules on all input data models within the `com.xentic.<service>` packages.

2. **MUST NOT** use validation annotations directly on the entity classes that are mapped to the database. Instead, create separate DTO (Data Transfer Object) classes in `com.xentic.<service>.dto` for validation purposes.

3. **SHOULD** provide meaningful error messages in validation annotations to enhance user experience. For example:
   ```java
   @NotBlank(message = "Username must not be blank")
   private String username;
   ```

4. **MUST** implement a global exception handler using `@ControllerAdvice` to manage validation errors consistently across all controllers. This ensures that all validation errors are captured and formatted uniformly.

5. **MUST NOT** return raw validation error messages to the client. Instead, format the response in a structured manner, such as:
   ```json
   {
       "errors": {
           "username": "Username must not be blank",
           "email": "Email should be valid"
       }
   }
   ```

6. **SHOULD** log validation errors at the appropriate logging level (e.g., WARN or ERROR) to facilitate debugging and auditing.

7. **MUST** use the `@Valid` annotation in controller methods to trigger validation on incoming request bodies. For example:
   ```java
   @PostMapping("/users")
   public ResponseEntity<User> createUser(@Valid @RequestBody UserDTO userDTO) {
       // Implementation
   }
   ```

8. **SHOULD** utilize custom validation annotations for complex validation logic that cannot be handled by standard annotations. Custom annotations should be placed in the `com.xentic.<service>.validation` package.

9. **MUST** ensure that all validation logic is accompanied by unit tests to verify correct behavior. Use JUnit and Mockito for testing validation constraints.

10. **MUST NOT** hard-code validation messages. Instead, externalize them in a properties file to support internationalization and easier maintenance. For example, create a `messages.properties` file:
    ```properties
    username.blank=Username must not be blank
    email.invalid=Email should be valid
    ```

11. **SHOULD** document all custom validation annotations and their usage in the service’s README file to ensure clarity for all developers.

12. **MUST** adhere to the naming conventions for validation groups when using `@GroupSequence` to define the order of validation checks.

13. **SHOULD** consider performance implications when using complex validation logic. Keep validation checks efficient to avoid slowing down the application.

14. **MUST** ensure that all validation-related dependencies are included in the `pom.xml` as specified in the example configuration section.

15. **MUST NOT** mix validation logic with business logic. Keep validation and business processing separate to maintain clean architecture.

16. **SHOULD** review and update validation rules periodically as part of the service's maintenance cycle to accommodate changes in business requirements.

By following these standards and policies, Xentic will ensure a robust and maintainable approach to Bean Validation across all services, leading to higher quality and more reliable software products.

## Architecture and design

The architecture for implementing Bean Validation in Spring Boot applications at Xentic is designed to ensure a clear separation of concerns, maintainability, and scalability. The following diagram illustrates the component interactions and data flows within the system.

```mermaid
graph TD;
    A[Client] -->|HTTP Request| B[Controller]
    B -->|@Valid| C[Service]
    C -->|Business Logic| D[Repository]
    C -->|Validation Errors| E[Global Exception Handler]
    E -->|Formatted Errors| F[Client]
```

### Data Flows

1. **Client to Controller**: The client sends an HTTP request containing data that needs validation.
2. **Controller to Service**: The controller uses the `@Valid` annotation to trigger validation on the incoming request body before passing it to the service layer.
3. **Service to Repository**: If validation passes, the service layer processes the business logic and interacts with the repository to persist data.
4. **Validation Errors**: If validation fails, the global exception handler captures the validation errors and formats them into a structured response.
5. **Response to Client**: The formatted error messages are sent back to the client for display.

### Integration Points

- **Spring Boot**: The framework provides built-in support for Bean Validation through the `spring-boot-starter-validation` dependency.
- **ControllerAdvice**: The global exception handler is integrated using `@ControllerAdvice`, allowing centralized error management across all controllers.
- **DTOs**: Data Transfer Objects (DTOs) are used to separate validation logic from entity classes, ensuring that validation rules are applied consistently.

### Failure Domains

1. **Validation Failures**: If the input data does not meet the specified validation criteria, the global exception handler will return a structured error response.
2. **Service Layer Issues**: Any business logic errors that occur during processing will also be handled by the global exception handler, ensuring that the client receives meaningful feedback.
3. **Database Interaction**: Failures during database operations (e.g., connection issues, constraint violations) should be managed separately but can also trigger validation error responses if applicable.

### Example Configuration

To configure Bean Validation in your Spring Boot application, ensure the following properties are set in your `application.yml`:

```yaml
spring:
  validation:
    enabled: true
    fail-fast: true
```

### Example SQL for Validation

When designing database schemas, ensure that constraints align with your validation rules. For example:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    CONSTRAINT username_not_blank CHECK (username <> ''),
    CONSTRAINT email_valid CHECK (email LIKE '%_@__%.__%')
);
```

### Summary

By adhering to this architecture and design framework, Xentic ensures that Bean Validation is effectively integrated within Spring Boot applications. This not only enhances the quality of the software but also provides a clear and maintainable structure for developers to follow.

## Configuration reference

### application.yml

The following configuration settings are recommended for enabling and customizing Bean Validation in your Spring Boot application. 

```yaml
spring:
  validation:
    enabled: true # Enables Bean Validation
    fail-fast: true # Fails immediately on validation errors
  messages:
    basename: messages # Base name for message properties
```

### Environment Variables

| Variable Name                   | Default Value | Production Value |
|----------------------------------|---------------|------------------|
| `SPRING_VALIDATION_ENABLED`      | `true`        | `true`           |
| `SPRING_VALIDATION_FAIL_FAST`    | `false`       | `true`           |
| `SPRING_MESSAGES_BASENAME`       | `messages`    | `messages`       |

### Terraform Configuration

To manage the environment variables through Terraform, use the following configuration:

```hcl
resource "aws_lambda_function" "my_lambda" {
  function_name = "my_lambda_function"
  handler       = "com.xentic.MyHandler::handleRequest"
  runtime       = "java11"

  environment {
    SPRING_VALIDATION_ENABLED = "true"
    SPRING_VALIDATION_FAIL_FAST = "true"
    SPRING_MESSAGES_BASENAME = "messages"
  }
}
```

### Validation Messages Properties

Ensure that validation messages are externalized in a properties file located at `src/main/resources/messages.properties`. Below is an example of the contents:

```properties
username.blank=Username must not be blank
email.invalid=Email should be valid
password.size=Password must be at least 6 characters long
```

### Example SQL for Database Constraints

Ensure that your database schema aligns with the validation rules defined in your application. Here’s an example SQL schema for a `users` table:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    CONSTRAINT username_not_blank CHECK (username <> ''),
    CONSTRAINT email_valid CHECK (email LIKE '%_@__%.__%'),
    CONSTRAINT password_size CHECK (LENGTH(password) >= 6)
);
```

### Summary of Configuration

- **application.yml**: Must include settings for enabling validation and specifying message properties.
- **Environment Variables**: Should be configured to allow flexibility between development and production environments.
- **Terraform**: Must be used to manage environment variables for cloud deployments.
- **Database Schema**: Must reflect validation rules to ensure data integrity.

By following these configuration standards, Xentic ensures that Bean Validation is effectively integrated and managed across all services, leading to consistent and reliable application behavior.

## Implementation guide

To implement Bean Validation in your Spring Boot application at Xentic, follow these step-by-step guidelines. This implementation guide includes examples of DTOs, custom validation annotations, and unit tests.

### Step 1: Create a UserDTO Class

The first step is to create a Data Transfer Object (DTO) that will hold the user data and apply validation annotations.

```java
package com.xentic.user.dto;

import javax.validation.constraints.Email;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Size;

public class UserDTO {

    @NotBlank(message = "{username.blank}")
    private String username;

    @Email(message = "{email.invalid}")
    @NotBlank(message = "{email.blank}")
    private String email;

    @Size(min = 6, message = "{password.size}")
    private String password;

    // Getters and Setters
    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }
}
```

### Step 2: Create a Custom Validation Annotation

In cases where built-in annotations are insufficient, create a custom validation annotation. For example, a custom annotation to validate the username format.

```java
package com.xentic.user.validation;

import javax.validation.Constraint;
import javax.validation.Payload;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Constraint(validatedBy = UsernameValidator.class)
@Target({ ElementType.FIELD, ElementType.METHOD, ElementType.PARAMETER, ElementType.ANNOTATION_TYPE })
@Retention(RetentionPolicy.RUNTIME)
public @interface ValidUsername {
    String message() default "{username.invalid}";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}
```

### Step 3: Implement the Custom Validator

Next, implement the logic for the custom validator.

```java
package com.xentic.user.validation;

import javax.validation.ConstraintValidator;
import javax.validation.ConstraintValidatorContext;

public class UsernameValidator implements ConstraintValidator<ValidUsername, String> {

    @Override
    public boolean isValid(String username, ConstraintValidatorContext context) {
        return username != null && username.matches("^[a-zA-Z0-9._-]{3,}$");
    }
}
```

### Step 4: Update UserDTO to Use the Custom Annotation

Use the custom annotation in the `UserDTO` class.

```java
@ValidUsername
private String username;
```

### Step 5: Create a UserController

Create a controller that handles user registration and uses the `@Valid` annotation to trigger validation.

```java
package com.xentic.user.controller;

import com.xentic.user.dto.UserDTO;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @PostMapping
    public ResponseEntity<String> createUser(@Validated @RequestBody UserDTO userDTO) {
        // Logic to save user
        return ResponseEntity.ok("User created successfully");
    }
}
```

### Step 6: Create a Global Exception Handler

Implement a global exception handler to manage validation errors.

```java
package com.xentic.user.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

import java.util.HashMap;
import java.util.Map;

@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, String>> handleValidationExceptions(MethodArgumentNotValidException ex) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getFieldErrors().forEach(error -> {
            errors.put(error.getField(), error.getDefaultMessage());
        });
        return new ResponseEntity<>(errors, HttpStatus.BAD_REQUEST);
    }
}
```

### Step 7: Write Unit Tests for Validation

Finally, write unit tests to ensure the validation logic works as expected.

```java
package com.xentic.user.validation;

import com.xentic.user.dto.UserDTO;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.validation.BeanPropertyBindingResult;
import org.springframework.validation.Validator;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest
public class UserValidationTests {

    private final Validator validator;

    public UserValidationTests(Validator validator) {
        this.validator = validator;
    }

    @Test
    public void whenUsernameIsValid_thenNoValidationErrors() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("validUser123");
        userDTO.setEmail("user@example.com");
        userDTO.setPassword("password");

        BeanPropertyBindingResult bindingResult = new BeanPropertyBindingResult(userDTO, "userDTO");
        validator.validate(userDTO, bindingResult);

        assertFalse(bindingResult.hasErrors());
    }

    @Test
    public void whenUsernameIsInvalid_thenValidationErrors() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("us"); // Invalid username
        userDTO.setEmail("user@example.com");
        userDTO.setPassword("password");

        BeanPropertyBindingResult bindingResult = new BeanPropertyBindingResult(userDTO, "userDTO");
        validator.validate(userDTO, bindingResult);

        assertTrue(bindingResult.hasErrors());
    }
}
```

### Summary of Implementation Steps

1. **Create DTO**: Define a `UserDTO` class with validation annotations.
2. **Custom Annotation**: Develop a custom validation annotation for complex rules.
3. **Custom Validator**: Implement the logic for the custom annotation.
4. **Controller**: Create a controller that uses the DTO and validation.
5. **Global Exception Handler**: Manage validation errors globally.
6. **Unit Tests**: Write tests to ensure validation works as expected.

By following these implementation steps, Xentic can ensure that Bean Validation is effectively applied across its Spring Boot applications, leading to higher quality and more reliable software products.

## Security requirements

### Threat Model Summary

Xentic applications must adhere to a robust threat model that identifies potential security risks and mitigates them effectively. The following threats should be considered:

- **Unauthorized Access**: Ensure that only authenticated users can access sensitive resources.
- **Data Breach**: Protect sensitive data from exposure through encryption and secure coding practices.
- **Injection Attacks**: Validate all user inputs to prevent SQL injection, XSS, and command injection attacks.
- **Session Hijacking**: Implement secure session management practices to prevent session fixation and hijacking.

### Authentication and Authorization (AuthN/Z)

- **Authentication**: Xentic MUST use Spring Security for authentication. All endpoints must be secured and require valid tokens for access.
- **Authorization**: Role-based access control (RBAC) MUST be implemented to restrict access to resources based on user roles. Use annotations like `@PreAuthorize` to enforce security rules.

Example configuration for Spring Security:

```java
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .csrf().disable()
            .authorizeRequests()
            .antMatchers("/api/public/**").permitAll()
            .antMatchers("/api/admin/**").hasRole("ADMIN")
            .anyRequest().authenticated()
            .and()
            .oauth2ResourceServer().jwt();
    }
}
```

### Secrets Management

- **Environment Variables**: Secrets MUST NOT be hardcoded. All sensitive information such as API keys and database passwords MUST be stored in environment variables or a secrets management service (e.g., HashiCorp Vault).
- **Configuration Management**: Use Spring Cloud Config or similar tools to manage configuration properties securely.

Example configuration in `application.yml`:

```yaml
spring:
  datasource:
    url: jdbc:postgresql://db.internal.xentic.io:5432/xentic
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}
```

### Input Validation

- **Validation Framework**: Xentic MUST utilize Bean Validation (JSR 380) for input validation on all API endpoints.
- **Custom Validations**: For complex validation rules, custom annotations MUST be created and used.
- **Error Handling**: Validation errors MUST be handled gracefully and communicated back to the client in a structured format.

Example of a validation error response:

```json
{
    "errors": {
        "username": "Username must be at least 3 characters long",
        "email": "Email must be a valid email address"
    }
}
```

### Audit Logging

- **Logging Framework**: Use SLF4J with Logback for logging purposes. All security-related events MUST be logged for audit purposes.
- **Log Sensitive Information**: Sensitive information (e.g., passwords) MUST NOT be logged. Use `MASKED` or similar strategies to obscure sensitive data in logs.
- **Audit Trails**: Xentic MUST maintain an audit trail for critical actions such as user logins, data modifications, and access to sensitive resources.

Example logging configuration in `logback-spring.xml`:

```xml
<configuration>
    <appender name="FILE" class="ch.qos.logback.core.FileAppender">
        <file>logs/audit.log</file>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss} - %msg%n</pattern>
        </encoder>
    </appender>

    <logger name="com.xentic.security" level="INFO" additivity="false">
        <appender-ref ref="FILE"/>
    </logger>
</configuration>
```

### Summary of Security Requirements

- **Threat Model**: Identify and mitigate potential security risks.
- **Authentication/Authorization**: Use Spring Security for robust authentication and role-based authorization.
- **Secrets Management**: Store sensitive data securely using environment variables or secrets management tools.
- **Input Validation**: Implement Bean Validation for all user inputs and handle errors gracefully.
- **Audit Logging**: Log security events and maintain an audit trail for critical actions.

By adhering to these security requirements, Xentic ensures that its applications remain secure and resilient against potential threats.

## Testing strategy

Xentic applications MUST implement a comprehensive testing strategy that includes unit tests, integration tests, and contract tests to ensure the reliability and correctness of the application. The following outlines the approach to each testing type, coverage targets, and example test classes.

### Unit Tests

- **Purpose**: Validate individual components in isolation.
- **Coverage Target**: A minimum of 80% code coverage for all service and controller classes.
- **Framework**: JUnit 5 and Mockito MUST be used for unit testing.

Example unit test for the `UserService`:

```java
package com.xentic.user.service;

import com.xentic.user.dto.UserDTO;
import com.xentic.user.repository.UserRepository;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import static org.mockito.Mockito.*;

public class UserServiceTests {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    public UserServiceTests() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    public void whenCreateUser_thenUserIsSaved() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("validUser123");
        userDTO.setEmail("user@example.com");
        userDTO.setPassword("password");

        userService.createUser(userDTO);
        verify(userRepository, times(1)).save(any());
    }
}
```

### Integration Tests

- **Purpose**: Validate interactions between components and external systems (e.g., databases, message queues).
- **Coverage Target**: A minimum of 70% code coverage for integration tests.
- **Framework**: Spring Boot Test MUST be used for integration testing.

Example integration test for the `UserController`:

```java
package com.xentic.user.controller;

import com.xentic.user.dto.UserDTO;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
public class UserControllerIntegrationTests {

    @Autowired
    private MockMvc mockMvc;

    @Test
    public void whenValidUser_thenReturns200() throws Exception {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("validUser123");
        userDTO.setEmail("user@example.com");
        userDTO.setPassword("password");

        mockMvc.perform(post("/api/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"username\":\"validUser123\", \"email\":\"user@example.com\", \"password\":\"password\"}"))
                .andExpect(status().isOk());
    }
}
```

### Contract Tests

- **Purpose**: Ensure that the API contracts between services are adhered to.
- **Framework**: Pact MUST be used for contract testing.
- **Coverage Target**: All public APIs MUST have corresponding contract tests.

Example contract test using Pact:

```java
package com.xentic.user.contract;

import au.com.dius.pact.consumer.junit5.PactConsumerTestExt;
import au.com.dius.pact.consumer.junit5.Pact;
import au.com.dius.pact.consumer.dsl.PactDslWithProvider;
import au.com.dius.pact.consumer.dsl.PactDslJsonBody;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;

import static org.junit.jupiter.api.Assertions.assertEquals;

@ExtendWith(PactConsumerTestExt.class)
public class UserContractTests {

    @Pact(consumer = "UserServiceConsumer", provider = "UserServiceProvider")
    public RequestResponsePact createPact(PactDslWithProvider builder) {
        PactDslJsonBody body = new PactDslJsonBody()
                .stringType("username", "validUser123")
                .stringType("email", "user@example.com")
                .stringType("password", "password");

        return builder
                .given("User does not exist")
                .uponReceiving("A request to create a user")
                .path("/api/users")
                .method("POST")
                .body(body)
                .willRespondWith()
                .status(200)
                .body("User created successfully")
                .toPact();
    }

    @Test
    public void testUserCreation() {
        // Implement the test logic here
        assertEquals(1, 1); // Placeholder assertion
    }
}
```

### Summary of Testing Strategy

1. **Unit Tests**: 
   - Validate individual components.
   - Target 80% code coverage.
   - Use JUnit 5 and Mockito.

2. **Integration Tests**: 
   - Validate interactions between components.
   - Target 70% code coverage.
   - Use Spring Boot Test.

3. **Contract Tests**: 
   - Ensure API contracts are adhered to.
   - Use Pact for contract testing.
   - All public APIs MUST have corresponding contract tests.

By following this testing strategy, Xentic can ensure that its applications are robust, maintainable, and compliant with quality standards.

## Observability and operations

Xentic applications MUST implement comprehensive observability practices to ensure performance, reliability, and maintainability. This includes metrics, logs, traces, dashboards, alerts, and Service Level Objectives (SLOs). The following outlines the required components for effective observability.

### Metrics

- **Monitoring Framework**: Xentic MUST use Micrometer for metrics collection.
- **Key Metrics**: The following metrics MUST be tracked:
  - Request latency (e.g., average, 95th percentile)
  - Error rates (e.g., 4xx and 5xx responses)
  - System resource utilization (CPU, memory, disk I/O)
  - Database query performance

Example configuration in `application.yml` for Micrometer with Prometheus:

```yaml
management:
  metrics:
    export:
      prometheus:
        enabled: true
```

### Logs

- **Log Format**: Logs MUST be structured (e.g., JSON format) to facilitate parsing and querying.
- **Log Levels**: The following log levels MUST be used:
  - `DEBUG` for development and troubleshooting
  - `INFO` for general operational messages
  - `WARN` for potential issues
  - `ERROR` for error messages
- **Centralized Logging**: Logs MUST be sent to a centralized logging solution (e.g., ELK Stack, Splunk).

Example logging configuration in `logback-spring.xml` for structured logging:

```xml
<configuration>
    <appender name="JSON" class="ch.qos.logback.core.FileAppender">
        <file>logs/application.json</file>
        <encoder class="net.logstash.logback.encoder.LoggingEventCompositeJsonEncoder">
            <providers>
                <timestamp />
                <pattern>
                    <pattern>
                        {
                            "level": "%level",
                            "thread": "%thread",
                            "logger": "%logger",
                            "message": "%message"
                        }
                    </pattern>
                </pattern>
            </providers>
        </encoder>
    </appender>

    <root level="INFO">
        <appender-ref ref="JSON"/>
    </root>
</configuration>
```

### Traces

- **Distributed Tracing**: Xentic MUST implement distributed tracing using Spring Cloud Sleuth and Zipkin.
- **Trace Context**: All services MUST propagate trace context across service calls to enable end-to-end tracing.

Example configuration in `application.yml` for Sleuth:

```yaml
spring:
  sleuth:
    sampler:
      probability: 1.0  # 100% of requests will be traced
```

### Dashboards

- **Dashboard Tools**: Use Grafana or similar tools to visualize metrics and logs.
- **Key Dashboards**: Create dashboards for:
  - Application performance metrics
  - Error rates and response times
  - System health and resource utilization

### Alerts

- **Alerting Framework**: Use Prometheus Alertmanager or similar tools for alerting.
- **Alert Conditions**: The following alerts MUST be configured:
  - High error rates (e.g., > 5% 5xx responses)
  - Latency thresholds (e.g., average request time > 500ms)
  - Resource utilization (e.g., CPU usage > 80% for 5 minutes)

Example alerting rule in Prometheus:

```yaml
groups:
  - name: application-alerts
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) by (service) / sum(rate(http_requests_total[5m])) by (service) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected for {{ $labels.service }}"
          description: "More than 5% of requests are failing in the last 5 minutes."
```

### Service Level Objectives (SLOs)

- **Defining SLOs**: Xentic MUST define SLOs for critical services. SLOs MUST include:
  - Availability (e.g., 99.9% uptime)
  - Performance (e.g., 95th percentile response time < 200ms)
- **Monitoring SLOs**: SLOs MUST be monitored continuously, and deviations MUST trigger alerts.

### On-Call Runbook Steps

In the event of an incident, the following steps MUST be followed:

1. **Identify the Incident**: Use dashboards and alerts to identify the scope and impact.
2. **Assess the Severity**: Classify the incident based on its severity (e.g., critical, major, minor).
3. **Communicate**: Notify relevant stakeholders and teams using incident communication channels (e.g., Slack, email).
4. **Investigate**: Analyze logs and traces to identify the root cause.
5. **Mitigate**: Implement a temporary fix to restore service.
6. **Document**: Record the incident details, actions taken, and resolution in the incident management system.
7. **Postmortem**: Conduct a postmortem analysis to identify improvements and prevent recurrence.

By adhering to these observability and operations standards, Xentic ensures that applications are monitored effectively, enabling rapid response to incidents and maintaining high service reliability.

## Migration and versioning

Xentic applications MUST adhere to strict migration and versioning practices to maintain stability and compatibility across services. The following guidelines outline the upgrade paths, deprecation policies, backward compatibility requirements, and rollback procedures.

### Upgrade Paths

- **Major Version Upgrades**: When upgrading to a new major version (e.g., from 1.x to 2.x), Xentic MUST:
  - Review the release notes for breaking changes.
  - Update dependencies in the `pom.xml` or `build.gradle` files accordingly.
  - Perform thorough testing of all impacted services.
  
Example dependency update in `pom.xml`:

```xml
<dependency>
    <groupId>com.xentic.auth</groupId>
    <artifactId>auth-starter</artifactId>
    <version>2.0.0</version> <!-- Update to the new major version -->
</dependency>
```

- **Minor Version Upgrades**: Minor version upgrades (e.g., from 1.0 to 1.1) SHOULD be straightforward and MAY include new features or improvements without breaking changes. Testing is still required but may be less extensive.

### Deprecation Policy

- **Deprecation Notices**: Any feature or API that is to be deprecated MUST be documented in the release notes. Deprecated features MUST remain functional for at least one major version cycle before removal.
- **Deprecation Warnings**: Code that uses deprecated features MUST generate warnings during compilation or runtime to inform developers.

Example of a deprecation warning in code:

```java
@Deprecated
public void oldMethod() {
    // This method is deprecated and will be removed in future versions.
}
```

### Backward Compatibility

- **Backward Compatibility**: Xentic MUST ensure that new versions of services are backward compatible with previous versions, allowing clients to upgrade without breaking existing functionality.
- **API Versioning**: APIs MUST be versioned using URL path versioning (e.g., `/api/v1/users`). This allows multiple versions of an API to coexist.

Example of API versioning in a controller:

```java
@RestController
@RequestMapping("/api/v1/users")
public class UserController {
    // API methods for version 1
}
```

### Rollback Procedures

- **Rollback Strategy**: In case of a failed deployment, Xentic MUST have a rollback strategy in place. This includes:
  - Maintaining previous versions of the application in the deployment environment.
  - Documenting the rollback process in the deployment runbook.

Example rollback command using Kubernetes:

```bash
kubectl rollout undo deployment/user-service
```

- **Testing Rollbacks**: Rollback procedures MUST be tested regularly to ensure they work as expected in a production environment.

### Migration Steps

1. **Plan the Migration**: Identify the services and components that need to be migrated. Create a migration timeline.
2. **Backup Data**: Ensure that all data is backed up before proceeding with the migration.
3. **Update Configuration**: Modify configuration files as necessary to accommodate new features or changes.
4. **Deploy Incrementally**: Where possible, deploy changes incrementally to minimize risk.
5. **Monitor Post-Migration**: After the migration, monitor application performance and logs for any anomalies.

### Documentation

- **Migration Documentation**: All migration processes MUST be documented in detail, including:
  - Steps taken during the migration.
  - Any issues encountered and how they were resolved.
  - Changes made to the system architecture or configurations.

By adhering to these migration and versioning standards, Xentic ensures that its applications remain stable, maintainable, and capable of evolving without disrupting existing services.

## FAQ, anti-patterns, and checklists

### FAQ

1. **What is Bean Validation?**
   - Bean Validation is a Java specification that provides a way to define and validate constraints on Java objects.

2. **How do I implement Bean Validation in Spring Boot?**
   - You MUST include the `spring-boot-starter-validation` dependency in your `pom.xml` or `build.gradle`.

   ```xml
   <dependency>
       <groupId>org.springframework.boot</groupId>
       <artifactId>spring-boot-starter-validation</artifactId>
   </dependency>
   ```

3. **What annotations are commonly used in Bean Validation?**
   - Commonly used annotations include:
     - `@NotNull`
     - `@Size`
     - `@Min`
     - `@Max`
     - `@Email`

4. **Can I create custom validation annotations?**
   - Yes, you MUST create custom validation annotations by implementing the `ConstraintValidator` interface.

5. **How do I validate a request body in a Spring controller?**
   - Use the `@Valid` annotation on the method parameter.

   ```java
   @PostMapping("/users")
   public ResponseEntity<User> createUser(@Valid @RequestBody User user) {
       // Handle user creation
   }
   ```

6. **What happens if validation fails?**
   - Spring will automatically return a `400 Bad Request` response with validation error details.

7. **Can I group validation constraints?**
   - Yes, you SHOULD use validation groups to apply different constraints based on the context.

8. **How do I handle validation errors globally?**
   - Implement a `@ControllerAdvice` class to handle `MethodArgumentNotValidException`.

   ```java
   @ControllerAdvice
   public class GlobalExceptionHandler {
       @ExceptionHandler(MethodArgumentNotValidException.class)
       public ResponseEntity<ErrorResponse> handleValidationExceptions(MethodArgumentNotValidException ex) {
           // Build and return error response
       }
   }
   ```

9. **Is it possible to use Bean Validation with JPA?**
   - Yes, you MUST use Bean Validation annotations on JPA entity fields for automatic validation during persistence operations.

10. **How do I test Bean Validation constraints?**
    - Use the `Validator` interface from the `javax.validation` package to programmatically validate objects in your unit tests.

### Anti-patterns

| Anti-pattern                        | Description                                                                 |
|-------------------------------------|-----------------------------------------------------------------------------|
| Using Bean Validation on DTOs only | Validation MUST be applied on both DTOs and entities to ensure consistency. |
| Ignoring validation errors          | MUST NOT ignore validation errors; they should be handled gracefully.       |
| Overusing custom validations        | Custom validations SHOULD be used sparingly; prefer built-in constraints.   |
| Not validating nested objects       | Nested objects MUST be validated using `@Valid` to ensure complete validation.|
| Hardcoding error messages           | Error messages MUST be externalized to support localization and maintainability. |

### Pre-Merge Checklist

- [ ] All validation constraints are applied correctly.
- [ ] Custom validation annotations are documented.
- [ ] Unit tests cover validation scenarios.
- [ ] Validation error handling is implemented globally.
- [ ] No validation logic is hardcoded in controllers.

### Production Checklist

- [ ] All code has been reviewed and approved.
- [ ] Migration scripts for database changes are tested.
- [ ] Performance tests have been conducted to ensure no degradation.
- [ ] Monitoring for validation errors is set up.
- [ ] Documentation is updated to reflect any changes in validation logic.
