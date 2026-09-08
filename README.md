# 📄 Financial Document Extraction Engine

An LLM-powered pipeline that extracts structured financial data (revenue, EPS, guidance, sentiment) from quarterly earnings release PDFs, with schema validation and a measured accuracy benchmark.

**🔗 Live Demo:** https://financial-document-extractor-zdm6y6jvkvdg3v3kistuel.streamlit.app/

## What it does

- **Parses** quarterly earnings PDFs and extracts raw text via `pdfplumber`
- **Extracts structured data** using an LLM (Groq, `openai/gpt-oss-120b`) constrained to a strict Pydantic schema — no free-text hallucination, every field is typed and validated
- **Scores confidence** — the model self-reports high/medium/low confidence per extraction based on how clearly the source text stated each figure
- **Detects sentiment** — flags whether results beat, missed, or were in line with analyst estimates, when explicitly stated in the document
- **Benchmarked accuracy** — includes an evaluation harness comparing extracted fields against manually labeled ground truth

## Results

On a labeled test document, the extraction pipeline achieved:
- **100% field-level accuracy** (10/10 fields correctly extracted)
- **~1.1–1.7s average processing time** per document (PDF parse + LLM extraction, end-to-end)

## Architecture
PDF upload (Streamlit)
↓
pdfplumber — text extraction (capped at 15k chars for bounded latency/cost)
↓
Groq LLM — structured extraction (JSON-schema-constrained, temperature=0.1)
↓
Pydantic validation — typed, parseable output
↓
Streamlit frontend — structured results display

A standalone FastAPI service wrapping this same pipeline is included (`app/main.py`), runnable locally via `uvicorn app.main:app`, with interactive docs at `/docs`. The hosted demo calls the extraction pipeline directly from Streamlit rather than through a separately-hosted API, to keep the deployment footprint to a single free-tier service.

## Tech stack

Python · FastAPI · Groq API · pdfplumber · Pydantic · Streamlit

## Key engineering decisions

- **Schema-constrained extraction, not free-text generation**: the LLM is forced into a strict JSON schema via Groq's `response_format`, so output is always parseable and every field is typed — this is what makes the pipeline testable and production-viable, not just a chatbot wrapper.
- **Low temperature (0.1)**: extraction tasks need consistency and factual grounding, not creativity — this materially reduces hallucinated figures compared to default sampling.
- **Self-reported confidence scoring**: the model flags its own certainty per extraction, giving downstream consumers (e.g. a trading desk) a signal for when to double-check a figure against the source.
- **Graceful degradation**: if the LLM returns malformed JSON, the pipeline falls back to a low-confidence null result instead of crashing — a single bad response never takes down the service.
- **Bounded document length**: text is capped at 15k characters before hitting the LLM, keeping latency and cost predictable regardless of document size.
- **Cloud-portable secrets handling**: the Groq API key is read from a local `.env` in development and from Streamlit Cloud's secrets manager in production, via a single fallback-aware helper function.

## Run it locally

**Backend (FastAPI):**
```bash
git clone https://github.com/Dhayalramesh/financial-document-extractor.git
cd financial-document-extractor
python -m venv venv
venv\Scripts\activate  # or source venv/bin/activate on Mac/Linux
pip install -r requirements.txt
```


Create a `.env` file with your free Groq API key (get one at console.groq.com):

Start the backend:
```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`.

**Frontend (Streamlit):**
```bash
streamlit run frontend.py
```

Visit `http://localhost:8501` to upload a PDF and see extracted results.

## Running the evaluation

```bash
python -m app.eval
```

Compares extraction output against `sample_docs/labels.json` and prints field-level accuracy.

## Known limitations

- Text-based PDFs only — scanned/image-only PDFs are not supported (no OCR layer)
- Exact-match evaluation is strict; semantically correct but differently-formatted values (e.g. "Rs. 4,850 crore" vs "₹4850 Cr") would be scored as mismatches
- Groq's free tier model availability changes periodically (this project uses `openai/gpt-oss-120b` as of Sept 2026); model ID may need updating over time
- The hosted demo runs the extraction pipeline directly rather than through the FastAPI service, to avoid maintaining two separate free-tier deployments
