"""
Notification Service
Handles sending of system notifications via multiple channels (Email, WhatsApp, In-App).
Uses Jinja2 templates for content generation.
"""

import logging
import os
from datetime import datetime
from flask import current_app
from jinja2 import Environment, FileSystemLoader

from app import db
from app.models.auth.user import User
from app.models.notifications.notification_preferences import NotificationPreferences
from app.models.notifications.notification_type_preferences import NotificationTypePreferences
from app.services.notifications.channels.email_channel import EmailChannel
from app.services.notifications.channels.whatsapp_channel import WhatsAppChannel
from app.services.notifications.channels.in_app_channel import InAppChannel

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for managing and sending system notifications.
    Replaces the old database-driven template system with file-based Jinja2 templates.
    """

    def __init__(self, app=None):
        """
        Initialize the notification service.
        
        Args:
            app: Flask application instance (optional)
        """
        self.app = app
        self.env = None
        self.email_channel = None
        self.whatsapp_channel = None
        self.in_app_channel = None
        
        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize service with application context.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        template_dir = os.path.join(app.root_path, 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
        # Initialize channels
        # Note: These channels might require current_app context during initialization
        # if they access config immediately.
        with app.app_context():
            self.email_channel = EmailChannel()
            self.whatsapp_channel = WhatsAppChannel()
            self.in_app_channel = InAppChannel()

    def _send_notification(self, template_name, user_id, variables, message_type=None, priority=None, channels=None):
        """
        Internal method to render templates and send to enabled channels.
        
        Args:
            template_name: Base name of the template (e.g. 'enrollment_confirmation')
            user_id: ID of the recipient user
            variables: Dictionary of variables for template rendering
            message_type: Type of message (e.g. 'enrollment_confirmation')
            priority: Priority level for WhatsApp messages
            channels: List of predefined channels to use (e.g. ['email', 'whatsapp']).
                     If None, uses user preferences. If specified, overrides preferences.
        Returns:
            bool: True if processing initiated successfully, False otherwise
        """
        try:
            # Ensure we have channels initialized
            if not self.env:
                if current_app:
                    self.init_app(current_app)
                else:
                    logger.error("NotificationService not initialized with app context")
                    return False

            # Fetch user
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found for notification {template_name}")
                return False

            # Add generic variables
            if 'recipient_name' not in variables:
                variables['recipient_name'] = f"{user.first_name} {user.last_name}"
            variables['user_email'] = user.email
            variables['user_phone'] = user.phone
            
            # Add footer variables if not already provided (required by email base template)
            if 'platform_url' not in variables:
                variables['platform_url'] = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
            if 'unsubscribe_url' not in variables:
                variables['unsubscribe_url'] = f"{variables['platform_url']}/unsubscribe"
            if 'preferences_url' not in variables:
                variables['preferences_url'] = f"{variables['platform_url']}/notifications/preferences"
            if 'current_year' not in variables:
                variables['current_year'] = datetime.now().year

            # Fetch user preferences
            prefs = NotificationPreferences.query.filter_by(user_id=user_id).first()
            
            # If channels are predefined, use them. Otherwise use user preferences.
            if channels:
                # Normalize channel names to lowercase
                channels = [ch.lower() for ch in channels]
                email_enabled = 'email' in channels and bool(user.email)
                sms_enabled = 'whatsapp' in channels and bool(user.phone)
                in_app_enabled = 'in_app' in channels
            else:
                # Determine enabled channels (Default: Email=True, SMS/WA=False, In-App=True)
                email_enabled = True
                sms_enabled = False
                in_app_enabled = True
                
                if prefs:
                    email_enabled = prefs.email_enabled
                    sms_enabled = prefs.sms_enabled
                    in_app_enabled = prefs.in_app_enabled

                # Check for type-specific preferences (overrides global if stricter or just checks specific settings)
                # Typically, if global is disabled, type is disabled.
                # If global is enabled, type can disable it.
                type_pref = NotificationTypePreferences.query.filter_by(
                    user_id=user_id,
                    notification_type=template_name
                ).first()

                if type_pref:
                    # If preference record exists, use its values combined with global switch?
                    # Usually type preference is an override.
                    # But if global "Enable Email" is off, specific emails shouldn't be sent.
                    # So we AND them or use global as master switch.
                    email_enabled = email_enabled and type_pref.email
                    # Map global sms_enabled to type whatsapp
                    sms_enabled = sms_enabled and type_pref.whatsapp
                    in_app_enabled = in_app_enabled and type_pref.in_app

            # ------------------------------------------------------------------
            # 1. Email Channel
            # ------------------------------------------------------------------
            if email_enabled and user.email:
                try:
                    # Load template: notifications/email/{template_name}.html
                    template_path = f"notifications/email/{template_name}.html"
                    html_content = None
                    plain_text_content = None
                    subject = "Notification"
                    
                    try:
                        template = self.env.get_template(template_path)
                        # Render HTML content
                        html_content = template.render(**variables)
                        
                        module = template.make_module(variables)
                        subject = getattr(module, 'subject', 'Notification')
                        
                        # Handle subject interpolation if it contains {{ variables }}
                        if '{{' in subject:
                            subject = self.env.from_string(subject).render(**variables)
                    except Exception as template_error:
                        logger.warning(f"Email template not found for {template_name}: {template_path}. Skipping email.")
                        html_content = None
                    
                    # Try to render plain text version if it exists
                    try:
                        text_template_path = f"notifications/email/{template_name}.txt"
                        text_template = self.env.get_template(text_template_path)
                        plain_text_content = text_template.render(**variables)
                    except Exception:
                        # Plain text template not available, that's okay
                        pass
                    
                    if html_content:
                        # Send with HTML content (and optional plain text fallback)
                        self.email_channel.send(
                            recipient=user.email,
                            subject=subject,
                            content=plain_text_content,  # Plain text fallback
                            html_content=html_content
                        )
                        logger.info(f"Email notification {template_name} sent to {user.email}")
                except Exception as e:
                    logger.error(f"Error sending email {template_name} to {user.email}: {e}")

            # ------------------------------------------------------------------
            # 2. WhatsApp Channel
            # ------------------------------------------------------------------
            if sms_enabled and user.phone:
                try:
                    # Load template: notifications/whatsapp/{template_name}.txt
                    template_path = f"notifications/whatsapp/{template_name}.txt"
                    template = None
                    try:
                        template = self.env.get_template(template_path)
                    except Exception as template_error:
                        logger.warning(f"WhatsApp template not found for {template_name}: {template_path}. Skipping WhatsApp.")
                    
                    if template:
                        content = template.render(**variables)
                        
                        # Get messageType and priority from variables if provided, otherwise auto-determine
                        message_type = variables.get("messageType")
                        priority = variables.get("priority")
                        
                        # Only auto-assign if not explicitly provided
                        if not message_type:
                            message_type = "NOTIFICATION"  # Default
                            if template_name == "otp_verification" or "otp" in template_name.lower():
                                message_type = "OTP"
                            elif template_name == "password_reset_request" or "forgot_password" in template_name.lower():
                                message_type = "OTP"
                        
                        if not priority:
                            priority = "NORMAL"  # Default
                            if template_name == "otp_verification" or "otp" in template_name.lower():
                                priority = "HIGH"
                            elif template_name == "password_reset_request" or "forgot_password" in template_name.lower():
                                priority = "HIGH"
                            elif "alert" in template_name.lower() or "suspicious" in template_name.lower() or "locked" in template_name.lower():
                                priority = "HIGH"
                            elif "urgent" in template_name.lower():
                                priority = "HIGH"
                        
                        logger.info(f"Sending WhatsApp notification {template_name} to {user.phone} - MessageType: {message_type}, Priority: {priority}, ContentLength: {len(content)}")
                        
                        send_result = self.whatsapp_channel.send(
                            phone=user.phone,
                            content=content,
                            messageType=message_type,
                            priority=priority
                        )
                        
                        if send_result.get("status") == "sent":
                            logger.info(f"WhatsApp notification {template_name} sent to {user.phone}")
                        else:
                            logger.warning(f"WhatsApp notification {template_name} failed to send to {user.phone}: {send_result.get('error', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"Error sending whatsapp {template_name} to {user.phone}: {e}", exc_info=True)

            # ------------------------------------------------------------------
            # 3. In-App Channel
            # ------------------------------------------------------------------
            if in_app_enabled:
                try:
                    # Load template: notifications/in_app/{template_name}.jinja
                    template_path = f"notifications/in_app/{template_name}.jinja"
                    try:
                        template = self.env.get_template(template_path)
                    except Exception as template_error:
                        logger.warning(f"In-App template not found for {template_name}: {template_path}. Skipping in-app notification.")
                        template = None
                    
                    if template:
                        # Extract subject/title
                        module = template.make_module(variables)
                        subject = getattr(module, 'subject', 'Notification')
                        if '{{' in subject:
                            subject = self.env.from_string(subject).render(**variables)
                        
                        # Render body/content
                        # If template has a 'body' block, use it. Otherwise render whole file.
                        if 'body' in template.blocks:
                            ctx = template.new_context(variables)
                            content = ''.join(template.blocks['body'](ctx))
                        else:
                            content = template.render(**variables)
                        
                        content = content.strip()
                        
                        self.in_app_channel.send(
                            recipient=user_id,
                            content=content,
                            subject=subject,
                            title=subject,
                            notification_type=template_name,
                            # Add any derived action_url or resource info if available in variables
                            action_url=variables.get('action_url') or variables.get('url') or variables.get('link')
                        )
                        logger.info(f"In-App notification {template_name} sent to user {user_id}")
                except Exception as e:
                    logger.error(f"Error sending in-app {template_name}: {e}")

            return True

        except Exception as e:
            logger.error(f"Critical error in _send_notification: {e}")
            return False
        
    def send_register_otp(self, user_id, otp_code, expiry_minutes=None, message_type=None, priority=None, channels=None):
        """
        Send registration OTP notification.
        Variables: otp_code, expiry_minutes
        
        Args:
            user_id: ID of the recipient user
            otp_code: The OTP code to send
            expiry_minutes: Minutes the OTP is valid for (default: 5)
            message_type: WhatsApp message type (auto-determined if not provided)
            priority: WhatsApp priority level (auto-determined if not provided)
            channels: List of channels to use (e.g. ['email', 'whatsapp', 'in_app']).
                     If None, uses user preferences.
        """
        variables = {
            "otp_code": otp_code,
            "expiry_minutes": expiry_minutes or 5,
        }
        return self._send_notification('registration_otp', user_id, variables, message_type=message_type, priority=priority, channels=channels)
    
    def send_enrollment_confirmation(self, user_id, course_name, course_url, current_year, instructor_name, platform_url, preferences_url, recipient_name, start_date, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send enrollment_confirmation notification.
        Variables: course_name, course_url, current_year, instructor_name, platform_url, preferences_url, recipient_name, start_date, unsubscribe_url
        """
        variables = {
            'course_name': course_name,
            'course_url': course_url,
            'current_year': current_year,
            'instructor_name': instructor_name,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'start_date': start_date,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('enrollment_confirmation', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_enrollment_expiration_warning(self, user_id, course_name, course_url, current_year, days_remaining, expiry_date, platform_url, preferences_url, recipient_name, renew_url, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send enrollment_expiration_warning notification.
        Variables: course_name, course_url, current_year, days_remaining, expiry_date, platform_url, preferences_url, recipient_name, renew_url, unsubscribe_url
        """
        variables = {
            'course_name': course_name,
            'course_url': course_url,
            'current_year': current_year,
            'days_remaining': days_remaining,
            'expiry_date': expiry_date,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'renew_url': renew_url,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('enrollment_expiration_warning', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_course_invitation_confirmation(self, user_id, course_name, course_url, current_year, inviter_name, platform_url, preferences_url, recipient_name, registration_url, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send course_invitation_confirmation notification.
        Variables: course_name, course_url, current_year, inviter_name, platform_url, preferences_url, recipient_name, registration_url, unsubscribe_url
        """
        variables = {
            'course_name': course_name,
            'course_url': course_url,
            'current_year': current_year,
            'inviter_name': inviter_name,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'registration_url': registration_url,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('course_invitation_confirmation', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_enrollment_request_admin(self, user_id, course_name, current_year, platform_url, preferences_url, recipient_name, request_date, review_url, student_email, student_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send enrollment_request_admin notification.
        Variables: course_name, current_year, platform_url, preferences_url, recipient_name, request_date, review_url, student_email, student_name, unsubscribe_url
        """
        variables = {
            'course_name': course_name,
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'request_date': request_date,
            'review_url': review_url,
            'student_email': student_email,
            'student_name': student_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('enrollment_request_admin', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_enrollment_request_approved_rejected(self, user_id, course_name, course_url, current_year, platform_url, preferences_url, reason, recipient_name, status, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send enrollment_request_approved_rejected notification.
        Variables: course_name, course_url, current_year, platform_url, preferences_url, reason, recipient_name, status, unsubscribe_url
        """
        variables = {
            'course_name': course_name,
            'course_url': course_url,
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'reason': reason,
            'recipient_name': recipient_name,
            'status': status,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('enrollment_request_approved_rejected', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_welcome_new_enrollment(self, user_id, course_name, course_url, current_year, first_lesson_url, instructor_name, platform_url, preferences_url, recipient_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send welcome_new_enrollment notification.
        Variables: course_name, course_url, current_year, first_lesson_url, instructor_name, platform_url, preferences_url, recipient_name, unsubscribe_url
        """
        variables = {
            'course_name': course_name,
            'course_url': course_url,
            'current_year': current_year,
            'first_lesson_url': first_lesson_url,
            'instructor_name': instructor_name,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('welcome_new_enrollment', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_assignment_submitted_instructor(self, user_id, assignment_name, course_name, current_year, platform_url, preferences_url, recipient_name, student_name, submission_url, submitted_at, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send assignment_submitted_instructor notification.
        Variables: assignment_name, course_name, current_year, platform_url, preferences_url, recipient_name, student_name, submission_url, submitted_at, unsubscribe_url
        """
        variables = {
            'assignment_name': assignment_name,
            'course_name': course_name,
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'student_name': student_name,
            'submission_url': submission_url,
            'submitted_at': submitted_at,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('assignment_submitted_instructor', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_assignment_graded_student(self, user_id, assignment_name, course_name, current_year, feedback, grade, max_grade, platform_url, preferences_url, recipient_name, submission_url, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send assignment_graded_student notification.
        Variables: assignment_name, course_name, current_year, feedback, grade, max_grade, platform_url, preferences_url, recipient_name, submission_url, unsubscribe_url
        """
        variables = {
            'assignment_name': assignment_name,
            'course_name': course_name,
            'current_year': current_year,
            'feedback': feedback,
            'grade': grade,
            'max_grade': max_grade,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'submission_url': submission_url,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('assignment_graded_student', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_assignment_submitted_late_instructor(self, user_id, assignment_name, course_name, current_year, delay, due_date, platform_url, preferences_url, recipient_name, student_name, submission_url, submitted_at, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send assignment_submitted_late_instructor notification.
        Variables: assignment_name, course_name, current_year, delay, due_date, platform_url, preferences_url, recipient_name, student_name, submission_url, submitted_at, unsubscribe_url
        """
        variables = {
            'assignment_name': assignment_name,
            'course_name': course_name,
            'current_year': current_year,
            'delay': delay,
            'due_date': due_date,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'student_name': student_name,
            'submission_url': submission_url,
            'submitted_at': submitted_at,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('assignment_submitted_late_instructor', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_submission_comment_added(self, user_id, assignment_name, comment_preview, commenter_name, course_name, current_year, platform_url, preferences_url, recipient_name, submission_url, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send submission_comment_added notification.
        Variables: assignment_name, comment_preview, commenter_name, course_name, current_year, platform_url, preferences_url, recipient_name, submission_url, unsubscribe_url
        """
        variables = {
            'assignment_name': assignment_name,
            'comment_preview': comment_preview,
            'commenter_name': commenter_name,
            'course_name': course_name,
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'submission_url': submission_url,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('submission_comment_added', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_essay_question_graded(self, user_id, course_name, current_year, feedback, grade, lesson_name, lesson_url, max_grade, platform_url, preferences_url, recipient_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send essay_question_graded notification.
        Variables: course_name, current_year, feedback, grade, lesson_name, lesson_url, max_grade, platform_url, preferences_url, recipient_name, unsubscribe_url
        """
        variables = {
            'course_name': course_name,
            'current_year': current_year,
            'feedback': feedback,
            'grade': grade,
            'lesson_name': lesson_name,
            'lesson_url': lesson_url,
            'max_grade': max_grade,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('essay_question_graded', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_upcoming_due_date_reminder(self, user_id, assignment_name, course_name, current_year, due_date, platform_url, preferences_url, recipient_name, submission_url, time_until_due, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send upcoming_due_date_reminder notification.
        Variables: assignment_name, course_name, current_year, due_date, platform_url, preferences_url, recipient_name, submission_url, time_until_due, unsubscribe_url
        """
        variables = {
            'assignment_name': assignment_name,
            'course_name': course_name,
            'current_year': current_year,
            'due_date': due_date,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'submission_url': submission_url,
            'time_until_due': time_until_due,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('upcoming_due_date_reminder', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_past_due_date_reminder(self, user_id, assignment_name, course_name, current_year, due_date, overdue_by, platform_url, preferences_url, recipient_name, submission_url, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send past_due_date_reminder notification.
        Variables: assignment_name, course_name, current_year, due_date, overdue_by, platform_url, preferences_url, recipient_name, submission_url, unsubscribe_url
        """
        variables = {
            'assignment_name': assignment_name,
            'course_name': course_name,
            'current_year': current_year,
            'due_date': due_date,
            'overdue_by': overdue_by,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'submission_url': submission_url,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('past_due_date_reminder', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_activity_start_date_reminder(self, user_id, activity_name, activity_url, course_name, current_year, platform_url, preferences_url, recipient_name, start_date, time_until_start, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send activity_start_date_reminder notification.
        Variables: activity_name, activity_url, course_name, current_year, platform_url, preferences_url, recipient_name, start_date, time_until_start, unsubscribe_url
        """
        variables = {
            'activity_name': activity_name,
            'activity_url': activity_url,
            'course_name': course_name,
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'start_date': start_date,
            'time_until_start': time_until_start,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('activity_start_date_reminder', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_quiz_attempt_overdue_warning(self, user_id, course_name, current_year, due_date, platform_url, preferences_url, quiz_name, quiz_url, recipient_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send quiz_attempt_overdue_warning notification.
        Variables: course_name, current_year, due_date, platform_url, preferences_url, quiz_name, quiz_url, recipient_name, unsubscribe_url
        """
        variables = {
            'course_name': course_name,
            'current_year': current_year,
            'due_date': due_date,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'quiz_name': quiz_name,
            'quiz_url': quiz_url,
            'recipient_name': recipient_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('quiz_attempt_overdue_warning', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_quiz_submission_confirmation_student(self, user_id, course_name, current_year, platform_url, preferences_url, quiz_name, quiz_url, recipient_name, submitted_at, total_questions, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send quiz_submission_confirmation_student notification.
        Variables: course_name, current_year, platform_url, preferences_url, quiz_name, quiz_url, recipient_name, submitted_at, total_questions, unsubscribe_url
        """
        variables = {
            'course_name': course_name,
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'quiz_name': quiz_name,
            'quiz_url': quiz_url,
            'recipient_name': recipient_name,
            'submitted_at': submitted_at,
            'total_questions': total_questions,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('quiz_submission_confirmation_student', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_quiz_submission_notification_instructor(self, user_id, course_name, current_year, platform_url, preferences_url, quiz_name, recipient_name, student_name, submission_url, submitted_at, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send quiz_submission_notification_instructor notification.
        Variables: course_name, current_year, platform_url, preferences_url, quiz_name, recipient_name, student_name, submission_url, submitted_at, unsubscribe_url
        """
        variables = {
            'course_name': course_name,
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'quiz_name': quiz_name,
            'recipient_name': recipient_name,
            'student_name': student_name,
            'submission_url': submission_url,
            'submitted_at': submitted_at,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('quiz_submission_notification_instructor', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_quiz_graded_notification(self, user_id, course_name, current_year, max_score, passed, percentage, platform_url, preferences_url, quiz_name, quiz_url, recipient_name, score, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send quiz_graded_notification notification.
        Variables: course_name, current_year, max_score, passed, percentage, platform_url, preferences_url, quiz_name, quiz_url, recipient_name, score, unsubscribe_url
        """
        variables = {
            'course_name': course_name,
            'current_year': current_year,
            'max_score': max_score,
            'passed': passed,
            'percentage': percentage,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'quiz_name': quiz_name,
            'quiz_url': quiz_url,
            'recipient_name': recipient_name,
            'score': score,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('quiz_graded_notification', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_badge_awarded(self, user_id, awarded_at, badge_description, badge_name, badges_url, course_name, current_year, platform_url, preferences_url, recipient_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send badge_awarded notification.
        Variables: awarded_at, badge_description, badge_name, badges_url, course_name, current_year, platform_url, preferences_url, recipient_name, unsubscribe_url
        """
        variables = {
            'awarded_at': awarded_at,
            'badge_description': badge_description,
            'badge_name': badge_name,
            'badges_url': badges_url,
            'course_name': course_name,
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('badge_awarded', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_course_completion_certificate(self, user_id, certificate_id, certificate_url, completion_date, course_name, current_year, platform_url, preferences_url, recipient_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send course_completion_certificate notification.
        Variables: certificate_id, certificate_url, completion_date, course_name, current_year, platform_url, preferences_url, recipient_name, unsubscribe_url
        """
        variables = {
            'certificate_id': certificate_id,
            'certificate_url': certificate_url,
            'completion_date': completion_date,
            'course_name': course_name,
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('course_completion_certificate', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_ceus_earned(self, user_id, ceu_credits, ceus_url, course_name, current_year, platform_url, preferences_url, recipient_name, total_ceus, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send ceus_earned notification.
        Variables: ceu_credits, ceus_url, course_name, current_year, platform_url, preferences_url, recipient_name, total_ceus, unsubscribe_url
        """
        variables = {
            'ceu_credits': ceu_credits,
            'ceus_url': ceus_url,
            'course_name': course_name,
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'total_ceus': total_ceus,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('ceus_earned', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_new_badge_created(self, user_id, badge_description, badge_name, badge_url, course_name, created_by, current_year, platform_url, preferences_url, recipient_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send new_badge_created notification.
        Variables: badge_description, badge_name, badge_url, course_name, created_by, current_year, platform_url, preferences_url, recipient_name, unsubscribe_url
        """
        variables = {
            'badge_description': badge_description,
            'badge_name': badge_name,
            'badge_url': badge_url,
            'course_name': course_name,
            'created_by': created_by,
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('new_badge_created', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_feedback_review_submission(self, user_id, course_name, current_year, platform_url, preferences_url, rating, recipient_name, review_preview, review_url, reviewer_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send feedback_review_submission notification.
        Variables: course_name, current_year, platform_url, preferences_url, rating, recipient_name, review_preview, review_url, reviewer_name, unsubscribe_url
        """
        variables = {
            'course_name': course_name,
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'rating': rating,
            'recipient_name': recipient_name,
            'review_preview': review_preview,
            'review_url': review_url,
            'reviewer_name': reviewer_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('feedback_review_submission', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_new_forum_post_reply(self, user_id, course_name, current_year, forum_topic, forum_url, platform_url, poster_name, preferences_url, recipient_name, reply_preview, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send new_forum_post_reply notification.
        Variables: course_name, current_year, forum_topic, forum_url, platform_url, poster_name, preferences_url, recipient_name, reply_preview, unsubscribe_url
        """
        variables = {
            'course_name': course_name,
            'current_year': current_year,
            'forum_topic': forum_topic,
            'forum_url': forum_url,
            'platform_url': platform_url,
            'poster_name': poster_name,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'reply_preview': reply_preview,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('new_forum_post_reply', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_daily_forum_digest(self, user_id, current_year, digest_date, forum_url, new_replies_count, new_topics_count, platform_url, preferences_url, recipient_name, top_topics, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send daily_forum_digest notification.
        Variables: current_year, digest_date, forum_url, new_replies_count, new_topics_count, platform_url, preferences_url, recipient_name, top_topics, unsubscribe_url
        """
        variables = {
            'current_year': current_year,
            'digest_date': digest_date,
            'forum_url': forum_url,
            'new_replies_count': new_replies_count,
            'new_topics_count': new_topics_count,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'top_topics': top_topics,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('daily_forum_digest', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_new_personal_message(self, user_id, current_year, message_preview, message_url, platform_url, preferences_url, recipient_name, sender_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send new_personal_message notification.
        Variables: current_year, message_preview, message_url, platform_url, preferences_url, recipient_name, sender_name, unsubscribe_url
        """
        variables = {
            'current_year': current_year,
            'message_preview': message_preview,
            'message_url': message_url,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'sender_name': sender_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('new_personal_message', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_user_added_to_conversation(self, user_id, added_by, conversation_name, conversation_url, current_year, participants, platform_url, preferences_url, recipient_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send user_added_to_conversation notification.
        Variables: added_by, conversation_name, conversation_url, current_year, participants, platform_url, preferences_url, recipient_name, unsubscribe_url
        """
        variables = {
            'added_by': added_by,
            'conversation_name': conversation_name,
            'conversation_url': conversation_url,
            'current_year': current_year,
            'participants': participants,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('user_added_to_conversation', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_new_course_announcement(self, user_id, announcement_preview, announcement_title, announcement_url, course_name, current_year, platform_url, posted_by, preferences_url, recipient_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send new_course_announcement notification.
        Variables: announcement_preview, announcement_title, announcement_url, course_name, current_year, platform_url, posted_by, preferences_url, recipient_name, unsubscribe_url
        """
        variables = {
            'announcement_preview': announcement_preview,
            'announcement_title': announcement_title,
            'announcement_url': announcement_url,
            'course_name': course_name,
            'current_year': current_year,
            'platform_url': platform_url,
            'posted_by': posted_by,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('new_course_announcement', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_comment_learning_plan(self, user_id, comment_preview, commenter_name, current_year, learning_plan_name, plan_url, platform_url, preferences_url, recipient_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send comment_learning_plan notification.
        Variables: comment_preview, commenter_name, current_year, learning_plan_name, plan_url, platform_url, preferences_url, recipient_name, unsubscribe_url
        """
        variables = {
            'comment_preview': comment_preview,
            'commenter_name': commenter_name,
            'current_year': current_year,
            'learning_plan_name': learning_plan_name,
            'plan_url': plan_url,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('comment_learning_plan', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_site_backup_status(self, user_id, admin_url, backup_date, backup_duration, backup_size, backup_status, current_year, error_message, platform_url, preferences_url, recipient_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send site_backup_status notification.
        Variables: admin_url, backup_date, backup_duration, backup_size, backup_status, current_year, error_message, platform_url, preferences_url, recipient_name, unsubscribe_url
        """
        variables = {
            'admin_url': admin_url,
            'backup_date': backup_date,
            'backup_duration': backup_duration,
            'backup_size': backup_size,
            'backup_status': backup_status,
            'current_year': current_year,
            'error_message': error_message,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('site_backup_status', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_new_software_update(self, user_id, current_year, platform_url, preferences_url, recipient_name, release_notes, scheduled_maintenance, unsubscribe_url, update_url, version, message_type=None, priority=None, channels=None):
        """
        Send new_software_update notification.
        Variables: current_year, platform_url, preferences_url, recipient_name, release_notes, scheduled_maintenance, unsubscribe_url, update_url, version
        """
        variables = {
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'release_notes': release_notes,
            'scheduled_maintenance': scheduled_maintenance,
            'unsubscribe_url': unsubscribe_url,
            'update_url': update_url,
            'version': version,
        }
        return self._send_notification('new_software_update', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_critical_site_error(self, user_id, affected_service, current_year, error_message, error_time, error_type, error_url, platform_url, preferences_url, recipient_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send critical_site_error notification.
        Variables: affected_service, current_year, error_message, error_time, error_type, error_url, platform_url, preferences_url, recipient_name, unsubscribe_url
        """
        variables = {
            'affected_service': affected_service,
            'current_year': current_year,
            'error_message': error_message,
            'error_time': error_time,
            'error_type': error_type,
            'error_url': error_url,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('critical_site_error', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_batch_user_upload_summary(self, user_id, current_year, errors_summary, failed, platform_url, preferences_url, recipient_name, report_url, successful, total_users, unsubscribe_url, upload_date, message_type=None, priority=None, channels=None):
        """
        Send batch_user_upload_summary notification.
        Variables: current_year, errors_summary, failed, platform_url, preferences_url, recipient_name, report_url, successful, total_users, unsubscribe_url, upload_date
        """
        variables = {
            'current_year': current_year,
            'errors_summary': errors_summary,
            'failed': failed,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'report_url': report_url,
            'successful': successful,
            'total_users': total_users,
            'unsubscribe_url': unsubscribe_url,
            'upload_date': upload_date,
        }
        return self._send_notification('batch_user_upload_summary', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_password_reset_request(self, user_id, current_year, expiry_time, ip_address, platform_url, preferences_url, recipient_name, reset_url, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send password_reset_request notification.
        Variables: current_year, expiry_time, ip_address, platform_url, preferences_url, recipient_name, reset_url, unsubscribe_url
        """
        variables = {
            'current_year': current_year,
            'expiry_time': expiry_time,
            'ip_address': ip_address,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'reset_url': reset_url,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('password_reset_request', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_ilt_booking_confirmation(self, user_id, booking_status, booking_url, current_year, instructor_name, platform_url, preferences_url, recipient_name, session_date, session_name, session_time, unsubscribe_url, venue, message_type=None, priority=None, channels=None):
        """
        Send ilt_booking_confirmation notification.
        Variables: booking_status, booking_url, current_year, instructor_name, platform_url, preferences_url, recipient_name, session_date, session_name, session_time, unsubscribe_url, venue
        """
        variables = {
            'booking_status': booking_status,
            'booking_url': booking_url,
            'current_year': current_year,
            'instructor_name': instructor_name,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'session_date': session_date,
            'session_name': session_name,
            'session_time': session_time,
            'unsubscribe_url': unsubscribe_url,
            'venue': venue,
        }
        return self._send_notification('ilt_booking_confirmation', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_ilt_session_start_reminder(self, user_id, current_year, join_url, platform_url, preferences_url, recipient_name, session_date, session_name, session_time, time_until, unsubscribe_url, venue, message_type=None, priority=None, channels=None):
        """
        Send ilt_session_start_reminder notification.
        Variables: current_year, join_url, platform_url, preferences_url, recipient_name, session_date, session_name, session_time, time_until, unsubscribe_url, venue
        """
        variables = {
            'current_year': current_year,
            'join_url': join_url,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'session_date': session_date,
            'session_name': session_name,
            'session_time': session_time,
            'time_until': time_until,
            'unsubscribe_url': unsubscribe_url,
            'venue': venue,
        }
        return self._send_notification('ilt_session_start_reminder', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_ilt_session_joining_instructions(self, user_id, current_year, instructions, join_url, meeting_id, passcode, platform_url, preferences_url, recipient_name, session_date, session_name, session_time, unsubscribe_url, venue, message_type=None, priority=None, channels=None):
        """
        Send ilt_session_joining_instructions notification.
        Variables: current_year, instructions, join_url, meeting_id, passcode, platform_url, preferences_url, recipient_name, session_date, session_name, session_time, unsubscribe_url, venue
        """
        variables = {
            'current_year': current_year,
            'instructions': instructions,
            'join_url': join_url,
            'meeting_id': meeting_id,
            'passcode': passcode,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'session_date': session_date,
            'session_name': session_name,
            'session_time': session_time,
            'unsubscribe_url': unsubscribe_url,
            'venue': venue,
        }
        return self._send_notification('ilt_session_joining_instructions', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_ilt_waitlist_update(self, user_id, current_year, platform_url, preferences_url, recipient_name, session_date, session_name, session_url, unsubscribe_url, waitlist_position, waitlist_status, message_type=None, priority=None, channels=None):
        """
        Send ilt_waitlist_update notification.
        Variables: current_year, platform_url, preferences_url, recipient_name, session_date, session_name, session_url, unsubscribe_url, waitlist_position, waitlist_status
        """
        variables = {
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'session_date': session_date,
            'session_name': session_name,
            'session_url': session_url,
            'unsubscribe_url': unsubscribe_url,
            'waitlist_position': waitlist_position,
            'waitlist_status': waitlist_status,
        }
        return self._send_notification('ilt_waitlist_update', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_ilt_signup_prompt(self, user_id, available_seats, current_year, platform_url, preferences_url, recipient_name, session_date, session_name, session_url, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send ilt_signup_prompt notification.
        Variables: available_seats, current_year, platform_url, preferences_url, recipient_name, session_date, session_name, session_url, unsubscribe_url
        """
        variables = {
            'available_seats': available_seats,
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'session_date': session_date,
            'session_name': session_name,
            'session_url': session_url,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('ilt_signup_prompt', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_mentor_connection_request(self, user_id, current_year, message, platform_url, preferences_url, recipient_name, request_url, requester_name, requester_role, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send mentor_connection_request notification.
        Variables: current_year, message, platform_url, preferences_url, recipient_name, request_url, requester_name, requester_role, unsubscribe_url
        """
        variables = {
            'current_year': current_year,
            'message': message,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'request_url': request_url,
            'requester_name': requester_name,
            'requester_role': requester_role,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('mentor_connection_request', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_performance_review_reminder(self, user_id, current_year, due_date, platform_url, preferences_url, recipient_name, review_period, review_url, reviewee_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send performance_review_reminder notification.
        Variables: current_year, due_date, platform_url, preferences_url, recipient_name, review_period, review_url, reviewee_name, unsubscribe_url
        """
        variables = {
            'current_year': current_year,
            'due_date': due_date,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'review_period': review_period,
            'review_url': review_url,
            'reviewee_name': reviewee_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('performance_review_reminder', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_welcome_message(self, user_id, current_year, dashboard_url, platform_url, preferences_url, recipient_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send welcome_message notification.
        Variables: current_year, dashboard_url, platform_url, preferences_url, recipient_name, unsubscribe_url
        """
        variables = {
            'current_year': current_year,
            'dashboard_url': dashboard_url,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('welcome_message', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_otp_verification(self, user_id, current_year, expires_in, otp_code, platform_url, preferences_url, recipient_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send otp_verification notification.
        Variables: current_year, expires_in, otp_code, platform_url, preferences_url, recipient_name, unsubscribe_url
        """
        variables = {
            'current_year': current_year,
            'expires_in': expires_in,
            'otp_code': otp_code,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('otp_verification', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_forgot_password_otp(self, user_id, current_year, expires_in, otp_code, platform_url, preferences_url, recipient_name, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send forgot_password_otp notification.
        Variables: current_year, expires_in, otp_code, platform_url, preferences_url, recipient_name, unsubscribe_url
        """
        variables = {
            'current_year': current_year,
            'expires_in': expires_in,
            'otp_code': otp_code,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('forgot_password_otp', user_id, variables, message_type=message_type, priority=priority, channels=channels)


    def send_password_reset_confirmation(self, user_id, current_year, platform_url, preferences_url, recipient_name, reset_time, support_url, unsubscribe_url, message_type=None, priority=None, channels=None):
        """
        Send password_reset_confirmation notification.
        Variables: current_year, platform_url, preferences_url, recipient_name, reset_time, support_url, unsubscribe_url
        """
        variables = {
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
            'reset_time': reset_time,
            'support_url': support_url,
            'unsubscribe_url': unsubscribe_url,
        }
        return self._send_notification('password_reset_confirmation', user_id, variables, message_type=message_type, priority=priority, channels=channels)

    def send_registration_pending_admin_review(self, user_id, current_year, platform_url, preferences_url, recipient_name, message_type=None, priority=None, channels=None):
        """
        Send registration_pending_admin_review notification.
        Variables: current_year, platform_url, preferences_url, recipient_name
        """
        variables = {
            'current_year': current_year,
            'platform_url': platform_url,
            'preferences_url': preferences_url,
            'recipient_name': recipient_name,
        }
        return self._send_notification('registration_pending_admin_review', user_id, variables, message_type=message_type, priority=priority, channels=channels)

    def send_account_locked(self, user_id, failed_attempts, ban_duration_hours, ban_expires_at, recipient_name, support_url, message_type=None, priority=None, channels=None):
        """
        Send account_locked notification.
        Variables: failed_attempts, ban_duration_hours, ban_expires_at, recipient_name, support_url
        """
        ban_expires_str = (
            ban_expires_at.strftime("%Y-%m-%d %H:%M UTC") if ban_expires_at else "N/A"
        )
        variables = {
            'failed_attempts': str(failed_attempts),
            'ban_duration_hours': str(ban_duration_hours),
            'ban_expires_at': ban_expires_str,
            'recipient_name': recipient_name,
            'support_url': support_url,
        }
        return self._send_notification('account_locked', user_id, variables, message_type=message_type, priority=priority, channels=channels)

    def send_suspicious_login_alert(self, user_id, ip_address, user_agent, recipient_name, support_url, message_type=None, priority=None, channels=None):
        """
        Send suspicious_login_alert notification.
        Variables: ip_address, login_time, user_agent, recipient_name, support_url
        """
        from datetime import datetime
        login_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        variables = {
            'ip_address': ip_address,
            'login_time': login_time,
            'user_agent': user_agent,
            'recipient_name': recipient_name,
            'support_url': support_url,
        }
        return self._send_notification('suspicious_login_alert', user_id, variables, message_type=message_type, priority=priority, channels=channels)

    def send_student_account_activated(self, user_id, recipient_name, dashboard_url, support_url, message_type=None, priority=None, channels=None):
        """
        Send student_account_activated notification.
        Variables: recipient_name, dashboard_url, support_url
        """
        variables = {
            'recipient_name': recipient_name,
            'dashboard_url': dashboard_url,
            'support_url': support_url,
        }
        return self._send_notification('student_account_activated', user_id, variables, message_type=message_type, priority=priority, channels=channels)

    def send_student_account_banned(self, user_id, recipient_name, ban_reason, banned_at, ban_expires_at, support_url, message_type=None, priority=None, channels=None):
        """
        Send student_account_banned notification.
        Variables: recipient_name, ban_reason, banned_at, ban_expires_at, support_url
        """
        # Format dates for display
        banned_at_str = banned_at.strftime("%Y-%m-%d %H:%M") if banned_at else "Unknown"
        ban_expires_at_str = ban_expires_at.strftime("%Y-%m-%d %H:%M") if ban_expires_at else None
        
        variables = {
            'recipient_name': recipient_name,
            'ban_reason': ban_reason or 'Not specified',
            'banned_at': banned_at_str,
            'ban_expires_at': ban_expires_at_str,
            'support_url': support_url,
        }
        return self._send_notification('student_account_banned', user_id, variables, message_type=message_type, priority=priority, channels=channels)

    def send_teacher_account_activated(self, user_id, recipient_name, dashboard_url, support_url, message_type=None, priority=None, channels=None):
        """
        Send teacher_account_activated notification.
        Variables: recipient_name, dashboard_url, support_url
        """
        variables = {
            'recipient_name': recipient_name,
            'dashboard_url': dashboard_url,
            'support_url': support_url,
        }
        return self._send_notification('teacher_account_activated', user_id, variables, message_type=message_type, priority=priority, channels=channels)

    def send_teacher_account_banned(self, user_id, recipient_name, ban_reason, banned_at, ban_expires_at, support_url, message_type=None, priority=None, channels=None):
        """
        Send teacher_account_banned notification.
        Variables: recipient_name, ban_reason, banned_at, ban_expires_at, support_url
        """
        # Format dates for display
        banned_at_str = banned_at.strftime("%Y-%m-%d %H:%M") if banned_at else "Unknown"
        ban_expires_at_str = ban_expires_at.strftime("%Y-%m-%d %H:%M") if ban_expires_at else None
        
        variables = {
            'recipient_name': recipient_name,
            'ban_reason': ban_reason or 'Not specified',
            'banned_at': banned_at_str,
            'ban_expires_at': ban_expires_at_str,
            'support_url': support_url,
        }
        return self._send_notification('teacher_account_banned', user_id, variables, message_type=message_type, priority=priority, channels=channels)

    def send_student_welcome_first_approval(self, user_id, recipient_name, dashboard_url, support_url, message_type=None, priority=None, channels=None):
        """
        Send student_welcome_first_approval notification.
        Variables: recipient_name, dashboard_url, support_url
        """
        variables = {
            'recipient_name': recipient_name,
            'dashboard_url': dashboard_url,
            'support_url': support_url,
        }
        return self._send_notification('student_welcome_first_approval', user_id, variables, message_type=message_type, priority=priority, channels=channels)

    def send_teacher_welcome_first_approval(self, user_id, recipient_name, dashboard_url, support_url, message_type=None, priority=None, channels=None):
        """
        Send teacher_welcome_first_approval notification.
        Variables: recipient_name, dashboard_url, support_url
        """
        variables = {
            'recipient_name': recipient_name,
            'dashboard_url': dashboard_url,
            'support_url': support_url,
        }
        return self._send_notification('teacher_welcome_first_approval', user_id, variables, message_type=message_type, priority=priority, channels=channels)

    def send_student_account_created(self, user_id, username, temporary_password, email, login_url=None, support_email=None, support_phone=None, message_type=None, priority=None, channels=None):
        """
        Send student_account_created notification for new student account creation.
        Variables: username, temporary_password, email, login_url, support_email, support_phone
        """
        # Derive defaults if not provided
        frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
        login_url = login_url or f"{frontend_url}/login"
        support_email = support_email or current_app.config.get("SUPPORT_EMAIL", "support@example.com")
        support_phone = support_phone or current_app.config.get("SUPPORT_PHONE", "+1-800-000-0000")
        
        variables = {
            'username': username,
            'temporary_password': temporary_password,
            'email': email,
            'login_url': login_url,
            'support_email': support_email,
            'support_phone': support_phone,
        }
        return self._send_notification('student_account_created', user_id, variables, message_type=message_type, priority=priority, channels=channels)

    def send_student_password_reset(self, user_id, username, temporary_password, email, login_url=None, support_email=None, support_phone=None, message_type=None, priority=None, channels=None):
        """
        Send student_password_reset notification for password reset.
        Variables: username, temporary_password, email, login_url, support_email, support_phone
        """
        # Derive defaults if not provided
        frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
        login_url = login_url or f"{frontend_url}/login"
        support_email = support_email or current_app.config.get("SUPPORT_EMAIL", "support@example.com")
        support_phone = support_phone or current_app.config.get("SUPPORT_PHONE", "+1-800-000-0000")
        
        variables = {
            'username': username,
            'temporary_password': temporary_password,
            'email': email,
            'login_url': login_url,
            'support_email': support_email,
            'support_phone': support_phone,
        }
        return self._send_notification('student_password_reset', user_id, variables, message_type=message_type, priority=priority, channels=channels)

    def send_teacher_account_created(self, user_id, username, temporary_password, email, login_url=None, support_email=None, support_phone=None, message_type=None, priority=None, channels=None):
        """
        Send teacher_account_created notification for new teacher/instructor account creation.
        Variables: username, temporary_password, email, login_url, support_email, support_phone
        """
        # Derive defaults if not provided
        frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
        login_url = login_url or f"{frontend_url}/login"
        support_email = support_email or current_app.config.get("SUPPORT_EMAIL", "support@example.com")
        support_phone = support_phone or current_app.config.get("SUPPORT_PHONE", "+1-800-000-0000")
        
        variables = {
            'username': username,
            'temporary_password': temporary_password,
            'email': email,
            'login_url': login_url,
            'support_email': support_email,
            'support_phone': support_phone,
        }
        return self._send_notification('teacher_account_created', user_id, variables, message_type=message_type, priority=priority, channels=channels)

    def send_teacher_password_reset(self, user_id, username, temporary_password, email, login_url=None, support_email=None, support_phone=None, message_type=None, priority=None, channels=None):
        """
        Send teacher_password_reset notification for instructor password reset.
        Variables: username, temporary_password, email, login_url, support_email, support_phone
        """
        # Derive defaults if not provided
        frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
        login_url = login_url or f"{frontend_url}/login"
        support_email = support_email or current_app.config.get("SUPPORT_EMAIL", "support@example.com")
        support_phone = support_phone or current_app.config.get("SUPPORT_PHONE", "+1-800-000-0000")
        
        variables = {
            'username': username,
            'temporary_password': temporary_password,
            'email': email,
            'login_url': login_url,
            'support_email': support_email,
            'support_phone': support_phone,
        }
        return self._send_notification('teacher_password_reset', user_id, variables, message_type=message_type, priority=priority, channels=channels)
