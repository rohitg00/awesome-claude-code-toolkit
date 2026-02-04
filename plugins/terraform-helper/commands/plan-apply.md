# /plan-apply - Terraform Plan and Apply

Run Terraform plan, review changes, and apply infrastructure updates.

## Steps

1. Verify the Terraform working directory and state backend configuration
2. Run `terraform init` to initialize providers and modules
3. Select or verify the target workspace (dev, staging, production)
4. Run `terraform plan -out=tfplan` to generate an execution plan
5. Parse the plan output to summarize changes: resources to add, change, destroy
6. Highlight destructive changes (destroy or replace) that need special attention
7. Check for potential issues: security group changes, IAM policy modifications
8. Show estimated cost impact using infracost if available
9. Ask for user confirmation before applying, especially for destructive changes
10. Run `terraform apply tfplan` to execute the approved plan
11. Verify the apply completed successfully and note any errors
12. Save the plan output and apply results for audit purposes

## Rules

- Always run plan before apply; never apply without reviewing changes
- Require explicit confirmation for any resource destruction
- Double-confirm when applying to production workspaces
- Use plan files (-out flag) to ensure the applied changes match the reviewed plan
- Never auto-approve applies in production environments
- Check for state lock before running plan or apply
- Log all plan and apply operations with timestamps for audit trails
