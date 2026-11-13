.PHONY: install test lint demo eval ingest api ui up down ci

PYTHON ?= python3
VENV ?= .venv
PY := $(VENV)/bin/python

install:
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -U pip
	$(PY) -m pip install -e ".[dev]"

lint:
	$(PY) -m ruff check src tests ui
	$(PY) -m ruff format --check src tests ui
	$(PY) -m mypy src

test:
	LLM_MODE=mock GRAPH_BACKEND=memory AGRITRACE_AS_OF=2026-11-13 $(PY) -m pytest

demo:
	LLM_MODE=mock GRAPH_BACKEND=memory AGRITRACE_AS_OF=2026-11-13 $(PY) -m agritrace.demo

eval:
	LLM_MODE=mock GRAPH_BACKEND=memory AGRITRACE_AS_OF=2026-11-13 $(PY) -m agritrace.eval.runner

ingest:
	LLM_MODE=mock GRAPH_BACKEND=memory $(PY) -m agritrace.ingest

api:
	LLM_MODE=mock GRAPH_BACKEND=memory PORT=$${PORT:-8000} $(PY) -m agritrace.api.main

ui:
	LLM_MODE=mock GRAPH_BACKEND=memory $(PY) -m streamlit run ui/streamlit_app.py --server.address 0.0.0.0 --server.port 8501

up:
	docker compose up --build

down:
	docker compose down

ci: lint test eval
