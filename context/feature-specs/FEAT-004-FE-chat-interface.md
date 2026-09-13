# FEAT-004-FE — Web-Based Chat Interface & Stream Renderer (P0)

**Layer**: Frontend  
**Goal**: Deliver a responsive, modern web chat interface that connects over WebSocket to `/ws/chat`, visualizes token-by-token streaming, preserves in-session dialogue history, renders quick action chips, and handles session resets.

---

## Depends on / Context pack / Consumes
**Depends on**: `context/feature-specs/000-shared-contracts.md`, `FEAT-003-BE-websocket-api.md`  
**Context pack**:
```typescript
export interface InboundEnvelope {
  type: "user_message" | "reset_session" | "ping";
  session_id?: string;
  payload?: Record<string, any>;
}

export interface OutboundEnvelope {
  type: "session_created" | "stream_start" | "token" | "stream_end" | "error" | "pong";
  session_id: string;
  payload: Record<string, any>;
}

export interface StreamEndMetrics {
  ttft_ms: number;
  tokens_per_second: number;
  total_tokens: number;
}
```
**Consumes**: WebSocket `/ws/chat` protocol exposed by `FEAT-003-BE`.

---

## Scope
- **Scope (In)**:
  - Vanilla HTML5/CSS3/JavaScript client application (or lightweight Vite SPA).
  - WebSocket manager handling connection lifecycle, automatic reconnects, and heartbeats.
  - Streaming accumulator: appends arriving `token` frames to active assistant message bubble with blinking cursor.
  - Quick action chips (`📦 Track ORD-1085`, `🔄 Return Policy`, `🎧 Headphones under $150`).
  - Session reset button clearing the DOM and emitting `reset_session`.
  - Latency badge displaying TTFT and tokens/sec once stream completes.
- **Scope (Out)**:
  - Server-side token generation or memory storage (handled in `FEAT-001` through `FEAT-003`).

---

## Tech & Files to Touch
- `frontend/index.html` — Accessible DOM structure with message list, input box, action chips, and header.
- `frontend/style.css` — CSS implementation utilizing tokens from `context/ui-context.md`.
- `frontend/app.js` — WebSocket client, state management, and DOM event listeners.
- `tests/test_frontend.js` — DOM interaction and event handling tests via simulated DOM.

---

## Tests to Write FIRST
1. `test_render_user_message_adds_bubble_to_dom`: Calling `appendMessage('user', 'Hello')` adds element with class `message-user`.
2. `test_stream_start_creates_assistant_bubble_with_cursor`: On `stream_start`, an assistant bubble is inserted with class `streaming-cursor`.
3. `test_token_appends_text_to_current_bubble`: Sequential `token` frames append text without clearing existing content.
4. `test_stream_end_removes_cursor_and_renders_metrics`: On `stream_end`, cursor is removed and telemetry badge displays `TTFT` and `tok/s`.
5. `test_reset_button_clears_message_list`: Clicking reset button empties DOM messages container.

---

## Implementation Steps
1. Create `frontend/index.html` with semantic structure: `<header>`, `<main id="chat-window">`, `<div id="chips-container">`, `<footer id="input-container">`.
2. Create `frontend/style.css` implementing color tokens, message bubbles, cursor animation, and layout from `context/ui-context.md`.
3. Create `frontend/app.js`:
   - Initialize WebSocket pointing to `ws://${window.location.host}/ws/chat`.
   - Implement message router dispatching on `data.type`.
   - Implement `handleToken(token)` appending text to active message node and auto-scrolling.
   - Implement `handleStreamEnd(payload)` updating latency chip and removing cursor.
   - Bind submit button, keyboard Enter handler, and quick chip click listeners.

---

## Acceptance Criteria
- [ ] User message appears immediately in DOM upon sending.
- [ ] Assistant response renders word-by-word as `token` events arrive.
- [ ] Animated streaming cursor is visible while streaming and disappears upon `stream_end`.
- [ ] Clicking "Reset Session" clears message view and resets stored `session_id`.
- [ ] Disconnected status badge updates from "Connected" to "Disconnected (Reconnecting...)".

---

## Definition of Done
- [ ] Frontend tests pass 100% in fake DOM runner (`node tests/test_frontend.js`).
- [ ] Zero unhandled JavaScript exceptions in browser console.
- [ ] UI verified visually against `context/ui-context.md` design tokens.

---

## Edge Cases to Handle
- Rapid keypresses: disable send button while stream is active; re-enable on `stream_end` or `error`.
- Long text messages: wrap text cleanly with `word-break: break-word` to prevent horizontal overflow.
- Server drop mid-stream: display error banner and remove pending cursor cleanly.

---

## Pre-flight Check
Confirm `FEAT-003-VERIFY-websocket-api.md` passes and `/ws/chat` is operational.

---

## What's Next
- `FEAT-004-VERIFY-chat-interface.md` — Verification pass.
- `FEAT-005-INT-eval-and-benchmarks.md` — Latency benchmarks and adversarial evaluation.

---

## Ambiguity Resolution Protocol
If you encounter a case not covered by this spec:
1. Do NOT silently guess.
2. Make the smallest reasonable assumption needed to proceed.
3. Log it in `context/feature-specs/DEVIATIONS.md` as: `[FEAT-004-FE] — [what was ambiguous] — [assumption made]`.
4. Continue implementation; do not block unless it alters `000-shared-contracts.md`.
