# /optimize-prompt - Optimize AI Prompt

Rewrite and optimize an AI prompt for better performance and reliability.

## Steps

1. Read the original prompt and understand its intended purpose
2. Identify the target model and use case (chat, completion, function calling)
3. Restructure the prompt with clear sections: role, context, task, constraints, format
4. Rewrite ambiguous instructions with specific, measurable language
5. Add or improve output format specification with examples
6. Include edge case handling instructions
7. Add few-shot examples if the task benefits from them
8. Implement chain-of-thought reasoning for complex tasks
9. Add guardrails: what the model should not do, how to handle uncertainty
10. Optimize token usage: remove redundant words, consolidate instructions
11. A/B test the original vs optimized prompt with sample inputs
12. Present the optimized prompt with annotations explaining each change

## Rules

- Preserve the original intent; do not change what the prompt is trying to achieve
- Use imperative language for instructions (do X, not "you should X")
- Place the most important instructions at the beginning and end of the prompt
- Use XML tags or markdown headers to separate prompt sections
- Include a fallback instruction for when the model cannot complete the task
- Test with adversarial inputs to verify robustness
- Keep the optimized prompt as concise as possible while maintaining effectiveness
