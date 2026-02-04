# /check-licenses - Check License Compliance

Check all dependency licenses for compliance with project requirements.

## Steps

1. Detect the package manager: npm, pip, Maven, Gradle, Cargo, Go modules
2. List all direct and transitive dependencies with their versions
3. Retrieve the license type for each dependency
4. Classify licenses: permissive (MIT, Apache-2.0, BSD), copyleft (GPL, AGPL), other
5. Check dependencies against the project's allowed license list
6. Flag any copyleft licenses that may require source code disclosure
7. Identify dependencies with unknown, missing, or custom licenses
8. Check for license compatibility with the project's own license
9. Detect dual-licensed packages and determine which license applies
10. Generate a compliance report: dependency, version, license, status (allowed/flagged/unknown)
11. Calculate the total count by license type
12. Flag any newly added dependencies since the last check

## Rules

- Default allowed licenses: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, 0BSD
- Always flag AGPL and GPL licenses as they require careful review
- Check transitive dependencies, not just direct dependencies
- Verify license files exist in dependency packages, not just package.json declarations
- Handle SPDX license expressions (AND, OR, WITH exceptions)
- Report on development-only dependencies separately (less restrictive)
- Update the allowed license list through project configuration, not hardcoding
