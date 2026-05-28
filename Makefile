.PHONY: help install install-dev migrate migrate-fresh createsuperuser static seed \
        runserver test clean lint format coverage docker-build docker-up docker-down \
        docker-logs db-backup db-restore

help:
	@echo "Bodas - Wedding Event Management Platform"
	@echo ""
	@echo "Available commands:"
	@echo "  make install              Install dependencies"
	@echo "  make install-dev          Install dev dependencies"
	@echo "  make migrate              Run migrations"
	@echo "  make migrate-fresh        Fresh database migration"
	@echo "  make createsuperuser      Create admin user"
	@echo "  make static               Collect static files"
	@echo "  make seed                 Load initial data"
	@echo "  make runserver            Start development server"
	@echo "  make test                 Run tests"
	@echo "  make clean                Remove generated files"
	@echo "  make lint                 Run linting"
	@echo "  make format               Format code"
	@echo "  make coverage             Generate coverage report"
	@echo "  make docker-build         Build Docker image"
	@echo "  make docker-up            Start Docker services"
	@echo "  make docker-down          Stop Docker services"
	@echo "  make docker-logs          View Docker logs"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install black flake8 isort pytest pytest-django pytest-cov

migrate:
	python manage.py migrate

migrate-fresh:
	python manage.py flush --no-input
	python manage.py migrate

createsuperuser:
	python manage.py createsuperuser

static:
	python manage.py collectstatic --noinput

seed:
	python manage.py loaddata web/fixtures/providers.json

runserver:
	python manage.py runserver

test:
	python manage.py test

test-coverage:
	pytest --cov=web --cov-report=html

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	rm -rf build/ dist/ htmlcov/ .coverage .pytest_cache/

lint:
	flake8 web config
	isort --check-only web config

format:
	black web config
	isort web config

docker-build:
	docker build -t bodas:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-migrate:
	docker-compose exec web python manage.py migrate

docker-createsuperuser:
	docker-compose exec web python manage.py createsuperuser

docker-seed:
	docker-compose exec web python manage.py loaddata web/fixtures/providers.json
