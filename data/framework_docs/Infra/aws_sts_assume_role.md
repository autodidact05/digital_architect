# STS Assume Role Patterns — AWS

## Overview and scope

The purpose of this document is to establish standards and best practices for implementing Assume Role patterns in AWS within the Xentic platform. This standard aims to provide a comprehensive guide for engineers and architects to ensure consistency, security, and efficiency when leveraging AWS roles for cross-account access and temporary permissions.

### Audience

This document is intended for:
- AWS Cloud Architects
- DevOps Engineers
- Software Developers
- Security Engineers
- System Administrators

### Scope

This standard covers:
- Configuration of AWS IAM roles for Assume Role patterns
- Best practices for role permissions and trust relationships
- Implementation patterns for various use cases, including cross-account access and service-to-service communication
- Code examples in Java and infrastructure as code (IaC) configurations

### Non-goals

This document does NOT cover:
- General AWS IAM best practices not related to Assume Role patterns
- Detailed AWS service configurations outside the context of role assumptions
- Non-AWS cloud provider patterns

### Glossary

| Term                | Definition                                                                                  |
|---------------------|---------------------------------------------------------------------------------------------|
| Assume Role         | A process that allows an entity to temporarily take on the permissions of another IAM role. |
| IAM                  | Identity and Access Management, a service that helps control access to AWS resources.       |
| Cross-Account Access | The ability to access resources in one AWS account from another AWS account.               |
| Trust Relationship   | A policy that defines which entities can assume a specific IAM role.                       |

### How This Standard Fits the Xentic Platform

The Xentic platform is built on a microservices architecture that requires secure and efficient communication between services. Implementing Assume Role patterns is critical for:
- Enabling secure access to shared resources across multiple services and accounts
- Reducing the risk of long-term credentials by leveraging temporary security credentials
- Ensuring compliance with security policies and best practices

By adhering to the standards outlined in this document, Xentic engineers will contribute to a robust security posture while maintaining operational efficiency.

### Example Configuration

