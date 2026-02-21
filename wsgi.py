"""
WSGI entry point for production deployment
Used with Gunicorn or other WSGI servers
"""

import os
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

from app import create_app

# Create Flask application
app = create_app(config_name=os.environ.get('FLASK_ENV', 'production'))

if __name__ == '__main__':
    app.run()
