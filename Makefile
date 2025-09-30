test:
	poetry run pytest -m "not e2e" --cov=src --cov-report=term-missing --cov-fail-under=80

format:
	poetry run black src tests

lint:
	poetry run ruff check src tests

quality: format lint test
