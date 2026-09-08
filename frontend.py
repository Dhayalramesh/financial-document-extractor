"""Streamlit frontend — upload a PDF, run extraction directly (no
separate API hop), display structured results.

Note: app/main.py contains the full FastAPI service for this same
pipeline, runnable locally via `uvicorn app.main:app`. This frontend
calls the pipeline functions directly for the hosted demo to avoid
running two separate free-tier services.
"""

import streamlit as st
import time
from app.pdf_parser import extract_text_from_pdf
from app.extractor import extract_earnings_data

st.set_page_config(page_title="Financial Document Extractor", layout="wide")

st.title("📄 Financial Document Extraction Engine")
st.caption(
    "Upload a quarterly earnings release PDF. An LLM extracts structured financial "
    "metrics (revenue, EPS, guidance, sentiment) with schema validation. "
    "A FastAPI service wrapping this same pipeline is included in the repo "
    "(`app/main.py`) — this demo calls it directly to keep hosting simple."
)

uploaded_file = st.file_uploader("Upload earnings PDF", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Extracting..."):
        file_bytes = uploaded_file.getvalue()

        if len(file_bytes) == 0:
            st.error("Uploaded file is empty.")
            st.stop()

        try:
            document_text = extract_text_from_pdf(file_bytes)
        except Exception as e:
            st.error(f"Could not parse PDF: {e}")
            st.stop()

        if len(document_text.strip()) < 20:
            st.error("Could not extract meaningful text from PDF (may be a scanned/image-only PDF).")
            st.stop()

        try:
            result = extract_earnings_data(document_text, uploaded_file.name)
        except Exception as e:
            st.error(f"Extraction failed: {e}")
            st.stop()

    extracted = result.extracted.model_dump()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Extracted Data")

        conf = extracted.get("extraction_confidence") or "unknown"
        conf_color = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(conf, "⚪")
        st.markdown(f"**Confidence:** {conf_color} {conf}")

        c1, c2 = st.columns(2)
        with c1:
            st.metric("Company", extracted.get("company_name") or "—")
            st.metric("Revenue", extracted.get("revenue") or "—")
            st.metric("EPS", extracted.get("eps") or "—")
        with c2:
            st.metric("Period", extracted.get("period") or "—")
            rev_growth = extracted.get("revenue_yoy_growth_pct")
            st.metric("Revenue YoY", f"{rev_growth}%" if rev_growth is not None else "—")
            eps_growth = extracted.get("eps_yoy_growth_pct")
            st.metric("EPS YoY", f"{eps_growth}%" if eps_growth is not None else "—")

        sentiment = extracted.get("result_sentiment")
        if sentiment and sentiment != "not_stated":
            emoji = {"beat": "✅", "miss": "❌", "inline": "➖"}.get(sentiment, "")
            st.info(f"{emoji} Result sentiment: **{sentiment.upper()}**")

        if extracted.get("guidance_summary"):
            st.markdown("**Guidance / Outlook:**")
            st.write(extracted["guidance_summary"])

        if extracted.get("key_risks"):
            st.markdown("**Key Risks:**")
            st.write(extracted["key_risks"])

    with col2:
        st.subheader("Pipeline Stats")
        st.metric("Processing time", f"{result.processing_time_ms:.0f} ms")
        st.metric("Document length parsed", f"{result.raw_text_char_count:,} chars")

    with st.expander("Raw JSON response"):
        st.json(result.model_dump())