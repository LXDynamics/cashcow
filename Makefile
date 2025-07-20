.PHONY: help build start stop restart logs clean backup restore test lint format

# Default environment
ENV ?= development

# Help
help:
	@echo "CashCow Development and Deployment Commands"
	@echo ""
	@echo "Development Commands:"
	@echo "  make install          Install dependencies"
	@echo "  make dev              Start development servers"
	@echo "  make test             Run all tests"
	@echo "  make lint             Run linting"
	@echo "  make format           Format code"
	@echo "  make clean            Clean up temporary files"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make build            Build Docker images"
	@echo "  make start            Start all services"
	@echo "  make stop             Stop all services"
	@echo "  make restart          Restart all services"
	@echo "  make logs             Show service logs"
	@echo ""
	@echo "Deployment Commands:"
	@echo "  make deploy           Deploy to development"
	@echo "  make deploy-prod      Deploy to production"
	@echo "  make backup           Create backup"
	@echo "  make restore BACKUP=<file>  Restore from backup"
	@echo ""
	@echo "Environment: $(ENV)"

# Development setup
install:
	poetry install
	cd src/cashcow/web/frontend && npm install

# Development servers
dev:
	@echo "Starting development servers..."
	poetry run uvicorn cashcow.web.api.main:app --reload --host 0.0.0.0 --port 8000 &
	cd src/cashcow/web/frontend && npm start &
	@echo "API: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"

# Testing
test:
	poetry run pytest tests/ -v

test-coverage:
	poetry run pytest tests/ --cov=cashcow --cov-report=html --cov-report=term

# Code quality
lint:
	poetry run ruff check src/ tests/
	poetry run mypy src/
	cd src/cashcow/web/frontend && npm run lint

format:
	poetry run black src/ tests/
	poetry run ruff check --fix src/ tests/
	cd src/cashcow/web/frontend && npm run format

# Docker operations
build:
	docker-compose build

start:
	docker-compose up -d

stop:
	docker-compose down

restart: stop start

logs:
	docker-compose logs -f

# Deployment
deploy:
	@./scripts/deploy.sh development

deploy-prod:
	@./scripts/deploy.sh production

# Backup and restore
backup:
	@./scripts/backup.sh

restore:
ifndef BACKUP
	@echo "Error: BACKUP parameter required. Usage: make restore BACKUP=<backup_file>"
	@exit 1
endif
	@./scripts/restore.sh $(BACKUP)

# Database operations
db-migrate:
	poetry run alembic upgrade head

db-seed:
	poetry run python -m cashcow.scripts.seed_data

db-reset:
	docker-compose exec postgres psql -U cashcow -d cashcow -c "DROP SCHEMA IF EXISTS cashcow CASCADE; CREATE SCHEMA cashcow;"
	$(MAKE) db-migrate
	$(MAKE) db-seed

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	cd src/cashcow/web/frontend && npm run clean || true

# Security
security-check:
	poetry run safety check
	poetry run bandit -r src/
	cd src/cashcow/web/frontend && npm audit

# Performance testing
load-test:
	@echo "Load testing setup removed. Use external tools like k6, Apache Bench, or wrk for load testing."

# Health checks
health:
	@curl -f http://localhost:8000/api/health || echo "API not available"
	@curl -f http://localhost:80/health || echo "Nginx not available"

# Production utilities
prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

prod-shell:
	docker-compose -f docker-compose.prod.yml exec cashcow bash

prod-db-shell:
	docker-compose -f docker-compose.prod.yml exec postgres psql -U cashcow -d cashcow

# Monitoring
monitor:
	@echo "Opening monitoring dashboards..."
	@echo "Grafana: http://localhost:3001"
	@echo "Prometheus: http://localhost:9090"