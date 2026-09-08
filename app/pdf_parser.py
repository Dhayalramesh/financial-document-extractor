"""PDF text extraction. O(n) in number of pages — no recursion,
no re-parsing; single linear pass over the document.
"""

import pdfplumber
from io import BytesIO


def extract_text_from_pdf(file_bytes: bytes, max_chars: int = 15000) -> str:
    """Extracts text from a PDF's bytes, capped at max_chars to keep
    LLM context usage bounded and cost/latency predictable."""
    text_parts = []
    total_len = 0

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
            total_len += len(page_text)
            if total_len >= max_chars:
                break

    full_text = "\n".join(text_parts)
    return full_text[:max_chars]