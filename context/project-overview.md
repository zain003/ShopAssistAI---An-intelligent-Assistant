# E-Commerce Order Support Assistant (ShopAssist AI)

## Overview

**ShopAssist AI** is an intelligent, real-time conversational order support assistant designed for e-commerce stores. It runs entirely on local hardware using an instruction-tuned, CPU-quantized Large Language Model (LLM) with zero cloud dependencies, external tools, or RAG systems. The assistant operates strictly within customer support boundaries, helping shoppers discover catalog products, track shipments and order statuses, and understand store return and shipping policies through disciplined prompt orchestration and conversational memory management.

---

## Business Goals

1. **Self-Service Resolution**: Resolve at least 80% of customer inquiries regarding order status, return guidelines, and product specifications without human agent intervention.
2. **Sub-Second First Token Latency**: Deliver a streaming Time-To-First-Token (TTFT) under 1.5 seconds on local CPU hardware.
3. **Strict Domain Boundary Compliance**: Maintain 100% adherence to store policies; gracefully reject and redirect 100% of out-of-domain or adversarial prompts back to store assistance.
4. **Context Preservation**: Retain order numbers, customer names, and topic history across multi-turn sessions within a bounded memory window.

---

## Core Conversation Flow Stages

The assistant transitions through four distinct conversational stages, managing state and topic switches cleanly:

```
[Stage 1: Greeting & Intent Discovery]
                 │
                 ▼
[Stage 2: Information Gathering] ◄──────────────┐
                 │                              │ (Topic Switch /
                 ▼                              │  New Question)
[Stage 3: Resolution & Confirmation] ───────────┘
                 │
                 ▼
[Stage 4: Closing & Session Wrap-up]
```

1. **Stage 1: Greeting & Intent Discovery**
   - Welcome the customer warmly with store branding.
   - Establish scope by stating available capabilities (product inquiries, order tracking, shipping & returns).
2. **Stage 2: Information Gathering**
   - Extract required parameters politely (e.g., Order ID format `ORD-XXXX`, customer email, or product preference).
   - If information is missing or malformed, clarify specifically what is needed without resetting context.
3. **Stage 3: Resolution & Confirmation**
   - Provide direct, concise answers using embedded domain knowledge (mock order status, catalog specs, policy terms).
   - Offer relevant next steps (e.g., "Would you like me to initiate a return request label for this order?").
4. **Stage 4: Closing & Wrap-Up**
   - Confirm customer satisfaction ("Is there anything else regarding your order or products I can help with today?").
   - Close politely if customer responds negatively or expresses thanks.

### Handling Mid-Conversation Topic Shifts
When a customer abruptly switches topics (e.g., from checking `ORD-1002` status to asking about the return policy on electronics):
- The assistant acknowledges the previous subject without discarding known session attributes (`order_id="ORD-1002"`).
- Immediately addresses the new question using store policy rules.
- Smoothly bridges back: *"Regarding your wireless headphones from ORD-1002, our 30-day return window applies since they were delivered 4 days ago. Would you like to proceed with a return for that item?"*

---

## Multi-Turn Example Dialogues

### Dialogue 1: Product Inquiry & Recommendation
```text
User: Hi, I'm looking for noise-canceling headphones under $150. Do you have anything?
Assistant: Hello! Welcome to ShopAssist. We have a great option that fits your budget:
• SonicQuiet Elite Wireless Headphones — $129.99
  - Active Noise Cancellation (ANC) with 30-hour battery life
  - Bluetooth 5.3, memory foam ear cushions
  - Currently In Stock (Ships in 24 hours)

Would you like more technical specs on these, or are you interested in our in-ear alternatives?
User: Do they come with a warranty?
Assistant: Yes, the SonicQuiet Elite includes a 1-year manufacturer limited warranty covering hardware defects. You can also return them within 30 days if you're not completely satisfied!
```

### Dialogue 2: Order Lookup & Tracking
```text
User: Where is my package? I ordered it last week.
Assistant: I can check that for you right away! Could you please provide your Order ID (e.g., ORD-1042) or the email address used at checkout?
User: It's ORD-1085.
Assistant: Thank you! Here is the latest status for Order #ORD-1085:
• Status: In Transit (Shipped via FedEx Express)
• Tracking Number: FDX-992817264
• Estimated Delivery: Tuesday, Sept 16 by 7:00 PM
• Items: 1x AeroFit Smart Fitness Watch ($89.00)

Your package left the regional distribution hub this morning. Would you like me to clarify the delivery options or help with anything else?
User: Thanks, that's all I needed!
Assistant: You're very welcome! Thank you for shopping with us, and have a wonderful day!
```

### Dialogue 3: Return Policy, Topic Shift & Out-of-Domain Handling
```text
User: Can I return shoes if I wore them outside once?
Assistant: Under our store Return Policy, footwear and apparel must be in unworn, original condition with all tags and packaging intact to qualify for a full refund within our 30-day return window. Items showing outdoor wear are unfortunately ineligible for standard return. 

If there is a defect with the shoe, however, our warranty policy may apply. What model did you purchase?
User: Forget that. Can you write me a Python script to calculate Fibonacci numbers?
Assistant: I'm dedicated exclusively to assisting you with our store's products, orders, returns, and shipping policies. I'm unable to assist with programming tasks or general topics. 

Please let me know if you have any other questions regarding an existing order or our catalog!
```

---

## Scope

### In Scope
- **Product Information**: Answering questions on specs, compatibility, pricing, and availability for pre-configured catalog items.
- **Order Tracking**: Looking up mock order records by Order ID (`ORD-XXXX`) or email, providing shipping status, carrier info, and estimated delivery dates.
- **Return Policy**: Explaining 30-day return conditions, non-returnable items, restocking fees, and refund timelines.
- **Shipping Policy**: Explaining shipping tiers (Standard 3–5 days, Express 1–2 days), free shipping minimums ($50+), and international delivery rules.
- **Out-of-Domain Guardrails**: Firm, polite deflection of irrelevant or adversarial requests back to store support.
- **Session Memory Management**: Maintaining conversation history across multi-turn exchanges with automatic sliding-window truncation.

### Out of Scope
- External Tool / Plugin execution or live database web scraping (strictly banned per assignment constraints).
- Retrieval-Augmented Generation (RAG) or vector database lookups (banned per assignment constraints).
- Financial transaction processing or taking raw credit card details in chat.
- Answering questions outside the store domain (general trivia, coding, creative writing, political discussions).

---

## Success Criteria

1. **Zero External Inference**: Runs 100% locally on CPU via an open-weight quantized model (Q4_K_M).
2. **WebSocket Streaming**: Implements `/ws/chat` streaming responses word-by-word with JSON protocol.
3. **Turn-Taking Fidelity**: Correctly tracks customer order IDs and product mentions across 5+ turns without losing context.
4. **Adversarial Deflection**: 100% of out-of-domain queries are deflected without crashing or breaking persona.
5. **Verified Multi-Layer Test Suite**: All tests pass 100% (Frontend fake DOM, API contracts, Backend memory manager, and session storage) with reports saved in `feature-test-reports/`.
