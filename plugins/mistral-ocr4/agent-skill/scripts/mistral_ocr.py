#!/usr/bin/env python3
"""
mistral_ocr.py — dependency-free CLI client for the Mistral OCR4 + Document AI API.

This is the executable core of the `mistral-ocr4` Agent Skill. Agent Skills run in a
sandbox without a local MCP server, so OCR happens as plain HTTPS from this script.
It mirrors the mistral-ocr4 MCP tool surface 1:1 — extraction only; the calling model
does all reasoning.

Stdlib only (urllib, json, ssl) — no pip install required. Honors HTTPS_PROXY and
SSL_CERT_FILE from the environment automatically.

Auth: reads MISTRAL_API_KEY from the environment.
Env overrides: MISTRAL_BASE_URL (default https://api.mistral.ai),
               MISTRAL_OCR_MODEL (default mistral-ocr-latest).

Every subcommand prints the raw Mistral JSON to stdout and exits non-zero on error.
"""

import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid

BASE_URL = os.environ.get("MISTRAL_BASE_URL", "https://api.mistral.ai").rstrip("/")
DEFAULT_OCR_MODEL = os.environ.get("MISTRAL_OCR_MODEL", "mistral-ocr-latest")


def _api_key() -> str:
    key = os.environ.get("MISTRAL_API_KEY", "")
    if not key:
        _die("MISTRAL_API_KEY is not set in the environment.")
    return key


def _die(msg: str, body=None, code: int = 1):
    out = {"error": msg}
    if body is not None:
        out["body"] = body
    json.dump(out, sys.stderr, indent=2)
    sys.stderr.write("\n")
    sys.exit(code)


def _emit(data):
    json.dump(data, sys.stdout, indent=2)
    sys.stdout.write("\n")


def _full_url(path: str, query: dict | None = None) -> str:
    url = path if path.startswith("http") else f"{BASE_URL}/{path.lstrip('/')}"
    if query:
        from urllib.parse import urlencode

        clean = {k: v for k, v in query.items() if v is not None}
        if clean:
            url += ("&" if "?" in url else "?") + urlencode(clean)
    return url


def request(method: str, path: str, body=None, query: dict | None = None):
    """Generic authenticated JSON request — foundation for every typed command."""
    url = _full_url(path, query)
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Accept": "application/json",
    }
    data = None
    if body is not None and method.upper() != "GET":
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    return _send(req)


def _send(req: urllib.request.Request):
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
        _die(f"Mistral API error {e.code} {e.reason}", body=parsed, code=2)
    except urllib.error.URLError as e:
        _die(f"Network error reaching Mistral: {e.reason}", code=3)
    try:
        return json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return raw


def upload_file(path: str, purpose: str = "ocr"):
    """Multipart upload to POST /v1/files (stdlib multipart, no `requests`)."""
    if not os.path.isfile(path):
        _die(f"File not found: {path}")
    with open(path, "rb") as f:
        content = f.read()
    filename = os.path.basename(path)
    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    boundary = f"----mistralocr{uuid.uuid4().hex}"

    def field(name, value):
        return (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        ).encode("utf-8")

    body = bytearray()
    body += field("purpose", purpose)
    body += (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
        f'filename="{filename}"\r\nContent-Type: {ctype}\r\n\r\n'
    ).encode("utf-8")
    body += content
    body += f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        _full_url("/v1/files"),
        data=bytes(body),
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Accept": "application/json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    return _send(req)


def _json_arg(value, label):
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        _die(f"--{label} must be valid JSON: {e}")


def build_document(a):
    if a.document:
        return _json_arg(a.document, "document")
    if a.document_url:
        return {"type": "document_url", "document_url": a.document_url}
    if a.image_url:
        return {"type": "image_url", "image_url": a.image_url}
    if a.file_id:
        return {"type": "file", "file_id": a.file_id}
    if a.document_base64:
        return {"type": "document_url", "document_url": a.document_base64}
    if a.image_base64:
        return {"type": "image_url", "image_url": a.image_base64}
    _die(
        "No input. Provide one of: --document-url, --image-url, --file-id, "
        "--document-base64, --image-base64, or --document."
    )


# --------------------------------------------------------------------------- #
# Subcommand handlers
# --------------------------------------------------------------------------- #
def cmd_ocr(a):
    payload = {"model": a.model or DEFAULT_OCR_MODEL, "document": build_document(a)}
    if a.pages is not None:
        payload["pages"] = [int(p) for p in a.pages.split(",") if p.strip() != ""]
    for flag, key in [
        (a.include_image_base64, "include_image_base64"),
        (a.extract_header, "extract_header"),
        (a.extract_footer, "extract_footer"),
        (a.include_blocks, "include_blocks"),
    ]:
        if flag:
            payload[key] = True
    if a.image_limit is not None:
        payload["image_limit"] = a.image_limit
    if a.image_min_size is not None:
        payload["image_min_size"] = a.image_min_size
    if a.table_format:
        payload["table_format"] = a.table_format
    if a.confidence_scores_granularity:
        payload["confidence_scores_granularity"] = a.confidence_scores_granularity
    bbox = _json_arg(a.bbox_annotation_format, "bbox-annotation-format")
    if bbox is not None:
        payload["bbox_annotation_format"] = bbox
    docann = _json_arg(a.document_annotation_format, "document-annotation-format")
    if docann is not None:
        payload["document_annotation_format"] = docann
    _emit(request("POST", "/v1/ocr", body=payload))


def cmd_files_upload(a):
    _emit(upload_file(a.path, a.purpose))


def cmd_files_list(a):
    _emit(request("GET", "/v1/files", query={
        "page": a.page, "page_size": a.page_size, "purpose": a.purpose}))


