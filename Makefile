PYTHON ?= python3
COMPOSE ?= docker compose
export PYTHONPATH := src

.PHONY: help setup up down simulate ingest detect test lint demo generate-data rag-ingest eval logs

help:
	@echo "FactoryPulse targets: setup up down demo test eval generate-data rag-ingest"

setup:
	$(PYTHON) -m pip install -e ".[dev]"

generate-data:
	$(PYTHON) data/generate_incidents.py
	$(PYTHON) data/generate_manuals.py

rag-ingest:
	$(PYTHON) -m factorypulse.rag.ingest

up:
	$(COMPOSE) up -d --build
	@echo "Waiting for API health on :18000 ..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do \
	  curl -sf http://localhost:18000/health && exit 0; \
	  sleep 4; \
	done; exit 1

down:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f --tail=200

simulate:
	$(PYTHON) -m factorypulse.simulator.replay --duration 60

ingest:
	$(PYTHON) -m factorypulse.ingestion.consumer

detect:
	$(PYTHON) -m factorypulse.detection.runner --once

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check src tests

eval:
	$(PYTHON) evals/run_evals.py --smoke 10
	@latest=$$(ls -1 evals/results/*.json | tail -n 1); \
	  mkdir -p web/public/evals; \
	  cp $$latest web/public/evals/latest.json; \
	  echo "copied $$latest -> web/public/evals/latest.json"

demo: up
	@echo "Injecting bearing_degradation fault..."
	curl -sf -X POST "http://localhost:18000/simulate/inject-fault?type=bearing_degradation" | $(PYTHON) -m json.tool
	@echo "Diagnosing latest event..."
	@eid=$$(curl -sf "http://localhost:18000/events?limit=1" | $(PYTHON) -c 'import sys,json; print(json.load(sys.stdin)[0]["event_id"])'); \
	  curl -sf -X POST "http://localhost:18000/diagnose/$$eid" | $(PYTHON) -m json.tool
	@echo "UI: http://localhost:13000  API docs: http://localhost:18000/docs"
