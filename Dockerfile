# syntax=docker/dockerfile:1

FROM python:3.11.11-slim AS build
WORKDIR /src
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=README.md,target=README.md \
    --mount=type=bind,source=src,target=src \
    --mount=type=cache,target=/root/.cache/pip \
    pip install --no-compile .

FROM python:3.11.11-slim AS runtime
WORKDIR /app
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser
COPY --from=build --chown=1001:1001 /opt/venv /opt/venv
COPY --link --chown=1001:1001 src /app/src
COPY --link --chown=1001:1001 ontology /app/ontology
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    AGRITRACE_ONTOLOGY=/app/ontology/traceability.ttl \
    PORT=8000 \
    LLM_MODE=mock \
    GRAPH_BACKEND=memory
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/health')"]
LABEL org.opencontainers.image.source="https://github.com/MourabitElBachir/traceability-graph-agents" \
      org.opencontainers.image.title="AgriTrace"
ENTRYPOINT ["python", "-m", "agritrace.api.main"]
