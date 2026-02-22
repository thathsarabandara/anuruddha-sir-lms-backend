#!/bin/bash
# Database initialization test script
# Use this to verify database setup without starting the full application

set -e

echo "🔍 LMS Backend - Database Initialization Test"
echo "=============================================="
echo ""

# Check if we're in the correct directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Run this script from the project root."
    exit 1
fi

# Check if virtual environment is active
if [ -z "$VIRTUAL_ENV" ] && [ ! -f "venv/bin/activate" ]; then
    echo "⚠️  Note: No virtual environment detected"
    echo "   Consider activating one for better isolation"
    echo ""
fi

# Check dependencies
echo "📦 Checking dependencies..."
python -c "import flask; print('   ✓ Flask')" 2>/dev/null || echo "   ✗ Flask not installed"
python -c "import sqlalchemy; print('   ✓ SQLAlchemy')" 2>/dev/null || echo "   ✗ SQLAlchemy not installed"
python -c "import pymysql; print('   ✓ PyMySQL')" 2>/dev/null || echo "   ✗ PyMySQL not installed"
python -c "import flask_migrate; print('   ✓ Flask-Migrate')" 2>/dev/null || echo "   ✗ Flask-Migrate not installed"
echo ""

# Check environment variables
echo "🔐 Checking environment variables..."
if [ -z "$FLASK_ENV" ]; then
    echo "   ⚠️  FLASK_ENV not set (will default to development)"
else
    echo "   ✓ FLASK_ENV=$FLASK_ENV"
fi

if [ -z "$DATABASE_URL" ]; then
    echo "   ⚠️  DATABASE_URL not set (will use config default)"
else
    # Hide password in output
    MASKED_URL=$(echo "$DATABASE_URL" | sed 's/:[^@]*@/:*****@/')
    echo "   ✓ DATABASE_URL=$MASKED_URL"
fi
echo ""

# Test database connection
echo "🔌 Testing database connection..."
python -c "
import os
from app import create_app, db
from app.utils.database import DatabaseInitializer

app = create_app('development')
db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')
print(f'   Database URI: {db_uri}')

try:
    initializer = DatabaseInitializer(db_uri, app.logger)
    if initializer.verify_connection():
        print('   ✓ Connection successful')
    else:
        print('   ✗ Connection failed')
        exit(1)
except Exception as e:
    print(f'   ✗ Error: {str(e)}')
    exit(1)
" || exit 1
echo ""

# Test database initialization
echo "🗄️  Testing database auto-initialization..."
python -c "
import os
from app import create_app, db
from app.utils.database import init_database

app = create_app('development')
with app.app_context():
    if init_database(app, db):
        app.logger.info('✓ Database initialization test passed')
    else:
        app.logger.error('✗ Database initialization test failed')
        exit(1)
" || exit 1
echo ""

# List available models (if any)
echo "📋 Checking models..."
python -c "
import pkgutil
import importlib
import sys

try:
    import app.models
    model_count = 0
    
    # List all Python files in models directory
    for importer, modname, ispkg in pkgutil.iter_modules(app.models.__path__):
        if not modname.startswith('_'):
            try:
                importlib.import_module(f'app.models.{modname}')
                model_count += 1
                print(f'   ✓ Loaded: app.models.{modname}')
            except Exception as e:
                print(f'   ⚠️  Failed to load app.models.{modname}: {str(e)}')
    
    if model_count == 0:
        print('   ℹ️  No models found (this is OK for new projects)')
    else:
        print(f'   Total: {model_count} model(s) loaded')
except ImportError:
    print('   ℹ️  Models package not ready yet')
" 
echo ""

echo "✅ Database initialization test completed!"
echo ""
echo "📚 For more information, see:"
echo "   - docs/DATABASE_INITIALIZATION.md"
echo "   - .devcontainer/README.md"
echo ""
