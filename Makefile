# Fall back to the installer's location so uv works right after `make uv`
UV := $(or $(shell command -v uv 2>/dev/null),$(HOME)/.local/bin/uv)
FLASK := $(UV) run flask --app makeitso

.PHONY: help
help:
	@echo "make uv        Install uv if it is not already installed"
	@echo "make install   Install uv, Python and all dependencies into .venv"
	@echo "make run       Run the dev server on http://localhost:8000"
	@echo "make shell     Open a Python shell with the app loaded"
	@echo "make lint      Check code style and common mistakes (ruff)"
	@echo "make format    Auto-format code and fix lint issues (ruff)"
	@echo "make typecheck Check types (ty)"

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
