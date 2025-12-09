.PHONY: install test lint format security init-db run

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

lint:
	flake8 app/ tests/
	black --check app/ tests/

format:
	black app/ tests/

security:
	bandit -r app/

init-db:
	python init_db.py

run:
	uvicorn app.main:app --reload --port 8501

