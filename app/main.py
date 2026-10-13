"""Aplicação FastAPI — roda localmente e no Vercel.

O arquivo enviado NÃO passa pela função serverless (o Vercel limita o corpo da
requisição a ~4,5 MB). Em vez disso:

  1. `POST /api/presign` devolve uma URL assinada do Vercel Blob.
  2. O navegador envia o arquivo DIRETO para o Blob.
  3. `POST /api/format` baixa o arquivo do Blob, aplica a formatação ABNT e
     devolve a URL do arquivo corrigido (também no Blob).
  4. `POST /api/cleanup` apaga o resultado depois do download.

No Vercel, arquivos em `public/` são servidos pelo CDN; localmente montamos
`public/` para servir o front-end.
"""
import os
import sys
import tempfile
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from abnt import adjust, blob, config, pdf_docx  # noqa: E402

blob.load_env_files(BASE_DIR)

PUBLIC_DIR = os.path.join(BASE_DIR, "public")
MAX_BYTES = 50 * 1024 * 1024  # limite de tamanho do arquivo (agora no Vercel Blob)
ALLOWED_EXT = {".docx", ".pdf"}

DOCX_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
PDF_TYPE = "application/pdf"
CONTENT_TYPES = {".docx": DOCX_TYPE, ".pdf": PDF_TYPE}

app = FastAPI(title="Formatador ABNT")


@app.get("/api/health")
async def health():
    return {"status": "ok", "storage": blob.is_configured()}


def _safe_name(filename):
    base = os.path.basename(filename or "documento")
    keep = []
    for char in base:
        if char.isalnum() or char in "._- ":
            keep.append(char)
    cleaned = "".join(keep).strip() or "documento"
    return cleaned[:120]


def _ext_of(filename):
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "Envie um arquivo .docx ou .pdf.")
    return ext


@app.post("/api/presign")
async def presign(request: Request):
    if not blob.is_configured():
        raise HTTPException(
            503,
            "O armazenamento de arquivos ainda não está configurado. "
            "Tente novamente em instantes.",
        )

    payload = await request.json()
    filename = payload.get("filename") or ""
    size = int(payload.get("size") or 0)
    ext = _ext_of(filename)

    if size and size > MAX_BYTES:
        raise HTTPException(
            413,
            f"O arquivo tem {size / 1048576:.1f} MB. O limite é "
            f"{MAX_BYTES // 1048576} MB.",
        )

    pathname = f"uploads/{uuid.uuid4().hex}/{_safe_name(filename)}"
    allowed = [CONTENT_TYPES[ext], "application/octet-stream"]
    try:
        info = blob.issue_presigned_put(pathname, MAX_BYTES, allowed)
    except blob.BlobError as exc:
        raise HTTPException(502, str(exc)) from exc

    return JSONResponse(info)


@app.post("/api/format")
async def format_document(request: Request):
    if not blob.is_configured():
        raise HTTPException(
            503,
            "O armazenamento de arquivos ainda não está configurado. "
            "Tente novamente em instantes.",
        )

    payload = await request.json()
    pathname = payload.get("pathname") or ""
    filename = payload.get("filename") or os.path.basename(pathname)
    font = payload.get("font") or ""

    if not pathname.startswith("uploads/"):
        raise HTTPException(400, "Referência de arquivo inválida.")
    ext = _ext_of(filename)
    if font not in config.FONT_CHOICES:
        raise HTTPException(400, "Fonte inválida. Escolha Arial ou Times New Roman.")

    try:
        data = blob.fetch(blob.public_url(pathname))
    except blob.BlobError as exc:
        raise HTTPException(404, str(exc)) from exc

    if not data:
        raise HTTPException(400, "O arquivo está vazio.")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "O arquivo excede o limite permitido.")

    source_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as source:
            source.write(data)
            source_path = source.name

        if ext == ".docx":
            output, report = adjust.adjust_docx(source_path, font, filename)
        else:
            output, report = pdf_docx.build_from_pdf(source_path, font, filename)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            422,
            "Não consegui processar este arquivo. Verifique se ele não está "
            f"corrompido ou protegido por senha. Detalhe: {exc}",
        ) from exc
    finally:
        if source_path and os.path.exists(source_path):
            try:
                os.remove(source_path)
            except OSError:
                pass

    base_name = os.path.splitext(os.path.basename(filename))[0]
    result_name = f"{base_name}_ABNT.docx"
    result_pathname = f"results/{uuid.uuid4().hex}/{_safe_name(result_name)}"
    try:
        stored = blob.put_bytes(result_pathname, output, DOCX_TYPE)
    except blob.BlobError as exc:
        raise HTTPException(502, str(exc)) from exc

    blob.delete(pathname)  # apaga o arquivo enviado (melhor esforço)

    return JSONResponse({
        "filename": result_name,
        "report": report,
        "result_url": stored.get("url") or blob.public_url(result_pathname),
        "result_pathname": stored.get("pathname") or result_pathname,
    })


@app.post("/api/cleanup")
async def cleanup(request: Request):
    if not blob.is_configured():
        return JSONResponse({"status": "skipped"})
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        payload = {}
    pathname = payload.get("pathname") or ""
    if pathname.startswith("results/"):
        blob.delete(pathname)
    return JSONResponse({"status": "ok"})


# Local: serve o front-end. No Vercel, o CDN cuida de `public/`.
if not os.environ.get("VERCEL"):
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="public")
