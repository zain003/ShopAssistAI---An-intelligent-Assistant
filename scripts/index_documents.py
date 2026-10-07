"""CLI runner script for offline document indexing in ShopAssist AI.

Usage:
    python scripts/index_documents.py [--docs-dir data/documents] [--store-dir data/vector_store] [--rebuild]
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path so backend package is discoverable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.rag.indexer import DocumentIndexer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("indexer_cli")


def main() -> int:
    parser = argparse.ArgumentParser(description="ShopAssist AI Document Indexer CLI")
    parser.add_argument(
        "--docs-dir",
        type=str,
        default="data/documents",
        help="Path to markdown documents directory (default: data/documents)",
    )
    parser.add_argument(
        "--store-dir",
        type=str,
        default="data/vector_store",
        help="Path to vector store directory (default: data/vector_store)",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force full re-indexing and overwrite existing cache",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("   SHOPASSIST AI — OFFLINE RAG INDEXING PIPELINE")
    print("=" * 60)
    print(f"Corpus Directory   : {args.docs_dir}")
    print(f"Store Directory    : {args.store_dir}")
    print(f"Force Rebuild      : {args.rebuild}")
    print("-" * 60)

    try:
        indexer = DocumentIndexer(
            docs_dir=args.docs_dir,
            store_dir=args.store_dir,
        )

        start_time = time.time()
        result = indexer.index_corpus(force_rebuild=args.rebuild)
        total_time = time.time() - start_time

        print("\nINDEXING COMPLETE:")
        print(f"  • Total Documents Ingested : {result['total_docs']}")
        print(f"  • New Documents Embedded   : {result['new_docs']}")
        print(f"  • Skipped Unchanged Docs   : {result['skipped_docs']}")
        print(f"  • Total Chunks Indexed     : {result['total_chunks']}")
        print(f"  • Wall Time Elapsed        : {total_time:.2f}s ({result['duration_ms']}ms)")
        print("=" * 60)
        return 0

    except Exception as e:
        logger.exception("Indexing pipeline failed with error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
