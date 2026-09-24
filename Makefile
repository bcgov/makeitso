# Fall back to the installer's location so uv works right after `make uv`
UV := $(or $(shell command -v uv 2>/dev/null),$(HOME)/.local/bin/uv)
FLASK := $(UV) run flask --app makeitso
DB_NAME := mis
HTMX_VERSION := 2.0.11
ALPINE_VERSION := 3.17.4
VENDOR_DIR := src/makeitso/static/vendor
PSQL := psql

.PHONY: help
help:
	@echo "make uv             Install uv if it is not already installed"
	@echo "make install        Install uv, Python and all dependencies into .venv"
	@echo "make run            Run the dev server on http://localhost:8000"
	@echo "make shell          Open a Python shell with the app loaded"
	@echo "make redis-install  Install Redis with Homebrew if it is not already installed"
	@echo "make redis          Run a local Redis server (installs it first if needed)"
	@echo "make worker         Run a background job worker (RQ)"
	@echo "make lint           Check code style and common mistakes (ruff)"
	@echo "make format         Auto-format code and fix lint issues (ruff)"
	@echo "make typecheck      Check types (ty)"
	@echo "make vendor         Download pinned front-end libraries into static/vendor"

.PHONY: uv
uv:
	@test -x "$(UV)" || { \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}

.PHONY: install
install: uv
	$(UV) sync

.PHONY: run
run:
	$(FLASK) run --debug --port 8000

.PHONY: shell
shell:
	$(FLASK) shell

# Install the Redis server with Homebrew unless redis-server is already available.
.PHONY: redis-install
redis-install:
	@command -v redis-server >/dev/null 2>&1 || { \
		command -v brew >/dev/null 2>&1 || { \
			echo "Homebrew not found. Install Redis with your package manager,"; \
			echo "e.g. 'sudo apt install redis-server' (Debian/Ubuntu)."; \
			exit 1; \
		}; \
		echo "Installing Redis..."; \
		brew install redis; \
	}

# Run Redis; --save "" disables snapshots, so no dump.rdb is written to the repo
.PHONY: redis
redis: redis-install
	redis-server --save ""

# Run an RQ worker through `flask worker`, so jobs have the Flask app context
.PHONY: worker
worker:
	$(FLASK) worker

.PHONY: lint
lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .

.PHONY: format
format:
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

.PHONY: typecheck
typecheck:
	$(UV) run ty check

.PHONY: create_db
create_db: ## Ensure that the $(DB_NAME) database exists
create_db:
	@$(PSQL) -d postgres -tc "SELECT count(*) FROM pg_database WHERE datname = '$(DB_NAME)'" | \
		grep -q 1 || \
		$(PSQL) -d postgres -c "CREATE DATABASE $(DB_NAME)";

.PHONY: vendor
vendor:
	mkdir -p $(VENDOR_DIR)/htmx $(VENDOR_DIR)/alpinejs
	curl -fsSL https://cdn.jsdelivr.net/npm/htmx.org@$(HTMX_VERSION)/dist/htmx.min.js -o $(VENDOR_DIR)/htmx/htmx.min.js
	curl -fsSL https://cdn.jsdelivr.net/npm/@alpinejs/csp@$(ALPINE_VERSION)/dist/cdn.min.js -o $(VENDOR_DIR)/alpinejs/alpine.min.js

.PHONY: init_db
init_db:
	$(FLASK) db init

# Named migration: ARGS='-m "named-migration"'
.PHONY: migrate
migrate:
	@if [ -z "$(ARGS)" ]; then \
		echo "Error: ARGS is empty. Please name your migration."; \
		exit 1; \
	else \
		$(FLASK) db migrate $(ARGS); \
	fi

.PHONY: upgrade_db
upgrade_db:
	$(FLASK) db upgrade $(ARGS)

# ARGS='<revision_id>' - downgrade to specific revision
# ARGS='-3' - downgrade the last 3 revisions
.PHONY: downgrade_db
downgrade_db:
	$(FLASK) db downgrade $(ARGS)
