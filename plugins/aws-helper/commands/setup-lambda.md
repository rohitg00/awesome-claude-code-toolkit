# /setup-lambda - Setup AWS Lambda Function

Configure and deploy an AWS Lambda function with proper settings.

## Steps

1. Ask the user for the function name, runtime (Node.js, Python, Go), and trigger type
2. Create the Lambda function handler file with the appropriate template
3. Generate the IAM role and policy with least-privilege permissions
4. Configure environment variables for the function
5. Set memory allocation (default 256MB) and timeout (default 30s) based on workload
6. Configure the trigger: API Gateway, S3 event, SQS queue, EventBridge schedule, or DynamoDB stream
7. Set up VPC configuration if the function needs database or internal service access
8. Add CloudWatch log group with appropriate retention period (default 30 days)
9. Configure dead letter queue for failed invocations
10. Create the deployment package or container image configuration
11. Generate the IaC definition (CloudFormation, SAM, or CDK) for the Lambda
12. Document the function: purpose, trigger, environment variables, and IAM permissions

## Rules

- Always use least-privilege IAM policies; never use AdministratorAccess
- Set appropriate memory and timeout; do not use maximum values by default
- Include error handling and structured logging in the handler template
- Configure reserved concurrency if the function should be rate-limited
- Use environment variables for configuration, not hardcoded values
- Enable X-Ray tracing for production functions
- Add tags for cost allocation: team, project, environment
