# NTXP Contacts — app image (live page + /api + /api/v1 + /mcp + /carddav + peer webhooks).
# Built by CI (.github/workflows/contacts-image.yml) and PULLED by the Hostinger Docker Manager —
# that manager cannot build images. Build context = contacts-db/.
#
# Deliberately NOT in the image (kept on the VPS and mounted read-only):
#   /engine   the proprietary NTXP Branded Document engine (license: NTXP only, no redistribution)
#   /assets   the NTXP logo
# The renderer's *public* dependencies (Chromium, Playwright, python-docx, ...) are installed here.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    NTXP_ASSETS_DIR=/assets NTXP_DOC_ENGINE=/engine/scripts/render.py NTXP_DOC_PYTHON=python
WORKDIR /app
COPY pyproject.toml README.md ./
COPY ntxp_contacts ./ntxp_contacts
RUN pip install ".[mcp,remote,postgres]" \
 && pip install playwright python-docx lxml pikepdf reportlab pypdfium2 Pillow \
 && playwright install --with-deps chromium && chmod -R a+rX /ms-playwright
RUN useradd -m ntxp && chown -R ntxp /app
USER ntxp
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=4)"
CMD ["ntxp", "serve-http", "--host", "0.0.0.0", "--port", "8080"]
