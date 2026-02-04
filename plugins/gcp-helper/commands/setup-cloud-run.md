# /setup-cloud-run - Setup Google Cloud Run Service

Configure and deploy a Cloud Run service with best practices.

## Steps

1. Ask the user for the service name, runtime, and source code location
2. Create or verify the Dockerfile for the application
3. Configure the Cloud Run service with appropriate settings:
   - CPU allocation (default: 1 vCPU)
   - Memory limit (default: 512Mi)
   - Max instances (default: 10)
   - Min instances (default: 0 for cost savings, 1 for low latency)
4. Set up environment variables and secret references from Secret Manager
5. Configure the service account with least-privilege IAM roles
6. Set up Cloud SQL connection if database access is needed
7. Configure custom domain mapping if a domain is provided
8. Set up Cloud Build trigger for automated deployments from the repository
9. Configure health check endpoint for the service
10. Set up Cloud Monitoring alerts for error rate and latency
11. Generate the gcloud deploy command or Cloud Deploy configuration
12. Document the service: URL, scaling config, environment variables, IAM roles

## Rules

- Always use a dedicated service account, never the default compute service account
- Set appropriate CPU and memory limits; do not use maximum values
- Configure min instances to 0 for non-production to save costs
- Use Secret Manager for sensitive configuration, not environment variables
- Enable Cloud Armor if the service is publicly accessible
- Set request timeout appropriate to the workload (default 300s)
- Use concurrency setting to match the application's thread safety
