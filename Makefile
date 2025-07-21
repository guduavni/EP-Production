.PHONY: help install test lint format clean run build up down restart logs shell db-shell test-api test-unit test-e2e

# Default target
help:
	@echo "EP-Simulator - ICAO English Proficiency Assessment"
	@echo "\nAvailable targets:"
	@echo "  install     Install dependencies"
	@echo "  test        Run all tests"
	@echo "  lint        Run linters"
	@echo "  format      Format code with Black and isort"
	@echo "  clean       Remove Python and build artifacts"
	@echo "  run         Run the development server"
	@echo "  build       Build Docker images"
	@echo "  up          Start all services"
	@echo "  down        Stop all services"
	@echo "  restart     Restart all services"
	@echo "  logs        View service logs"
	@echo "  shell       Open a shell in the web container"
	@echo "  db-shell    Open a MongoDB shell"

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test: test-unit test-e2e

# Run linters
lint:
	flake8 app tests
	black --check app tests
	isort --check-only app tests
	mypy app

# Format code
format:
	black app tests
	isort app tests

# Clean up
clean:
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	find . -type f -name '*.py[co]' -delete
	rm -rf .coverage htmlcov/
	
# Run the development server
run:
	export FLASK_APP=app.py
	export FLASK_ENV=development
	flask run --host=0.0.0.0 --port=5000

# Build Docker images
build:
	docker-compose build

# Start all services
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Restart all services
restart:
	docker-compose restart

# View service logs
logs:
	docker-compose logs -f

# Open a shell in the web container
shell:
	docker-compose exec web bash

# Open a MongoDB shell
db-shell:
	docker-compose exec mongo mongosh -u $$(grep MONGO_INITDB_ROOT_USERNAME .env | cut -d '=' -f2) -p $$(grep MONGO_INITDB_ROOT_PASSWORD .env | cut -d '=' -f2)

# Run unit tests
test-unit:
	docker-compose exec -T web pytest tests/unit -v --cov=app --cov-report=term-missing

# Run end-to-end tests
test-e2e:
	docker-compose exec -T web pytest tests/e2e -v
