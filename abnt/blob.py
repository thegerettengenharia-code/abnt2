"""Cliente mínimo do Vercel Blob, sem dependências externas (só urllib).

Fluxo usado pelo site:
  1. O navegador pede a esta função uma URL de upload assinada (`issue_presigned_put`)
     e envia o arquivo DIRETO para o Vercel Blob — assim o arquivo não passa pela
     função serverless e o limite de ~4,5 MB do Vercel deixa de existir.
  2. A função baixa o arquivo do Blob (`fetch`), aplica a formatação ABNT e envia o
     resultado de volta ao Blob (`put_bytes`), devolvendo apenas a URL do resultado.
  3. Os arquivos (entrada e saída) são apagados (`delete`) logo em seguida.
"""
import base64
import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://vercel.com/api/blob"
API_VERSION = "12"
PUBLIC_HOST_SUFFIX = ".public.blob.vercel-storage.com"


class BlobError(RuntimeError):
    """Erro ao conversar com o Vercel Blob."""


def load_env_files(base_dir):
    """Carrega .env.local/.env quando as variáveis ainda não estão no ambiente.

    No Vercel as variáveis são injetadas pelo próprio serviço; localmente lemos
    o arquivo gerado por `vercel env pull`.
    """
    if os.environ.get("BLOB_READ_WRITE_TOKEN"):
        return
    for name in (".env.local", ".env"):
        path = os.path.join(base_dir, name)
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    os.environ.setdefault(
                        key.strip(), value.strip().strip('"').strip("'")
                    )
        except OSError:
            continue


def is_configured():
    return bool(os.environ.get("BLOB_READ_WRITE_TOKEN"))


def _token():
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    if not token:
        raise BlobError(
            "Armazenamento Vercel Blob não configurado "
            "(BLOB_READ_WRITE_TOKEN ausente)."
        )
    return token


def store_id():
    parts = _token().split("_")
    if len(parts) < 4:
        raise BlobError("BLOB_READ_WRITE_TOKEN inválido.")
    return parts[3]


def public_url(pathname):
    quoted = urllib.parse.quote(pathname, safe="/")
    return f"https://{store_id().lower()}{PUBLIC_HOST_SUFFIX}/{quoted}"


def _request_id():
    nonce = base64.urlsafe_b64encode(os.urandom(9)).decode("ascii").rstrip("=")
    return f"{store_id()}:{int(time.time() * 1000)}:{nonce}"


def _base_headers(authorized=True):
    headers = {
        "x-api-version": API_VERSION,
        "x-vercel-blob-store-id": store_id(),
        "x-api-blob-request-id": _request_id(),
        "x-api-blob-request-attempt": "0",
    }
    if authorized:
        headers["authorization"] = f"Bearer {_token()}"
    return headers


def _send(url, method, headers, data=None, timeout=120):
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:300]
        raise BlobError(f"Vercel Blob respondeu {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise BlobError(f"Falha de rede ao acessar o Vercel Blob: {exc.reason}") from exc


def _b64url(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _presign_url(pathname, delegation_token, client_signing_token):
    canonical = "\n".join(sorted(["operation=put", f"pathname={pathname}"]))
    signature = _b64url(
        hmac.new(
            client_signing_token.encode("utf-8"),
            canonical.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    )
    query = urllib.parse.urlencode(
        {
            "pathname": pathname,
            "vercel-blob-delegation": delegation_token,
            "vercel-blob-signature": signature,
        }
    )
    return f"{API_URL}/?{query}"


def issue_presigned_put(pathname, max_bytes, content_types, valid_for_ms=3600_000):
    """Cria uma URL de PUT assinada para o navegador enviar o arquivo direto ao Blob."""
    body = json.dumps(
        {
            "pathname": pathname,
            "operations": ["put"],
            "validUntil": int(time.time() * 1000) + int(valid_for_ms),
            "maximumSizeInBytes": int(max_bytes),
            "allowedContentTypes": list(content_types),
        }
    ).encode("utf-8")

    headers = _base_headers()
    headers["content-type"] = "application/json"
    _, raw = _send(API_URL + "/signed-token", "POST", headers, data=body, timeout=60)
    payload = json.loads(raw)

    return {
        "upload_url": _presign_url(
            pathname, payload["delegationToken"], payload["clientSigningToken"]
        ),
        "pathname": pathname,
        "store_id": store_id(),
    }


def put_bytes(pathname, data, content_type="application/octet-stream"):
    """Envia bytes ao Blob a partir do servidor (usado para o resultado)."""
    headers = _base_headers()
    headers["x-vercel-blob-access"] = "public"
    headers["x-content-type"] = content_type
    query = urllib.parse.urlencode({"pathname": pathname})
    _, raw = _send(f"{API_URL}/?{query}", "PUT", headers, data=data)
    return json.loads(raw)


def fetch(url, timeout=120):
    """Baixa o conteúdo de uma URL pública do Blob."""
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise BlobError(
            f"O arquivo enviado não foi encontrado no armazenamento ({exc.code})."
        ) from exc
    except urllib.error.URLError as exc:
        raise BlobError(f"Falha de rede ao baixar o arquivo: {exc.reason}") from exc


def delete(pathname):
    """Apaga um objeto do Blob (melhor esforço)."""
    headers = _base_headers()
    query = urllib.parse.urlencode({"pathname": pathname})
    try:
        status, _ = _send(f"{API_URL}/?{query}", "DELETE", headers, timeout=60)
        return status
    except BlobError:
        return None
