# /verify-contract - Verify API Contract

Verify that a provider service fulfills all consumer contracts.

## Steps

1. Locate all Pact contract files for the current provider service
2. List the consumers and their interaction counts from each contract
3. Start the provider service in test mode if not already running
4. Configure provider states handler to set up required test data
5. Run the Pact verification against each consumer contract
6. For each interaction, report: description, status (pass/fail), response time
7. If verification fails, show the diff between expected and actual response
8. Check for missing provider states and report them
9. Verify backward compatibility with previous contract versions
10. Generate a verification results summary with overall pass/fail
11. Publish verification results to the Pact Broker if configured

## Rules

- All provider states must be implemented before verification
- Run verification against the latest consumer contract version
- Do not skip failing interactions; report all failures
- Include response time for each verified interaction
- Ensure the provider is running with test data, not production data
- Log the provider version being verified for traceability
- Clean up test data after verification completes
