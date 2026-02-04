# /generate-readme - Generate README

Generate a comprehensive README.md from project analysis.

## Steps

1. Scan the project root for key files: package.json, Cargo.toml, pyproject.toml, go.mod, Makefile
2. Detect the project type, language, framework, and build system
3. Read existing documentation files for context (CONTRIBUTING.md, docs/, wiki)
4. Analyze the source code structure: main entry points, modules, and public API
5. Extract project name, version, description, and license from manifest files
6. Identify installation steps from lock files and build configuration
7. Find usage examples from test files, examples directory, or existing docs
8. Detect available scripts/commands from package.json scripts or Makefile targets
9. Check for CI/CD configuration to document build and deployment status
10. Generate the README with sections: Title, Description, Installation, Usage, API, Contributing, License
11. Add badges for build status, version, license, and coverage if available
12. Write the README.md to the project root

## Rules

- Preserve any existing README content the user wants to keep
- Use the project's actual commands, not generic placeholders
- Include real code examples from the project when possible
- Keep the README concise; link to detailed docs instead of duplicating
- Add a table of contents for READMEs longer than 100 lines
- Do not include auto-generated timestamps or tool attribution
- Match the tone and style of existing project documentation
