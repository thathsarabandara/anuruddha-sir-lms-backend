# LMS Backend - Flask Application

A comprehensive Learning Management System (LMS) backend built with Flask, designed to facilitate online education with multiple user roles including Super Admin, Admin, Teachers, and Students.

## 📋 Project Overview

This is the backend API for a full-featured Learning Management System supporting:
- **Authentication & Authorization** (JWT, Role-based access control)
- **User Management** (Profiles, preferences, activity tracking)
- **Course Management** (Creation, enrollment, progress tracking)
- **Quizzes & Assessments** (Multiple question types, grading)
- **Notifications** (Email, SMS, In-app)
- **Certifications** (Generation & management)
- **Payments** (Stripe integration)
- **Rewards System** (Points, badges, leaderboards)
- **Dashboard** (Role-based analytics)

## 🛠 Technology Stack

### Backend
- **Framework**: Flask 2.3.3
- **Language**: Python 3.10+
- **ORM**: SQLAlchemy with Flask-SQLAlchemy

### Database & Caching
- **Primary Database**: MySQL 8.0+
- **Caching**: Redis 7
- **Message Queue**: Apache Kafka 7.5.0

### Authentication & Security
- **Auth**: JWT (JSON Web Tokens)
- **Password Hashing**: bcrypt
- **Encryption**: cryptography

### External Services
- **Email**: SendGrid / SMTP
- **Payments**: Stripe
- **File Storage**: AWS S3 / Local
- **Monitoring**: Optional (Prometheus + Grafana)

### Development Tools
- **Testing**: pytest, pytest-cov
- **Code Quality**: black, flake8, pylint
- **API Docs**: Flasgger/Swagger
- **WSGI Server**: Gunicorn

## 📁 Project Structure

```
anu-backend-flask/
├── app/
│   ├── __init__.py                 # Flask app factory
│   ├── config.py                   # Configuration management
│   ├── main.py                     # Entry point
│   ├── wsgi.py                     # Production WSGI entry
│   ├── routes/                     # API route blueprints
│   │   ├── __init__.py
│   │   └── health_routes.py        # Health check endpoints
│   ├── models/                     # Database models (SQLAlchemy)
│   │   └── __init__.py
│   ├── services/                   # Business logic layer
│   │   └── __init__.py
│   ├── middleware/                 # Request/response interceptors
│   │   └── __init__.py
│   └── utils/                      # Utility functions & helpers
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration & fixtures
│   └── test_health.py              # Health check tests
├── migrations/                     # Database migrations (Alembic)
├── logs/                           # Application logs
├── uploads/                        # User uploads directory
├── Dockerfile                      # Docker image definition
├── docker-compose.yml              # Multi-container orchestration
├── .dockerignore                   # Docker build exclusions
├── .gitignore                      # Git exclusions
├── .env.example                    # Environment template
├── requirements.txt                # Python dependencies
├── pytest.ini                      # Pytest configuration
├── .flake8                         # Flake8 code style config
├── wsgi.py                         # Production WSGI entry
└── README.md                       # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Docker & Docker Compose (for containerized setup)
- Git

### Option 1: Local Development Setup

1. **Clone the repository**
   ```bash
   cd anu-backend-flask
   ```

2. **Create and activate virtual environment**
   ```bash
   # On Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   # Create tables (automatic with Flask-SQLAlchemy)
   export FLASK_APP=main.py
   export FLASK_ENV=development
   ```

6. **Run the development server**
   ```bash
   python main.py
   ```

   The server will start at `http://localhost:5000`

7. **Verify health check**
   ```bash
   curl http://localhost:5000/api/v1/health
   ```

### Option 2: Docker Setup (Recommended)

1. **Setup environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Build and start containers**
   ```bash
   docker-compose up -d
   ```

3. **Verify services are running**
   ```bash
   docker-compose ps
   ```

4. **Check health**
   ```bash
   curl http://localhost:5000/api/v1/health
   ```

5. **View logs**
   ```bash
   docker-compose logs -f backend
   ```

## 📚 API Endpoints

### Health Check Endpoints
- `GET /api/v1/health` - Main health check
- `GET /api/v1/health/ready` - Readiness probe
- `GET /api/v1/health/live` - Liveness probe

Response example:
```json
{
  "status": "healthy",
  "service": "LMS Backend",
  "version": "1.0.0",
  "timestamp": "2023-09-15T10:30:00.000000",
  "environment": "development",
  "database": "healthy"
}
```

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```env
# Core
FLASK_ENV=development
FLASK_APP=main.py
DEBUG=True
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database
DATABASE_URL=mysql+pymysql://user:pass@host:3306/dbname

# Cache & Queue
REDIS_URL=redis://localhost:6379/0
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=app-password

# Payments
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# AWS S3
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_S3_BUCKET=your-bucket
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f backend

# Execute command in backend container
docker-compose exec backend python -c "import app"

# Rebuild images
docker-compose up -d --build

# Remove all volumes (clean database)
docker-compose down -v

# Access MySQL
docker-compose exec mysql mysql -u root -p

# Access Redis CLI
docker-compose exec redis redis-cli

# View running containers
docker-compose ps

# Prune unused Docker resources
docker system prune -a
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app tests/

# Run specific test file
pytest tests/test_health.py

# Run specific test
pytest tests/test_health.py::TestHealthCheck::test_health_check

# Run tests matching pattern
pytest -k "health"

# Run tests with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov=app --cov-report=html tests/
# Open htmlcov/index.html in browser
```

