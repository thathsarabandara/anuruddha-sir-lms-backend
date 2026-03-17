"""
Student Management Service
Handles operations for managing student accounts
including listing, activating, and banning students
"""

import logging
from datetime import datetime

from flask import current_app

from app import db
from app.exceptions import ValidationError, AuthorizationError
from app.models import User, UserAccountStatus, UserRole, Role, StudentProfile
from app.services.health.base_service import BaseService
from datetime import datetime

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


class StudentManagementService(BaseService):
    """Service for student management operations"""

    # ==================== STUDENTS MANAGEMENT ====================
    @staticmethod
    def get_student_statistics():
        """
        Get statistics about student accounts
        
        Returns:
            dict: {
                'total_students': int,
                'active_students': int,
                'pending_students': int,
                'banned_students': int
            }
        """
        try:
            total_students = db.session.query(User).join(
                UserRole, User.user_id == UserRole.user_id
            ).join(
                Role, UserRole.role_id == Role.role_id
            ).filter(Role.role_name == 'student').count()
            
            active_students = db.session.query(User).join(
                UserRole, User.user_id == UserRole.user_id
            ).join(
                Role, UserRole.role_id == Role.role_id
            ).join(
                UserAccountStatus, User.user_id == UserAccountStatus.user_id
            ).filter(
                (Role.role_name == 'student') &
                (UserAccountStatus.is_active == True) &
                (UserAccountStatus.is_banned == False)
            ).count()
            
            pending_students = db.session.query(User).join(
                UserRole, User.user_id == UserRole.user_id
            ).join(
                Role, UserRole.role_id == Role.role_id
            ).join(
                UserAccountStatus, User.user_id == UserAccountStatus.user_id
            ).filter(
                (Role.role_name == 'student') &
                (UserAccountStatus.is_active == False)&
                (UserAccountStatus.is_banned == False)
            ).count()
            
            banned_students = db.session.query(User).join(
                UserRole, User.user_id == UserRole.user_id
            ).join(
                Role, UserRole.role_id == Role.role_id
            ).join(
                UserAccountStatus, User.user_id == UserAccountStatus.user_id
            ).filter(
                (Role.role_name == 'student') &
                (UserAccountStatus.is_banned == True)&
                (UserAccountStatus.is_active == True)
            ).count()
            
            return {
                'total_students': total_students,
                'active_students': active_students,
                'pending_students': pending_students,
                'banned_students': banned_students
            }
            
        except Exception as e:
            logger.error(f"Error getting student statistics: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to get student statistics: {str(e)}")


    @staticmethod
    def list_students(search_query=None, status_filter="all", page=1, limit=10):
        """
        List all students with optional status filtering
        
        Args:
            search_query: Search query for student names or emails
            status_filter: Filter by status - 'all', 'active', 'pending', 'banned' or None for all
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
            valid_statuses = ['all', 'active', 'pending', 'banned']
            
            if status_filter and status_filter not in valid_statuses:
                raise ValidationError(
                    f"Invalid status filter. Must be one of: {', '.join(valid_statuses)}"
                )
            
            # Start query with student role users, joined with account status
            query = db.session.query(User).join(
                UserRole, User.user_id == UserRole.user_id
            ).join(
                Role, UserRole.role_id == Role.role_id
            ).outerjoin(
                UserAccountStatus, User.user_id == UserAccountStatus.user_id
            ).filter(Role.role_name == 'student')
            
            # Apply search filter if provided
            if search_query:
                query = query.filter(
                    (User.first_name.ilike(f"%{search_query}%")) |
                    (User.last_name.ilike(f"%{search_query}%")) |
                    (User.email.ilike(f"%{search_query}%"))
                )
            
            # Apply status filter if provided
            if status_filter:
                if status_filter == 'all':
                    # No additional filtering needed for 'all'
                    pass
                elif status_filter == 'active':
                    query = query.filter(
                        (UserAccountStatus.is_active == True) &
                        (UserAccountStatus.is_banned == False)
                    )
                elif status_filter == 'pending':
                    query = query.filter(
                        (UserAccountStatus.is_active == False) &
                        (UserAccountStatus.is_banned == False)
                    )
                elif status_filter == 'banned':
                    query = query.filter(
                        (UserAccountStatus.is_active == True) &
                        (UserAccountStatus.is_banned == True)
                    )
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            students = query.offset(offset).limit(limit).all()
            
            # Format response
            students_data = [
                StudentManagementService._format_user_with_status(student)
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
            user = StudentManagementService._get_student_by_id(student_id)
            
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
                support_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:5173')}/support"
                
                if is_first_activation:
                    # Send welcome message for first-time approval
                    _send_notification_safely(
                        'send_student_welcome_first_approval',
                        user_id=student_id,
                        username=user.username,
                        dashboard_url=dashboard_url,
                        support_url=support_url
                    )
                else:
                    # Send standard activation notification
                    _send_notification_safely(
                        'send_student_account_activated',
                        user_id=student_id,
                        username=user.username,
                        dashboard_url=dashboard_url,
                        support_url=support_url
                    )
            except Exception as e:
                logger.error(f"Error sending activation notification: {str(e)}", exc_info=True)
            
            return StudentManagementService._format_user_with_status(user)
            
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
            user = StudentManagementService._get_student_by_id(student_id)
            
            account_status = user.account_status
            ban_expires_at = None
            
            if not account_status:
                account_status = UserAccountStatus(
                    user_id=student_id,
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
                support_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:5173')}/support"
                
                _send_notification_safely(
                    'send_student_account_banned',
                    user_id=student_id,
                    username=user.username,
                    ban_reason=reason,
                    banned_at=banned_at,
                    ban_expires_at=ban_expires_at,
                    support_url=support_url
                )
            except Exception as e:
                logger.error(f"Error sending ban notification: {str(e)}", exc_info=True)
            
            return StudentManagementService._format_user_with_status(user)
            
        except ValidationError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error banning student {student_id}: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to ban student: {str(e)}")


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
    def _format_user_with_status(user):
        """
        Format user data with account status information
        
        Args:
            user: User object
            
        Returns:
            dict: Formatted user data
        """
        student_profile = StudentProfile.query.filter_by(user_id=user.user_id).first()
        
        user_dict = {
            'id': user.user_id,  # Add id field for frontend compatibility
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': f"{user.first_name} {user.last_name}",
            'phone': user.phone,
            'profile_picture': user.profile_picture,
            'bio': user.bio,
            'email_verified': user.email_verified,
            'phone_verified': user.phone_verified,
            'date_of_birth': student_profile.date_of_birth.isoformat() if student_profile and student_profile.date_of_birth else None,
            'grade_level': student_profile.grade_level if student_profile else None,
            'school': student_profile.school if student_profile else None,
            'address': student_profile.address if student_profile else None,
            'parent_name': student_profile.parent_name if student_profile else None,
            'parent_contact': student_profile.parent_contact if student_profile else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
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
        user_dict['roles'] = [role.role.role_name for role in user_roles if role.role]
        
        return user_dict

    # ==================== ADMIN STUDENT CREATE & EDIT ====================

    @staticmethod
    def create_verified_student(first_name, last_name, email, phone=None, date_of_birth=None,
                               grade_level=None, school=None, address=None, parent_name=None, 
                               parent_contact=None):
        """
        Create a new verified student account directly (admin only)

        Args:
            first_name: Student's first name
            last_name: Student's last name
            email: Student's email (must be unique)
            phone: Optional phone number
            date_of_birth: Optional DOB (YYYY-MM-DD)
            grade_level: Optional grade level
            school: Optional school name
            address: Optional address
            parent_name: Optional parent name
            parent_contact: Optional parent contact

        Returns:
            dict: Created student with temporary password

        Raises:
            ValidationError: If required fields missing or email exists
        """
        try:
            import uuid
            import secrets
            from werkzeug.security import generate_password_hash

            # Validate required fields
            if not first_name or not first_name.strip():
                raise ValidationError("First name is required")
            if not last_name or not last_name.strip():
                raise ValidationError("Last name is required")
            if not email or not email.strip():
                raise ValidationError("Email is required")

            # Check email uniqueness
            existing_user = User.query.filter_by(email=email.lower()).first()
            if existing_user:
                raise ValidationError("Email already exists")

            # Generate temporary password
            temp_password = secrets.token_urlsafe(12)
            password_hash = generate_password_hash(temp_password)

            # Generate username
            user_id = str(uuid.uuid4())
            username = f"{first_name.lower()}_{user_id[-4:]}"

            # Create user
            user = User(
                user_id=user_id,
                username=username,
                email=email.lower(),
                password_hash=password_hash,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                phone=phone,
                email_verified=True,
                phone_verified=bool(phone)
            )

            db.session.add(user)
            db.session.flush()

            # Assign student role
            try:
                student_role = Role.query.filter_by(role_name='student').first()
                if student_role:
                    user_role = UserRole(user_id=user_id, role_id=student_role.role_id)
                    db.session.add(user_role)
            except Exception as e:
                logger.warning(f"Failed to assign student role: {str(e)}")

            # Create student profile
            try:
                student_profile = StudentProfile(
                    user_id=user_id,
                    date_of_birth=datetime.strptime(date_of_birth, "%Y-%m-%d").date() if date_of_birth else None,
                    grade_level=grade_level,
                    school=school,
                    address=address,
                    parent_name=parent_name,
                    parent_contact=parent_contact
                )
                db.session.add(student_profile)
            except Exception as e:
                logger.warning(f"Failed to create student profile: {str(e)}")

            # Create account status
            account_status = UserAccountStatus(user_id=user_id, is_active=True, is_banned=False)
            db.session.add(account_status)

            db.session.commit()
            logger.info(f"Student created: {user_id}")

            # Send notifications
            _send_notification_safely(
                'send_student_account_created',
                user_id=user_id,
                username=username,
                email=email,
                temporary_password=temp_password,
                login_url=f"{current_app.config.get('FRONTEND_URL', 'http://localhost:5173')}/login",
                support_email="support@lms.example.com",
                support_phone="+1-800-000-0000"
            )

            return {
                'user_id': user_id,
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'temporary_password': temp_password,
                'message': 'Credentials sent to student via email and WhatsApp'
            }

        except ValidationError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating student: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to create student: {str(e)}")

    @staticmethod
    def reset_student_password(student_id, send_notification=True):
        """
        Reset student password and optionally send notification
        
        Args:
            student_id: Student user ID
            send_notification: Whether to send password reset notification
            
        Returns:
            dict: Updated student with new temporary password
            
        Raises:
            ValidationError: If student not found
        """
        try:
            import secrets
            from werkzeug.security import generate_password_hash

            user = User.query.filter_by(user_id=student_id).first()
            if not user:
                raise ValidationError(f"Student with ID {student_id} not found")

            # Generate new temporary password
            temp_password = secrets.token_urlsafe(12)
            user.password_hash = generate_password_hash(temp_password)
            db.session.commit()

            logger.info(f"Password reset for student {student_id}")

            if send_notification:
                _send_notification_safely(
                    'send_student_password_reset',
                    user_id=student_id,
                    username=user.username,
                    email=user.email,
                    temporary_password=temp_password,
                    login_url=f"{current_app.config.get('FRONTEND_URL', 'http://localhost:5173')}/login",
                    support_email="support@lms.example.com",
                    support_phone="+1-800-000-0000"
                )

            return {
                'user_id': student_id,
                'email': user.email,
                'username': user.username,
                'temporary_password': temp_password if not send_notification else None,
                'message': 'Password reset. New credentials sent to student.'
            }

        except ValidationError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resetting student password: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to reset password: {str(e)}")

    @staticmethod
    def edit_student_details(student_id, first_name=None, last_name=None, phone=None,
                            date_of_birth=None, grade_level=None, school=None, 
                            address=None, parent_name=None, parent_contact=None):
        """
        Edit student profile details
        
        Args:
            student_id: Student user ID
            first_name: First name
            last_name: Last name
            phone: Phone number
            date_of_birth: Date of birth (YYYY-MM-DD)
            grade_level: Grade level
            school: School name
            address: Address
            parent_name: Parent name
            parent_contact: Parent contact
            
        Returns:
            dict: Updated student data
            
        Raises:
            ValidationError: If student not found
        """
        try:
            user = User.query.filter_by(user_id=student_id).first()
            if not user:
                raise ValidationError(f"Student with ID {student_id} not found")

            # Update user fields
            if first_name:
                user.first_name = first_name.strip()
            if last_name:
                user.last_name = last_name.strip()
            if phone is not None:
                user.phone = phone
            if date_of_birth:
                user.date_of_birth = datetime.strptime(date_of_birth, "%Y-%m-%d").date()

            # Update student profile
            student_profile = StudentProfile.query.filter_by(user_id=student_id).first()
            if not student_profile:
                student_profile = StudentProfile(user_id=student_id)
                db.session.add(student_profile)

            if grade_level is not None:
                student_profile.grade_level = grade_level
            if school is not None:
                student_profile.school = school
            if address is not None:
                student_profile.address = address
            if parent_name is not None:
                student_profile.parent_name = parent_name
            if parent_contact is not None:
                student_profile.parent_contact = parent_contact

            user.updated_at = datetime.utcnow()
            db.session.commit()

            logger.info(f"Student details updated: {student_id}")
            return StudentManagementService._format_user_with_status(user)

        except ValidationError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error editing student details: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to edit student details: {str(e)}")
