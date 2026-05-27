.PHONY: help dev-db setup-db ingest query test lint clean package

help:
	@echo "Available targets:"
	@echo "  dev-db      Start local pgvector (Docker)"
	@echo "  setup-db    Create tables and indexes"
	@echo "  ingest      Ingest docs from a directory:  make ingest ARGS='--source data/sample_docs'"
	@echo "  query       Interactive query CLI"
	@echo "  test        Run tests"
	@echo "  lint        Run ruff linter"
	@echo "  package     Build Lambda deployment zips"
	@echo "  clean       Remove build artifacts"

dev-db:
	docker compose up -d pgvector
	@echo "pgvector running on localhost:5432  (db=ragdb user=postgres pass=localdev)"

setup-db:
	python scripts/setup_db.py

ingest:
	python scripts/ingest.py $(ARGS)

query:
	python scripts/query.py

test:
	python -m pytest tests/ -v

lint:
	ruff check src/ tests/ scripts/

package:
	python scripts/package_lambdas.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info .pytest_cache
