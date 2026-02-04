Analyze and improve an AI prompt for clarity, specificity, and effectiveness.

## Steps

1. Read the provided prompt or command definition.
2. Evaluate against prompt quality dimensions:
   - **Clarity**: Is the instruction unambiguous?
   - **Specificity**: Does it define the expected output format?
   - **Context**: Does it provide enough background information?
   - **Constraints**: Are boundaries and rules clearly stated?
   - **Examples**: Are there concrete examples of good output?
3. Identify common issues:
   - Vague verbs ("handle", "process", "manage") without specifics.
   - Missing edge case guidance.
   - No output format specification.
   - Contradictory instructions.
   - Missing success criteria.
4. Rewrite the prompt with improvements:
   - Add structured sections (Steps, Format, Rules).
   - Replace vague instructions with specific actions.
   - Add output format with examples.
   - Define explicit constraints and error handling.
5. Compare original vs improved versions side by side.

## Format

```
Prompt Analysis:
  Clarity: <1-5>/5
  Specificity: <1-5>/5
  Context: <1-5>/5

Issues found:
  - <issue description>

Improved prompt:
  <rewritten prompt>

Changes made:
  - <what was improved and why>
```

## Rules

- Preserve the original intent; only improve clarity and structure.
- Use imperative mood for instructions ("Run X" not "You should run X").
- Every prompt should have Steps, Format, and Rules sections.
- Limit prompts to under 50 lines; split complex workflows into sub-commands.
- Test the improved prompt against the original to verify better results.
