---
name: llm-integration
description: LLM integration patterns including API usage, streaming, function calling, RAG pipelines, and cost optimization
---

# LLM Integration

## API Client Pattern

```typescript
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

async function generateResponse(
  systemPrompt: string,
  userMessage: string,
  options?: { maxTokens?: number; temperature?: number }
): Promise<string> {
  const response = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: options?.maxTokens ?? 1024,
    temperature: options?.temperature ?? 0,
    system: systemPrompt,
    messages: [{ role: "user", content: userMessage }],
  });

  const textBlock = response.content.find(block => block.type === "text");
  return textBlock?.text ?? "";
}
```

## Streaming Responses

```typescript
async function streamResponse(
  messages: Array<{ role: "user" | "assistant"; content: string }>,
  onChunk: (text: string) => void
): Promise<string> {
  const stream = client.messages.stream({
    model: "claude-sonnet-4-20250514",
    max_tokens: 4096,
    messages,
  });

  let fullText = "";

  for await (const event of stream) {
    if (event.type === "content_block_delta" && event.delta.type === "text_delta") {
      onChunk(event.delta.text);
      fullText += event.delta.text;
    }
  }

  return fullText;
}

const response = await streamResponse(
  [{ role: "user", content: "Explain async/await in TypeScript" }],
  (chunk) => process.stdout.write(chunk)
);
```

## Function Calling (Tool Use)

```typescript
const tools: Anthropic.Tool[] = [
  {
    name: "search_database",
    description: "Search the product database by name, category, or price range",
    input_schema: {
      type: "object" as const,
      properties: {
        query: { type: "string", description: "Search query" },
        category: { type: "string", description: "Product category filter" },
        max_price: { type: "number", description: "Maximum price" },
      },
      required: ["query"],
    },
  },
];

async function agentLoop(userMessage: string): Promise<string> {
  const messages: Anthropic.MessageParam[] = [
    { role: "user", content: userMessage },
  ];

  while (true) {
    const response = await client.messages.create({
      model: "claude-sonnet-4-20250514",
      max_tokens: 4096,
      tools,
      messages,
    });

    if (response.stop_reason === "end_turn") {
      const text = response.content.find(b => b.type === "text");
      return text?.text ?? "";
    }

    const toolUse = response.content.find(b => b.type === "tool_use");
    if (!toolUse || toolUse.type !== "tool_use") break;

    const result = await executeToolCall(toolUse.name, toolUse.input);

    messages.push({ role: "assistant", content: response.content });
    messages.push({
      role: "user",
      content: [{ type: "tool_result", tool_use_id: toolUse.id, content: result }],
    });
  }

  return "";
}
```

## RAG Pipeline

```typescript
import { embed } from "./embeddings";

interface Chunk {
  id: string;
  text: string;
  metadata: Record<string, string>;
  embedding: number[];
}

async function retrieveAndGenerate(query: string): Promise<string> {
  const queryEmbedding = await embed(query);

  const relevantChunks = await vectorDb.search({
    vector: queryEmbedding,
    topK: 5,
    filter: { source: "documentation" },
  });

  const context = relevantChunks
    .map((chunk, i) => `[${i + 1}] ${chunk.text}`)
    .join("\n\n");

  const response = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 2048,
    system: `Answer questions using the provided context. Cite sources with [n] notation. If the context doesn't contain the answer, say so.`,
    messages: [
      {
        role: "user",
        content: `Context:\n${context}\n\nQuestion: ${query}`,
      },
    ],
  });

  return response.content[0].type === "text" ? response.content[0].text : "";
}
```

## Document Chunking

```typescript
function chunkDocument(
  text: string,
  options: { chunkSize: number; overlap: number }
): string[] {
  const { chunkSize, overlap } = options;
  const chunks: string[] = [];
  const sentences = text.split(/(?<=[.!?])\s+/);
  let current = "";

  for (const sentence of sentences) {
    if (current.length + sentence.length > chunkSize && current.length > 0) {
      chunks.push(current.trim());
      const words = current.split(" ");
      const overlapWords = words.slice(-Math.floor(overlap / 5));
      current = overlapWords.join(" ") + " " + sentence;
    } else {
      current += (current ? " " : "") + sentence;
    }
  }

  if (current.trim()) chunks.push(current.trim());
  return chunks;
}
```

## Cost Optimization

```typescript
function selectModel(task: TaskType): string {
  switch (task) {
    case "classification":
    case "extraction":
      return "claude-haiku-4-20250514";
    case "analysis":
    case "coding":
      return "claude-sonnet-4-20250514";
    case "complex-reasoning":
      return "claude-opus-4-5-20251101";
    default:
      return "claude-sonnet-4-20250514";
  }
}
```

Use the smallest model that achieves acceptable quality. Cache embeddings and responses where possible. Batch requests when latency is not critical.

## Anti-Patterns

- Sending entire documents when only relevant chunks are needed
- Not implementing retry logic with exponential backoff for API calls
- Ignoring token usage tracking (leads to unexpected costs)
- Using the most expensive model for simple classification tasks
- Not validating or sanitizing LLM output before using it in code
- Building RAG without evaluating retrieval quality first

## Checklist

- [ ] API calls wrapped with retry logic and error handling
- [ ] Streaming used for user-facing responses
- [ ] Function calling schemas include clear descriptions
- [ ] RAG chunks sized appropriately (500-1000 tokens) with overlap
- [ ] Model selection based on task complexity
- [ ] Token usage tracked and monitored for cost control
- [ ] LLM output validated before downstream use
- [ ] Embeddings cached to avoid redundant API calls
