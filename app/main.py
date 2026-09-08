"""FastAPI application. Single endpoint: upload a PDF, get back
structured earnings data.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.pdf_parser import extract_text_from_pdf
from app.extractor import extract_earnings_data
from app.schemas import ExtractionResponse

app = FastAPI(title="Financial Document Extraction Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo project — fine for now; restrict in real production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "financial-document-extractor"}


@app.post("/extract", response_model=ExtractionResponse)
async def extract_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    document_text = extract_text_from_pdf(file_bytes)
    if len(document_text.strip()) < 20:
        raise HTTPException(
            status_code=422,
            detail="Could not extract meaningful text from PDF (may be a scanned/image-only PDF)",
        )

    result = extract_earnings_data(document_text, file.filename)
    return result