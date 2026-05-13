.PHONY: help build test deploy setup clean

help:  ## Show this help
	@echo "SupremeAI Makefile"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build backend JAR
	./gradlew clean build -x test

test: ## Run all tests
	./gradlew test

compile: ## Compile only
	./gradlew compileJava

lint: ## Run code style checks
	./gradlew spotlessCheck

format: ## Format code
	./gradlew spotlessApply

deploy: ## Deploy all services to Cloud Run (requires gcloud & docker)
	@echo "Deploying backend, reverse-engineering, and simulator-runtime..."
	bash deploy.sh

setup: ## Create GCP infrastructure only
	bash infrastructure/setup.sh

docker-build: ## Build all Docker images locally
	docker build -t gcr.io/$(shell echo $$GCP_PROJECT_ID)/supremeai-backend:latest .
	docker build -t gcr.io/$(shell echo $$GCP_PROJECT_ID)/reverse-engineering:latest -f reverse-engineering/Dockerfile reverse-engineering
	docker build -t gcr.io/$(shell echo $$GCP_PROJECT_ID)/simulator-runtime:latest -f simulator-runtime/Dockerfile simulator-runtime

docker-push: ## Push all Docker images to GCR
	docker push gcr.io/$(shell echo $$GCP_PROJECT_ID)/supremeai-backend:latest
	docker push gcr.io/$(shell echo $$GCP_PROJECT_ID)/reverse-engineering:latest
	docker push gcr.io/$(shell echo $$GCP_PROJECT_ID)/simulator-runtime:latest

clean: ## Clean build artifacts
	./gradlew clean
	rm -rf build/
	rm -rf dashboard/dist/
	rm -rf reverse-engineering/__pycache__ simulator-runtime/__pycache__

local-run: ## Run backend locally (requires env vars)
	@echo "Starting backend on http://localhost:8080"
	@echo "Ensure Firestore emulator is running: firebase emulators:start"
	GCP_PROJECT_ID=supremeai-459910 ./gradlew bootRun

simulate-reveng: ## Run reverse engineering locally against a URL
	cd reverse-engineering && uvicorn main:app --reload --port 8081

simulate-simulator: ## Run simulator runtime locally
	cd simulator-runtime && uvicorn main:app --reload --port 8082

dashboard: ## Start React dashboard
	cd dashboard && npm install && npm run dev
