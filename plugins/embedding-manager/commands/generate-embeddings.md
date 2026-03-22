# /generate-embeddings - Generate Vector Embeddings

Generate vector embeddings for text data using embedding models.

## Steps

1. Ask the user for the input data: text file, database table, or API responses
2. Select the embedding model: OpenAI text-embedding-3, Cohere embed, Sentence-BERT, or local model
3. Preprocess the input text: clean, normalize, truncate to model's max token length
4. Batch the inputs for efficient API calls (batch size based on model limits)
5. Generate embeddings with retry logic for API rate limits and transient errors
6. Validate embedding dimensions match the expected model output
7. Normalize embeddings to unit length for cosine similarity searches
8. Store embeddings with their source text and metadata in the vector database
9. Create an index for efficient nearest-neighbor search
10. Verify embedding quality by checking similarity of known-similar items
11. Report: total items embedded, dimensions, storage size, API cost estimate
12. Save the embedding configuration for future regeneration

## Rules

- Batch API calls to stay within rate limits and reduce costs
- Implement exponential backoff retry for API failures
- Truncate text to the model's maximum token length before embedding
- Normalize embeddings for consistent similarity calculations
- Store the model name and version with embeddings for reproducibility
- Cache embeddings to avoid regenerating unchanged content
- Monitor API costs and set spending alerts for large datasets
