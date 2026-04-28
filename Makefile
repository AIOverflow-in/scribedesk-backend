# Load environment variables from .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Default shell
SHELL := /bin/bash

# Default values (can be overridden by .env)
HOST ?= 0.0.0.0
PORT ?= 8000

.PHONY: help dev install clean db-init db-up db-down db-status db-history seed-admin seed-templates delete-user

.DEFAULT_GOAL := dev

help:
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

workflow:
	powershell.exe -ExecutionPolicy Bypass -File "$(CURDIR)/workflow.ps1"

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Run API server (Dev - Hot Reload)
	@echo "Starting server on $(HOST):$(PORT)..."
	uvicorn src.main:app --reload --host $(HOST) --port $(PORT)

clean: ## Clean pycache and celery files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf celerybeat-schedule* || true


# --- Database & Migrations ---

db-init: ## Generate a new migration (usage: make db-init m="message")
	$(if $(m),,$(error Error: Please provide a message using m="message"))
	alembic revision --autogenerate -m "$(m)"

db-up: ## Apply all migrations to head
	alembic upgrade head

db-down: ## Rollback the last migration (-1)
	alembic downgrade -1

db-status: ## Show current database migration level
	alembic current

db-history: ## Show migration history
	alembic history --verbose


# --- Seeders ---

seed-admin: ## Create initial admin user (interactive)
	@echo "Running Admin User Seeder..."
	python -m src.seeders.admin_seeder

seed-templates: ## Seed system templates
	@echo "Running System Templates Seeder..."
	python -m src.seeders.templates_seeder

delete-user: ## Delete user and all data (dev only, usage: make delete-user email="test@example.com")
	$(if $(email),,$(error Error: Please provide an email using email="test@example.com"))
	python -m src.cli delete-user $(email)