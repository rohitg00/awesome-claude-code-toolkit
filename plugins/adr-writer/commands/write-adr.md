# /write-adr - Write Architecture Decision Record

Create a new Architecture Decision Record documenting a technical decision.

## Steps

1. Ask the user for the decision title and context
2. Determine the next ADR number by scanning existing ADRs in the docs/adr directory
3. Ask about the decision context: what problem is being solved and why now
4. Gather the options considered with pros and cons for each
5. Document the chosen option and the reasoning behind the decision
6. Identify consequences: what changes, what trade-offs are accepted
7. Note the decision status: proposed, accepted, deprecated, or superseded
8. Link to related ADRs if this decision supersedes or relates to previous ones
9. Format the ADR using the standard template: Title, Status, Context, Decision, Consequences
10. Save the ADR as `docs/adr/NNNN-title-slug.md` with zero-padded number
11. Update the ADR index file if one exists
12. Report the created ADR path and number

## Rules

- Follow the Michael Nygard ADR format (Title, Status, Context, Decision, Consequences)
- Number ADRs sequentially with zero-padded 4-digit numbers (0001, 0002)
- Keep the title concise and descriptive of the decision, not the problem
- Include at least two alternatives that were considered
- Document consequences honestly, including negative trade-offs
- Never modify existing accepted ADRs; create a new one that supersedes
- Create the docs/adr directory if it does not exist
