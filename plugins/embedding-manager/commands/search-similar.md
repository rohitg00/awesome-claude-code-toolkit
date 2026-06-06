# /search-similar - Search Similar Items

Find semantically similar items using vector similarity search.

## Steps

1. Take the search query text from the user
2. Generate an embedding for the query using the same model as the index
3. Perform approximate nearest neighbor search in the vector store
4. Retrieve the top-K most similar items (default: 10)
5. Calculate and display similarity scores for each result
6. Apply metadata filters if specified (category, date range, source)
7. Re-rank results using cross-encoder for improved precision
8. Deduplicate results that are too similar to each other (similarity > 0.95)
9. Format results with: rank, similarity score, source text, metadata
10. Provide a relevance assessment for the top results
11. Suggest query refinements if results are not satisfactory
12. Cache the query embedding for repeated searches

## Rules

- Use the same embedding model for queries and indexed items
- Set a minimum similarity threshold to filter irrelevant results (default: 0.5)
- Return metadata with results for context and source attribution
- Handle empty results gracefully with alternative search suggestions
- Limit result count to avoid overwhelming output (max 50)
- Include the similarity metric used (cosine, dot product, euclidean)
- Cache frequently searched queries for faster response times
