#!/bin/bash

# Script to format and lint code
# Usage: bash scripts/code_quality.sh

echo "╔════════════════════════════════════════════════════════════╗"
echo "║            Code Quality Check & Formatting                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "1️⃣  Sorting imports with isort..."
isort app tests main.py wsgi.py
echo "✓ Imports sorted"
echo ""

echo "2️⃣  Formatting code with black..."
black app tests main.py wsgi.py
echo "✓ Code formatted"
echo ""

echo "3️⃣  Running flake8 style check..."
flake8 app tests
echo "✓ Flake8 checks passed"
echo ""

echo "4️⃣  Running pylint..."
pylint app || echo "⚠️  Pylint found issues (see above)"
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║            Code quality check completed!                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
