# Assignment 2: Adding Retrieval-Augmented Generation (RAG)

## Introduction

In Assignment 1 you built a conversational assistant that relied only on prompt orchestration and conversation memory. That works for general dialogue, but a real business assistant must also answer questions from specific documents it was never trained on, such as policies, price lists, FAQs, and catalogues.

In this assignment you will add that ability using **Retrieval-Augmented Generation (RAG)**, so the assistant looks up relevant information before answering instead of guessing.

**Constraint:** External tools and agents are still not allowed. Everything must be done with RAG only.

## Objectives

- Build an offline pipeline that chunks, embeds, and indexes 50-100 domain documents.
- Retrieve the most relevant chunks for each user query and ground the response in them.
- Preserve real-time token streaming; retrieval must not make the assistant feel slower.
- Fail gracefully when retrieval finds nothing useful, rather than forcing a bad answer.

## System Architecture

You are extending your Assignment 1 architecture with one new module. **The WebSocket API contract from Assignment 1 must not change.**

```
Web UI <--WebSocket--> FastAPI Backend <--> Conversation Manager <--> Local LLM Engine
                                                    |
                                                    +--> Retrieval Module (Embedding + Vector Store)
                                                                |
                                                        Your Document Collection
```

## Document Collection

Build a corpus of **50-100 documents** for the business use case you chose in Assignment 1. Accepted formats: PDF, plain text, Markdown, or HTML.

Suggested content by domain:

| Domain | Suggested documents |
|---|---|
| Gym / Fitness Membership | Membership plans, class schedules, trainer bios, gym policies |
| Real Estate Rental & Leasing | Property listings, lease terms, building policies |
| Event & Venue Booking | Venue packages, catering menus, booking terms |
| Library | Catalogue, borrowing policies, fine rules |
| Car Rental | Fleet listing, pricing, insurance terms |
| E-Commerce Order Support | Product FAQs, return policy, shipping information |

You may write the documents yourself, adapt real public examples, or generate a first draft with an AI tool and edit it. Whichever you choose, the documents must be realistic enough that grounded answers are **meaningfully different** from ungrounded ones.

## Tasks

### Phase I: Indexing Pipeline

- Chunk your documents using a chunking strategy you define and can justify.
- Embed each chunk with a local, CPU-friendly embedding model (e.g., `all-MiniLM-L6-v2` via sentence-transformers, or a GGUF-compatible embedding model).
- Store the embeddings in a CPU vector store such as Chroma or FAISS.
- Make the pipeline **re-runnable**, so you can update the document set later without rebuilding everything from scratch.

### Phase II: Retrieval Integration

For every user query, your conversation manager must:

- Embed the query and retrieve the top-k most relevant chunks (**k ≥ 3**).
- Inject the retrieved chunks into the prompt without exceeding the model's context window. You need an **explicit strategy** for this (e.g., a token budget).
- Ground the response in the retrieved content, and refer back to the source document where appropriate.

### Phase III: Keeping It Real-Time

Retrieval adds a step before generation begins, so it is the most likely cause of slowdown. Design around it:

- **Latency:** Benchmark retrieval time separately from generation time and aim to keep retrieval **under one second**. Report the numbers in your README. Overall latency should be as low as possible.
- **Streaming:** Token streaming over the WebSocket must work exactly as it did in Assignment 1.
- **Caching:** Cache embeddings or results for queries you expect to repeat.
- **Concurrency:** The system must still support concurrent users. When multiple users trigger RAG (or tools) at the same time, it must remain responsive.

### Phase IV: Failure Handling

Your system must handle each of the following without crashing or hanging:

1. **No relevant matches:** If a query has no relevant results in the corpus, the assistant should say so and fall back to normal conversation rather than fabricating an answer from a weak match.
2. **Retrieval infrastructure failure:** The vector store or embedding step fails or times out.
3. **Context overflow:** A retrieved chunk, combined with conversation history, would exceed the context window.

## Evaluation

| Criterion | Weight |
|---|---|
| Correctness & Completeness | 50% |
| Viva (code walkthrough, live Q&A, reproducing your prompts) | 25% |
| Real-time behaviour & performance (latency, streaming, failure handling) | 25% |
| **Total** | **100%** |
| Bonus (see below) | up to +10% |

## Bonus (up to +10%)

Choose **at most one**:

- **Hybrid search or re-ranking:** Combine keyword and vector search, or add a re-ranking step over your top-k results. Show whether it improves retrieval quality.
- **Visible citations:** Show the user, directly in the chat UI, which source document(s) an answer was grounded in.
- **Something else:** Any other creative idea earns extra credit, provided it does not disrupt the required functionality.

## Deliverables

Submit a GitHub repository (or .zip) containing:

1. **Your document collection.**
2. **Your offline indexing pipeline script.**
3. **Your updated conversation manager** with the retrieval module integrated.
4. **An updated README.md** covering:
   - Embedding model and vector store choice, and why
   - Chunking and top-k parameters
   - Retrieval latency benchmarks
   - Architecture diagram
   - Known limitations
