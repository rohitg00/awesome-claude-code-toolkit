Create a structured implementation plan for the requested feature or change.

## Steps

### 1. Requirements Analysis
- Clarify the goal: what problem does this solve and for whom?
- List functional requirements (what the system must do).
- List non-functional requirements (performance, security, scalability).
- Identify constraints (timeline, tech stack, backward compatibility).

### 2. Architecture Review
- Read the existing codebase structure to understand current patterns.
- Identify which modules, services, or components are affected.
- Determine if the change fits the existing architecture or requires structural changes.
- Check for existing utilities, patterns, or abstractions to reuse.

### 3. Step Breakdown
- Break the work into ordered, independently testable steps.
- Each step should be completable in one session and produce a working state.
- Format each step as:
  - **What**: The concrete deliverable.
  - **Where**: Which files or modules to touch.
  - **How**: Technical approach and key decisions.
  - **Test**: How to verify this step works.

### 4. Risk Assessment
- Identify what could go wrong at each step.
- Note dependencies on external systems or teams.
- Call out areas with high uncertainty that may need spikes.
- Suggest fallback approaches for risky steps.

### 5. Output the Plan
Present as a numbered checklist that can be executed sequentially.

## Rules

- Plans should target 3-10 steps. Fewer means the scope might be too narrow, more means break it into phases.
- Each step must leave the system in a deployable state. No half-implemented features.
- Include data migration steps if schema changes are involved.
- Flag anything that requires coordination with other people or teams.
- Estimate relative complexity (small/medium/large) for each step, not time.
