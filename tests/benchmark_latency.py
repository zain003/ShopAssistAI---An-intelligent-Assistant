"""CPU Latency Benchmarking Harness for ShopAssist AI.

Measures Time-To-First-Token (TTFT in ms), Generation Throughput (tokens/sec),
and total inference duration over standard e-commerce queries per FEAT-005-INT.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Tuple

from backend.contracts import BenchmarkResult, StreamEndPayload
from backend.conversation.manager import ConversationManager
from backend.core.llm import LLMEngine

# 5 Standard E-Commerce Queries across core customer support flows
STANDARD_BENCHMARK_PROMPTS: List[str] = [
    "Where is my order ORD-1085 and when will it arrive?",
    "What is your return policy for audio products and shoes?",
    "Can you recommend wireless headphones with noise cancellation under $150?",
    "How much does express shipping cost and what is the cutoff time for same-day dispatch?",
    "Can I return an item after 45 days if it was defective?",
]


def calculate_mean_ttft(results: List[BenchmarkResult]) -> float:
    """Calculates the arithmetic mean TTFT in milliseconds.

    Args:
        results: List of BenchmarkResult objects.

    Returns:
        float: Average TTFT rounded to 2 decimal places (0.0 if empty).
    """
    if not results:
        return 0.0
    return round(sum(r.ttft_ms for r in results) / len(results), 2)


def calculate_mean_tokens_per_sec(results: List[BenchmarkResult]) -> float:
    """Calculates the arithmetic mean throughput in tokens per second.

    Args:
        results: List of BenchmarkResult objects.

    Returns:
        float: Average tokens/sec rounded to 2 decimal places (0.0 if empty).
    """
    if not results:
        return 0.0
    return round(sum(r.tokens_per_second for r in results) / len(results), 2)


def calculate_summary_statistics(results: List[BenchmarkResult]) -> Dict[str, float]:
    """Computes min, max, and mean metrics across benchmark runs.

    Args:
        results: List of BenchmarkResult objects.

    Returns:
        Dict[str, float]: Dictionary containing aggregated latency and throughput metrics.
    """
    if not results:
        return {
            "total_runs": 0.0,
            "min_ttft_ms": 0.0,
            "max_ttft_ms": 0.0,
            "mean_ttft_ms": 0.0,
            "min_tokens_per_sec": 0.0,
            "max_tokens_per_sec": 0.0,
            "mean_tokens_per_sec": 0.0,
            "mean_duration_ms": 0.0,
        }

    ttfts = [r.ttft_ms for r in results]
    tps = [r.tokens_per_second for r in results]
    durations = [r.total_duration_ms for r in results]

    return {
        "total_runs": float(len(results)),
        "min_ttft_ms": round(min(ttfts), 2),
        "max_ttft_ms": round(max(ttfts), 2),
        "mean_ttft_ms": calculate_mean_ttft(results),
        "min_tokens_per_sec": round(min(tps), 2),
        "max_tokens_per_sec": round(max(tps), 2),
        "mean_tokens_per_sec": calculate_mean_tokens_per_sec(results),
        "mean_duration_ms": round(sum(durations) / len(durations), 2),
    }


class BenchmarkRunner:
    """Automated benchmark harness for measuring CPU inference latency."""

    def __init__(
        self,
        engine: Optional[LLMEngine] = None,
        conversation_manager: Optional[ConversationManager] = None,
    ) -> None:
        """Initializes the benchmark harness.

        Args:
            engine: Optional LLMEngine instance (defaults to standard LLMEngine).
            conversation_manager: Optional ConversationManager instance.
        """
        self.engine = engine or LLMEngine()
        self.conversation_manager = conversation_manager or ConversationManager()

    async def run_benchmarks(
        self,
        sample_prompts: Optional[List[str]] = None,
        discard_warmup: bool = True,
        stream_generator_fn: Optional[
            Callable[[List[Dict[str, str]], str], AsyncGenerator[Tuple[str, Optional[StreamEndPayload]], None]]
        ] = None,
    ) -> List[BenchmarkResult]:
        """Executes latency benchmarks across test prompts.

        Args:
            sample_prompts: List of prompt strings to test.
            discard_warmup: When True, run #0 (warmup) is executed and discarded
                from final results to prevent cold-start skew.
            stream_generator_fn: Optional generator function override for mocking.

        Returns:
            List[BenchmarkResult]: List of benchmark results for valid runs.
        """
        prompts = sample_prompts if sample_prompts is not None else STANDARD_BENCHMARK_PROMPTS
        results: List[BenchmarkResult] = []

        # Run #0: Warmup run (preloads weights into RAM; discarded to prevent skew)
        if discard_warmup:
            warmup_session = self.conversation_manager.get_or_create_session("benchmark_warmup_sess")
            self.conversation_manager.add_user_message(warmup_session.session_id, "Hello ShopAssist")
            warmup_payload = self.conversation_manager.build_chat_payload(warmup_session.session_id)

            gen = (
                stream_generator_fn(warmup_payload, "warmup_turn_0")
                if stream_generator_fn is not None
                else self.engine.generate_stream(warmup_payload, turn_id="warmup_turn_0")
            )
            async for _token, _end_payload in gen:
                pass

        # Measured benchmark runs (Runs 1 to N)
        for idx, prompt in enumerate(prompts, start=1):
            session_id = f"benchmark_sess_{idx}"
            session = self.conversation_manager.get_or_create_session(session_id)
            self.conversation_manager.add_user_message(session_id, prompt)
            chat_payload = self.conversation_manager.build_chat_payload(session_id)

            gen = (
                stream_generator_fn(chat_payload, f"bench_turn_{idx}")
                if stream_generator_fn is not None
                else self.engine.generate_stream(chat_payload, turn_id=f"bench_turn_{idx}")
            )

            end_payload: Optional[StreamEndPayload] = None
            async for _token, payload in gen:
                if payload is not None:
                    end_payload = payload

            if end_payload is not None:
                result = BenchmarkResult(
                    run_index=idx,
                    ttft_ms=end_payload.ttft_ms,
                    total_tokens=end_payload.total_tokens,
                    total_duration_ms=end_payload.total_duration_ms,
                    tokens_per_second=end_payload.tokens_per_second,
                )
                results.append(result)

        return results


def print_benchmark_table(results: List[BenchmarkResult], prompts: List[str]) -> None:
    """Formats and prints an ASCII summary table of benchmark results to stdout.

    Args:
        results: List of BenchmarkResult objects.
        prompts: List of prompt strings tested.
    """
    stats = calculate_summary_statistics(results)

    print("\n" + "=" * 92)
    print("                SHOPASSIST AI — CPU LATENCY & THROUGHPUT BENCHMARK")
    print("=" * 92)
    print(f"{'Run':<5} | {'Prompt Query':<38} | {'TTFT (ms)':<10} | {'Tokens':<7} | {'Duration (ms)':<13} | {'Tokens/s':<8}")
    print("-" * 92)

    for r in results:
        p_text = prompts[r.run_index - 1] if r.run_index - 1 < len(prompts) else "Prompt"
        truncated_prompt = (p_text[:35] + "...") if len(p_text) > 38 else p_text
        print(
            f"#{r.run_index:<4} | {truncated_prompt:<38} | {r.ttft_ms:<10.2f} | "
            f"{r.total_tokens:<7} | {r.total_duration_ms:<13.2f} | {r.tokens_per_second:<8.2f}"
        )

    print("-" * 92)
    print("SUMMARY METRICS (Cold-Start Skew Discarded):")
    print(f"  • Total Evaluated Runs:  {int(stats['total_runs'])}")
    print(f"  • Time-To-First-Token:   Min: {stats['min_ttft_ms']}ms | Mean: {stats['mean_ttft_ms']}ms | Max: {stats['max_ttft_ms']}ms")
    print(f"  • Generation Throughput: Min: {stats['min_tokens_per_sec']} tps | Mean: {stats['mean_tokens_per_sec']} tps | Max: {stats['max_tokens_per_sec']} tps")
    print(f"  • Average Duration:      {stats['mean_duration_ms']}ms")
    print("=" * 92 + "\n")


async def main() -> int:
    """Main CLI entrypoint for running latency benchmarks."""
    runner = BenchmarkRunner()

    is_ready = await runner.engine.is_ready()
    if not is_ready:
        print("[WARNING] Local Ollama service is not ready or model is missing. Cannot run live benchmarks.")
        return 1

    print("[INFO] Starting CPU Latency Benchmark (5 queries, warmup discarded)...")
    results = await runner.run_benchmarks()
    print_benchmark_table(results, STANDARD_BENCHMARK_PROMPTS)
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
