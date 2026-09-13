# UI Context

## Theme & Aesthetic

**ShopAssist AI** features a modern, high-polish e-commerce customer support interface. The design language employs a sleek dark mode with layered slate surfaces, crisp typography, responsive micro-animations, and subtle glowing accent borders. It delivers an intuitive, ChatGPT-style real-time conversational experience optimized for quick resolution of e-commerce inquiries.

---

## Design Tokens & CSS Variables

All UI components must consume these CSS custom properties. No hardcoded hex values are permitted.

```css
:root {
  /* Backgrounds */
  --bg-base: #0a0e17;              /* Deep space slate */
  --bg-surface: #111827;           /* Card & chat pane background */
  --bg-surface-elevated: #1f2937;  /* Hover surfaces and modals */
  --bg-input: #151d2f;             /* Text input background */

  /* Text Colors */
  --text-primary: #f9fafb;         /* High-contrast crisp text */
  --text-secondary: #d1d5db;       /* Body content & messages */
  --text-muted: #9ca3af;           /* Timestamps, meta labels */
  --text-placeholder: #6b7280;     /* Input placeholders */

  /* Accents & States */
  --accent-primary: #3b82f6;       /* Vibrant royal blue */
  --accent-hover: #2563eb;         /* Interactive hover */
  --accent-subtle: rgba(59, 130, 246, 0.15); /* Chip badges */
  --user-bubble: #2563eb;          /* User message bubble */
  --assistant-bubble: #1e293b;     /* Assistant message bubble */
  
  /* Status Indicators */
  --state-success: #10b981;        /* Connected / In Stock */
  --state-warning: #f59e0b;        /* Streaming / In Transit */
  --state-error: #ef4444;          /* Disconnected / Error */

  /* Borders & Dividers */
  --border-default: #2d3748;       /* Standard borders */
  --border-focus: #3b82f6;         /* Focused inputs */

  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
}
```

---

## Typography

| Role               | Font Family                                            | Size / Weight            |
| ------------------ | ------------------------------------------------------ | ------------------------ |
| **Primary Text**   | `'Inter', -apple-system, BlinkMacSystemFont, sans-serif` | 14px / Regular (400)     |
| **Headings**       | `'Inter', sans-serif`                                  | 16px–18px / SemiBold (600)|
| **Order / SKU / Code**| `'JetBrains Mono', 'Fira Code', monospace`             | 13px / Medium (500)      |

---

## Border Radius Scale

| Context               | Value    | Usage                                    |
| --------------------- | -------- | ---------------------------------------- |
| **Chips / Tags**      | `9999px` | Pill chips for quick actions             |
| **Inputs & Buttons**  | `8px`    | Input boxes, send button, reset action   |
| **Message Bubbles**   | `16px`   | Rounded chat messages with tail accent   |
| **Main Containers**   | `12px`   | Outer chat container & order cards       |

---

## Component Specifications

### 1. Header Bar
- Title: **ShopAssist AI** with a shopping bag icon.
- Connection Status Badge:
  - Green dot + text `"Connected"` when WebSocket is open.
  - Pulsing amber dot + `"Streaming..."` during token reception.
  - Red dot + `"Disconnected (Reconnecting...)"` on drop.
- Action: `"New Session"` / `"Reset"` button with confirmation tooltip.

### 2. Message Stream Container
- Flex column with `overflow-y: auto`, smooth auto-scrolling pinned to bottom while streaming.
- **User Bubble**: Right-aligned, `--user-bubble` background, white text.
- **Assistant Bubble**: Left-aligned, `--assistant-bubble` background, with subtle border `--border-default`.
- **Streaming Cursor**: An animated blinking vertical bar (`|` or subtle pulse dot) appended to the end of the streaming message until `stream_end` arrives.

### 3. Quick Action Chips
A row of clickable pill chips above the input to guide user flows:
- `📦 Track ORD-1085`
- `🎧 Noise Canceling Headphones`
- `🔄 Return Policy`
- `🚚 Shipping Rates`

### 4. Input Area
- Textarea or flexible input field supporting multiline expansion.
- Placeholder: `"Ask about products, track order ORD-XXXX, or return policies..."`
- Keyboard shortcuts: `Enter` to submit, `Shift + Enter` for newline.
- Primary Send Button with paper airplane or arrow icon.
