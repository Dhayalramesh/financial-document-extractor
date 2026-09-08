"""Streamlit frontend — upload a PDF, call the FastAPI backend,
display structured results.
"""

import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Financial Document Extractor", layout="wide")

# When running locally, backend is localhost. When deployed, this
# gets overridden via Streamlit secrets (set in Cloud dashboard).
API_URL = os.environ.get("EXTRACTOR_API_URL", "http://localhost:8000")

st.title("📄 Financial Document Extraction Engine")
st.caption(
    "Upload a quarterly earnings release PDF. An LLM extracts structured financial "
    "metrics (revenue, EPS, guidance, sentiment) with schema validation."
)

uploaded_file = st.file_uploader("Upload earnings PDF", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Extracting..."):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        try:
            response = requests.post(f"{API_URL}/extract", files=files, timeout=60)
        except requests.exceptions.ConnectionError:
            st.error(f"Could not reach the extraction API at {API_URL}. Is the backend running?")
            st.stop()

    if response.status_code != 200:
        st.error(f"Extraction failed: {response.json().get('detail', 'Unknown error')}")
        st.stop()

    result = response.json()
    extracted = result["extracted"]

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
        st.metric("Processing time", f"{result['processing_time_ms']:.0f} ms")
        st.metric("Document length parsed", f"{result['raw_text_char_count']:,} chars")

    with st.expander("Raw JSON response"):
        st.json(result)