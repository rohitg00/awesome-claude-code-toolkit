# /configure-s3 - Configure AWS S3 Bucket

Create and configure an S3 bucket with security best practices.

## Steps

1. Ask the user for the bucket purpose: static hosting, file storage, backups, logs
2. Generate a globally unique bucket name following naming conventions
3. Configure bucket policy based on access requirements (private, public-read, CDN-only)
4. Enable server-side encryption (AES-256 or KMS) by default
5. Block all public access unless explicitly required for static hosting
6. Configure CORS rules if the bucket serves content to web applications
7. Set up lifecycle rules: transition to Glacier after 90 days, expire after 365 days
8. Enable versioning for data protection and accidental deletion recovery
9. Configure access logging to a separate logging bucket
10. Set up event notifications for object creation or deletion if needed
11. Generate the IaC definition (CloudFormation or CDK) for the bucket
12. Document bucket configuration: name, region, access policy, encryption, lifecycle

## Rules

- Always block public access unless the user explicitly requires public hosting
- Enable encryption at rest for all buckets
- Use bucket policies over ACLs (ACLs are legacy)
- Enable versioning for any bucket containing user data or important files
- Configure lifecycle rules to manage storage costs
- Set up access logging for compliance and audit requirements
- Use regional bucket names to avoid global namespace conflicts
