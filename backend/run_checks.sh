#!/bin/bash

echo "=== Running Backend Checks ==="

echo "1. Formatting check (black)..."
black --check app/ tests/ || echo "Formatting issues found. Run 'black app/ tests/' to fix."

echo "2. Linting (flake8)..."
flake8 app/ tests/ || echo "Linting issues found."

echo "3. Security scan (bandit)..."
bandit -r app/ || echo "Security issues found."

echo "4. Running tests..."
pytest tests/ -v || echo "Tests failed."

echo "=== Checks Complete ==="

