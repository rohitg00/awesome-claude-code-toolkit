# /create-module - Create Terraform Module

Create a reusable Terraform module for infrastructure provisioning.

## Steps

1. Ask the user for the module purpose: networking, compute, database, storage, etc.
2. Create the module directory structure: main.tf, variables.tf, outputs.tf, versions.tf
3. Define input variables with descriptions, types, defaults, and validation rules
4. Write the resource definitions in main.tf using the appropriate provider
5. Define output values for resource attributes needed by other modules
6. Set provider version constraints in versions.tf
7. Add local values for computed or derived configurations
8. Include conditional resource creation using count or for_each
9. Add proper tagging strategy: Name, Environment, Project, ManagedBy
10. Create a README.md with usage examples and variable descriptions
11. Add a basic examples/ directory with a complete usage example
12. Validate the module with `terraform validate` and `terraform fmt`

## Rules

- Every variable must have a description and type constraint
- Use snake_case for all resource and variable names
- Pin provider versions to prevent unexpected upgrades
- Use data sources instead of hardcoding resource IDs
- Make the module environment-agnostic (dev/staging/prod via variables)
- Include sensible defaults for optional variables
- Never hardcode credentials or account IDs in the module
