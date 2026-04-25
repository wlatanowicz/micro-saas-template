# docker-start runs in the foreground; migrate requires db and backend containers to be running.
.PHONY: docker-start migrate

docker-start:
	docker compose up --build

migrate:
	docker compose exec backend uv run alembic upgrade head

make-migrations:
	docker compose exec backend uv run alembic revision --autogenerate
