"""Unit tests for FEAT-007: Real-Time Vector Retrieval, Prompt Grounding & Failure Handling."""

from __future__ import annotations

import asyncio
import time
from typing import List, Tuple
from unittest.mock import MagicMock
import pytest

from backend.contracts import DocumentChunk, RetrievalResult
from backend.conversation import ConversationManager, RAGConversationManager
from backend.conversation.orchestrator import format_retrieved_context, render_system_prompt
from backend.rag.cache import QueryCache
from backend.rag.retriever import VectorRetriever
from backend.rag.vector_store import CPUVectorStore


def create_sample_chunks() -> List[DocumentChunk]:
    """Helper to create dummy chunks with known embeddings."""
    return [
        DocumentChunk(
            chunk_id="chunk_1",
            doc_id="return_policy",
            title="Return Policy",
            section_header="Overview",
            content="Our return window is 30 days from delivery for full refund.",
            token_count=15,
            char_count=65,
            chunk_index=0,
            embedding=[1.0] + [0.0] * 383,  # Unit vector along axis 0
        ),
        DocumentChunk(
            chunk_id="chunk_2",
            doc_id="shipping_policy",
            title="Shipping Guidelines",
            section_header="Standard Shipping",
            content="Standard shipping takes 3 to 5 business days and is free over $50.",
            token_count=18,
            char_count=75,
            chunk_index=0,
            embedding=[0.8, 0.6] + [0.0] * 382,
        ),
        DocumentChunk(
            chunk_id="chunk_3",
            doc_id="product_soundflow",
            title="SoundFlow Headphones",
            section_header="Specs",
            content="SoundFlow Pro ANC headphones feature 40 hours of battery life.",
            token_count=16,
            char_count=68,
            chunk_index=0,
            embedding=[0.7, 0.7] + [0.0] * 382,
        ),
        DocumentChunk(
            chunk_id="chunk_4",
            doc_id="warranty_policy",
            title="Warranty Terms",
            section_header="Coverage",
            content="Standard warranty covers 1 year of hardware manufacturing defects.",
            token_count=14,
            char_count=69,
            chunk_index=0,
            embedding=[0.0, 1.0] + [0.0] * 382,
        ),
    ]


@pytest.mark.asyncio
async def test_retrieve_returns_top_k_chunks_with_scores() -> None:
    """Verifies query returns at least 3 chunks sorted by descending cosine score."""
    store = CPUVectorStore(embedding_dim=384)
    chunks = create_sample_chunks()
    store.add_chunks(chunks)

    retriever = VectorRetriever(vector_store=store)
    # Mock _get_model to return a deterministic query vector
    mock_model = MagicMock()
    mock_model.encode.return_value = [1.0] + [0.0] * 383
    retriever._model = mock_model

    result = await retriever.retrieve("What is your return policy?", top_k=3, score_threshold=0.45)

    assert isinstance(result, RetrievalResult)
    assert not result.is_fallback
    assert len(result.chunks) == 3
    assert len(result.citations) == 3

    # Check descending order
    scores = [c.score for c in result.citations]
    assert scores == sorted(scores, reverse=True)
    assert result.citations[0].doc_id == "return_policy"
    assert result.citations[0].score >= 0.99


@pytest.mark.asyncio
async def test_query_cache_avoids_recomputation() -> None:
    """Verifies subsequent query with identical text sets from_cache=True and resolves in < 10ms."""
    store = CPUVectorStore(embedding_dim=384)
    store.add_chunks(create_sample_chunks())

    retriever = VectorRetriever(vector_store=store)
    mock_model = MagicMock()
    mock_model.encode.return_value = [1.0] + [0.0] * 383
    retriever._model = mock_model

    # First retrieval (cold)
    res1 = await retriever.retrieve("return policy details", top_k=3)
    assert not res1.from_cache

    # Second retrieval (cached)
    start = time.perf_counter()
    res2 = await retriever.retrieve("return policy details", top_k=3)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert res2.from_cache is True
    assert elapsed_ms < 10.0, f"Cache retrieval took {elapsed_ms}ms, expected < 10ms"
    assert len(res2.chunks) == len(res1.chunks)
    assert res2.query == res1.query


