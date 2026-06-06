# Dependency Management

## Version Pinning
- Pin exact versions in applications: `"lodash": "4.17.21"` not `"^4.17.21"`.
- Use ranges in libraries to avoid peer dependency conflicts: `"react": "^18.0.0"`.
- Commit lockfiles (`package-lock.json`, `pnpm-lock.yaml`, `Pipfile.lock`, `Cargo.lock`) to version control.
- Never run `npm install` or `pip install` without updating the lockfile.

## Adding Dependencies
- Check the package before adding: maintenance status, download count, open issues, last publish date.
- Prefer packages with zero or few transitive dependencies.
- Avoid packages that duplicate functionality already in the project or standard library.
- Document the reason for adding each dependency in the commit message.
- Prefer well-known packages: `zod` over `yup`, `date-fns` over `moment`, `got` over `request`.

## Auditing
- Run `npm audit`, `pip audit`, or `cargo audit` on every CI build.
- Fail the build on critical or high severity vulnerabilities.
- Use Dependabot or Renovate for automated dependency update PRs.
- Review Dependabot PRs weekly. Do not let them accumulate.
- Track known vulnerabilities in a security dashboard (Snyk, GitHub Security Advisories).

## Update Policies
- Critical security patches: apply within 24 hours.
- High security patches: apply within 7 days.
- Major version updates: evaluate quarterly. Test in a branch before merging.
- Minor and patch updates: batch monthly. Run full test suite before merging.
- Framework upgrades (React, Next.js, Django): plan as a dedicated task with migration guide review.

## Monorepo Dependencies
- Use workspace protocol (`workspace:*`) for internal package references.
- Hoist common dependencies to the root `package.json` to avoid duplication.
- Use `peerDependencies` for packages shared across workspace packages.
- Run `pnpm dedupe` or `npm dedupe` after major dependency changes.

## License Compliance
- Maintain an approved license list: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC.
- Flag GPL, AGPL, and SSPL dependencies for legal review before use.
- Run license checks in CI using `license-checker` or `pip-licenses`.
- Document any license exceptions in `LICENSE-EXCEPTIONS.md`.
