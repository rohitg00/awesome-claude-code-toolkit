---
name: prompt-engineering
description: Prompt engineering patterns including structured prompts, chain-of-thought, few-shot learning, and system prompt design
---

# Prompt Engineering

## Structured System Prompt

```
You are a senior code reviewer. Your role is to analyze pull requests for:
1. Correctness - logic errors, edge cases, off-by-one errors
2. Security - injection, authentication, data exposure
3. Performance - N+1 queries, unnecessary allocations, missing indexes
4. Maintainability - naming, complexity, test coverage

For each issue found, respond with:
- Severity: critical | warning | suggestion
- File and line reference
- What is wrong
- How to fix it (with code snippet)

If the code is well-written, say so briefly. Do not invent problems.
```

Structure system prompts with role, scope, output format, and constraints. Be explicit about what the model should NOT do.

## Chain-of-Thought

```
Analyze this database query for performance issues.

Think step by step:
1. Identify the tables and joins involved
2. Check if appropriate indexes exist for the WHERE and JOIN conditions
3. Look for full table scans or cartesian products
4. Estimate the row count at each step
5. Suggest specific index creation or query restructuring

Query:
SELECT o.*, u.name, p.title
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN products p ON o.product_id = p.id
WHERE o.created_at > '2024-01-01'
AND u.country = 'US'
ORDER BY o.created_at DESC
LIMIT 50;
```

Chain-of-thought prompting improves accuracy on reasoning tasks by forcing the model to show intermediate steps.

## Few-Shot Examples

```
Convert natural language to SQL. Follow these examples:

Input: "How many orders were placed last month?"
Output: SELECT COUNT(*) FROM orders WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') AND created_at < DATE_TRUNC('month', CURRENT_DATE);

Input: "Top 5 customers by total spending"
Output: SELECT customer_id, SUM(total_amount) AS total_spent FROM orders GROUP BY customer_id ORDER BY total_spent DESC LIMIT 5;

Input: "Products that have never been ordered"
Output: SELECT p.* FROM products p LEFT JOIN order_items oi ON p.id = oi.product_id WHERE oi.id IS NULL;

Now convert:
Input: "Average order value per country for the last quarter"
```

Provide 3-5 diverse examples that demonstrate the expected format and edge cases.

## Tool Use / Function Calling

```json
{
  "tools": [
    {
      "name": "search_codebase",
      "description": "Search for code patterns across the repository. Use when you need to find implementations, usages, or definitions.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Regex pattern or keyword to search for"
          },
          "file_type": {
            "type": "string",
            "description": "File extension filter (e.g., 'ts', 'py')"
          }
        },
        "required": ["query"]
      }
    }
  ]
}
```

Write tool descriptions that explain WHEN to use the tool, not just what it does.

## Prompt Template Pattern

```python
def build_review_prompt(diff: str, context: str, rules: list[str]) -> str:
    rules_text = "\n".join(f"- {rule}" for rule in rules)

    return f"""Review this code diff against the following rules:
{rules_text}

Context about the codebase:
{context}

Diff to review:
```
{diff}
```

Respond with a JSON array of findings. If no issues, return an empty array.
Each finding: {{"severity": "critical|warning|info", "line": number, "message": "string", "suggestion": "string"}}"""
```

## Anti-Patterns

- Vague instructions like "be helpful" or "do your best"
- Asking the model to "be creative" when you need deterministic output
- Not specifying output format (JSON, markdown, plain text)
- Stuffing too many unrelated tasks into a single prompt
- Using negations ("don't do X") without saying what to do instead
- Not testing prompts with adversarial or edge-case inputs

## Checklist

- [ ] System prompt defines role, scope, format, and constraints
- [ ] Chain-of-thought used for multi-step reasoning tasks
- [ ] Few-shot examples cover typical and edge cases
- [ ] Output format explicitly specified (JSON schema, markdown, etc.)
- [ ] Tool descriptions explain when and why to use each tool
- [ ] Prompts tested with adversarial inputs
- [ ] Temperature and top_p set appropriately for the task
- [ ] Prompt templates are parameterized, not hardcoded strings
