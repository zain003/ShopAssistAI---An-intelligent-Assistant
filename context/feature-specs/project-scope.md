Introduction
Large Language Models (LLMs) have made it possible to build conversational agents that hold natural, multi-turn
dialogue. Getting one to run reliably in production, however, is a systems problem as much as an
NLP problem: it needs careful prompt design, session handling, concurrency, and attention to latency. In this assignment
you will design and build a conversational AI system that runs entirely on your own CPU, exposes a real-time API, and
ships with a simple web chat interface.
Constraint: Tools and Retrieval-Augmented Generation (RAG) are not allowed in this assignment. Every response must
come from prompt orchestration and conversational memory alone.
Objective
● Run a quantized, open-weight LLM locally on CPU — no cloud model APIs.
● Support real-time, streaming responses over WebSocket.
● Maintain conversation state across turns within a session.
● Handle multiple concurrent users without one blocking another.
● Expose a clean, documented API.
● Provide a simple, ChatGPT-style web interface.
System Architecture Overview
Your system must follow this general shape. You decide how to split the conversation manager internally.
● Frontend — a web-based chat interface.
● Backend API — a FastAPI server with REST + WebSocket endpoints.

● Conversation Manager — session handling, history management, prompt orchestration.
● LLM Engine — local inference using a quantized model.
Tasks
Phase I — Business Case Selection
Each group must select one of the business domains below and build a chatbot that stays strictly within that domain's
tone, policies, and constraints. You are open to add any extra functionalities in your systems as long as they are within the
domains and they will be awarded with extra marks.
Gym / Fitness Membership Assistant — Helps prospective and current members with class schedules, membership
plans, trainer info, and booking or freezing memberships.
• Real Estate Rental & Leasing Assistant — Helps renters browse listings, understand lease terms and building
policies, and schedule viewings.
• Event & Venue Booking Assistant — Helps clients explore venue packages and catering options and check date
availability for an event.
• Library Assistant — Helps patrons search the catalogue, understand borrowing policies, and renew or check due dates.
• Car Rental Assistant — Helps customers check fleet availability, pricing, and insurance terms, and book a rental.
• E-Commerce Order Support Assistant — Helps customers with product questions, order tracking, and the
return/shipping policy.
Your README should include a written use-case description, at least three example dialogues, and a conversation flow
design that names the distinct stages your assistant moves through (for example: greeting, information gathering,
confirmation, closing) and explains how it handles a user changing topic mid conversation. Any generic flow that can
belong to any domain can lose marks. Your system must not answer irrelevant queries and include proper strategies to
handle them.
Phase II — Local LLM Selection and Optimization
Pick a small, CPU-friendly instruction-tuned model. Stay in the 0.5B–4B parameter range at a Q4 quantization (for example,
a small Qwen, Phi, Gemma, or any other open model). Ollama is the easiest way to get a model running locally; llama.cpp
and vLLM are also acceptable if you want more control.
● Your README should include a short write-up of your context memory management scheme — how you
decide what conversation history to keep in the prompt as it grows.
● Also, it should inference latency benchmarks for your chosen model on your own hardware (tokens/second, time to
first token).
Phase III — Conversation Manager and Prompt Orchestration
Your conversation manager must:
● Maintain dialogue history for the session.
● Enforce the conversational policies of your chosen domain (what the assistant will and will not do).

● Handle turn-taking logic cleanly.
● Build structured system prompts.
● Stay faithful to earlier context across multiple turns.
Reminder: no tools, agents, plugins, or RAG here. All of the assistant's apparent intelligence must come from prompt
design and context window management.
Phase IV — Backend API Implementation
● A WebSocket endpoint, /ws/chat, using a JSON request/response format.
● Asynchronous request handling, so one user's request does not block another's.
● Streaming token output (the response should appear word by word, not all at once).
● Robust error handling — a malformed request or a model error should return a clear error message, not crash the
connection.
● Deliverable: the FastAPI service with working WebSocket streaming.
● Deliverable: clear run and setup instructions.
Phase V — Web-Based Chat Interface
● Real-time messaging with visible streaming as the response arrives.
● Conversation history visible in the UI.
● A reset / new session control.
● Clean, usable UI. It does not need to be fancy, but it should not be confusing.
Phase VI — Production Readiness and Evaluation
Before you submit, test your system the way a real user would test it or try to break it:
● Latency: measure and report time-to-first-token and total response time under normal load.
● Correctness: verify the assistant stays in character and follows your domain's policies across a range of test
conversations, including ones that try to push it off-topic.
● Failure handling: deliberately break things (send a malformed message, disconnect mid-stream, open several
sessions at once) and confirm the system fails gracefully instead of crashing.
System Requirements
● Fully local inference — no cloud model APIs.
● Instruction-tuned, in-character conversational responses.
● Context tracking across turns within a session.
● CPU-optimized inference.
● Streaming output over WebSocket.
Evaluation Criteria

Criterion Weight
Correctness & Completeness 50%
Viva (code walkthrough, live Q&A) 25%
Real-time Behaviour & Performance (latency, streaming, failure
handling) 25%
Total 100%
Bonus up to +10%

Deliverables & Submission Guidelines
Submit a single GitHub repository (or .zip) containing:
● All source code: backend, frontend, and any scripts.
● A README.md covering:
1. setup instructions,
2. an architecture diagram,
3. your model selection and why you picked it,
4. your latency benchmarks,
5. and known limitations of your system.
A Loom video demoing your system is optional but recommended.
Bonus
Pick at most one for the bonus credit on this assignment:
● Cloud deployment: deploy your chatbot to a free-tier host such as Vercel. Share the public URL in your
README.
● UX/persona polish: a visibly more thoughtful UI/UX or a persona that stays convincingly in character under
adversarial testing, beyond what Phase V asks for.