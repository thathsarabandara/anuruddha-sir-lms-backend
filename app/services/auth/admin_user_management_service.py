"""
Admin User Management Service
Handles admin-only operations for managing students and teachers
including listing, activating, and banning users
"""

import logging
from datetime import datetime

from flask import current_app

from app import db
from app.exceptions import ValidationError, AuthorizationError
from app.models import User, UserAccountStatus, UserRole, Role, StudentProfile, TeacherProfile
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


def _send_notification_safely(method_name, user_id, **kwargs):
    """
    Safe notification sender that won't block main flow on errors.
    
    Args:
        method_name: Name of the NotificationService method to call
        user_id: User ID to send notification to
        **kwargs: Additional arguments for the notification method
    """
    try:
        from app.services.notifications import NotificationService
        
        service = NotificationService()
        method = getattr(service, method_name)
        method(user_id=user_id, channels=['email', 'whatsapp'], **kwargs)
        logger.info(f"Notification {method_name} sent to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send {method_name} notification to {user_id}: {str(e)}", exc_info=True)


class AdminUserManagementService(BaseService):
    """Service for admin user management operations"""

    # ==================== STUDENTS MANAGEMENT ====================

    @staticmethod
    def list_students(status_filter=None, page=1, limit=10):
        """
        List all students with optional status filtering
        
        Args:
            status_filter: Filter by status - 'active', 'pending', 'banned' or None for all
            page: Page number for pagination (1-indexed)
            limit: Number of records per page
            
        Returns:
            dict: {
                'total': int,
                'page': int,
                'limit': int,
                'students': list[dict]
            }
            
        Raises:
            ValidationError: If invalid status_filter provided
        """
        try:
            # Valid status filters
            valid_statuses = ['active', 'pending', 'banned']
            
            if status_filter and status_filter not in valid_statuses:
                raise ValidationError(
                    f"Invalid status filter. Must be one of: {', '.join(valid_statuses)}"
                )
            
            # Start query with student role users
            query = db.session.query(User).join(
                UserRole, User.user_id == UserRole.user_id
            ).join(
                Role, UserRole.role_id == Role.role_id
            ).filter(Role.role_name == 'student')
            
            # Apply status filter if provided
            if status_filter:
                account_status = db.session.query(UserAccountStatus).filter(
                    UserAccountStatus.user_id == User.user_id
                ).correlate(User)
                
                if status_filter == 'active':
                    query = query.filter(
                        db.exists(
                            db.session.query(1).filter(
                                (UserAccountStatus.user_id == User.user_id),
                                (UserAccountStatus.is_active == True),
                                (UserAccountStatus.is_banned == False)
                            )
                        )
                    )
                elif status_filter == 'pending':
                    query = query.filter(
                        db.exists(
                            db.session.query(1).filter(
                                (UserAccountStatus.user_id == User.user_id),
                                (UserAccountStatus.is_active == False)
                            )
                        )
                    )
                elif status_filter == 'banned':
                    query = query.filter(
                        db.exists(
                            db.session.query(1).filter(
                                (UserAccountStatus.user_id == User.user_id),
                                (UserAccountStatus.is_banned == True)
                            )
                        )
                    )
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            students = query.offset(offset).limit(limit).all()
            
            # Format response
            students_data = [
                AdminUserManagementService._format_user_with_status(student)
                for student in students
            ]
            
            return {
                'total': total,
                'page': page,
                'limit': limit,
                'students': students_data
            }
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error listing students: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to list students: {str(e)}")

    @staticmethod
    def activate_student(student_id):
        """
        Activate a student account
        
        Args:
            student_id: UUID of student user
            
        Returns:
            dict: Updated user data
            
        Raises:
            ValidationError: If student not found
        """
        try:
            user = AdminUserManagementService._get_student_by_id(student_id)
            
            # Check if this is first-time activation
            account_status = user.account_status
            is_first_activation = False
            
            if not account_status:
                account_status = UserAccountStatus(
                    user_id=student_id,
                    is_active=True,
                    is_banned=False
                )
                db.session.add(account_status)
                is_first_activation = True
            else:
                is_first_activation = not account_status.is_active
                account_status.is_active = True
                account_status.is_banned = False
                account_status.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Student {student_id} activated by admin")
            
            # Send appropriate notification
            try:
                recipient_name = f"{user.first_name} {user.last_name}".strip()
                dashboard_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:5173')}/dashboard"
                support_url = f"{current_app.config.get('SUPPORT_URL', 'http://localhost:5173')}/support"
                
                if is_first_activation:
                    # Send welcome message for first-time approval
                    _send_notification_safely(
                        'send_student_welcome_first_approval',
                        user_id=student_id,
                        recipient_name=recipient_name,
                        dashboard_url=dashboard_url,
                        support_url=support_url
                    )
                else:
                    # Send standard activation notification
                    _send_notification_safely(
                        'send_student_account_activated',
                        user_id=student_id,
                        recipient_name=recipient_name,
                        dashboard_url=dashboard_url,
                        support_url=support_url
                    )
            except Exception as e:
                logger.error(f"Error sending activation notification: {str(e)}", exc_info=True)
            
            return AdminUserManagementService._format_user_with_status(user)
            
        except ValidationError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error activating student {student_id}: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to activate student: {str(e)}")

    @staticmethod
    def ban_student(student_id, reason=None, ban_duration_hours=None):
        """
        Ban a student account
        
        Args:
            student_id: UUID of student user
            reason: Reason for banning
            ban_duration_hours: Duration in hours (None for permanent)
            
        Returns:
            dict: Updated user data
            
        Raises:
            ValidationError: If student not found
        """
        try:
            user = AdminUserManagementService._get_student_by_id(student_id)
            
            account_status = user.account_status
            ban_expires_at = None
            
            if not account_status:
                account_status = UserAccountStatus(
                    user_id=student_id,
                    is_active=False,
                    is_banned=True,
                    ban_reason=reason,
                    banned_at=datetime.utcnow()
                )
                if ban_duration_hours:
                    from datetime import timedelta
                    ban_expires_at = datetime.utcnow() + timedelta(hours=ban_duration_hours)
                    account_status.ban_expires_at = ban_expires_at
                db.session.add(account_status)
            else:
                account_status.is_banned = True
                account_status.is_active = False
                account_status.ban_reason = reason
                account_status.banned_at = datetime.utcnow()
                if ban_duration_hours:
                    from datetime import timedelta
                    ban_expires_at = datetime.utcnow() + timedelta(hours=ban_duration_hours)
                    account_status.ban_expires_at = ban_expires_at
                else:
                    account_status.ban_expires_at = None
                account_status.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Student {student_id} banned by admin. Reason: {reason}")
            
            # Send ban notification
            try:
                recipient_name = f"{user.first_name} {user.last_name}".strip()
                banned_at = account_status.banned_at if account_status.banned_at else datetime.utcnow()
                support_url = f"{current_app.config.get('SUPPORT_URL', 'http://localhost:5173')}/support"
                
                _send_notification_safely(
                    'send_student_account_banned',
                    user_id=student_id,
                    recipient_name=recipient_name,
                    ban_reason=reason,
                    banned_at=banned_at,
                    ban_expires_at=ban_expires_at,
                    support_url=support_url
                )
            except Exception as e:
                logger.error(f"Error sending ban notification: {str(e)}", exc_info=True)
            
            return AdminUserManagementService._format_user_with_status(user)
            
        except ValidationError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error banning student {student_id}: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to ban student: {str(e)}")

    # ==================== TEACHERS MANAGEMENT ====================

    @staticmethod
    def list_teachers(status_filter=None, page=1, limit=10):
        """
        List all teachers with optional status filtering
        
        Args:
            status_filter: Filter by status - 'active', 'pending', 'banned' or None for all
            page: Page number for pagination (1-indexed)
            limit: Number of records per page
            
        Returns:
            dict: {
                'total': int,
                'page': int,
                'limit': int,
                'teachers': list[dict]
            }
            
        Raises:
            ValidationError: If invalid status_filter provided
        """
        try:
            # Valid status filters
            valid_statuses = ['active', 'pending', 'banned']
            
            if status_filter and status_filter not in valid_statuses:
                raise ValidationError(
                    f"Invalid status filter. Must be one of: {', '.join(valid_statuses)}"
                )
            
            # Start query with teacher role users
            query = db.session.query(User).join(
                UserRole, User.user_id == UserRole.user_id
            ).join(
                Role, UserRole.role_id == Role.role_id
            ).filter(Role.role_name == 'teacher')
            
            # Apply status filter if provided
            if status_filter:
                if status_filter == 'active':
                    query = query.filter(
                        db.exists(
                            db.session.query(1).filter(
                                (UserAccountStatus.user_id == User.user_id),
                                (UserAccountStatus.is_active == True),
                                (UserAccountStatus.is_banned == False)
                            )
                        )
                    )
                elif status_filter == 'pending':
                    query = query.filter(
                        db.exists(
                            db.session.query(1).filter(
                                (UserAccountStatus.user_id == User.user_id),
                                (UserAccountStatus.is_active == False)
                            )
                        )
                    )
                elif status_filter == 'banned':
                    query = query.filter(
                        db.exists(
                            db.session.query(1).filter(
                                (UserAccountStatus.user_id == User.user_id),
                                (UserAccountStatus.is_banned == True)
                            )
                        )
                    )
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            teachers = query.offset(offset).limit(limit).all()
            
            # Format response
            teachers_data = [
                AdminUserManagementService._format_user_with_status(teacher)
                for teacher in teachers
            ]
            
            return {
                'total': total,
                'page': page,
                'limit': limit,
                'teachers': teachers_data
            }
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error listing teachers: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to list teachers: {str(e)}")

    @staticmethod
    def activate_teacher(teacher_id):
        """
        Activate a teacher account
        
        Args:
            teacher_id: UUID of teacher user
            
        Returns:
            dict: Updated user data
            
        Raises:
            ValidationError: If teacher not found
        """
        try:
            user = AdminUserManagementService._get_teacher_by_id(teacher_id)
            
            # Check if this is first-time activation
            account_status = user.account_status
            is_first_activation = False
            
            if not account_status:
                account_status = UserAccountStatus(
                    user_id=teacher_id,
                    is_active=True,
                    is_banned=False
                )
                db.session.add(account_status)
                is_first_activation = True
            else:
                is_first_activation = not account_status.is_active
                account_status.is_active = True
                account_status.is_banned = False
                account_status.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Teacher {teacher_id} activated by admin")
            
            # Send appropriate notification
            try:
                recipient_name = f"{user.first_name} {user.last_name}".strip()
                dashboard_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:5173')}/dashboard"
                support_url = f"{current_app.config.get('SUPPORT_URL', 'http://localhost:5173')}/support"
                
                if is_first_activation:
                    # Send welcome message for first-time approval
                    _send_notification_safely(
                        'send_teacher_welcome_first_approval',
                        user_id=teacher_id,
                        recipient_name=recipient_name,
                        dashboard_url=dashboard_url,
                        support_url=support_url
                    )
                else:
                    # Send standard activation notification
                    _send_notification_safely(
                        'send_teacher_account_activated',
                        user_id=teacher_id,
                        recipient_name=recipient_name,
                        dashboard_url=dashboard_url,
                        support_url=support_url
                    )
            except Exception as e:
                logger.error(f"Error sending activation notification: {str(e)}", exc_info=True)
            
            return AdminUserManagementService._format_user_with_status(user)
            
        except ValidationError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error activating teacher {teacher_id}: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to activate teacher: {str(e)}")

    @staticmethod
    def ban_teacher(teacher_id, reason=None, ban_duration_hours=None):
        """
        Ban a teacher account
        
        Args:
            teacher_id: UUID of teacher user
            reason: Reason for banning
            ban_duration_hours: Duration in hours (None for permanent)
            
        Returns:
            dict: Updated user data
            
        Raises:
            ValidationError: If teacher not found
        """
        try:
            user = AdminUserManagementService._get_teacher_by_id(teacher_id)
            
            account_status = user.account_status
            ban_expires_at = None
            
            if not account_status:
                account_status = UserAccountStatus(
                    user_id=teacher_id,
                    is_active=False,
                    is_banned=True,
                    ban_reason=reason,
                    banned_at=datetime.utcnow()
                )
                if ban_duration_hours:
                    from datetime import timedelta
                    ban_expires_at = datetime.utcnow() + timedelta(hours=ban_duration_hours)
                    account_status.ban_expires_at = ban_expires_at
                db.session.add(account_status)
            else:
                account_status.is_banned = True
                account_status.is_active = False
                account_status.ban_reason = reason
                account_status.banned_at = datetime.utcnow()
                if ban_duration_hours:
                    from datetime import timedelta
                    ban_expires_at = datetime.utcnow() + timedelta(hours=ban_duration_hours)
                    account_status.ban_expires_at = ban_expires_at
                else:
                    account_status.ban_expires_at = None
                account_status.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Teacher {teacher_id} banned by admin. Reason: {reason}")
            
            # Send ban notification
            try:
                recipient_name = f"{user.first_name} {user.last_name}".strip()
                banned_at = account_status.banned_at if account_status.banned_at else datetime.utcnow()
                support_url = f"{current_app.config.get('SUPPORT_URL', 'http://localhost:5173')}/support"
                
                _send_notification_safely(
                    'send_teacher_account_banned',
                    user_id=teacher_id,
                    recipient_name=recipient_name,
                    ban_reason=reason,
                    banned_at=banned_at,
                    ban_expires_at=ban_expires_at,
                    support_url=support_url
                )
            except Exception as e:
                logger.error(f"Error sending ban notification: {str(e)}", exc_info=True)
            
            return AdminUserManagementService._format_user_with_status(user)
            
        except ValidationError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error banning teacher {teacher_id}: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to ban teacher: {str(e)}")

    # ==================== HELPER METHODS ====================

    @staticmethod
    def _get_student_by_id(student_id):
        """
        Get student user by ID, validating they have student role
        
        Args:
            student_id: UUID of student
            
        Returns:
            User: Student user object
            
        Raises:
            ValidationError: If student not found or not a student
        """
        user = User.query.filter_by(user_id=student_id).first()
        
        if not user:
            raise ValidationError(f"Student with ID {student_id} not found")
        
        # Verify user has student role
        has_student_role = db.session.query(UserRole).join(
            Role, UserRole.role_id == Role.role_id
        ).filter(
            (UserRole.user_id == student_id) & (Role.role_name == 'student')
        ).first()
        
        if not has_student_role:
            raise ValidationError(f"User {student_id} is not a student")
        
        return user

    @staticmethod
    def _get_teacher_by_id(teacher_id):
        """
        Get teacher user by ID, validating they have teacher role
        
        Args:
            teacher_id: UUID of teacher
            
        Returns:
            User: Teacher user object
            
        Raises:
            ValidationError: If teacher not found or not a teacher
        """
        user = User.query.filter_by(user_id=teacher_id).first()
        
        if not user:
            raise ValidationError(f"Teacher with ID {teacher_id} not found")
        
        # Verify user has teacher role
        has_teacher_role = db.session.query(UserRole).join(
            Role, UserRole.role_id == Role.role_id
        ).filter(
            (UserRole.user_id == teacher_id) & (Role.role_name == 'teacher')
        ).first()
        
        if not has_teacher_role:
            raise ValidationError(f"User {teacher_id} is not a teacher")
        
        return user

    @staticmethod
    def _format_user_with_status(user):
        """
        Format user data with account status information
        
        Args:
            user: User object
            
        Returns:
            dict: Formatted user data
        """
        user_dict = {
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'email_verified': user.email_verified,
            'phone_verified': user.phone_verified,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
        }
        
        # Add account status if available
        if user.account_status:
            user_dict['account_status'] = {
                'is_active': user.account_status.is_active,
                'is_banned': user.account_status.is_banned,
                'ban_reason': user.account_status.ban_reason,
                'banned_at': user.account_status.banned_at.isoformat() if user.account_status.banned_at else None,
                'ban_expires_at': user.account_status.ban_expires_at.isoformat() if user.account_status.ban_expires_at else None,
            }
        else:
            user_dict['account_status'] = {
                'is_active': True,
                'is_banned': False,
                'ban_reason': None,
                'banned_at': None,
                'ban_expires_at': None,
            }
        
        # Add user roles
        user_roles = UserRole.query.filter_by(user_id=user.user_id).all()
        user_dict['roles'] = [
            role.role.role_name for role in user_roles if role.role
        ]
        
        return user_dict
