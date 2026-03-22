# /setup-functions - Setup Azure Functions

Configure and deploy an Azure Functions application.

## Steps

1. Ask the user for the function name, runtime (.NET, Node.js, Python, Java), and trigger type
2. Initialize the function app project with the appropriate runtime template
3. Create the function handler with the selected trigger binding
4. Configure app settings and connection strings for the function
5. Set up the hosting plan: Consumption (serverless), Premium, or Dedicated
6. Configure authentication and authorization if the function exposes HTTP endpoints
7. Set up managed identity for accessing Azure resources without credentials
8. Configure Application Insights for monitoring and logging
9. Set up input and output bindings: Blob Storage, Queue, Cosmos DB, Event Hub
10. Create the deployment configuration: Azure DevOps pipeline or GitHub Actions
11. Generate the ARM template or Bicep file for infrastructure as code
12. Document: function URL, trigger type, bindings, app settings, scaling behavior

## Rules

- Use Consumption plan for event-driven workloads to minimize costs
- Always configure Application Insights for production functions
- Use managed identities instead of connection strings for Azure resource access
- Set function timeout appropriate to the workload (Consumption max: 10 min)
- Configure CORS settings for HTTP-triggered functions called from browsers
- Enable deployment slots for production functions to support zero-downtime deploys
- Store secrets in Azure Key Vault, reference them via app settings
