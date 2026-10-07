"""Markdown header-aware chunking for ShopAssist domain documents.

Implements header-aware segmentation splitting documents by H1 (#) and H2 (##)
tags, bounding chunks between 100 and 500 characters with overlapping windows.
"""

from __future__ import annotations

import re
from typing import List, Tuple
from backend.contracts import DocumentChunk, DocumentMetadata


def estimate_tokens(text: str) -> int:
    """Estimate token count for a text chunk using word and whitespace ratio."""
    words = text.split()
    if not words:
        return 0
    # Standard estimate: ~1.33 tokens per word or ~4 chars per token
    return max(1, int(len(words) * 1.33))


def chunk_markdown_document(
    doc_meta: DocumentMetadata,
    text: str,
    chunk_size: int = 400,
    chunk_overlap: int = 50,
) -> List[DocumentChunk]:
    """Split a markdown document into semantic chunks preserving header context.
    
    Args:
        doc_meta: Document metadata containing doc_id, title, category, etc.
        text: Raw markdown text content.
        chunk_size: Target maximum character length per chunk (default: 400).
        chunk_overlap: Sliding window character overlap (default: 50).
        
    Returns:
        List of DocumentChunk instances with title and section headers populated.
    """
    clean_text = text.strip()
    if not clean_text:
        return []

    # 1. Extract main title (# Title) if present
    doc_title = doc_meta.title
    title_match = re.search(r"^#\s+(.+)$", clean_text, flags=re.MULTILINE)
    if title_match:
        doc_title = title_match.group(1).strip()

    # 2. Split text into sections by ## or ### headings
    section_pattern = re.compile(r"^(#{2,3}\s+.+)$", flags=re.MULTILINE)
    splits = section_pattern.split(clean_text)

    # Accumulate (section_header, section_body) pairs
    sections: List[Tuple[str, str]] = []

    # If the text starts with content before any H2/H3 header
    initial_content = splits[0].strip()
    if initial_content:
        # Check if there is lead-in text after H1 title
        lines = [line.strip() for line in initial_content.splitlines() if line.strip() and not line.startswith("# ")]
        lead_text = "\n".join(lines).strip()
        if lead_text:
            sections.append(("Overview", lead_text))

    # Process pairs of (header, content) from regex split
    for i in range(1, len(splits), 2):
        raw_header = splits[i].strip()
        header_text = re.sub(r"^#{2,3}\s+", "", raw_header).strip()
        body_text = splits[i + 1].strip() if i + 1 < len(splits) else ""
        if body_text:
            sections.append((header_text, body_text))

    # If no sections were identified (e.g. doc lacks ## headers), treat all as General
    if not sections:
        sections.append(("General", clean_text))

    chunks: List[DocumentChunk] = []
    chunk_index = 0

    for section_header, section_body in sections:
        # Include context header prefix so semantic meaning is preserved
        header_prefix = f"[{doc_title} - {section_header}]\n"
        full_section_content = f"{header_prefix}{section_body}"

        # If full section fits comfortably within bounds (<= 500 chars)
        if len(full_section_content) <= chunk_size + 100:
            content_str = full_section_content
            # Ensure at least 100 chars if possible
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{doc_meta.doc_id}_c{chunk_index}",
                    doc_id=doc_meta.doc_id,
                    title=doc_title,
                    section_header=section_header,
                    content=content_str,
                    token_count=estimate_tokens(content_str),
                    char_count=len(content_str),
                    chunk_index=chunk_index,
                )
            )
            chunk_index += 1
        else:
            # Sliding window over long section content
            step = max(50, chunk_size - chunk_overlap)
            body_len = len(section_body)
            start = 0

            while start < body_len:
                end = min(start + chunk_size, body_len)
                sub_body = section_body[start:end].strip()
                
                # Expand slightly to sentence/paragraph boundary if available
                if end < body_len:
                    last_period = sub_body.rfind(". ")
                    if last_period > chunk_size // 2:
                        sub_body = sub_body[: last_period + 1].strip()
                        end = start + len(sub_body)

                chunk_content = f"{header_prefix}{sub_body}".strip()
                
                # Bound chunk length between 100 and 500 chars
                if len(chunk_content) < 100 and end < body_len:
                    # Extend forward to meet minimum length
                    ext_end = min(start + 150, body_len)
                    sub_body = section_body[start:ext_end].strip()
                    chunk_content = f"{header_prefix}{sub_body}".strip()

                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{doc_meta.doc_id}_c{chunk_index}",
                        doc_id=doc_meta.doc_id,
                        title=doc_title,
                        section_header=section_header,
                        content=chunk_content,
                        token_count=estimate_tokens(chunk_content),
                        char_count=len(chunk_content),
                        chunk_index=chunk_index,
                    )
                )
                chunk_index += 1
                start += step
                if start >= body_len:
                    break

    return chunks
