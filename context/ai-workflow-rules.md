# AI Workflow Rules

## Development Approach

Build **ShopAssist AI** incrementally using a strict, spec-driven workflow. The context files in `context/` and feature specification files in `context/feature-specs/` define all system boundaries, data contracts, and implementation requirements.

Always implement against the approved feature specs—never guess, speculate, or infer behavior from scratch.

---

## Assignment Hard Constraints

1. **Strictly No External Tools, Agents, or Plugins**: The assistant must not invoke external tool-calling frameworks (e.g. LangChain agents, function calling tools, or live web search). All responses must emerge purely from prompt orchestration and conversation memory.
2. **Strictly No Retrieval-Augmented Generation (RAG)**: Do not use vector databases (Chroma, Pinecone, FAISS) or embeddings-based retrieval. Domain knowledge (catalog, mock orders, policies) must be injected directly into structured system prompts.
3. **Local CPU Inference Only**: Inference must run entirely on local CPU using a quantized open-weight model (Q4_K_M). Cloud model APIs (OpenAI, Anthropic, Gemini, Groq, etc.) are strictly forbidden.

---

## Scoping & Splitting Rules

- **One Spec Unit at a Time**: Work sequentially through the file plan: Backend (`BE`) first, then Frontend (`FE`), followed by Verification (`VERIFY`).
- **Target Size Discipline**: Every spec file must remain between 80–150 lines. If a feature layer exceeds 150 lines, split it into modular sub-specs (e.g. `schema` and `logic`).
- **Split Multi-Concern Changes**: Never combine backend WebSocket logic, prompt templating, and frontend DOM updates in a single implementation step.

---

## Handling Ambiguity & Deviations

- If a requirement or edge case is missing or ambiguous, do NOT silently invent an ad-hoc solution.
- Make the smallest reasonable assumption necessary to proceed.
- Immediately log the assumption in `context/feature-specs/DEVIATIONS.md` using the format:
  ```markdown
  - **[FILE-ID]**: [What was ambiguous] -> [Assumption made]
  ```
- If the ambiguity affects core schemas in `000-shared-contracts.md`, **STOP** and request explicit user confirmation.

---

## Protected Files

Do not modify or diverge from the following files without explicit instructions:
- `context/feature-specs/000-shared-contracts.md` (Single source of truth for all types and schemas).
- `context/testing-strategy.md` (Quality assurance policies and DoD).

---

## Before Moving to the Next Unit ("Stop-the-Line" Quality Gate)

A feature spec is NOT complete until all of the following conditions are satisfied:
1. The code runs end-to-end within its specified scope.
2. No invariant in `context/architecture.md` was violated.
3. All unit, WebSocket API, and DOM simulation tests pass 100% (`pytest tests/`). Zero failing or skipped tests.
4. Latency benchmarks (TTFT < 1.5s) are verified where applicable.
5. A dedicated SQA test report is generated and saved in `feature-test-reports/FEAT-XXX-test-report.md`.
6. `context/progress-tracker.md` and `context/feature-specs/INDEX.md` are updated to reflect the passing status.
