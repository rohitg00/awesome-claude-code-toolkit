# /create-contract - Create API Contract

Create a Pact contract definition for consumer-driven contract testing.

## Steps

1. Ask the user for the consumer service name and provider service name
2. Identify the API interactions to define (endpoints, methods, request/response schemas)
3. Check if Pact is installed in the project; if not, suggest installation
4. Create the contract test file with consumer and provider configuration
5. Define each interaction: request method, path, headers, query params, and body
6. Specify expected response status codes, headers, and body matchers
7. Use Pact matchers (like, eachLike, term) for flexible matching instead of exact values
8. Add provider states for each interaction describing required preconditions
9. Generate the contract test and run it to produce the Pact file
10. Validate the generated Pact JSON file is well-formed
11. Save the Pact file to the pacts directory for sharing with the provider team

## Rules

- Use semantic versioning for consumer and provider names
- Prefer Pact matchers over exact value matching for resilient contracts
- Each interaction must have a unique description
- Include both success and error response scenarios
- Do not include authentication tokens in the contract; use provider states instead
- Keep contracts focused on the data structure, not specific values
- Name contract files as `consumer-provider.json`
