# /index-docs - Index Documents for RAG

Index documents into a vector store for retrieval-augmented generation.

## Steps

1. Ask the user for the document source: directory, URLs, database, or API
2. Detect document types: PDF, markdown, HTML, text, code, DOCX
3. Load documents using appropriate parsers for each file type
4. Split documents into chunks using semantic-aware chunking:
   - Respect paragraph and section boundaries
   - Target chunk size: 500-1000 tokens with 100-token overlap
5. Clean and preprocess chunks: remove boilerplate, normalize whitespace
6. Generate embeddings for each chunk using the configured embedding model
7. Store embeddings in the vector database: Pinecone, Weaviate, Chroma, or pgvector
8. Create metadata for each chunk: source file, page number, section title, date
9. Build an index mapping for fast retrieval and source citation
10. Validate the index by running sample queries and checking relevance
11. Report: documents indexed, total chunks, vector dimensions, storage size
12. Save the indexing configuration for incremental updates

## Rules

- Use semantic chunking that respects document structure over fixed-size splitting
- Include sufficient overlap between chunks to preserve context at boundaries
- Store source metadata with each chunk for citation and provenance
- Handle duplicate documents by comparing content hashes before indexing
- Support incremental indexing: add new documents without re-indexing everything
- Use the same embedding model for indexing and querying
- Monitor embedding costs and set budget alerts for large document sets
