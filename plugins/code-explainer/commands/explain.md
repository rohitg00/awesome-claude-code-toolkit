Explain a code file, function, or concept in clear, structured language.

## Steps

1. Read the target code (file path, function name, or code block).
2. Determine the audience level from context (junior, mid, senior, non-technical).
3. Analyze the code structure:
   - Purpose: What problem does this code solve?
   - Inputs: What data does it receive and from where?
   - Processing: What transformations or logic does it apply?
   - Outputs: What does it produce or modify?
   - Side effects: What external state does it change?
4. Break down complex sections:
   - Explain algorithms step by step.
   - Clarify language-specific idioms or patterns.
   - Describe the data flow through the code.
5. Identify design patterns in use (Observer, Strategy, Factory, etc.).
6. Note any non-obvious behavior, gotchas, or edge cases.
7. Provide analogies for complex concepts when appropriate.

## Format

```
## <File/Function Name>

### Purpose
<one-sentence summary>

### How It Works
1. <step-by-step explanation>

### Key Concepts
- <pattern/concept>: <explanation>

### Gotchas
- <non-obvious behavior to be aware of>

### Dependencies
- <what this code depends on>
- <what depends on this code>
```

## Rules

- Explain the "why" not just the "what"; anyone can read the code.
- Use concrete examples with real values from the codebase.
- Avoid jargon unless explaining it; match the audience level.
- Keep explanations under 100 lines; link to deeper resources for complex topics.
- Do not restate code as prose; explain the intent and reasoning behind it.