## 📊 Code Quality

```bash
# Format code with black
black app tests

# Check code style
flake8 app tests

# Lint with pylint
pylint app

# Sort imports
isort app tests
```

## 📖 Database Migrations

```bash
# Initialize migrations (first time only)
flask db init

# Create migration
flask db migrate -m "Migration message"

# Apply migration
flask db upgrade

# Downgrade migration
flask db downgrade
```

## 🔐 Security Best Practices

1. **Environment Variables**: Never commit `.env` file - use `.env.example`
2. **Secret Keys**: Generate strong random keys for production
3. **HTTPS**: Use HTTPS in production
4. **CORS**: Configure CORS appropriately
5. **Rate Limiting**: Implement rate limiting for APIs
6. **Input Validation**: Always validate user inputs
7. **SQL Injection**: Use parameterized queries (SQLAlchemy handles this)
8. **CSRF Protection**: Enable CSRF for session-based auth

## 📝 Logging

Logs are stored in `logs/lms_backend.log` with the following format:
```
2023-09-15 10:30:00,123 INFO: Request started
2023-09-15 10:30:01,456 ERROR: Database connection failed
```

## 🔧 Development Workflow

1. Create a new feature branch
   ```bash
   git checkout -b feature/feature-name
   ```

2. Make changes and write tests
   ```bash
   # Edit code
   # Write tests in tests/
   pytest
   ```

3. Format and lint code
   ```bash
   black app tests
   flake8 app tests
   ```

4. Commit changes
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. Push to remote
   ```bash
   git push origin feature/feature-name
   ```

## 📦 Dependencies Management

### Adding a new dependency
```bash
# Add to requirements.txt
pip install new-package
pip freeze | grep -i new-package >> requirements.txt

# Update in Docker
docker-compose up -d --build
```

### Updating dependencies
```bash
# Upgrade all packages
pip install -U -r requirements.txt

# Update specific package
pip install --upgrade package-name
```

## 🆘 Troubleshooting

### Database connection issues
```bash
# Check MySQL container
docker-compose exec mysql mysqladmin ping

# Check database
docker-compose exec mysql mysql -u root -p -e "SHOW DATABASES;"
```

### Redis connection issues
```bash
# Check Redis connection
docker-compose exec redis redis-cli ping

# View Redis data
docker-compose exec redis redis-cli KEYS '*'
```

### Port conflicts
```bash
# Find process using port
lsof -i :5000

# Kill process
kill -9 <PID>
```

### Clear cache and rebuild
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d --build  # Rebuild and start
```

## 📚 Module Documentation

For detailed documentation on each module, see the `/docs` directory:

- [01_AUTH_MODULE.md](../docs/modules/01_AUTH_MODULE.md) - Authentication
- [02_USERS_MODULE.md](../docs/modules/02_USERS_MODULE.md) - User Management
- [03_COURSES_MODULE.md](../docs/modules/03_COURSES_MODULE.md) - Course Management
- [04_QUIZZES_MODULE.md](../docs/modules/04_QUIZZES_MODULE.md) - Assessments
- [05_NOTIFICATIONS_MODULE.md](../docs/modules/05_NOTIFICATIONS_MODULE.md) - Notifications
- [06_REVIEW_MODULE.md](../docs/modules/06_REVIEW_MODULE.md) - Reviews
- [07_REWARDS_MODULE.md](../docs/modules/07_REWARDS_MODULE.md) - Gamification
- [08_CERTIFICATIONS_MODULE.md](../docs/modules/08_CERTIFICATIONS_MODULE.md) - Certificates
- [09_PAYMENT_MODULE.md](../docs/modules/09_PAYMENT_MODULE.md) - Payments
- [10_DASHBOARD_MODULE.md](../docs/modules/10_DASHBOARD_MODULE.md) - Analytics
- [11_FINANCE_MODULE.md](../docs/modules/11_FINANCE_MODULE.md) - Finance

## 🤝 Contributing

1. Follow the existing code style
2. Write tests for new features
3. Update documentation
4. Create clear, descriptive commit messages
5. Submit pull requests to development branch

## 📄 License

This project is proprietary and confidential.

## 👥 Development Team

- **Project Lead**: Anuruddha (Sir)

## 📞 Support

For issues, questions, or contributions, please refer to the project documentation or contact the development team.

---

**Last Updated**: September 15, 2023  
**Version**: 1.0.0  
**Status**: In Development
