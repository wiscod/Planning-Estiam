.PHONY: install run refresh test lint

install:
	pip install -r requirements.txt

run:
	PYTHONPATH=src uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

refresh:
	python3 src/scraper.py

test:
	pytest

lint:
	flake8 src/ tests/ --max-line-length=100
