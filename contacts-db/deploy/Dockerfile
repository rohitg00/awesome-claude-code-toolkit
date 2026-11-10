# NTXP Contacts — app image (API + live page + MCP + CardDAV).
#   docker build -f deploy/Dockerfile -t ntxp-contacts .                    # without the doc engine
#   docker build -f deploy/Dockerfile --build-arg WITH_ENGINE=1 -t ntxp-contacts .   # server-side PDF/DOCX via the NTXP engine
# Build context = contacts-db/. The NTXP Branded Document engine and logo are PROPRIETARY and are not in git:
# deploy.sh copies them from the installed skill into deploy/engine and deploy/assets before building.
FROM python:3.12-slim
ARG WITH_ENGINE=0
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 NTXP_ASSETS_DIR=/assets
WORKDIR /app
COPY pyproject.toml README.md ./
COPY ntxp_contacts ./ntxp_contacts
RUN pip install ".[mcp,remote,postgres]"
COPY deploy/engine/ /engine/
COPY deploy/assets/ /assets/
RUN if [ "$WITH_ENGINE" = "1" ]; then \
      pip install playwright python-docx lxml pikepdf reportlab pypdfium2 Pillow && \
      playwright install --with-deps chromium; \
    fi
ENV NTXP_DOC_ENGINE=/engine/scripts/render.py NTXP_DOC_PYTHON=python
RUN useradd -m ntxp && chown -R ntxp /app /engine /assets
USER ntxp
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=4)"
CMD ["ntxp", "serve-http", "--host", "0.0.0.0", "--port", "8080"]
