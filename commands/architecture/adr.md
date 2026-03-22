Write an Architecture Decision Record documenting a significant technical decision.

## Steps

1. Ask for or infer the decision topic from the argument (e.g., "use PostgreSQL over MongoDB").
2. Scan the codebase for existing ADRs in `docs/adr/`, `docs/decisions/`, or `adr/` directories.
3. Determine the next ADR number by counting existing records.
4. Research the current codebase to gather context:
   - What technologies are currently used.
   - What constraints exist (team size, performance requirements, existing integrations).
5. Draft the ADR with all required sections.
6. Create the file as `docs/adr/NNNN-<slug>.md`.
7. If a `docs/adr/README.md` index exists, add an entry for the new ADR.

## Format

```markdown
# ADR-NNNN: <Title>

## Status
Proposed | Accepted | Deprecated | Superseded by ADR-XXXX

## Context
What is the issue that we are seeing that motivates this decision?

## Decision
What is the change that we are proposing and/or doing?

## Consequences
What becomes easier or harder as a result of this decision?

### Positive
- Benefit 1

### Negative
- Tradeoff 1

### Risks
- Risk 1 with mitigation strategy
```

## Rules

- ADRs are immutable once accepted; create a new ADR to supersede an old one.
- Keep the context section factual and free of opinion.
- List at least one positive, one negative, and one risk consequence.
- Use the project's existing ADR format if one already exists.
- Date the ADR with the current date in the status section.
