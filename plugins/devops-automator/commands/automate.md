Create DevOps automation scripts for CI/CD pipelines, deployments, and infrastructure tasks.

## Steps


1. Identify the automation need:
2. Choose the automation platform:
3. Design the automation workflow:
4. Implement the automation:
5. Add safety guards:
6. Test the automation in a safe environment.
7. Document how to use and modify the automation.

## Format


```
Automation: <name>
Trigger: <event or schedule>
Platform: <GitHub Actions|GitLab CI|Shell>
Steps:
```


## Rules

- Always include a dry-run option for destructive operations.
- Use secrets management; never hardcode credentials.
- Add timeout limits to prevent runaway processes.

