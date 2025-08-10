# PantryPal Development Makefile
# Provides convenient commands for development, testing, and deployment

.PHONY: help install test lint format security deploy-dev deploy-prod clean

# Default target
help: ## Show this help message
	@echo "PantryPal Development Commands:"
	@echo
	@awk 'BEGIN {FS = ":.*##"; printf "\033[36m\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development
install: ## Install all dependencies
	@echo "Installing API dependencies..."
	cd api && pip install -r requirements.txt
	cd api && pip install pytest-cov black ruff safety bandit pre-commit
	@echo "Installing mobile dependencies..."
	cd expo/ppal && npm install
	@echo "Installing pre-commit hooks..."
	pre-commit install

install-dev: ## Install development dependencies only
	cd api && pip install pytest-cov black ruff safety bandit pre-commit
	pre-commit install

##@ Code Quality
format: ## Format code with black and prettier
	@echo "Formatting Python code..."
	cd api && black . --line-length=100
	@echo "Formatting TypeScript/JavaScript code..."
	cd expo/ppal && npx prettier --write "**/*.{js,jsx,ts,tsx,json}"

lint: ## Run linting checks
	@echo "Linting Python code..."
	cd api && ruff check .
	@echo "Linting TypeScript code..."
	cd expo/ppal && npx expo lint

lint-fix: ## Fix linting issues automatically
	@echo "Fixing Python linting issues..."
	cd api && ruff check . --fix
	@echo "Fixing TypeScript linting issues..."
	cd expo/ppal && npx expo lint --fix

type-check: ## Run type checking
	@echo "Type checking TypeScript..."
	cd expo/ppal && npx tsc --noEmit

##@ Testing
test: ## Run all tests
	@echo "Running API tests..."
	cd api && python -m pytest tests/ -v --cov=. --cov-report=term-missing
	@echo "Running mobile tests..."
	cd expo/ppal && npm test -- --watchAll=false

test-unit: ## Run unit tests only
	cd api && python -m pytest tests/ -v -m "not integration" --cov=. --cov-report=term-missing

test-integration: ## Run integration tests only
	cd api && python -m pytest tests/integration/ -v

test-smoke: ## Run smoke tests against deployed API
	cd api && python -m pytest tests/smoke/ -v

test-coverage: ## Generate detailed coverage report
	cd api && python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in api/htmlcov/index.html"

##@ Security
security: ## Run security scans
	@echo "Running Python security scan..."
	cd api && safety check
	cd api && bandit -r . -x tests/ -ll
	@echo "Running npm security audit..."
	cd expo/ppal && npm audit --audit-level=moderate

security-fix: ## Fix security vulnerabilities
	@echo "Fixing npm vulnerabilities..."
	cd expo/ppal && npm audit fix

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

##@ API Development
api-dev: ## Start API development server
	cd api && python app.py

api-build: ## Build API with SAM
	cd api && sam build --use-container

api-local: ## Start API locally with SAM
	cd api && sam local start-api --port 3001

api-logs: ## Get API logs from AWS
	cd api && sam logs --stack-name ppal --region us-east-1

##@ Mobile Development  
mobile-dev: ## Start mobile development server
	cd expo/ppal && npx expo start

mobile-build-ios: ## Build iOS app
	cd expo/ppal && npx eas build --platform ios

mobile-build-android: ## Build Android app
	cd expo/ppal && npx eas build --platform android

##@ Deployment
deploy-dev: ## Deploy to development environment
	@echo "Building and deploying to development..."
	cd api && sam build --use-container
	cd api && sam deploy --stack-name ppal-dev --parameter-overrides Environment=dev

deploy-staging: ## Deploy to staging environment
	@echo "Building and deploying to staging..."
	cd api && sam build --use-container
	cd api && sam deploy --stack-name ppal-staging --parameter-overrides Environment=staging

deploy-prod: ## Deploy to production environment
	@echo "Building and deploying to production..."
	cd api && sam build --use-container
	cd api && sam deploy --stack-name ppal --parameter-overrides Environment=production

rollback: ## Rollback production deployment
	@echo "Rolling back production deployment..."
	./scripts/rollback.sh --stack-name ppal --region us-east-1

health-check: ## Run health check against production
	cd api && python health_check.py --url https://bo1uqpm579.execute-api.us-east-1.amazonaws.com/Prod

##@ Utilities
clean: ## Clean build artifacts and cache files
	@echo "Cleaning Python cache..."
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	@echo "Cleaning API build artifacts..."
	rm -rf api/.aws-sam/
	@echo "Cleaning mobile cache..."
	cd expo/ppal && rm -rf node_modules/.cache
	@echo "Cleaning test artifacts..."
	rm -rf api/htmlcov/ api/.coverage api/.pytest_cache/

setup-dev: ## Set up development environment
	@echo "Setting up development environment..."
	make install-dev
	@echo "Running initial code formatting..."
	make format
	@echo "Running initial tests..."
	make test-unit
	@echo "Development environment ready!"

ci-check: ## Run all CI checks locally
	@echo "Running CI checks locally..."
	make lint
	make type-check  
	make test
	make security
	@echo "All CI checks passed!"

docker-build: ## Build Docker image locally
	cd api && docker build -t pantrypal-api:latest .

docker-run: ## Run Docker container locally
	docker run -p 8000:8000 pantrypal-api:latest

##@ Information
status: ## Show project status
	@echo "=== PantryPal Project Status ==="
	@echo "API Dependencies:"
	@cd api && pip list | grep -E "(fastapi|boto3|pytest)" || echo "  Dependencies not installed"
	@echo "Mobile Dependencies:" 
	@cd expo/ppal && npm list --depth=0 | grep -E "(expo|react)" || echo "  Dependencies not installed"
	@echo "AWS Stack Status:"
	@aws cloudformation describe-stacks --stack-name ppal --region us-east-1 --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "  Stack not found or AWS not configured"

validate-templates: ## Validate CloudFormation templates
	cd api && sam validate --template-file template.yaml