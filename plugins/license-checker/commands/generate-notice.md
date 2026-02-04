# /generate-notice - Generate License Notice

Generate a NOTICE file with all third-party license attributions.

## Steps

1. List all production dependencies with their license information
2. Read the full license text for each dependency
3. Group dependencies by license type for efficient presentation
4. Generate attribution entries: package name, version, author, license type
5. Include the full license text for each unique license type
6. Add copyright notices from each dependency's LICENSE file
7. Include any required attribution notices (Apache-2.0 NOTICE files)
8. Format the NOTICE file with clear sections and separators
9. Add the project's own copyright notice at the top
10. Include the generation date and tool version for reference
11. Validate that all required attributions are present
12. Save the NOTICE file to the project root

## Rules

- Include all production dependencies, even those with permissive licenses
- Reproduce the exact copyright notice from each dependency's LICENSE file
- Group by license type to avoid repeating the same license text
- Include the specific version of each dependency for accuracy
- Apache-2.0 requires reproducing NOTICE files from dependencies
- Update the NOTICE file with each release that changes dependencies
- Do not include development-only dependencies unless they ship with the product
