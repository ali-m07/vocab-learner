.PHONY: help install run build docker-build docker-run docker-compose-up docker-compose-down test clean build-ts watch-ts

help: ## Show available commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt
	cd frontend && npm install && npm run build

run: ## Run Flask application
	python backend/app.py

run-cli: ## Run CLI script
	python backend/vocab_learner.py

run-daily: ## Run daily review
	python backend/daily_review.py

build-ts: ## Build TypeScript
	cd frontend && npm run build

watch-ts: ## Watch TypeScript for development
	cd frontend && npm run watch

build: ## Build Docker image
	docker build -t vocab-learner:latest .

docker-run: ## Run Docker container
	docker run -d -p 5000:5000 \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/uploads:/app/uploads \
		--name vocab-learner \
		vocab-learner:latest

docker-compose-up: ## Run Docker Compose
	docker-compose up -d

docker-compose-down: ## Stop Docker Compose
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

helm-install: ## Install Helm chart
	helm install vocab-learner ./helm/vocab-learner

helm-upgrade: ## Upgrade Helm chart
	helm upgrade vocab-learner ./helm/vocab-learner

helm-uninstall: ## Uninstall Helm chart
	helm uninstall vocab-learner

test: ## Run tests (if available)
	@echo "Tests are under development..."

clean: ## Clean temporary files
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.apkg" -delete
	rm -rf .pytest_cache
	rm -rf dist/
	rm -rf build/

clean-data: ## Clean data files (caution!)
	rm -rf data/*.csv
	rm -rf uploads/*.apkg
