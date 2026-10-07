"""Pytest integration test suite for FEAT-009 RAG Evaluation & Benchmarks.

Asserts:
1. Sub-second CPU retrieval latency.
2. 5-client concurrency without deadlock.
3. Factual grounding verification against domain documents.
4. Phase IV failure mode fallback triggers.
5. Markdown evaluation report generation and export.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict

import pytest

from backend.rag.retriever import VectorRetriever
from backend.rag.vector_store import CPUVectorStore
from tests.benchmark_rag import RAGBenchmarkRunner
from tests.eval_rag_grounding import DOMAIN_GROUNDING_CASES, GroundingEvaluator


@pytest.fixture(scope="module")
def shared_runner() -> RAGBenchmarkRunner:
    """Fixture providing initialized and warmed up RAGBenchmarkRunner."""
    store = CPUVectorStore(embedding_dim=384)
    store_dir = Path("data/vector_store")
    if (store_dir / "chunks.json").exists():
        store.load(str(store_dir))
    retriever = VectorRetriever(vector_store=store)
    return RAGBenchmarkRunner(retriever=retriever)


@pytest.mark.asyncio
async def test_benchmark_measures_retrieval_under_one_second(shared_runner: RAGBenchmarkRunner) -> None:
    """AC-1: Verifies mean retrieval latency across test queries is strictly < 1000ms."""
    queries = [
        "What is your return policy and restocking fee?",
        "How much does express 2-day shipping cost?",
    ]
    metrics = await shared_runner.benchmark_retrieval_latency(queries=queries, runs=2)

    assert metrics["mean_cold_ms"] < 1000.0, f"Cold retrieval exceeded 1s: {metrics['mean_cold_ms']} ms"
    assert metrics["mean_cached_ms"] < 10.0, f"Cached retrieval exceeded 10ms: {metrics['mean_cached_ms']} ms"
    assert metrics["p50_cold_ms"] < 500.0, f"P50 latency exceeded 500ms: {metrics['p50_cold_ms']} ms"


@pytest.mark.asyncio
async def test_concurrent_retrieval_does_not_deadlock(shared_runner: RAGBenchmarkRunner) -> None:
    """AC-2: Verifies 5 concurrent async retrieval tasks complete within 3 seconds without deadlock."""
    queries = ["What is your return policy and restocking fee?"]
    result = await shared_runner.benchmark_concurrency(queries=queries, concurrent_clients=5)

    assert result["wall_time_s"] < 3.0, f"Concurrency test took too long: {result['wall_time_s']}s"
    assert result["total_queries"] == 5.0
    assert result["throughput_qps"] > 1.0
    assert result["avg_latency_ms"] < 1000.0


@pytest.mark.asyncio
async def test_grounding_evaluator_verifies_source_citation(shared_runner: RAGBenchmarkRunner) -> None:
    """AC-3: Verifies responses to policy questions retrieve matching source document citations."""
    grounding = await shared_runner.evaluate_grounding_fidelity(DOMAIN_GROUNDING_CASES)

    assert grounding["fidelity_rate"] >= 80.0, f"Fidelity rate too low: {grounding['fidelity_rate']}%"
    assert grounding["passed_cases"] >= 4
    assert len(grounding["details"]) == len(DOMAIN_GROUNDING_CASES)

    # Specific check: SoundFlow Pro headphones query must return SoundFlow guide chunk
    sf_detail = next(d for d in grounding["details"] if "soundflow_pro_headphones" in d["expected_doc"])
    assert sf_detail["faithful"] is True


@pytest.mark.asyncio
async def test_failure_mode_evaluator_confirms_fallback_on_irrelevant_query(
    shared_runner: RAGBenchmarkRunner,
) -> None:
    """AC-4: Verifies out-of-domain prompt emits is_fallback=True without crashing."""
    failure_checks = await shared_runner.evaluate_failure_handling()

    assert failure_checks["out_of_domain_fallback"] is True
    assert failure_checks["timeout_fallback"] is True
    assert failure_checks["empty_query_fallback"] is True


def test_export_report_writes_markdown_to_feature_reports(
    shared_runner: RAGBenchmarkRunner,
    tmp_path: Path,
) -> None:
    """AC-5: Verifies report file is generated with correct tables and written to disk."""
    dummy_results: Dict[str, Any] = {
        "latency": {
            "mean_cold_ms": 25.4,
            "p50_cold_ms": 22.1,
            "p95_cold_ms": 35.8,
            "mean_cached_ms": 0.05,
        },
        "concurrency": {
            "concurrent_clients": 5.0,
            "total_queries": 25.0,
            "wall_time_s": 0.35,
            "throughput_qps": 71.4,
            "avg_latency_ms": 65.2,
        },
        "grounding": {
            "fidelity_rate": 100.0,
            "total_cases": 5,
            "passed_cases": 5,
            "details": [
                {
                    "query": "What is return policy?",
                    "expected_doc": "return_policy",
                    "top_doc": "return_policy",
                    "score": 0.75,
                    "faithful": True,
                }
            ],
        },
        "failures": {
            "out_of_domain_fallback": True,
            "timeout_fallback": True,
            "empty_query_fallback": True,
        },
    }

    report_md = shared_runner.generate_rag_evaluation_report(dummy_results)
    assert "# Test Report: FEAT-009 — RAG Latency Benchmarks & Grounding Evaluation Suite" in report_md
    assert "Mean Cold CPU Latency" in report_md
    assert "Multi-User Concurrency Evaluation" in report_md
    assert "Phase IV Failure Mode Resilience Verification" in report_md

    out_file = tmp_path / "FEAT-009-test-report.md"
    out_file.write_text(report_md, encoding="utf-8")
    assert out_file.exists()
    assert len(out_file.read_text(encoding="utf-8")) > 500
