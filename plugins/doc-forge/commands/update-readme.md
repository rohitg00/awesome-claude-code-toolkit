# /doc-forge:update-readme

Update or create a README.md that accurately reflects the current state of the project.

## Process

1. Read the existing README.md if one exists:
   - Preserve any custom content, badges, or sections the author has written
   - Identify sections that are outdated based on current code
   - Note the existing structure and writing style to maintain consistency

2. Gather current project information:
   - Read package.json, pyproject.toml, Cargo.toml, or go.mod for name, version, description
   - Check the license file for license type
   - Read the entry point to understand what the project does
   - Run `git remote get-url origin` to determine the repository URL
   - Check CI workflow files for build/test commands
   - Look for Docker support (Dockerfile, docker-compose.yml)
   - Identify supported platforms and requirements

3. Generate or update these sections:

### Title and Description
- Project name as an H1 heading
- One-paragraph description of what the project does and who it is for
- Key badges: build status, version, license, language

### Installation
- Prerequisites (runtime version, system dependencies)
- Step-by-step installation commands for each supported method (npm, pip, cargo, brew)
- Verification command to confirm successful installation

### Quick Start
- Minimal working example: the fewest lines of code to see the project in action
- Expected output of the example
- Link to more detailed usage documentation

### Usage
- Core API or CLI commands with examples
- Configuration options with a table of environment variables or flags
- Common use cases with code snippets

### Development
- How to set up the development environment (clone, install deps, run tests)
- How to run the test suite
- How to build the project
- Code style and contribution guidelines (brief, or link to CONTRIBUTING.md)

### Architecture (for larger projects)
- High-level overview of the directory structure
- Key modules and their responsibilities
- Data flow or request lifecycle diagram (text-based)

### License
- License type with a link to the LICENSE file

4. Cross-reference the README against the actual codebase:
   - Verify that all installation commands work
   - Confirm that documented CLI flags or API methods exist in the code
   - Check that example code matches the current API signatures
   - Ensure version numbers are current

## Output

Write or update README.md in the project root. If updating, show a diff of changes for review.

## Rules

- Write for someone who has never seen the project before
- Lead with the value proposition: what problem does this solve
- Keep installation instructions copy-paste ready (no placeholder values that need editing)
- Use actual output from the project in examples, not fabricated output
- Do not pad the README with unnecessary sections; shorter is better if the project is simple
- Maintain the original author's voice and style when updating
- Test every code block mentally: would this actually run without errors?
- Include a "Troubleshooting" section only if there are known common issues
