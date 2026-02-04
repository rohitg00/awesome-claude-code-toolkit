# /configure-gcs - Configure Google Cloud Storage

Create and configure a GCS bucket with proper security settings.

## Steps

1. Ask the user for the bucket purpose: storage, hosting, backups, data lake
2. Choose the storage class: Standard, Nearline, Coldline, or Archive based on access patterns
3. Select the location: region, dual-region, or multi-region based on requirements
4. Configure uniform bucket-level access (recommended over ACLs)
5. Set up default encryption with Google-managed or customer-managed keys
6. Configure lifecycle rules: transition to cheaper storage classes, delete old objects
7. Enable object versioning for data protection
8. Set up CORS configuration for web application access
9. Configure IAM bindings with least-privilege access for service accounts
10. Set up Pub/Sub notifications for object change events if needed
11. Generate the Terraform or gcloud commands for bucket creation
12. Document: bucket name, location, storage class, lifecycle rules, access policy

## Rules

- Always enable uniform bucket-level access over legacy ACLs
- Choose the storage class based on actual access frequency
- Enable versioning for buckets containing important or user-generated data
- Set lifecycle rules to transition to cheaper storage after access decreases
- Use customer-managed encryption keys for sensitive data
- Configure retention policies for compliance requirements
- Avoid public access unless serving static website content
