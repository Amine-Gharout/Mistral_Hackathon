"""PDF loader using PyMuPDF — extracts text and tables from the ANAH 2026 guide."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import fitz  # pymupdf


def load_pdf(pdf_path: Path) -> list[dict]:
    """
    Extract text from each page of the PDF.

    Returns:
        List of dicts with {page_number, text, char_count}
    """
    if not pdf_path.exists():
        print(f"[RAG] PDF not found at {pdf_path}")
        return []

    doc = fitz.open(str(pdf_path))
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")

        if text.strip():
            pages.append({
                "page_number": page_num + 1,
                "text": text.strip(),
                "char_count": len(text.strip()),
            })

    doc.close()
    print(f"[RAG] Extracted {len(pages)} pages with text from {pdf_path.name}")
    return pages


def extract_text_blocks(pdf_path: Path) -> list[dict]:
    """
    Extract text blocks with position info for more granular chunking.

    Returns:
        List of dicts with {page_number, text, bbox, block_type}
    """
    if not pdf_path.exists():
        return []

    doc = fitz.open(str(pdf_path))
    blocks = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_blocks = page.get_text("dict")["blocks"]

        for block in page_blocks:
            if block.get("type") == 0:  # Text block
                text_parts = []
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text_parts.append(span.get("text", ""))

                text = " ".join(text_parts).strip()
                if text and len(text) > 10:
                    blocks.append({
                        "page_number": page_num + 1,
                        "text": text,
                        "bbox": block.get("bbox"),
                        "block_type": "text",
                    })

    doc.close()
    print(f"[RAG] Extracted {len(blocks)} text blocks from {pdf_path.name}")
    return blocks
