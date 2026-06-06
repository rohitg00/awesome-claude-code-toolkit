# /analyze-prompt - Analyze AI Prompt

Analyze an AI prompt for clarity, effectiveness, and potential issues.

## Steps

1. Read the prompt text provided by the user
2. Assess prompt structure: system instruction, context, task, format, examples
3. Check for clarity: ambiguous language, vague instructions, missing context
4. Evaluate specificity: are constraints clearly defined (length, format, tone)
5. Identify missing elements: examples, output format, edge case handling
6. Check for conflicting instructions that could confuse the model
7. Assess the prompt length: too short (underspecified) or too long (diluted focus)
8. Evaluate the role or persona definition if present
9. Check for proper few-shot examples if the task requires them
10. Identify potential failure modes: hallucination triggers, unsafe content risks
11. Score the prompt on: clarity (1-10), specificity (1-10), completeness (1-10)
12. Provide specific improvement recommendations ranked by impact

## Rules

- Evaluate against the stated goal of the prompt
- Consider the target model's capabilities and limitations
- Check for prompt injection vulnerabilities in user-facing prompts
- Assess whether the prompt uses chain-of-thought when needed
- Verify output format instructions are unambiguous
- Do not rewrite the entire prompt; suggest targeted improvements
- Consider token efficiency: remove redundant instructions
