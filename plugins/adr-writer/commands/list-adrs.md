# /list-adrs - List Architecture Decision Records

List and summarize all existing Architecture Decision Records.

## Steps

1. Locate the ADR directory (docs/adr, docs/decisions, or architecture/decisions)
2. Scan for all markdown files matching the ADR naming pattern
3. Parse each ADR file to extract: number, title, status, and date
4. Group ADRs by status: accepted, proposed, deprecated, superseded
5. Count ADRs in each status category
6. Display a formatted table: Number, Title, Status, Date
7. Highlight any proposed ADRs that need review
8. Identify superseded ADRs and link to their replacements
9. Show the total count and date range of decisions
10. Flag any ADRs with missing or malformed metadata
11. Suggest creating an ADR if no records exist yet

## Rules

- Sort ADRs by number in ascending order
- Clearly indicate the status of each ADR with visual markers
- Show supersession chains (ADR X superseded by ADR Y)
- Do not modify any ADR files when listing
- Report if the ADR directory is missing or empty
- Include file paths for easy navigation
