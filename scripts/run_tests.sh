#!/bin/bash

# Script to run tests with coverage report
# Usage: bash scripts/run_tests.sh [test_file]

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           Running Tests with Coverage Report               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ -z "$1" ]; then
    echo "Running all tests..."
    pytest -v --cov=app --cov-report=html --cov-report=term-missing tests/
else
    echo "Running tests from: $1"
    pytest -v --cov=app --cov-report=html --cov-report=term-missing "$1"
fi

echo ""
echo "✓ Tests completed!"
echo "Coverage report: htmlcov/index.html"
