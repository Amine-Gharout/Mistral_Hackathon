"""PDF download script for the ANAH 2026 Guide des aides financières."""

import hashlib
import sys
from pathlib import Path

import httpx


ANAH_PDF_URL = "https://www.anah.gouv.fr/document/guide-des-aides-financieres-0126"
FALLBACK_URL = "https://www.anah.gouv.fr/sites/default/files/2026-01/guide-aides-financieres-2026.pdf"

OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_PATH = OUTPUT_DIR / "anah_guide_2026.pdf"


def download_pdf(force: bool = False) -> Path:
    """Download the ANAH 2026 PDF if not already present."""
    if OUTPUT_PATH.exists() and not force:
        size = OUTPUT_PATH.stat().st_size
        if size > 100_000:  # At least 100KB for a valid PDF
            print(
                f"[RAG] PDF already exists at {OUTPUT_PATH} ({size:,} bytes). Skipping download.")
            return OUTPUT_PATH
        else:
            print(
                f"[RAG] Existing PDF too small ({size} bytes), re-downloading...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for url in [ANAH_PDF_URL, FALLBACK_URL]:
        try:
            print(f"[RAG] Downloading from {url}...")
            with httpx.Client(follow_redirects=True, timeout=60.0) as client:
                resp = client.get(url)
                resp.raise_for_status()

                content_type = resp.headers.get("content-type", "")
                if "pdf" in content_type or resp.content[:4] == b"%PDF":
                    OUTPUT_PATH.write_bytes(resp.content)
                    size = len(resp.content)
                    md5 = hashlib.md5(resp.content).hexdigest()
                    print(
                        f"[RAG] Downloaded {size:,} bytes (MD5: {md5}) to {OUTPUT_PATH}")
                    return OUTPUT_PATH
                else:
                    # Might be an HTML page with a download link
                    print(
                        f"[RAG] Response is not a PDF (content-type: {content_type}). Trying next URL...")
                    continue

        except Exception as e:
            print(f"[RAG] Failed to download from {url}: {e}")
            continue

    print("[RAG] WARNING: Could not download the ANAH PDF. RAG features will be limited.")
    print("[RAG] You can manually place the PDF at:", OUTPUT_PATH)
    return OUTPUT_PATH


if __name__ == "__main__":
    force = "--force" in sys.argv
    download_pdf(force=force)
