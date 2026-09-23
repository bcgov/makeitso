# Fall back to the installer's location so uv works right after `make uv`
UV := $(or $(shell command -v uv 2>/dev/null),$(HOME)/.local/bin/uv)
FLASK := $(UV) run flask --app makeitso

HTMX_VERSION := 2.0.11
ALPINE_VERSION := 3.17.4
VENDOR_DIR := src/makeitso/static/vendor

.PHONY: help
help:
	@echo "make uv        Install uv if it is not already installed"
	@echo "make install   Install uv, Python and all dependencies into .venv"
	@echo "make run       Run the dev server on http://localhost:8000"
	@echo "make shell     Open a Python shell with the app loaded"
	@echo "make lint      Check code style and common mistakes (ruff)"
	@echo "make format    Auto-format code and fix lint issues (ruff)"
	@echo "make typecheck Check types (ty)"
	@echo "make vendor    Download pinned front-end libraries into static/vendor"

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
