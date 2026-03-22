Create a full release with changelog, GitHub release, and package publishing.

## Steps


1. Verify the release is ready:
2. Generate release notes:
3. Create the GitHub release:
4. Publish packages if applicable:
5. Update documentation if API changes were made.
6. Notify stakeholders about the release.
7. Merge back to the development branch if using gitflow.

## Format


```
Release: v<version>
Date: <YYYY-MM-DD>
Highlights:
  - <key feature or fix>
```


## Rules

- Never release without passing CI/CD checks.
- Tag format must be `v<semver>` (e.g., v1.2.3).
- Include breaking change migration guides for major versions.

