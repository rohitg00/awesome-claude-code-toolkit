# /add-model - Add Data Model

Create a Swift data model with Codable conformance and validation.

## Steps

1. Ask the user for the model name and its properties with types
2. Create the model struct with Codable conformance
3. Add proper property types: String, Int, Double, Date, URL, optional types
4. Implement CodingKeys enum for JSON key mapping if API uses different naming
5. Add custom Decodable init for complex parsing (nested objects, date formats)
6. Implement Equatable and Hashable conformance for use in collections and SwiftUI
7. Add Identifiable conformance with a unique ID property
8. Create validation methods for business rules (email format, required fields)
9. Add computed properties for derived values (full name, formatted date)
10. Create a mock/preview instance for SwiftUI previews and testing
11. Add the model to the appropriate module or feature directory
12. Create unit tests for encoding, decoding, and validation

## Rules

- Use structs for models, not classes, unless reference semantics are required
- Make properties immutable (let) unless mutation is explicitly needed
- Handle optional fields gracefully with nil-coalescing or default values
- Use ISO 8601 date format for JSON dates with a custom decoder
- Include a static preview instance for SwiftUI development
- Follow Swift naming conventions: camelCase properties, PascalCase types
- Do not expose internal implementation details in the model's public API