@pytest.mark.asyncio
async def test_low_similarity_query_triggers_fallback() -> None:
    """Verifies out-of-domain query with score < 0.45 sets is_fallback=True and empty citations."""
    store = CPUVectorStore(embedding_dim=384)
    store.add_chunks(create_sample_chunks())

    retriever = VectorRetriever(vector_store=store)
    # Query orthogonal to stored vectors (axis 5)
    mock_model = MagicMock()
    mock_model.encode.return_value = [0.0, 0.0, 0.0, 0.0, 0.0, 1.0] + [0.0] * 378
    retriever._model = mock_model

    result = await retriever.retrieve(
        "Who is the president of Mars?",
        top_k=3,
        score_threshold=0.45,
    )

    assert result.is_fallback is True
    assert len(result.chunks) == 0
    assert len(result.citations) == 0


@pytest.mark.asyncio
async def test_retrieval_timeout_triggers_fallback_without_exception() -> None:
    """Simulates vector store delay > 1.0s; asserts returns fallback RetrievalResult without throwing."""
    store = CPUVectorStore(embedding_dim=384)
    retriever = VectorRetriever(vector_store=store)

    # Simulate an expensive search that hangs
    def slow_search(*args, **kwargs):
        time.sleep(1.5)
        return []

    retriever._sync_search = slow_search  # type: ignore

    # Run with 0.1s timeout
    result = await retriever.retrieve("slow search query", timeout_seconds=0.1)

    assert result.is_fallback is True
    assert len(result.chunks) == 0
    assert len(result.citations) == 0
    assert result.retrieval_ms > 50  # Captures elapsed time


def test_context_budget_caps_injected_tokens_under_500() -> None:
    """Verifies prompt orchestrator enforces 500-token ceiling on <retrieved_context>."""
    # Create 10 large chunks that would exceed 500 tokens if all injected
    chunks = []
    for i in range(10):
        chunks.append(
            DocumentChunk(
                chunk_id=f"large_chunk_{i}",
                doc_id=f"doc_{i}",
                title=f"Document {i}",
                section_header=f"Section {i}",
                content=f"Long detailed policy explanation text for document {i}. " * 15,
                token_count=120,
                char_count=500,
                chunk_index=i,
            )
        )

    retrieval_result = RetrievalResult(
        query="test query",
        chunks=chunks,
        citations=[],
        retrieval_ms=10.0,
        from_cache=False,
        is_fallback=False,
    )

    context_xml = format_retrieved_context(retrieval_result, max_tokens=500)
    assert "<retrieved_context>" in context_xml
    assert "</retrieved_context>" in context_xml

    # Total tokens in XML block must be bounded
    words = context_xml.split()
    estimated_tokens = int(len(words) * 1.33)
    assert estimated_tokens <= 520, f"Retrieved context exceeded token budget: {estimated_tokens}"

    # Verify injection into system prompt
    prompt = render_system_prompt(retrieved_context_xml=context_xml)
    assert "<retrieved_context>" in prompt
    assert "<store_persona>" in prompt


@pytest.mark.asyncio
async def test_rag_conversation_manager_builds_grounded_payload() -> None:
    """Verifies end-to-end RAGConversationManager retrieves context and injects into chat payload."""
    store = CPUVectorStore(embedding_dim=384)
    store.add_chunks(create_sample_chunks())

    retriever = VectorRetriever(vector_store=store)
    mock_model = MagicMock()
    mock_model.encode.return_value = [1.0] + [0.0] * 383
    retriever._model = mock_model

    base_manager = ConversationManager()
    base_manager.add_user_message("sess_101", "Can I return items within 30 days?")

    rag_manager = RAGConversationManager(base_manager=base_manager, retriever=retriever)
    payload, result = await rag_manager.build_rag_chat_payload(
        session_id="sess_101",
        user_query="Can I return items within 30 days?",
    )

    assert len(payload) >= 2
    assert payload[0]["role"] == "system"
    assert "<retrieved_context>" in payload[0]["content"]
    assert "Return Policy" in payload[0]["content"]
    assert not result.is_fallback
    assert len(result.citations) >= 1
