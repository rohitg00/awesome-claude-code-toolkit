Perform a security assessment of the codebase to identify vulnerabilities and risks.

## Steps


1. Scan for common vulnerability patterns:
2. Check authentication and authorization:
3. Check data handling:
4. Check dependency security:
5. Check configuration security:
6. Report findings with CVSS-based severity.

## Format


```
Security Assessment: <project>
Date: <date>
Findings:
  Critical (<CVSS 9.0+>): <count>
```


## Rules

- Check every user input path for injection vulnerabilities.
- Scan dependencies for known CVEs before every release.
- Never log sensitive data (passwords, tokens, PII).

