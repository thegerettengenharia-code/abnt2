# -*- coding: utf-8 -*-
"""Reproduz o fluxo do front-end contra o site em produção."""
import io
import json
import sys
import urllib.request

BASE = "https://abnt-formatador.vercel.app"


def post(url, payload, raw_headers=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("content-type", "application/json")
    for k, v in (raw_headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:500]
    except Exception as e:
        return None, str(e)


def put_file(url, content, headers):
    req = urllib.request.Request(url, data=content, method="PUT")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read()
            return resp.status, body.decode("utf-8", "replace")[:500]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:500]
    except Exception as e:
        return None, str(e)


def main():
    with open("tests/sample.docx", "rb") as fh:
        content = fh.read()

    print("1) presign...")
    st, info = post(f"{BASE}/api/presign", {"filename": "sample.docx", "size": len(content)})
    print("   ->", st, json.dumps(info)[:300] if st and st < 400 else info)
    if not (st and 200 <= st < 300):
        return

    print("2) upload ao Blob...")
    headers = {
        "x-api-version": "12",
        "x-vercel-blob-store-id": info.get("store_id", ""),
        "x-vercel-blob-access": "public",
        "x-content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "x-api-blob-request-id": info.get("store_id", "") + ":test:0",
        "x-api-blob-request-attempt": "0",
    }
    st, body = put_file(info["upload_url"], content, headers)
    print("   ->", st, str(body)[:300])
    if not (st and 200 <= st < 300):
        return

    print("3) format...")
    st, result = post(f"{BASE}/api/format", {
        "pathname": info["pathname"],
        "filename": "sample.docx",
        "font": "Times New Roman",
    })
    print("   ->", st, json.dumps(result)[:600] if st and st < 400 else result)

    if st and 200 <= st < 300:
        print("4) baixar resultado...")
        url = result["result_url"]
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = resp.read()
        print("   ->", len(data), "bytes; zip?", data[:2] == b"PK")
        with open("tests/e2e_ABNT.docx", "wb") as fh:
            fh.write(data)
        post(f"{BASE}/api/cleanup", {"pathname": result["result_pathname"]})


if __name__ == "__main__":
    sys.exit(main())
