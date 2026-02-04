---
name: aws-cloud-patterns
description: AWS cloud patterns for Lambda, ECS, S3, DynamoDB, and Infrastructure as Code with CDK/Terraform
---

# AWS Cloud Patterns

## Lambda Function Pattern

```typescript
import { APIGatewayProxyHandlerV2 } from "aws-lambda";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, GetCommand } from "@aws-sdk/lib-dynamodb";

const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));

export const handler: APIGatewayProxyHandlerV2 = async (event) => {
  const id = event.pathParameters?.id;
  if (!id) {
    return { statusCode: 400, body: JSON.stringify({ error: "Missing id" }) };
  }

  const result = await client.send(
    new GetCommand({ TableName: process.env.TABLE_NAME!, Key: { pk: id } })
  );

  if (!result.Item) {
    return { statusCode: 404, body: JSON.stringify({ error: "Not found" }) };
  }

  return {
    statusCode: 200,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(result.Item),
  };
};
```

Initialize SDK clients outside the handler to reuse connections across invocations.

## DynamoDB Single-Table Design

```typescript
interface OrderItem {
  pk: string;          // USER#<userId>
  sk: string;          // ORDER#<orderId>
  gsi1pk: string;      // ORDER#<orderId>
  gsi1sk: string;      // ITEM#<itemId>
  entityType: string;  // "Order" | "OrderItem"
  data: Record<string, any>;
  ttl?: number;
}

const params = {
  TableName: "AppTable",
  KeyConditionExpression: "pk = :pk AND begins_with(sk, :prefix)",
  ExpressionAttributeValues: {
    ":pk": `USER#${userId}`,
    ":prefix": "ORDER#",
  },
};
```

Design access patterns first, then model keys. Use GSIs for alternative query patterns.

## CDK Infrastructure

```typescript
import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as lambda from "aws-cdk-lib/aws-lambda-nodejs";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as apigateway from "aws-cdk-lib/aws-apigatewayv2";

export class ApiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const table = new dynamodb.Table(this, "AppTable", {
      partitionKey: { name: "pk", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "sk", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    const fn = new lambda.NodejsFunction(this, "ApiHandler", {
      entry: "src/handler.ts",
      runtime: cdk.aws_lambda.Runtime.NODEJS_22_X,
      architecture: cdk.aws_lambda.Architecture.ARM_64,
      memorySize: 256,
      timeout: cdk.Duration.seconds(10),
      environment: { TABLE_NAME: table.tableName },
    });

    table.grantReadWriteData(fn);
  }
}
```

## S3 Event Processing

```typescript
import { S3Event } from "aws-lambda";
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";

const s3 = new S3Client({});

export async function handler(event: S3Event) {
  for (const record of event.Records) {
    const bucket = record.s3.bucket.name;
    const key = decodeURIComponent(record.s3.object.key.replace(/\+/g, " "));

    const obj = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
    const body = await obj.Body?.transformToString();

    await processFile(key, body);
  }
}
```

## Anti-Patterns

- Hardcoding AWS credentials instead of using IAM roles
- Not setting Lambda timeout and memory appropriately
- Using `SELECT *` equivalent scans on DynamoDB instead of query with key conditions
- Creating one Lambda per CRUD operation instead of grouping by domain
- Missing CloudWatch alarms for error rates and throttling
- Not enabling point-in-time recovery on DynamoDB tables

## Checklist

- [ ] SDK clients initialized outside Lambda handler
- [ ] IAM roles follow least-privilege principle
- [ ] DynamoDB access patterns designed before table schema
- [ ] Lambda uses ARM64 architecture for cost savings
- [ ] S3 buckets have versioning and lifecycle policies
- [ ] CloudWatch alarms set for Lambda errors, duration, and throttles
- [ ] Infrastructure defined as code (CDK or Terraform)
- [ ] Secrets stored in Systems Manager Parameter Store or Secrets Manager
