.PHONY: help dev db db-admin api web test test-unit test-integration docs db-docs db-docs-diff clean

-include .env
export

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Infrastructure ──

db: ## Start DynamoDB Local + create table
	docker compose up -d dynamodb-local dynamodb-init

db-admin: db ## Start DynamoDB Local + Admin UI (http://localhost:8001)
	docker compose --profile dev up -d

# ── Application ──

api: ## Start API server (http://localhost:8080)
	cd api && .venv/bin/python main.py

web: ## Start frontend dev server (http://localhost:5173)
	cd web && pnpm dev

dev: db ## Start all services (run api/web in separate terminals)
	@echo ""
	@echo "  DynamoDB Local: http://localhost:8000"
	@echo ""
	@echo "  Run in separate terminals:"
	@echo "    make api   → http://localhost:8080"
	@echo "    make web   → http://localhost:5173"
	@echo ""

# ── Tests ──

test-unit: ## Run unit tests (no Docker needed)
	cd api && .venv/bin/python -m pytest tests/ --ignore=tests/integration -v
	cd web && pnpm test

test-integration: db ## Run integration tests (starts DynamoDB Local)
	cd api && .venv/bin/python -m pytest tests/integration/ -v

test: test-unit test-integration ## Run all tests

# ── Docs ──

docs: ## Generate OpenAPI spec and serve docs (http://localhost:9090)
	cd api && .venv/bin/python generate_openapi.py ../docs/openapi.json
	@echo "  Serving docs at http://localhost:9090"
	cd docs && python3 -m http.server 9090

# ── DB Docs ──

TBLS_VERSION := v1.94.5
TBLS := $(PWD)/bin/tbls
TBLS_OS := $(shell uname -s | tr '[:upper:]' '[:lower:]')
TBLS_ARCH := $(shell uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/')

$(TBLS):
	@mkdir -p $(PWD)/bin
	curl -sSL "https://github.com/k1LoW/tbls/releases/download/$(TBLS_VERSION)/tbls_$(TBLS_VERSION)_$(TBLS_OS)_$(TBLS_ARCH).tar.gz" \
		| tar -xz -C $(PWD)/bin tbls
	@chmod +x $(TBLS)

db-docs: db $(TBLS) ## Generate DynamoDB schema docs (docs-db/schema/)
	@AWS_ENDPOINT_URL=http://localhost:8000 \
		AWS_DEFAULT_REGION=ap-northeast-1 \
		AWS_ACCESS_KEY_ID=local \
		AWS_SECRET_ACCESS_KEY=local \
		$(TBLS) doc --force

db-docs-diff: db $(TBLS) ## Show diff between docs-db/schema/ and live DynamoDB Local
	@AWS_ENDPOINT_URL=http://localhost:8000 \
		AWS_DEFAULT_REGION=ap-northeast-1 \
		AWS_ACCESS_KEY_ID=local \
		AWS_SECRET_ACCESS_KEY=local \
		$(TBLS) diff

# ── Cleanup ──

clean: ## Stop and remove all containers
	docker compose --profile dev down
