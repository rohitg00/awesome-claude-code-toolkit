# /create-retriever - Create RAG Retriever

Build a retrieval component for RAG pipeline with optimized search.

## Steps

1. Configure the vector store connection and embedding model
2. Implement the retrieval function with configurable parameters:
   - Top-K results (default: 5)
   - Similarity threshold (default: 0.7)
   - Metadata filters (source, date range, category)
3. Add hybrid search combining vector similarity with keyword BM25 search
4. Implement re-ranking using a cross-encoder model for result quality
5. Add contextual compression to extract only relevant parts of retrieved chunks
6. Implement query transformation: expand, decompose, or rephrase the user query
7. Add caching for repeated queries with a configurable TTL
8. Build the prompt template that incorporates retrieved context
9. Add source citation formatting to trace answers to specific documents
10. Implement fallback behavior when no relevant documents are found
11. Add evaluation metrics: retrieval precision, recall, and MRR
12. Test the retriever with sample queries and verify relevance

## Rules

- Always return source citations with retrieved content
- Set a minimum similarity threshold to avoid irrelevant results
- Use re-ranking to improve result quality beyond pure vector similarity
- Implement query decomposition for complex multi-part questions
- Cache embeddings for frequently asked queries
- Handle empty results gracefully with a "no relevant information found" response
- Log retrieval metrics for continuous improvement
