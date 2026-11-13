.PHONY: help install lock upgrade sync \
        format format-check lint lint-ci lint-fix lint-loc lint-readme \
        typecheck test test-fast test-unit test-integration test-cov \
        check ci-local precommit clean \
        dev dev-data mcp-serve \
        docker-build docker-up docker-down docker-logs docker-url info

DOCKER_COMPOSE := $(shell if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then echo "docker compose"; elif command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo "docker compose"; fi)
COMPOSE := $(DOCKER_COMPOSE) -f docker/docker-compose.yml $(shell [ -f docker/.env ] && echo "--env-file docker/.env")

.DEFAULT_GOAL := help

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Install project and development dependencies with uv
	uv sync --group dev

sync: install ## Alias for install

lock: ## Resolve and update uv.lock
	uv lock

upgrade: ## Upgrade locked dependencies
	uv lock --upgrade

format: ## Format Python code
	uv run ruff format mitomap_link tests server.py mcp_server.py scripts

format-check: ## Check formatting without writing
	uv run ruff format --check mitomap_link tests server.py mcp_server.py scripts

lint: ## Lint Python code
	uv run ruff check mitomap_link tests server.py mcp_server.py scripts

lint-ci: ## Lint with GitHub-Actions output
	uv run ruff check mitomap_link tests server.py mcp_server.py scripts --output-format=github

lint-fix: ## Lint and apply safe fixes
	uv run ruff check mitomap_link tests server.py mcp_server.py scripts --fix

lint-loc: ## Enforce per-file line budget
	uv run python scripts/check_file_size.py

lint-readme: ## Enforce the GeneFoundry README Standard v1
	uv run python scripts/check_readme.py

typecheck: ## Type check package
	uv run mypy mitomap_link server.py mcp_server.py

test: ## Run unit tests quickly
	uv run pytest tests -q -m "not integration"

test-fast: ## Run unit tests in parallel
	uv run pytest tests -q -m "not integration" -n auto

test-unit: ## Run unit tests
	uv run pytest tests -q -m "not integration"

test-integration: ## Run live-endpoint integration tests
	uv run pytest tests -q -m "integration"

test-cov: ## Run tests with coverage
	uv run pytest tests -m "not integration" --cov=mitomap_link --cov-report=term-missing --cov-report=html

check: format lint ## Format and lint

ci-local: format-check lint-ci lint-loc lint-readme typecheck test-fast ## Fast local CI-equivalent checks

precommit: ci-local ## Run checks expected before commit

clean: ## Remove local caches and reports
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage coverage.xml dist build

dev: ## Start unified REST + MCP development server
	uv run python server.py --transport unified --host 127.0.0.1 --port 8000

dev-data: ## Build data/dev.sqlite from the tiny test-fixture dump excerpt (development only)
	mkdir -p data
	uv run python -c "from pathlib import Path; from mitomap_link.ingest.build import SourceInfo, build_database; build_database(open('tests/fixtures/mitomap.dump.excerpt.sql', encoding='utf-8'), Path('data/dev.sqlite'), SourceInfo('fixture', '0' * 64, 0, 'fixture'))"
	@echo "MITOMAP_LINK_DATA__LOCAL_DATABASE=data/dev.sqlite make dev"

mcp-serve: ## Start local stdio MCP server
	uv run python mcp_server.py

docker-build: ## Build Docker image
	$(COMPOSE) build

docker-up: ## Start Docker stack (random free host port; see docker/.env)
	$(COMPOSE) up -d
	@$(MAKE) --no-print-directory docker-url

docker-down: ## Stop Docker stack
	$(COMPOSE) down

docker-logs: ## Follow Docker logs
	$(COMPOSE) logs -f

docker-url: ## Print the MCP URL (host port the container is published on)
	@hostport=$$($(COMPOSE) port mitomap-link 8000 2>/dev/null); \
	port=$${hostport##*:}; \
	if [ -n "$$port" ]; then \
	  echo "mitomap-link MCP: http://127.0.0.1:$$port/mcp  (health: http://127.0.0.1:$$port/health)"; \
	  echo "Claude Code: claude mcp add --transport http mitomap-link --scope user http://127.0.0.1:$$port/mcp"; \
	else \
	  echo "mitomap-link container is not running. Start it with: make docker-up"; \
	fi

info: ## Show project information
	@echo "Project: mitomap-link"
	@echo "uv: $(shell uv --version 2>/dev/null || echo 'not installed')"
