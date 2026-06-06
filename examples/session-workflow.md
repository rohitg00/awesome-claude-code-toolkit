# Example: Productive Claude Code Session

A walkthrough of a typical development session building a user settings page.

## 1. Session Start

Load the project context and check the current state:

```
> /context load dev
> What's the current state of the settings feature? Check the issue and any existing code.
```

Claude reads the linked issue, scans the codebase for existing settings-related files,
and summarizes what exists and what needs to be built.

## 2. Plan Before Coding

Ask Claude to create a plan before writing code:

```
> Plan the implementation for the user settings page. Break it into steps.
```

Claude produces a task list:
1. Add `settings` table migration with user preferences columns.
2. Create the settings repository and service.
3. Add tRPC procedures for get/update settings.
4. Build the settings form component with validation.
5. Write tests for the service and API layer.

## 3. Implement Incrementally

Work through each step, verifying as you go:

```
> Start with step 1. Create the migration for the settings table.
```

Claude generates the migration SQL, runs `db:migrate`, and confirms it applied.

```
> Now create the repository and service for settings. Follow the existing patterns.
```

Claude finds the existing `UserRepository` as a reference, creates `SettingsRepository`
and `SettingsService` matching the same patterns.

## 4. Test Alongside Implementation

Write tests for each layer before moving to the next:

```
> Write unit tests for SettingsService. Cover the happy path and error cases.
```

Claude creates test file, runs the suite, fixes any failures. Only then moves to the
API and UI layers.

## 5. Verify Visually

For UI work, check the rendered output:

```
> Start the dev server and take a screenshot of the settings page.
```

Claude starts the server, navigates to the page with Puppeteer, and shares a screenshot
for review.

## 6. Self-Review Before PR

Before creating the PR, review your own changes:

```
> Review all the changes in this branch. Check for missing error handling,
  type safety issues, and test coverage gaps.
```

Claude runs `git diff main...HEAD`, reviews each file, and flags any issues to fix
before the PR.

## 7. Create the PR

```
> Create a PR for this branch. Link it to issue #42.
```

Claude pushes the branch, creates the PR with a structured description, and links
the issue.

## 8. Session Wrap-Up

Save learnings and context for the next session:

```
> Wrap up this session. Save what we learned and any follow-up items.
```

Claude updates the session notes in CLAUDE.md with decisions made, patterns discovered,
and pending work for the next session.