Below is an example of an IAM role configuration in YAML format for an Assume Role pattern:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  MyAssumeRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: MyAssumeRole
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: MyPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:ListBucket
                  - s3:GetObject
                Resource: arn:aws:s3:::my-bucket/*
```

By following this standard, Xentic aims to ensure that all teams implement Assume Role patterns in a consistent and secure manner, ultimately enhancing the overall integrity and security of our AWS environment.

## Standards and policies

1. **MUST** use the Xentic Java base package naming convention for all services utilizing Assume Role patterns, specifically `com.xentic.<service>`. This ensures consistency across the codebase.

2. **MUST NOT** hard-code AWS credentials in any application code. Instead, leverage IAM roles and the Assume Role functionality to obtain temporary credentials securely.

3. **MUST** define clear trust relationships in IAM role policies. The trust relationship must specify which entities (AWS accounts, services, or users) are allowed to assume the role. Example trust policy:

    ```yaml
    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            AWS: arn:aws:iam::123456789012:role/AnotherRole
          Action: sts:AssumeRole
    ```

4. **SHOULD** use AWS-managed policies wherever possible to simplify permission management and reduce the risk of overly permissive access.

5. **MUST** limit the permissions granted to roles to the minimum necessary for the task (principle of least privilege). Review and refine permissions regularly.

6. **SHOULD** implement logging for all Assume Role actions using AWS CloudTrail to monitor and audit role usage. This helps in identifying any unauthorized access attempts.

7. **MUST NOT** create IAM roles with overly broad permissions, such as `*` for actions or resources. Always specify the exact actions and resources required.

8. **MUST** use Infrastructure as Code (IaC) tools (e.g., AWS CloudFormation, Terraform) to manage IAM roles and policies. This promotes version control and reproducibility. Example Terraform configuration:

    ```hcl
    resource "aws_iam_role" "my_assume_role" {
      name               = "MyAssumeRole"
      assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
          {
            Effect = "Allow"
            Principal = {
              Service = "lambda.amazonaws.com"
            }
            Action = "sts:AssumeRole"
          },
        ]
      })
    }
    ```

9. **SHOULD** implement role session names to provide better traceability in logs. Use a unique identifier for each session when assuming roles.

10. **MUST** enforce MFA (Multi-Factor Authentication) for users who are allowed to assume roles with sensitive permissions. This adds an additional layer of security.

11. **MUST NOT** use the same IAM role for multiple services unless absolutely necessary. Each service should have its own role to avoid permission conflicts and improve security.

12. **SHOULD** regularly review and rotate IAM roles and their associated policies to ensure compliance with security best practices and to mitigate risks.

13. **MUST** document all IAM roles and their purposes within the internal documentation system at `https://docs.internal.xentic.io`. This ensures that all team members understand the roles and their intended use.

14. **MUST** include error handling in code when assuming roles, ensuring that the application can gracefully handle any failures in role assumption. Example Java code snippet:

    ```java
    try {
        AssumeRoleRequest assumeRoleRequest = new AssumeRoleRequest()
                .withRoleArn("arn:aws:iam::123456789012:role/MyAssumeRole")
                .withRoleSessionName("sessionName");
        AssumeRoleResult assumeRoleResult = stsClient.assumeRole(assumeRoleRequest);
        // Use the temporary credentials
    } catch (Exception e) {
        // Handle exception
        logger.error("Failed to assume role: {}", e.getMessage());
    }
    ```

15. **SHOULD** implement a tagging strategy for IAM roles to facilitate resource management and cost allocation. Tags should include owner, purpose, and environment (e.g., dev, test, prod).

By adhering to these standards and policies, Xentic ensures that all teams implement Assume Role patterns in a secure, efficient, and consistent manner, thus enhancing the overall integrity of our AWS environment.

## Architecture and design

The architecture for implementing Assume Role patterns in AWS at Xentic is designed to facilitate secure and efficient access to resources across multiple AWS accounts and services. Below is a component diagram and a detailed description of data flows, integration points, and failure domains.

### Component Diagram

```mermaid
graph TD;
    A[User/Service] -->|Assume Role| B[STS Service]
    B -->|Temporary Credentials| C[Target AWS Service]
    C -->|Resource Access| D[Resource (e.g., S3, DynamoDB)]
    E[CloudTrail] -->|Logs| B
    F[IAM Role] -->|Trust Policy| B
    G[Monitoring Service] -->|Alerts| E
```

### Data Flows

1. **Assume Role Request**:
   - The user or service initiates a request to the AWS Security Token Service (STS) to assume a specific IAM role.
   - The request includes the role ARN and a session name.

2. **Temporary Credentials Generation**:
   - Upon successful validation of the request, STS generates temporary security credentials (Access Key, Secret Key, and Session Token).
   - These credentials are returned to the user or service.

3. **Resource Access**:
   - The user or service uses the temporary credentials to access AWS resources (e.g., S3 buckets, DynamoDB tables).
   - The access is governed by the permissions defined in the assumed role's policy.

4. **Logging and Monitoring**:
   - All Assume Role actions are logged in AWS CloudTrail for auditing purposes.
   - Monitoring services can alert on suspicious activities based on these logs.

### Integration Points

- **AWS STS**: The primary integration point for assuming roles. All requests for temporary credentials are routed through this service.
- **IAM**: Trust relationships and permission policies are defined in IAM, which govern who can assume which roles.
- **CloudTrail**: Integrates with IAM and STS to provide logging of all Assume Role actions for compliance and security monitoring.
- **Monitoring Services**: Integrate with CloudTrail to provide real-time alerts and insights on role usage.

### Failure Domains

- **STS Service Failures**:
  - If the STS service is unavailable, users and services will not be able to assume roles, leading to potential application downtime.
  - **Mitigation**: Implement retries and fallback mechanisms in the application code.

- **IAM Policy Misconfigurations**:
  - Incorrectly configured trust policies or permissions can prevent role assumption or lead to unauthorized access.
  - **Mitigation**: Regular audits of IAM roles and policies should be conducted.

- **Network Issues**:
  - Network connectivity issues may hinder access to AWS services when using temporary credentials.
  - **Mitigation**: Implement robust error handling and retry logic in applications.

- **Logging Failures**:
  - If CloudTrail logging fails, auditing role usage becomes challenging, increasing security risks.
  - **Mitigation**: Ensure that logging is enabled and monitored for any failures.

### Summary

By adhering to the outlined architecture and design principles, Xentic can ensure a secure and efficient implementation of Assume Role patterns in AWS. This design not only enhances security through the use of temporary credentials but also facilitates compliance and operational efficiency across the organization.

## Configuration reference

### application.yml

The following is an example configuration for an application using Assume Role patterns in AWS. This configuration should be tailored to your specific service requirements.

```yaml
aws:
  sts:
    roleArn: arn:aws:iam::123456789012:role/MyAssumeRole
    sessionName: mySession
    region: us-west-2
  s3:
    bucketName: my-bucket
    objectKey: my-object
```

### Terraform Configuration

The following Terraform configuration defines an IAM role and its associated policies for assuming roles in AWS.

```hcl
provider "aws" {
  region = "us-west-2"
}

resource "aws_iam_role" "my_assume_role" {
  name               = "MyAssumeRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      },
    ]
  })
}

resource "aws_iam_policy" "my_policy" {
  name        = "MyPolicy"
  description = "Policy for accessing S3"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject"
        ]
        Resource = [
          "arn:aws:s3:::my-bucket",
          "arn:aws:s3:::my-bucket/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "my_role_policy_attachment" {
  policy_arn = aws_iam_policy.my_policy.arn
  role       = aws_iam_role.my_assume_role.name
}
```

### Environment Variables

The following table outlines the environment variables that should be set for applications utilizing Assume Role patterns. Default values are provided for development, while production values should be securely configured.

| Variable                | Default Value                     | Production Value                  |
|-------------------------|-----------------------------------|-----------------------------------|
| `AWS_REGION`           | `us-west-2`                      | `us-east-1`                       |
| `ROLE_ARN`             | `arn:aws:iam::123456789012:role/MyAssumeRole` | `arn:aws:iam::PROD_ACCOUNT_ID:role/ProdRole` |
| `SESSION_NAME`         | `devSession`                     | `prodSession`                     |
| `S3_BUCKET_NAME`       | `my-bucket`                      | `prod-bucket`                     |
| `S3_OBJECT_KEY`        | `dev-object`                     | `prod-object`                     |

### Summary

By following the above configuration references, Xentic ensures that applications can securely assume roles in AWS, adhering to best practices for security and maintainability. All configurations should be version-controlled and reviewed regularly to maintain compliance with internal standards.

## Implementation guide

To implement Assume Role patterns in AWS at Xentic, follow these detailed steps, ensuring adherence to the established standards and practices.

### Step 1: Define IAM Roles

Create IAM roles that your applications will assume. Each role should have a trust policy that specifies which entities can assume the role.

**Example Trust Policy for an IAM Role**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Step 2: Create IAM Policies

Define IAM policies that specify the permissions granted to the roles. Policies should be as granular as possible.

**Example IAM Policy**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ]
    }
  ]
}
```

### Step 3: Attach Policies to Roles

Attach the defined policies to the IAM roles created in Step 1.

**Example Terraform Configuration**:

```hcl
resource "aws_iam_policy" "my_policy" {
  name        = "MyPolicy"
  description = "Policy for accessing S3"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject"
        ]
        Resource = [
          "arn:aws:s3:::my-bucket",
          "arn:aws:s3:::my-bucket/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "my_role_policy_attachment" {
  policy_arn = aws_iam_policy.my_policy.arn
  role       = aws_iam_role.my_assume_role.name
}
```

### Step 4: Configure Application

Configure your application to use the AWS SDK to assume the role. This involves setting up the AWS SDK and providing the necessary configurations.

**Example Java Code to Assume Role**:

```java
import com.amazonaws.services.securitytoken.AWSSecurityTokenService;
import com.amazonaws.services.securitytoken.AWSSecurityTokenServiceClientBuilder;
import com.amazonaws.services.securitytoken.model.AssumeRoleRequest;
import com.amazonaws.services.securitytoken.model.AssumeRoleResult;

public class RoleAssumer {
    private static final String ROLE_ARN = "arn:aws:iam::123456789012:role/MyAssumeRole";
    private static final String SESSION_NAME = "mySession";

    public static void main(String[] args) {
        AWSSecurityTokenService stsClient = AWSSecurityTokenServiceClientBuilder.defaultClient();
        
        AssumeRoleRequest assumeRoleRequest = new AssumeRoleRequest()
                .withRoleArn(ROLE_ARN)
                .withRoleSessionName(SESSION_NAME);
        
        try {
            AssumeRoleResult assumeRoleResult = stsClient.assumeRole(assumeRoleRequest);
            // Use the temporary credentials
            String accessKeyId = assumeRoleResult.getCredentials().getAccessKeyId();
            String secretAccessKey = assumeRoleResult.getCredentials().getSecretAccessKey();
            String sessionToken = assumeRoleResult.getCredentials().getSessionToken();

            // Initialize a new client with the temporary credentials
            // Example: S3Client s3Client = new S3Client(accessKeyId, secretAccessKey, sessionToken);
        } catch (Exception e) {
            System.err.println("Failed to assume role: " + e.getMessage());
        }
    }
}
```

### Step 5: Handle Errors Gracefully

Ensure that your application handles errors gracefully when assuming roles. Implement retry logic and fallback mechanisms.

**Example Error Handling**:

```java
try {
    // Assume role logic
} catch (AmazonServiceException e) {
    // Handle AWS service exceptions
    logger.error("Service error: {}", e.getErrorMessage());
} catch (SdkClientException e) {
    // Handle client-side errors
    logger.error("Client error: {}", e.getMessage());
}
```

### Step 6: Logging and Monitoring

Set up logging for all Assume Role actions using AWS CloudTrail. Ensure that logs are monitored for any suspicious activity.

### Step 7: Review and Audit

Regularly review IAM roles, policies, and logs to ensure compliance with security best practices. Conduct audits to verify that roles are being used as intended.

### Summary

By following this implementation guide, Xentic ensures that all teams can securely and efficiently implement Assume Role patterns in AWS, adhering to best practices for security and maintainability. Each step is critical for maintaining a robust AWS environment.

## Security requirements

To ensure the security of applications utilizing Assume Role patterns in AWS, Xentic must adhere to the following security requirements across various domains:

### Threat Model Summary

- **Insider Threats**: Employees or contractors with access may misuse their privileges.
- **External Attacks**: Malicious actors may attempt to gain unauthorized access to AWS resources.
- **Data Breaches**: Compromised credentials could lead to unauthorized data access.
- **Misconfiguration Risks**: Incorrectly configured IAM roles and policies may expose resources.

### Authentication and Authorization

- **Use AWS IAM Roles**: Applications MUST use IAM roles for managing permissions rather than hardcoding credentials.
- **Role-Based Access Control (RBAC)**: Access to AWS resources MUST be granted based on the principle of least privilege.
- **Multi-Factor Authentication (MFA)**: MFA SHOULD be enforced for all IAM users with access to sensitive resources.

### Secrets Management

- **Use AWS Secrets Manager**: Secrets such as database credentials MUST be stored in AWS Secrets Manager instead of environment variables.
- **Rotate Secrets Regularly**: Secrets MUST be rotated on a regular basis to mitigate the risk of exposure.
- **Access Control**: Access to secrets MUST be restricted to only those IAM roles that require it.

### Input Validation

- **Sanitize Inputs**: All inputs from external sources MUST be validated and sanitized to prevent injection attacks.
- **Use Whitelisting**: Implement whitelisting for acceptable input formats and values.
- **Error Handling**: Error messages MUST not disclose sensitive information that could aid an attacker.

### Audit Logging

- **Enable CloudTrail**: AWS CloudTrail MUST be enabled to log all actions taken on AWS resources.
- **Log Access to Sensitive Operations**: Access to sensitive operations, such as assuming roles, MUST be logged and monitored.
- **Retention Policy**: Logs MUST be retained for at least 90 days for compliance and auditing purposes.
- **Alerting**: An alerting mechanism MUST be in place to notify administrators of suspicious activities or unauthorized access attempts.

### Example Configuration for Logging

To enable detailed logging in your application, configure AWS CloudTrail as follows:

```yaml
cloudtrail:
  isMultiRegionTrail: true
  includeGlobalServiceEvents: true
  isOrganizationTrail: false
  s3BucketName: my-cloudtrail-logs
  s3KeyPrefix: cloudtrail
  enableLogFileValidation: true
```

### Example IAM Policy for Logging

The following IAM policy grants permissions to write logs to an S3 bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::my-cloudtrail-logs/*"
    },
    {
      "Effect": "Allow",
      "Action": "cloudtrail:CreateTrail",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "cloudtrail:StartLogging",
      "Resource": "*"
    }
  ]
}
```

By implementing these security requirements, Xentic can significantly reduce the risk of security breaches and ensure compliance with internal and external regulations. Regular reviews and audits of security practices MUST be conducted to adapt to evolving threats.

## Testing strategy

To ensure the reliability and correctness of the Assume Role patterns implemented in AWS, Xentic must adopt a comprehensive testing strategy that encompasses unit tests, integration tests, and contract tests. Each type of test serves a specific purpose and collectively contributes to a robust application.

### Unit Tests

Unit tests are essential for verifying the functionality of individual components in isolation. Each method that interacts with AWS services or handles role assumption logic MUST be covered by unit tests.

- **Coverage Target**: A minimum of 80% code coverage is required for all classes related to Assume Role functionality.

**Example Unit Test Class**:

```java
import static org.mockito.Mockito.*;
import static org.junit.Assert.*;
import org.junit.Before;
import org.junit.Test;

public class RoleAssumerTest {
    private RoleAssumer roleAssumer;
    private AWSSecurityTokenService stsClient;

    @Before
    public void setUp() {
        stsClient = mock(AWSSecurityTokenService.class);
        roleAssumer = new RoleAssumer(stsClient);
    }

    @Test
    public void testAssumeRoleSuccess() {
        AssumeRoleResult mockResult = new AssumeRoleResult()
                .withCredentials(new Credentials()
                        .withAccessKeyId("mockAccessKeyId")
                        .withSecretAccessKey("mockSecretAccessKey")
                        .withSessionToken("mockSessionToken"));
        
        when(stsClient.assumeRole(any(AssumeRoleRequest.class))).thenReturn(mockResult);
        
        Credentials credentials = roleAssumer.assumeRole("mockRoleArn", "mockSessionName");
        
        assertNotNull(credentials);
        assertEquals("mockAccessKeyId", credentials.getAccessKeyId());
    }

    @Test(expected = AmazonServiceException.class)
    public void testAssumeRoleFailure() {
        when(stsClient.assumeRole(any(AssumeRoleRequest.class))).thenThrow(new AmazonServiceException("Service error"));
        
        roleAssumer.assumeRole("mockRoleArn", "mockSessionName");
    }
}
```

### Integration Tests

Integration tests validate the interaction between different components, including external services like AWS. These tests MUST be executed in an environment that closely resembles production.

- **Coverage Target**: At least 70% of integration points with AWS services should be covered by integration tests.

**Example Integration Test Class**:

```java
import org.junit.Test;
import static org.junit.Assert.*;
import com.amazonaws.services.securitytoken.AWSSecurityTokenServiceClientBuilder;

public class RoleAssumerIntegrationTest {
    @Test
    public void testAssumeRoleIntegration() {
        RoleAssumer roleAssumer = new RoleAssumer(AWSSecurityTokenServiceClientBuilder.defaultClient());
        Credentials credentials = roleAssumer.assumeRole("arn:aws:iam::123456789012:role/MyAssumeRole", "testSession");

        assertNotNull(credentials);
        assertNotNull(credentials.getAccessKeyId());
        assertNotNull(credentials.getSecretAccessKey());
    }
}
```

### Contract Tests

Contract tests ensure that the interactions between services adhere to defined contracts. This is particularly important when multiple services depend on the role assumption functionality.

- **Coverage Target**: All public APIs that interact with AWS services MUST have corresponding contract tests.

**Example Contract Test Class**:

```java
import org.junit.Test;
import static org.junit.Assert.*;
import org.springframework.cloud.contract.spec.Contract;

public class RoleAssumerContractTest {
    @Test
    public void testContract() {
        // Define the contract for the assume role interaction
        Contract.make {
            request {
                method 'POST'
                url '/assume-role'
                body([
                    roleArn: 'arn:aws:iam::123456789012:role/MyAssumeRole',
                    sessionName: 'testSession'
                ])
            }
            response {
                status 200
                body([
                    accessKeyId: 'mockAccessKeyId',
                    secretAccessKey: 'mockSecretAccessKey',
                    sessionToken: 'mockSessionToken'
                ])
            }
        }
    }
}
```

### Summary of Testing Strategy

| Test Type       | Coverage Target | Purpose                                         |
|------------------|-----------------|-------------------------------------------------|
| Unit Tests       | 80%             | Validate individual methods and logic           |
| Integration Tests| 70%             | Validate interactions with AWS services         |
| Contract Tests   | 100%            | Ensure adherence to defined service contracts    |

### Conclusion

By implementing a robust testing strategy that includes unit, integration, and contract tests, Xentic can ensure that the Assume Role patterns in AWS are reliable, maintainable, and compliant with internal standards. Regularly reviewing test coverage and updating tests in line with code changes MUST be part of the development lifecycle to maintain quality.

## Observability and operations

To ensure that the Assume Role patterns are functioning correctly and efficiently, Xentic MUST implement a comprehensive observability strategy that encompasses metrics, logs, traces, dashboards, alerts, and Service Level Objectives (SLOs). This strategy will facilitate proactive monitoring and rapid incident response.

### Metrics

Metrics MUST be collected to monitor the performance and usage of the Assume Role functionality. Key metrics to track include:

- **Role Assumption Latency**: Time taken to assume a role, measured in milliseconds.
- **Successful Role Assumptions**: Count of successful role assumptions over time.
- **Failed Role Assumptions**: Count of failed role assumptions, categorized by error type.
- **Average Session Duration**: Average duration of sessions created by assumed roles.

**Example Metrics Configuration** (using Prometheus):

```yaml
metrics:
  roleAssumptionLatency:
    type: histogram
    help: "Latency of role assumption in milliseconds"
    buckets: [10, 50, 100, 200, 500, 1000]
  successfulRoleAssumptions:
    type: counter
    help: "Count of successful role assumptions"
  failedRoleAssumptions:
    type: counter
    help: "Count of failed role assumptions"
  averageSessionDuration:
    type: gauge
    help: "Average duration of sessions created by assumed roles"
```

### Logs

Comprehensive logging MUST be implemented to capture all relevant events related to role assumptions. Logs should include:

- **Role ARN**: The ARN of the role being assumed.
- **Session Name**: The name of the session created.
- **Caller Identity**: Information about the user or service assuming the role.
- **Timestamps**: Time of the request and response.

**Example Log Configuration** (using Log4j):

```properties
log4j.rootLogger=INFO, file
log4j.appender.file=org.apache.log4j.FileAppender
log4j.appender.file.File=logs/role_assumption.log
log4j.appender.file.layout=org.apache.log4j.PatternLayout
log4j.appender.file.layout.ConversionPattern=%d{ISO8601} [%t] %-5p %c %x - %m%n
```

### Traces

Distributed tracing MUST be implemented to track requests across microservices. This allows for better understanding of the flow of requests and identification of bottlenecks.

- **Trace ID**: Each request MUST carry a unique trace ID.
- **Span Information**: Each operation (e.g., assuming a role) MUST be recorded as a span.

**Example Trace Configuration** (using OpenTelemetry):

```yaml
tracing:
  exporter:
    otlp:
      endpoint: "http://otel-collector:4317"
  resource:
    service.name: "role-assumer-service"
    service.version: "1.0.0"
```

### Dashboards

Dashboards MUST be created to visualize metrics and logs. Key components of the dashboard should include:

- **Role Assumption Latency Graph**: A line graph showing the latency of role assumptions over time.
- **Success/Failure Rate**: A pie chart displaying the ratio of successful to failed role assumptions.
- **Session Duration Histogram**: A histogram showing the distribution of session durations.

**Example Dashboard Configuration** (using Grafana):

```json
{
  "title": "Role Assumption Dashboard",
  "panels": [
    {
      "type": "graph",
      "title": "Role Assumption Latency",
      "targets": [
        {
          "target": "histogram(roleAssumptionLatency)"
        }
      ]
    },
    {
      "type": "piechart",
      "title": "Success/Failure Rate",
      "targets": [
        {
          "target": "successfulRoleAssumptions"
        },
        {
          "target": "failedRoleAssumptions"
        }
      ]
    },
    {
      "type": "histogram",
      "title": "Session Duration",
      "targets": [
        {
          "target": "averageSessionDuration"
        }
      ]
    }
  ]
}
```

### Alerts

Alerts MUST be configured to notify the operations team of any anomalies or issues. Key alerts to implement include:

- **High Latency Alert**: Triggered when role assumption latency exceeds a defined threshold (e.g., 500ms).
- **Failure Rate Alert**: Triggered when the failure rate of role assumptions exceeds 5% over a 5-minute window.
- **Session Duration Alert**: Triggered when the average session duration exceeds a defined threshold (e.g., 1 hour).

**Example Alert Configuration** (using Prometheus Alertmanager):

```yaml
groups:
  - name: role-assumption-alerts
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.95, sum(rate(roleAssumptionLatency[5m])) by (le)) > 500
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High Latency in Role Assumption"
          description: "Role assumption latency is above 500ms for the last 5 minutes."
      - alert: HighFailureRate
        expr: (failedRoleAssumptions / (successfulRoleAssumptions + failedRoleAssumptions)) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High Failure Rate in Role Assumption"
          description: "Failure rate of role assumptions is above 5%."
```

### Service Level Objectives (SLOs)

SLOs MUST be defined to measure the reliability and performance of the Assume Role functionality. Suggested SLOs include:

- **Availability**: 99.9% of role assumptions must succeed.
- **Latency**: 95% of role assumptions must complete within 500ms.
- **Error Rate**: Less than 1% of role assumptions should fail.

### On-Call Runbook Steps

In the event of an incident, the following runbook steps MUST be followed:

1. **Identify the Incident**: Check alerts and dashboards to confirm the incident.
2. **Assess Impact**: Determine the scope of the impact on users and services.
3. **Investigate Logs and Metrics**: Review logs and metrics to identify the root cause.
4. **Communicate**: Notify stakeholders of the incident and provide updates.
5. **Implement Fix**: Apply the necessary changes to resolve the issue.
6. **Post-Mortem**: Conduct a post-mortem analysis to identify lessons learned and improve the process.

By adhering to these observability and operations guidelines, Xentic can ensure that the Assume Role patterns are monitored effectively, enabling rapid detection and resolution of issues while maintaining high service reliability.

## Migration and versioning

When managing the lifecycle of the Assume Role patterns in AWS, Xentic MUST adhere to a structured migration and versioning strategy. This strategy includes upgrade paths, deprecation policies, backward compatibility, and rollback procedures to ensure a smooth transition between versions.

### Upgrade Paths

Xentic MUST provide clear upgrade paths for transitioning between major versions of the Assume Role patterns. Each upgrade path MUST include:

- **Release Notes**: Detailed documentation of changes, including new features, enhancements, and breaking changes.
- **Upgrade Steps**: A step-by-step guide on how to upgrade from one version to another.

**Example Upgrade Steps**:

1. **Backup Current Configuration**: Ensure all current configurations are backed up.
2. **Review Release Notes**: Analyze the release notes for any breaking changes.
3. **Update Dependencies**: Modify the `pom.xml` or `build.gradle` to include the new version.
4. **Run Tests**: Execute all unit and integration tests to validate the upgrade.
5. **Deploy to Staging**: Deploy the upgraded version to a staging environment for further testing.
6. **Monitor**: Closely monitor the staging environment for any issues.
7. **Deploy to Production**: Once validated, deploy to the production environment.

### Deprecation Policy

Xentic MUST implement a deprecation policy to manage the lifecycle of features within the Assume Role patterns. This policy MUST include:

- **Deprecation Notices**: Clear communication to users about deprecated features, including timelines for removal.
- **Grace Period**: A minimum grace period of six months between deprecation announcement and removal of features.
- **Documentation Updates**: Ensure that all documentation reflects deprecated features and suggests alternatives.

**Example Deprecation Notice**:

```markdown
### Deprecation Notice: `assumeRoleV1()`

The `assumeRoleV1()` method will be deprecated in version 2.0.0. Users are encouraged to migrate to `assumeRoleV2()` which offers enhanced security features. The deprecation will be effective from January 1, 2024, with removal planned for July 1, 2024.
```

### Backward Compatibility

Backward compatibility MUST be maintained wherever feasible to ensure that existing implementations continue to function without modification. When introducing breaking changes, Xentic MUST:

- **Versioning**: Use semantic versioning (MAJOR.MINOR.PATCH) to indicate changes. Breaking changes MUST increment the MAJOR version.
- **Feature Flags**: Introduce new features behind feature flags to allow gradual adoption.
- **Extensive Testing**: Conduct regression testing to ensure that existing features work as expected.

**Example Semantic Versioning**:

| Version   | Changes                                   |
|-----------|-------------------------------------------|
| 1.0.0    | Initial release                           |
| 1.1.0    | Added new feature X (backward compatible)|
| 2.0.0    | Introduced breaking changes               |

### Rollback Procedures

In the event of an unsuccessful deployment, Xentic MUST have rollback procedures in place. These procedures MUST include:

- **Rollback Plan**: A documented plan detailing how to revert to the previous stable version.
- **Automated Rollback Scripts**: Scripts to automate the rollback process, minimizing downtime.
- **Verification Steps**: Steps to verify that the rollback was successful and the system is functioning as expected.

**Example Rollback Steps**:

1. **Identify the Issue**: Determine the cause of the failure.
2. **Execute Rollback Script**: Run the automated rollback script to revert to the previous version.
3. **Verify System Health**: Check logs and metrics to ensure the system is stable.
4. **Communicate**: Notify stakeholders of the rollback and any next steps.

By adhering to these migration and versioning guidelines, Xentic can ensure that the Assume Role patterns in AWS are managed effectively, minimizing disruption and maintaining high service quality throughout the lifecycle of the software.

## FAQ, anti-patterns, and checklists

### FAQ

1. **What is the purpose of assuming a role in AWS?**
   - Assuming a role allows a user or service to temporarily gain permissions associated with that role, enabling secure access to AWS resources.

2. **How long can a session last when assuming a role?**
   - The maximum session duration is configurable, but by default, it is set to 1 hour. It can be extended up to 12 hours.

3. **What permissions are required to assume a role?**
   - The user or service must have the `sts:AssumeRole` permission for the role they wish to assume.

4. **Can a role be assumed by another role?**
   - Yes, roles can be configured to allow other roles to assume them, enabling a chain of trust.

5. **What happens if role assumption fails?**
   - The application MUST handle the failure gracefully, logging the error and notifying the relevant stakeholders.

6. **How can we audit role assumptions?**
   - AWS CloudTrail MUST be enabled to log all `AssumeRole` actions, allowing for auditing and compliance checks.

7. **Is it possible to restrict role assumption based on conditions?**
   - Yes, IAM policies can include conditions to restrict role assumptions based on factors like IP address or MFA status.

8. **What are best practices for managing IAM roles?**
   - Roles MUST follow the principle of least privilege, be named clearly, and have a defined lifecycle management process.

9. **How can we test role assumptions in a development environment?**
   - Use AWS IAM policies and roles in a sandbox environment, ensuring that tests do not affect production resources.

10. **What should be done if a role is no longer needed?**
    - The role MUST be deleted after ensuring that no resources or services depend on it, and documentation should be updated accordingly.

### Anti-Patterns

| Anti-Pattern                       | Description                                                                                     | Recommendation                                       |
|------------------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------|
| Hardcoding Role ARNs               | Directly embedding role ARNs in code.                                                         | Use configuration files or environment variables.   |
| Overly Permissive Roles            | Assigning broad permissions to roles without restrictions.                                     | Implement least privilege principle.                 |
| Ignoring Session Duration Limits    | Allowing sessions to exceed recommended duration.                                             | Set appropriate session duration limits.             |
| Not Using MFA for Sensitive Roles   | Failing to require MFA for roles that access sensitive resources.                             | Enforce MFA for all critical role assumptions.      |
| Lack of Logging and Monitoring      | Not enabling CloudTrail for role assumption actions.                                          | Always enable CloudTrail for auditing purposes.     |
| Unclear Role Naming Conventions     | Using ambiguous names for roles, making it hard to understand their purpose.                   | Adopt a clear and consistent naming convention.     |
| Not Reviewing Role Permissions      | Failing to periodically review and update role permissions.                                   | Conduct regular audits of role permissions.         |

### Pre-Merge Checklist

- [ ] Code adheres to Xentic's coding standards.
- [ ] Unit tests cover all new functionality.
- [ ] Integration tests pass successfully.
- [ ] Documentation is updated to reflect changes.
- [ ] Security review is completed.
- [ ] Code is peer-reviewed and approved.

### Production Checklist

- [ ] Ensure all environment variables are set correctly.
- [ ] Verify that IAM policies are correctly applied.
- [ ] Confirm that CloudTrail logging is enabled.
- [ ] Monitor application logs for any errors post-deployment.
- [ ] Validate that metrics and alerts are functioning as expected.
- [ ] Conduct a post-deployment review with the team.
