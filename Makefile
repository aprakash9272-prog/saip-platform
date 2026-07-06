.PHONY: help up down build logs ps \
	backend-install backend-run backend-migrate backend-revision backend-lint \
	frontend-install frontend-dev frontend-build frontend-lint

help:
	@echo "SAIP Platform — common commands"
	@echo ""
	@echo "  make up                  Start the full stack (db, backend, frontend) via docker-compose"
	@echo "  make down                Stop the stack"
	@echo "  make build               Rebuild all docker images"
	@echo "  make logs                Tail logs for all services"
	@echo "  make ps                  Show status of running services"
	@echo ""
	@echo "  make backend-install     Install backend dependencies into backend/.venv"
	@echo "  make backend-run         Run the backend API locally with reload"
	@echo "  make backend-migrate     Apply Alembic migrations"
	@echo "  make backend-revision    Generate a new Alembic revision (msg=\"...\")"
	@echo "  make backend-lint        Lint the backend"
	@echo ""
	@echo "  make frontend-install    Install frontend dependencies"
	@echo "  make frontend-dev        Run the frontend dev server"
	@echo "  make frontend-build      Build the frontend for production"
	@echo "  make frontend-lint       Lint the frontend"

up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

ps:
	docker compose ps

backend-install:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

backend-run:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload

backend-migrate:
	cd backend && . .venv/bin/activate && alembic upgrade head

backend-revision:
	cd backend && . .venv/bin/activate && alembic revision --autogenerate -m "$(msg)"

backend-lint:
	cd backend && . .venv/bin/activate && ruff check .

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-lint:
	cd frontend && npm run lint
