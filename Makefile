.PHONY: help install clean run test lint format docker-up docker-down migrate

help:
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║            LMS Backend - Development Commands              ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install           Install dependencies"
	@echo "  make venv              Create virtual environment"
	@echo "  make clean             Clean cache and build files"
	@echo ""
	@echo "Development:"
	@echo "  make run               Run development server"
	@echo "  make run-docker        Start services with Docker Compose"
	@echo "  make stop-docker       Stop Docker services"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test              Run tests"
	@echo "  make test-coverage     Run tests with coverage report"
	@echo "  make lint              Run code quality checks"
	@echo "  make format            Format code with black"
	@echo "  make isort             Sort imports"
	@echo ""
	@echo "Database:"
	@echo "  make migrate           Run database migrations"
	@echo "  make init-db           Initialize database"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build      Build Docker image"
	@echo "  make docker-push       Push image to registry"
	@echo ""

install:
	@echo "Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt

venv:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "Activate with: source venv/bin/activate (Linux/macOS) or venv\\Scripts\\activate (Windows)"

clean:
	@echo "Cleaning cache and build files..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

run:
	@echo "Starting development server on http://localhost:5000..."
	python main.py

run-docker:
	@echo "Starting Docker services..."
	docker-compose up -d

stop-docker:
	@echo "Stopping Docker services..."
	docker-compose down

logs-docker:
	@echo "Showing Docker logs..."
	docker-compose logs -f backend

test:
	@echo "Running tests..."
	pytest -v

test-coverage:
	@echo "Running tests with coverage..."
	pytest --cov=app --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	@echo "Running code quality checks..."
	@echo "Running flake8..."
	flake8 app tests
	@echo "Running pylint..."
	pylint app
	@echo "All checks passed!"

format:
	@echo "Formatting code with black..."
	black app tests main.py wsgi.py

isort:
	@echo "Sorting imports..."
	isort app tests main.py wsgi.py

migrate:
	@echo "Running database migrations..."
	flask db upgrade

init-db:
	@echo "Initializing database..."
	@echo "Make sure database service is running..."
	python -c "from app import create_app, db; app = create_app(); db.create_all()"

docker-build:
	@echo "Building Docker image..."
	docker-compose build

docker-push:
	@echo "Push Docker image (requires registry configuration)..."
	docker-compose push

shell:
	@echo "Opening Flask shell..."
	flask shell

db-shell:
	@echo "Opening database shell..."
	docker-compose exec mysql mysql -u root -p

redis-shell:
	@echo "Opening Redis CLI..."
	docker-compose exec redis redis-cli

health:
	@echo "Checking API health..."
	curl -s http://localhost:5000/api/v1/health | python -m json.tool

docs:
	@echo "Opening documentation..."
	@echo "Local docs: README.md"
	@echo "Module docs: ../docs/modules/"

requirements:
	@echo "Updating requirements file..."
	pip freeze > requirements.txt

.SILENT: help
