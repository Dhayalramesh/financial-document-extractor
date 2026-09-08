"""LLM-based structured extraction using Groq. Forces JSON-schema-
constrained output so results are parseable and testable, not just
free-text generation.
"""

import os
import time
import json
from groq import Groq
from dotenv import load_dotenv
from app.schemas import EarningsExtraction, ExtractionResponse

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"  # Groq deprecated llama-3.3-70b-versatile on Aug 16, 2026

SYSTEM_PROMPT = """You are a financial data extraction engine. You will be given raw text extracted from a company's quarterly earnings release or results PDF.

Extract the following fields into a JSON object matching this exact schema:
{
  "company_name": string or null,
  "ticker": string or null,
  "period": string or null,
  "revenue": string or null,
  "revenue_yoy_growth_pct": number or null,
  "eps": string or null,
  "eps_yoy_growth_pct": number or null,
  "net_profit": string or null,
  "net_margin_pct": number or null,
  "guidance_summary": string or null,
  "key_risks": string or null,
  "result_sentiment": "beat" | "miss" | "inline" | "not_stated",
  "extraction_confidence": "high" | "medium" | "low"
}

Rules:
- Only extract information explicitly present in the text. Do not infer or hallucinate numbers.
- If a field is not present in the text, use null.
- Output ONLY the JSON object, no other text, no markdown code fences.
- For extraction_confidence: "high" if figures are clearly stated with labels, "medium" if some inference of formatting was needed, "low" if the text is ambiguous or noisy.
"""


def extract_earnings_data(document_text: str, filename: str) -> ExtractionResponse:
    start = time.time()

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract data from this earnings document text:\n\n{document_text}"},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    raw_output = completion.choices[0].message.content
    processing_time_ms = (time.time() - start) * 1000

    try:
        parsed = json.loads(raw_output)
        extracted = EarningsExtraction(**parsed)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        extracted = EarningsExtraction(
            extraction_confidence="low",
            guidance_summary=f"[extraction parse error: {str(e)[:100]}]",
        )

    return ExtractionResponse(
        filename=filename,
        extracted=extracted,
        processing_time_ms=processing_time_ms,
        raw_text_char_count=len(document_text),
    )