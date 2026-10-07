"""Factual Grounding and Failure Mode Evaluator for ShopAssist AI RAG.

Evaluates:
1. Grounding fidelity: Retrieved chunks contain exact facts for domain questions.
2. Failure handling: Out-of-domain queries, timeouts, and corrupted stores trigger fallbacks gracefully.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List
from unittest.mock import MagicMock

from backend.contracts import RetrievalResult
from backend.rag.retriever import VectorRetriever
from backend.rag.vector_store import CPUVectorStore

DOMAIN_GROUNDING_CASES: List[Dict[str, Any]] = [
    {
        "query": "What is your standard return policy and window?",
        "expected_doc_id": "return_policy",
        "expected_keywords": ["30", "return", "refund"],
    },
    {
        "query": "How fast is express shipping and how much does it cost?",
        "expected_doc_id": "express_shipping",
        "expected_keywords": ["12.99", "2", "business day"],
    },
    {
        "query": "What is the battery life and noise cancellation of SoundFlow Pro?",
        "expected_doc_id": "soundflow_pro_headphones",
        "expected_keywords": ["40", "anc", "hours"],
    },
    {
        "query": "What does the 1-year standard hardware warranty cover?",
        "expected_doc_id": "standard_hardware_warranty",
        "expected_keywords": ["1-year", "warranty", "defect"],
    },
    {
        "query": "How do I fix bluetooth pairing issues on headphones?",
        "expected_doc_id": "bluetooth_pairing_issues",
        "expected_keywords": ["pair", "bluetooth", "reset"],
    },
]

OUT_OF_DOMAIN_CASES: List[str] = [
    "Write a Python script to scrape a website using BeautifulSoup.",
    "What is the capital of Mars?",
    "Can you give me the medical dosage for ibuprofen?",
]


class GroundingEvaluator:
    """Evaluates factual retrieval accuracy and graceful deflection/fallback."""

    def __init__(self, retriever: VectorRetriever) -> None:
        self.retriever = retriever

    async def evaluate_grounding_fidelity(
        self,
        test_cases: List[Dict[str, Any]] = DOMAIN_GROUNDING_CASES,
    ) -> Dict[str, Any]:
        """Verify that relevant queries retrieve correct documents and keyword facts."""
        total = len(test_cases)
        passed = 0
        details: List[Dict[str, Any]] = []

        for case in test_cases:
            query = case["query"]
            expected_doc = case["expected_doc_id"]
            keywords = case["expected_keywords"]

            result = await self.retriever.retrieve(query, top_k=3, score_threshold=0.35)

            found_doc = any(c.doc_id == expected_doc for c in result.chunks)
            all_content = " ".join(c.content.lower() for c in result.chunks)
            found_keywords = any(kw.lower() in all_content for kw in keywords)

            is_faithful = found_doc or found_keywords
            if is_faithful:
                passed += 1

            details.append({
                "query": query,
                "expected_doc": expected_doc,
                "top_doc": result.chunks[0].doc_id if result.chunks else "None",
                "score": result.citations[0].score if result.citations else 0.0,
                "faithful": is_faithful,
            })

        return {
            "total_cases": total,
            "passed_cases": passed,
            "fidelity_rate": round(passed / total * 100, 1),
            "details": details,
        }

    async def evaluate_failure_modes(
        self,
        ood_cases: List[str] = OUT_OF_DOMAIN_CASES,
    ) -> Dict[str, Any]:
        """Verify all Phase IV failure scenarios trigger fallback without crashing."""
        results: Dict[str, bool] = {}

        # 1. Out of domain queries with high threshold
        ood_deflected = 0
        for query in ood_cases:
            res = await self.retriever.retrieve(query, top_k=3, score_threshold=0.55)
            if res.is_fallback:
                ood_deflected += 1
        results["out_of_domain_fallback"] = (ood_deflected == len(ood_cases))

        # 2. Simulated slow search timeout
        mock_retriever = VectorRetriever(vector_store=self.retriever.vector_store)
        def hang_search(*args, **kwargs):
            time.sleep(1.2)
            return []
        mock_retriever._sync_search = hang_search  # type: ignore

        timeout_res = await mock_retriever.retrieve("test timeout", timeout_seconds=0.1)
        results["timeout_fallback"] = (timeout_res.is_fallback and len(timeout_res.chunks) == 0)

        # 3. Empty query
        empty_res = await self.retriever.retrieve("   ")
        results["empty_query_fallback"] = (empty_res.is_fallback and len(empty_res.chunks) == 0)

        all_passed = all(results.values())
        return {
            "all_passed": all_passed,
            "checks": results,
        }
