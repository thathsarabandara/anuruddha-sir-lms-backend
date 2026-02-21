"""
Main entry point for the Flask LMS Backend Application
"""

import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables from .env file
load_dotenv()

# Create Flask application instance
app = create_app(config_name=os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', True)
    
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║         LMS Backend - Flask Application Started             ║
    ║═════════════════════════════════════════════════════════════║
    ║ Environment: {os.environ.get('FLASK_ENV', 'development'):45} ║
    ║ Port: {port:60} ║
    ║ Debug: {debug:59} ║
    ║═════════════════════════════════════════════════════════════║
    ║ API Docs:     http://localhost:{port}/api/docs        ║
    ║ Health Check: http://localhost:{port}/api/v1/health      ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