def cmd_files_get(a):
    _emit(request("GET", f"/v1/files/{a.file_id}"))


def cmd_files_url(a):
    q = {} if a.expiry is None else {"expiry": a.expiry}
    _emit(request("GET", f"/v1/files/{a.file_id}/url", query=q))


def cmd_files_delete(a):
    _emit(request("DELETE", f"/v1/files/{a.file_id}"))


def cmd_batch_create(a):
    _emit(request("POST", "/v1/batch/jobs", body=_json_arg(a.payload, "payload")))


def cmd_batch_get(a):
    _emit(request("GET", f"/v1/batch/jobs/{a.job_id}"))


def cmd_batch_list(a):
    _emit(request("GET", "/v1/batch/jobs", query={
        "page": a.page, "page_size": a.page_size, "status": a.status}))


def cmd_batch_cancel(a):
    _emit(request("POST", f"/v1/batch/jobs/{a.job_id}/cancel"))


def cmd_models_list(a):
    _emit(request("GET", "/v1/models"))


def cmd_chat(a):
    _emit(request("POST", "/v1/chat/completions", body=_json_arg(a.payload, "payload")))


def cmd_request(a):
    _emit(request(
        a.method, a.path,
        body=_json_arg(a.body, "body"),
        query=_json_arg(a.query, "query"),
    ))


# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mistral_ocr.py",
        description="CLI client for Mistral OCR4 + Document AI (extraction only).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    o = sub.add_parser("ocr", help="Run OCR4 + structured annotations on a doc/image.")
    o.add_argument("--model", help=f"OCR model id (default {DEFAULT_OCR_MODEL}).")
    o.add_argument("--document-url", dest="document_url")
    o.add_argument("--image-url", dest="image_url")
    o.add_argument("--file-id", dest="file_id")
    o.add_argument("--document-base64", dest="document_base64")
    o.add_argument("--image-base64", dest="image_base64")
    o.add_argument("--document", help="Full Mistral document object as JSON.")
    o.add_argument("--pages", help="Comma-separated 0-indexed page numbers.")
    o.add_argument("--include-image-base64", action="store_true")
    o.add_argument("--image-limit", type=int)
    o.add_argument("--image-min-size", type=int)
    o.add_argument("--table-format", choices=["null", "markdown", "html"])
    o.add_argument("--extract-header", action="store_true")
    o.add_argument("--extract-footer", action="store_true")
    o.add_argument("--include-blocks", action="store_true")
    o.add_argument("--confidence-scores-granularity", choices=["page", "word"])
    o.add_argument("--bbox-annotation-format", help="response_format JSON schema.")
    o.add_argument("--document-annotation-format", help="response_format JSON schema.")
    o.set_defaults(func=cmd_ocr)

    u = sub.add_parser("files-upload", help="Upload a local file (-> file_id).")
    u.add_argument("--path", required=True)
    u.add_argument("--purpose", default="ocr")
    u.set_defaults(func=cmd_files_upload)

    fl = sub.add_parser("files-list", help="List stored files.")
    fl.add_argument("--page", type=int)
    fl.add_argument("--page-size", type=int)
    fl.add_argument("--purpose")
    fl.set_defaults(func=cmd_files_list)

    fg = sub.add_parser("files-get", help="Retrieve file metadata.")
    fg.add_argument("--file-id", dest="file_id", required=True)
    fg.set_defaults(func=cmd_files_get)

    fu = sub.add_parser("files-url", help="Get a signed download URL for a file.")
    fu.add_argument("--file-id", dest="file_id", required=True)
    fu.add_argument("--expiry", type=int, help="Expiry in hours.")
    fu.set_defaults(func=cmd_files_url)

    fd = sub.add_parser("files-delete", help="Delete a stored file.")
    fd.add_argument("--file-id", dest="file_id", required=True)
    fd.set_defaults(func=cmd_files_delete)

    bc = sub.add_parser("batch-create", help="Create a bulk OCR batch job.")
    bc.add_argument("--payload", required=True, help="Batch job payload as JSON.")
    bc.set_defaults(func=cmd_batch_create)

    bg = sub.add_parser("batch-get", help="Get a batch job status/result.")
    bg.add_argument("--job-id", dest="job_id", required=True)
    bg.set_defaults(func=cmd_batch_get)

    bl = sub.add_parser("batch-list", help="List batch jobs.")
    bl.add_argument("--page", type=int)
    bl.add_argument("--page-size", type=int)
    bl.add_argument("--status")
    bl.set_defaults(func=cmd_batch_list)

    bx = sub.add_parser("batch-cancel", help="Cancel a batch job.")
    bx.add_argument("--job-id", dest="job_id", required=True)
    bx.set_defaults(func=cmd_batch_cancel)

    ml = sub.add_parser("models-list", help="List available Mistral models.")
    ml.set_defaults(func=cmd_models_list)

    ch = sub.add_parser(
        "chat",
        help="Document QnA passthrough (POST /v1/chat/completions). Reasoning "
        "belongs to the calling model - use sparingly.",
    )
    ch.add_argument("--payload", required=True, help="Chat completions payload as JSON.")
    ch.set_defaults(func=cmd_chat)

    rq = sub.add_parser(
        "request", help="Generic authenticated passthrough to any Mistral endpoint."
    )
    rq.add_argument("--method", required=True,
                    choices=["GET", "POST", "PUT", "PATCH", "DELETE"])
    rq.add_argument("--path", required=True, help='e.g. "/v1/ocr".')
    rq.add_argument("--body", help="JSON request body.")
    rq.add_argument("--query", help="JSON object of query params.")
    rq.set_defaults(func=cmd_request)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
