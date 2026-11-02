.PHONY: api test generate validate up down
api:
	cd backend && uvicorn app.main:app --reload
test:
	cd backend && pytest -q
generate:
	cd backend && python -m generator.generate --scale starter --seed 20261022 --output ../data/generated
validate:
	cd backend && python -m validation.validate ../data/generated
up:
	docker compose up --build -d
down:
	docker compose down
