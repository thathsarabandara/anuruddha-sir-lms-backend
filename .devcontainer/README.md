# Development Container Setup

This directory contains the configuration for the development container setup using VS Code Dev Containers.

## 🚀 Quick Start - Database Auto-Initialization

**No manual database setup needed!** The application automatically:
- Creates the database if it doesn't exist
- Creates all required tables from models
- Verifies the connection

Just start the container and everything is ready to go.

## Prerequisites

- **Docker Desktop** or Docker + Docker Compose installed
- **VS Code** with the Remote - Containers extension installed
- Git

## Quick Start

### 1. Open in Dev Container

1. Open the project in VS Code
2. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
3. Search for and select **"Dev Containers: Reopen in Container"**
4. Wait for the container to build and start (first time may take 2-3 minutes)

### 2. Verify Setup

Once the container is running, verify everything is set up correctly:

```bash
# Inside the container terminal
python --version      # Should show Python 3.11.x
flask --version       # Should show Flask version
pytest --version      # Should show pytest version
```

## What's Included

### Development Tools
- **Python 3.11** with all project dependencies
- **pytest** - Testing framework with coverage support
- **black** - Code formatter
- **flake8** - Code linter
- **pylint** - Advanced linting
- **isort** - Import sorter
- **debugpy** - Python debugger
- **ipdb** - Interactive Python debugger
- **Flask-DebugToolbar** - Flask debugging toolbar

### Services
- **MySQL 8.0** - Database server
- **Redis 7** - Cache/Session store
- **Kafka 7.5** - Message broker
- **Zookeeper** - Kafka coordinator

### VS Code Extensions
- Python extension with Pylance
- Formatter (Black)
- Linter (Flake8, Ruff)
- REST Client
- Git Graph
- Docker support

## Common Commands

### Running the Application

```bash
# Start Flask development server (auto-reloading)
flask run --host=0.0.0.0 --port=5000

# Or using the run script
python run.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_health.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with Black
black app/ tests/

# Check linting issues
flake8 app/ tests/

# Sort imports
isort app/ tests/

# Using the quality script
bash scripts/code_quality.sh
```

### Database

```bash
# Database is auto-initialized when server starts
# No manual setup needed!

# But if you need to manage it manually:
flask db status          # Check database status
flask db init           # Initialize database and tables
flask db verify         # Verify connection
flask db reset          # Reset database (drops all data)
```

## Debugging

### VS Code Debugger

1. Set breakpoints in your code (click on the line number)
2. Press `F5` to start debugging
3. Use the debug console to inspect variables and run expressions

### Using pdb

```python
import pdb; pdb.set_trace()
```

### Using ipdb (enhanced pdb)

```python
import ipdb; ipdb.set_trace()
```

## Environment Variables

Edit `.devcontainer/.env.dev` to configure:
- Database credentials
- API keys
- Email settings
- AWS/Stripe configurations
- Logging levels

This file is automatically loaded in the dev container.

## Port Mappings

| Service | Port | Purpose |
|---------|------|---------|
| Flask API | 5000 | Web application |
| MySQL | 3306 | Database |
| Redis | 6379 | Cache/Session |
| Kafka | 9092 | Message broker |
| Debugger | 5678 | Python debugging |

All services are automatically forwarded to your host machine.

## Troubleshooting

### Container fails to start
```bash
# Check container logs
docker logs lms-backend-dev

# Rebuild the container
devcontainer rebuild
```

### Database connection issues
```bash
# Check MySQL is running
docker exec lms-mysql-dev mysqladmin ping -h localhost

# Check Redis is running
docker exec lms-redis-dev redis-cli ping
```

### Import errors
```bash
# Ensure all dependencies are installed
pip install -r /workspace/requirements.txt

# Reinstall in editable mode
pip install -e . --no-deps
```

### Port already in use
Edit `.devcontainer/docker-compose.yml` and change the port mappings.

## IDE Features

### Intellisense
- Full type hints support
- Go to Definition (Ctrl+Click)
- Find References (Shift+F12)
- Rename Symbol (F2)

### Formatting
- Auto-format on save (Black)
- Import organization (isort)
- Remove unused imports

### Testing
- Run tests from VS Code UI
- View test results inline
- Coverage reports

## Tips

1. **Hot Reload**: The Flask development server auto-reloads on code changes
2. **Logs**: Check `/workspace/logs/app.log` for application logs
3. **Database**: Use MySQL Workbench or DBeaver to connect to the database at `localhost:3306`
4. **Redis CLI**: Access Redis using `redis-cli` in the terminal
5. **Kafka**: Use Kafka console tools in the `kafka` container

## Stopping the Container

- **VS Code**: Select "Reopen Locally" or "Close Remote Connection"
- **Docker CLI**: `docker-compose down` (if running standalone)

## Additional Resources

- [Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [pytest Documentation](https://docs.pytest.org/)
