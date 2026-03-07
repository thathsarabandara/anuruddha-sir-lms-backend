"""
Registration Service
Handles user registration workflow for students and teachers.

Registration flow
─────────────────
  1. User submits form  → is_active=False, approval_status='pending_verification'
  2. User verifies OTP  → email_verified=True, approval_status='pending_approval'
  3. Admin approves     → is_active=True,  approval_status='approved'
"""

import uuid
import logging
from datetime import date as date_type

from app import db
from app.exceptions import ConflictError, ValidationError
from app.models.auth import OTPRequest, User, UserAccountStatus
from app.models.auth.role import Role
from app.models.auth.user_role import UserRole
from app.models.users.student_profile import StudentProfile
from app.models.users.teacher_profile import TeacherProfile
from app.services.base_service import BaseService
from app.services.notifications.notification_service import NotificationService
from app.utils.auth import OTPManager, PasswordManager, SessionManager
from app.utils.file_handler import FileHandler
from app.utils.validators import validate_email, validate_password

logger = logging.getLogger(__name__)


class RegistrationService(BaseService):
    """Service for user registration"""

    @staticmethod
    def register_user(
        email,
        password,
        first_name,
        last_name,
        phone=None,
        profile_picture=None,
        role="student",
        # ── Student-specific ────────────────────────────────────────────────
        date_of_birth=None,      # str 'YYYY-MM-DD' or date object
        grade_level=None,
        school=None,
        address=None,
        parent_name=None,
        parent_contact=None,
        # ── Teacher-specific ────────────────────────────────────────────────
        qualifications=None,
        subjects_taught=None,    # list[str]
        years_of_experience=None,
        language_of_instruction=None,
        professional_bio=None,
    ):
        """
        Register a new student or teacher.

        After successful registration the user's email is unverified and the
        account is inactive.  Workflow continues as:
            OTP verify  → approval_status='pending_approval'
            Admin OK    → approval_status='approved', is_active=True

        Returns:
            tuple: (user_dict, verification_token, otp_code)

        Raises:
            ValidationError: Invalid input
            ConflictError:   Email already registered
        """
        # ── Basic validation ─────────────────────────────────────────────────
        validate_email(email)
        PasswordManager.validate_password_strength(password)

        if not first_name or not last_name:
            raise ValidationError("First name and last name are required")

        if role not in ("student", "teacher"):
            raise ValidationError("role must be 'student' or 'teacher'")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            raise ConflictError("Email already registered")

        role_record = Role.query.filter_by(role_name=role).first()
        if not role_record:
            raise ValidationError("Specified role does not exist in the database")

        try:
            # ── Unique user ID + username ─────────────────────────────────
            user_id = str(uuid.uuid4())
            username = f"{first_name.lower()}_{user_id[-4:]}"
            while User.query.filter_by(username=username).first():
                user_id = str(uuid.uuid4())
                username = f"{first_name.lower()}_{user_id[-4:]}"

            # ── Handle profile picture upload ──────────────────────────────
            final_profile_picture = profile_picture
            if not profile_picture:
                try:
                    # Save uploaded profile picture
                    relative_path = FileHandler.save_profile_picture(
                        profile_picture, username, role=role
                    )
                    # Convert to URL format
                    final_profile_picture = FileHandler.get_file_url(relative_path)
                    logger.info(f"Profile picture uploaded for user {username}: {relative_path}")
                except Exception as e:
                    logger.warning(f"Failed to save profile picture: {str(e)}. Continuing without picture.")
                    # Don't fail registration if picture upload fails
                    final_profile_picture = None

            # ── Core user record ──────────────────────────────────────────
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=PasswordManager.hash_password(password),
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                profile_picture=final_profile_picture,
                email_verified=False,
            )

            # ── Account status (pending_verification) ─────────────────────
            account_status = UserAccountStatus(
                user_id=user_id,
                is_active=False,
                is_banned=False,
            )

            # ── Role assignment ───────────────────────────────────────────
            userrole = UserRole(user_id=user_id, role_id=role_record.role_id)

            # ── Role-specific profile ─────────────────────────────────────
            role_profile = None
            if role == "student":
                # Parse date_of_birth if supplied as string
                dob = None
                if date_of_birth:
                    if isinstance(date_of_birth, date_type):
                        dob = date_of_birth
                    else:
                        try:
                            from datetime import datetime
                            dob = datetime.strptime(str(date_of_birth), "%Y-%m-%d").date()
                        except ValueError:
                            raise ValidationError(
                                "date_of_birth must be in YYYY-MM-DD format"
                            )

                role_profile = StudentProfile(
                    user_id=user_id,
                    date_of_birth=dob,
                    grade_level=grade_level,
                    school=school,
                    address=address,
                    parent_name=parent_name,
                    parent_contact=parent_contact,
                )

            elif role == "teacher":
                profile = TeacherProfile(
                    user_id=user_id,
                    qualifications=qualifications,
                    years_of_experience=years_of_experience,
                    language_of_instruction=language_of_instruction,
                    professional_bio=professional_bio,
                    address=address,
                )
                if subjects_taught:
                    profile.set_subjects(
                        subjects_taught if isinstance(subjects_taught, list) else [subjects_taught]
                    )
                role_profile = profile

            # ── OTP / verification token ──────────────────────────────────
            otp_code = OTPManager.generate_otp_code()
            verification_token = OTPManager.generate_verification_token()
            otp_expiry = OTPManager.get_otp_expiry_time()

            # Determine OTP channel: use whatsapp if student passed whatsapp_number
            otp_channel = "both"
            otp_phone = phone

            otp_request = OTPRequest(
                user_id=user_id,
                email=email,
                phone=otp_phone,
                verification_token=verification_token,
                otp_code_hash=PasswordManager.hash_password(otp_code),
                purpose="registration",
                channel=otp_channel,
                expires_at=otp_expiry,
            )

            # ── Persist ───────────────────────────────────────────────────
            db.session.add(user)
            db.session.add(account_status)
            db.session.add(userrole)
            if role_profile:
                db.session.add(role_profile)
            db.session.add(otp_request)
            db.session.commit()

            # ── Send registration OTP notification (after commit) ─────────
            # Now the user exists in the database for the notification service to query
            try:
                NotificationService().send_register_otp(
                    user_id=user_id,
                    otp_code=otp_code,
                    message_type="OTP",
                    priority="HIGH",
                    channels=['email', 'whatsapp'] if otp_channel == "both" else [otp_channel],
                )
            except Exception as notification_error:
                # Log the error but don't fail registration if notification fails
                logger.warning(f"Failed to send registration OTP notification: {str(notification_error)}")

            # ── Redis OTP cache ───────────────────────────────────────────
            SessionManager.store_otp(
                verification_token,
                {
                    "otp_id": otp_request.otp_id,
                    "user_id": user_id,
                    "email": email,
                    "phone": otp_phone,
                    "purpose": "registration",
                    "channel": otp_channel,
                    "created_at": str(otp_request.created_at),
                    "expires_at": str(otp_expiry),
                },
            )

            logger.info(f"User registered: {email} (role={role}, id={user_id})")

            return (
                {
                    "email": email,
                    "username": username,
                    "first_name": first_name,
                    "role": role,
                    "approval_status": "pending_verification",
                },
                verification_token,
                otp_code,
            )

        except (ConflictError, ValidationError):
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration failed: {str(e)}")
            raise ValidationError(f"Registration failed: {str(e)}")

    @staticmethod
    def resend_otp(verification_token, channel="both"):
        """
        Resend OTP to user

        Args:
            email: User email
            verification_token: Verification token
            channel: Delivery channel (email, whatsapp, both)

        Returns:
            tuple: (otp_code, remains_attempts)

        Raises:
            ValidationError: If token is invalid or expired
        """
        try:
            # Get OTP from Redis
            otp_data = SessionManager.get_otp(verification_token)
            if not otp_data:
                raise ValidationError("Invalid or expired verification token")

            # Check resend attempt limit (max 3 per 5 minutes)
            otp_request = OTPRequest.query.filter_by(
                verification_token=verification_token
            ).first()

            if not otp_request:
                raise ValidationError("Verification token not found")

            if otp_request.attempt_count >= 3:
                raise ValidationError("Maximum resend attempts exceeded. Please try again later.")

            # Generate new OTP
            otp_code = OTPManager.generate_otp_code()
            otp_hash = PasswordManager.hash_password(otp_code)

            # Update OTP request
            otp_request.otp_code_hash = otp_hash
            otp_request.attempt_count += 1
            otp_request.channel = channel

            user = User.query.filter_by(user_id=otp_request.user_id).first()

            db.session.commit()

            try:
                NotificationService().send_register_otp(
                    user_id=user.user_id,
                    otp_code=otp_code,
                    message_type="OTP Resend",
                    priority="HIGH",
                    channels=['email', 'whatsapp'] if channel == "both" else [channel],
                )
            except Exception as notification_error:
                logger.warning(f"Failed to send OTP resend notification: {str(notification_error)}")

            # Update Redis
            otp_data["channel"] = channel
            SessionManager.store_otp(verification_token, otp_data)

            logger.info(f"OTP resent for user {user.email}")

            return verification_token, 3 - otp_request.attempt_count

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Resend OTP failed: {str(e)}")
            raise ValidationError(f"Resend OTP failed: {str(e)}")
