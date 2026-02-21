"""
Routes Module
API endpoint blueprints

Pattern:
    - Routes are thin - handle HTTP concerns only
    - Routes call services for business logic
    - Routes return JSON responses
    - All logic is in services, not routes
    
Structure:
    Each feature has a corresponding _routes.py file:
    - health_routes.py: Health check endpoints
    - auth_routes.py: Authentication endpoints (to be created)
    - user_routes.py: User management endpoints (to be created)
    - course_routes.py: Course endpoints (to be created)
    - etc.
    
Example:
    @bp.route('/endpoint', methods=['GET'])
    def get_endpoint():
        \"\"\"Handle GET request\"\"\"
        data = SomeService.get_data()  # Business logic in service
        return jsonify(data), 200      # Simple response in route
"""
