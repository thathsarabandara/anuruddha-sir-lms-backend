"""
Server startup entry point
Command: python run.py
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app

# Create application
app = create_app(config_name=os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║         LMS Backend - Starting Server                      ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
