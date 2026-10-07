# FEAT-008-FE — Web Chat UI Citation Badges & Retrieval Telemetry (P1)

**Layer**: Frontend  
**Goal**: Extend the Web Chat UI to render visible source citations directly below grounded assistant answers, provide interactive preview snippets, and display retrieval latency metrics alongside token generation telemetry.

---

## Depends on / Context pack / Consumes
**Depends on**: `context/feature-specs/000-shared-contracts.md`, `context/feature-specs/FEAT-004-FE-chat-interface.md`, `context/feature-specs/FEAT-007-BE-rag-retrieval-grounding.md`  
**Context pack**:
```typescript
export interface CitationItem {
  doc_id: string;
  title: string;
  section_header: string;
  score: number;
  snippet: string;
}

export interface StreamEndMetrics {
  turn_id: string;
  total_tokens: number;
  ttft_ms: number;
  total_duration_ms: number;
  tokens_per_second: number;
  retrieval_ms?: number;
  citations?: CitationItem[];
}
```
**Consumes**: `StreamEndMetrics`, `CitationItem` from `000-shared-contracts.md`; Web Chat UI from `FEAT-004-FE`.

---

## Provides / Exposes
```javascript
// Exposed client DOM utilities in frontend/app.js:
function renderCitationBadges(messageElement, citations) { /* Appends citation badge row */ }
function toggleCitationDrawer(citationId) { /* Expands snippet card */ }
function formatRetrievalTelemetry(metrics) { /* Returns "Retrieval: XXms | TTFT: XXms | XX tok/s" */ }
```

---

## Scope
- **Scope (In)**:
  - Source citation badge container appended below completed assistant messages with grounded context.
  - Interactive citation chip displaying document title and match percentage (e.g. `📄 Return Policy (89%)`).
  - Expandable drawer/popover showing section header, document ID, and source excerpt snippet.
  - Retrieval latency telemetry: renders `Retrieval: {retrieval_ms}ms` in the telemetry pill if present in `stream_end`.
  - Fallback indicator: if `citations` is empty and answer was ungrounded, displays subtle indicator `💬 Direct Dialogue (No matching doc)`.
  - Styling strictly consuming design tokens from `context/ui-context.md`.
- **Scope (Out)**:
  - Server-side token streaming or vector query execution (handled in `FEAT-007-BE`).

---

## Tech & Files to Touch
- `frontend/index.html` — Citation card template and container elements.
- `frontend/style.css` — Styling for citation pills, hover states, expandable snippet cards, and badges.
- `frontend/app.js` — WebSocket `stream_end` listener updating DOM with citations.
- `tests/test_frontend.js` — Simulated DOM tests verifying citation DOM node creation and event interactions.

---

## Tests to Write FIRST
1. `test_stream_end_with_citations_renders_citation_badges`: Verifies container with class `citations-container` is appended when `citations` array has items.
2. `test_clicking_citation_badge_expands_snippet_drawer`: Verifies clicking citation pill toggles class `is-expanded` on detail card.
3. `test_stream_end_renders_retrieval_latency_in_telemetry_badge`: Verifies telemetry text contains `Retrieval:` when `retrieval_ms` is supplied.
4. `test_fallback_turn_renders_general_mode_indicator`: Verifies presence of fallback badge when citations list is empty.
5. `test_empty_citations_does_not_render_empty_citation_container`: Verifies no empty container elements are left in the DOM.

---

## Implementation Steps
1. Add CSS rules in `frontend/style.css` for `.citations-container`, `.citation-pill`, `.citation-drawer`, and `.citation-snippet` using `--accent-subtle` and `--border-default`.
2. Update `frontend/app.js` `handleStreamEnd` to inspect `payload.citations` and `payload.retrieval_ms`.
3. Implement `renderCitationBadges` creating accessible button chips with `aria-expanded="false"`.
4. Add click listener to citation buttons toggling `.is-expanded` on snippet container.
5. Update telemetry string builder to prepend `Retrieval: ${metrics.retrieval_ms}ms | ` when present.
6. Add unit tests in `tests/test_frontend.js` and execute via Node test runner.

---

## Acceptance Criteria
- [ ] Grounded responses display at least one citation pill with document title and match percentage.
- [ ] Clicking a citation pill toggles visibility of the excerpt drawer without page refresh.
- [ ] Telemetry pill shows both `Retrieval:` and `TTFT:` values on completion of grounded turn.
- [ ] Responses with zero citations display the fallback badge or omit citation container without DOM errors.
- [ ] All interactive citation elements include keyboard focus styles and ARIA attributes.

---

## Definition of Done
- [ ] All simulated DOM tests in `tests/test_frontend.js` pass 100%.
- [ ] Browser console has zero uncaught exceptions during stream and citation expansion.
- [ ] Visual style complies with `context/ui-context.md`.
- [ ] Test report generated in `feature-test-reports/FEAT-008-test-report.md`.
- [ ] `context/feature-specs/INDEX.md` updated.

---

## Edge Cases to Handle
- **Long Document Titles**: Truncated with ellipsis to preserve horizontal layout.
- **Multiple Citations**: Wraps cleanly into a multi-row badge flexbox.
- **Missing Snippet Text**: Falls back to document title without broken layout.

---

## Pre-flight Check
Before starting, confirm `FEAT-007-VERIFY` passed. If not, stop and flag instead of proceeding.

---

## What's Next
- `FEAT-008-VERIFY-rag-citations-ui.md`
- `FEAT-009-INT-rag-eval-benchmarks.md`

---

## Ambiguity Resolution Protocol
If you encounter a case not covered by this spec:
1. Do NOT silently guess.
2. Make the smallest reasonable assumption needed to proceed.
3. Log it in `context/feature-specs/DEVIATIONS.md` as: `[FEAT-008-FE] — [what was ambiguous] — [assumption made]`
4. Continue implementation; do not block on it unless it affects the data model defined in `000-shared-contracts.md`, in which case STOP and flag for human review.
