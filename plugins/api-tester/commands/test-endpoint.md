Test an API endpoint with various request scenarios and validate responses.

## Steps

1. Parse the endpoint specification:
   - URL, HTTP method, headers, authentication.
   - Request body (JSON, form data, multipart).
   - Expected response status and body schema.
2. Generate test scenarios:
   - **Happy path**: Valid request with expected response.
   - **Validation**: Missing required fields, invalid types, out-of-range values.
   - **Auth**: Missing token, expired token, insufficient permissions.
   - **Edge cases**: Empty body, very large payload, special characters.
   - **Idempotency**: Repeated identical requests produce consistent results.
3. Execute each test:
   - Send the request using `curl` or `fetch`.
   - Capture response status, headers, body, and timing.
   - Validate against expected results.
4. Check response quality:
   - Correct content type header.
   - Consistent error format across failure cases.
   - Proper HTTP status codes (not 200 for errors).
   - No sensitive data in error responses.
5. Generate a test summary with pass/fail for each scenario.

## Format

```
API Test: <METHOD> <endpoint>

| Scenario | Status | Expected | Actual | Time | Result |
|----------|--------|----------|--------|------|--------|
| Valid request | 200 | 200 | 200 | 45ms | PASS |
| Missing auth | 401 | 401 | 401 | 12ms | PASS |
| Invalid body | 400 | 400 | 500 | 23ms | FAIL |

Pass: <N>/<total>
Issues: <list of failures>
```

## Rules

- Test authentication and authorization for every endpoint.
- Verify error responses do not leak stack traces or internal details.
- Check that CORS headers are set correctly for browser-accessible APIs.
- Test with realistic payloads, not minimal test data.
- Verify rate limiting works as documented.
