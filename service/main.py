from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import tempfile
import os

# Import the existing ABNT modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

app = FastAPI(title="ABNT Format Service")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class FormatRequest(BaseModel):
    content: Dict[str, Any]
    font: str = "Times New Roman"
    metadata: Optional[Dict[str, Any]] = None
    auto_fix: Optional[Dict[str, bool]] = None

class ValidateRequest(BaseModel):
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class ReferenceRequest(BaseModel):
    dois: List[str] = []
    isbns: List[str] = []
    urls: List[str] = []

class ExportRequest(BaseModel):
    content: Dict[str, Any]
    format: str  # "docx" | "pdf"
    filename: str

# --- Health Check ---
@app.get("/health")
async def health():
    return {"status": "ok", "service": "abnt-format-service"}

# --- Format Document ---
@app.post("/format")
async def format_document(req: FormatRequest):
    """Aplica formatação ABNT ao TipTap JSON → retorna TipTap JSON formatado"""
    try:
        # Convert TipTap JSON to python-docx Document
        doc = tiptap_to_docx(req.content)

        # Apply ABNT formatting using existing adjust.py
        # adjust.adjust_docx(doc, req.font, req.metadata.get("filename", "documento.docx"))

        # Convert back to TipTap JSON
        formatted_json = docx_to_tiptap(doc)

        # Validate
        report = validate_all(doc, req.metadata)

        return {
            "content": formatted_json,
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Validate Document ---
@app.post("/validate")
async def validate_document(req: ValidateRequest):
    """Valida sem modificar → retorna ValidationReport"""
    try:
        doc = tiptap_to_docx(req.content)
        report = validate_all(doc, req.metadata)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Generate References ---
@app.post("/references/generate")
async def generate_references(req: ReferenceRequest):
    """Crossref (DOI) / OpenLibrary (ISBN) / OpenAlex (URL) → ABNT entries"""
    try:
        entries = []
        for doi in req.dois:
            csl = await crossref_fetch(doi)
            abnt = csl_to_abnt(csl)
            entries.append({"csl": csl, "abnt": abnt, "source": "doi", "source_id": doi})
        for isbn in req.isbns:
            csl = await openlibrary_fetch(isbn)
            abnt = csl_to_abnt(csl)
            entries.append({"csl": csl, "abnt": abnt, "source": "isbn", "source_id": isbn})
        for url in req.urls:
            csl = await openalex_fetch(url)
            abnt = csl_to_abnt(csl)
            entries.append({"csl": csl, "abnt": abnt, "source": "url", "source_id": url})
        return {"references": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Import DOCX ---
@app.post("/import-docx")
async def import_docx(file: UploadFile = File(...)):
    """Upload .docx → TipTap JSON"""
    try:
        content = await file.read()
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Convert using mammoth + python-docx + classify
        tiptap_json = docx_to_tiptap_import(tmp_path)

        os.unlink(tmp_path)
        return {"content": tiptap_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Export DOCX ---
@app.post("/export-docx")
async def export_docx(req: ExportRequest):
    """TipTap JSON → .docx (bytes)"""
    try:
        doc = tiptap_to_docx(req.content)
        # apply final ABNT formatting
        # adjust.adjust_docx(doc, "Times New Roman", req.filename)

        from io import BytesIO
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={req.filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Export PDF ---
@app.post("/export-pdf")
async def export_pdf(req: ExportRequest):
    """TipTap JSON → PDF (bytes) via Playwright/Chromium"""
    try:
        # Render HTML → PDF with print CSS
        html = tiptap_to_html(req.content)
        pdf_bytes = await html_to_pdf(html)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={req.filename.replace('.docx', '.pdf')}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Helper Functions (Stubs - to be implemented with actual ABNT logic) ---

def tiptap_to_docx(json_content: Dict) -> Any:
    """Convert TipTap JSON to python-docx Document"""
    from docx import Document
    doc = Document()
    # TODO: Implement full conversion
    return doc

def docx_to_tiptap(doc: Any) -> Dict:
    """Convert python-docx Document to TipTap JSON"""
    # TODO: Implement full conversion
    return {"type": "doc", "content": []}

def docx_to_tiptap_import(filepath: str) -> Dict:
    """Import .docx file to TipTap JSON"""
    # TODO: Use mammoth + python-docx + classify
    return {"type": "doc", "content": []}

def tiptap_to_html(json_content: Dict) -> str:
    """Convert TipTap JSON to HTML for PDF rendering"""
    # TODO: Use TipTap HTML serializer
    return "<html><body></body></html>"

async def html_to_pdf(html: str) -> bytes:
    """Render HTML to PDF using Playwright"""
    # TODO: Use Playwright/Chromium
    return b"%PDF-1.4..."

def validate_all(doc: Any, metadata: Optional[Dict]) -> Dict:
    """Run all validations"""
    return {
        "estrutura": {"encontrados": [], "faltando": [], "ordem_incorreta": [], "pendencias": []},
        "citacoes": {"curtas_sem_aspas": [], "longas_com_aspas": [], "autor_formato": [], "footnotes_ok": True, "pendencias": []},
        "referencias": {"fora_ordem": [], "sem_entrelinha": False, "sem_negrito_ano": False, "sem_doi": [], "citadas_nao_referenciadas": [], "referenciadas_nao_citadas": [], "autor_formato": [], "pendencias": []},
        "elementos_visuais": {"caption_posicao": [], "numeracao_faltando": [], "fonte_faltando": [], "cross_ref_ordem": [], "pendencias": []},
        "capa": {"tem_capa": True, "tem_folha_rosto": True, "campos_faltando": [], "divergencias": []},
        "cross_check": {"orphans_citacoes": [], "orphans_referencias": []},
    }

async def crossref_fetch(doi: str) -> Dict:
    """Fetch CSL-JSON from Crossref API"""
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://api.crossref.org/works/{doi}")
        return resp.json()["message"]

async def openlibrary_fetch(isbn: str) -> Dict:
    """Fetch from OpenLibrary API"""
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://openlibrary.org/isbn/{isbn}.json")
        return resp.json()

async def openalex_fetch(url: str) -> Dict:
    """Fetch from OpenAlex API"""
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://api.openalex.org/works/{url}")
        return resp.json()

def csl_to_abnt(csl: Dict) -> str:
    """Convert CSL-JSON to ABNT formatted string"""
    # TODO: Use citeproc-python with ABNT style
    return "Referência formatada ABNT..."

from starlette.responses import Response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)