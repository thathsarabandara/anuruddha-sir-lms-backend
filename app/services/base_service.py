"""
Base Service Class
All services should extend this base class for common functionality
"""


class BaseService:
    """
    Base service class providing common patterns
    
    All service classes should extend this class.
    
    Example:
        class UserService(BaseService):
            @staticmethod
            def get_user(user_id):
                # Business logic
                return user_data
    """
    
    @staticmethod
    def to_dict(model):
        """
        Convert SQLAlchemy model to dictionary
        
        Args:
            model: SQLAlchemy model instance
        
        Returns:
            dict: Model as dictionary
        """
        if model is None:
            return None
        
        return {
            c.name: getattr(model, c.name)
            for c in model.__table__.columns
        }
    
    @staticmethod
    def to_list(models):
        """
        Convert list of SQLAlchemy models to list of dictionaries
        
        Args:
            models: List of SQLAlchemy model instances
        
        Returns:
            list: List of dictionaries
        """
        return [BaseService.to_dict(model) for model in models]
