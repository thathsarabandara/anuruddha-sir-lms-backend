#!/bin/bash

# Installation script for setting up development environment
# Run: bash install.sh

echo "╔════════════════════════════════════════════════════════════╗"
echo "║    LMS Backend - Development Environment Setup             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Copy .env file
echo ""
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ Created .env file - Please update with your configuration"
else
    echo "✓ .env file already exists"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           Setup Complete!                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Update .env file with your configuration"
echo ""
echo "3. For Docker setup:"
echo "   docker-compose up -d"
echo ""
echo "4. For local development:"
echo "   python main.py"
echo ""
echo "5. Check health:"
echo "   curl http://localhost:5000/api/v1/health"
echo ""
echo "For more information, see README.md"
