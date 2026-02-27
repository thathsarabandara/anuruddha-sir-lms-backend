"""Add In-App Notification Templates

Revision ID: nt002_inapp
Revises: nt001_email
Create Date: 2026-02-27

This migration seeds all in-app notification templates into the
notification_templates table. Each template uses structured plain text
with Jinja2-style {{variable}} placeholders, covering all relevant details
so the notification widget can render rich, readable in-app messages.
"""

import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import column, table

# ---------------------------------------------------------------------------
# Alembic revision metadata
# ---------------------------------------------------------------------------
revision = "nt002_inapp"
down_revision = "nt001_email"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Template definitions
# Each entry: notification_type, subject (used as notification title),
#             template_text (plain structured content), variables list
# ---------------------------------------------------------------------------
def _templates():
    return [
        # ═══════════════════════════════════════════════════════════════════
        # 1. COURSE ENROLLMENT & ACCESS
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "enrollment_confirmation",
            "subject": "Enrollment Confirmed — {{course_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "You have been successfully enrolled in {{course_name}}.\n\n"
                "DETAILS\n"
                "-------\n"
                "Course      : {{course_name}}\n"
                "Instructor  : {{instructor_name}}\n"
                "Start Date  : {{start_date}}\n\n"
                "Head to your dashboard to begin your learning journey.\n\n"
                "ACTION: Open course → {{course_url}}"
            ),
            "variables": ["recipient_name", "course_name", "instructor_name", "start_date", "course_url"],
        },
        {
            "notification_type": "enrollment_expiration_warning",
            "subject": "⏳ Enrollment Expiring in {{days_remaining}} Days — {{course_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "Your enrollment in {{course_name}} will expire soon.\n\n"
                "DETAILS\n"
                "-------\n"
                "Course          : {{course_name}}\n"
                "Expiry Date     : {{expiry_date}}\n"
                "Days Remaining  : {{days_remaining}}\n\n"
                "Complete your lessons before the expiry date, or renew your access to continue.\n\n"
                "ACTION: Renew enrollment → {{renew_url}}"
            ),
            "variables": ["recipient_name", "course_name", "expiry_date", "days_remaining", "renew_url"],
        },
        {
            "notification_type": "course_invitation_confirmation",
            "subject": "You've Been Invited to {{course_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "{{inviter_name}} has invited you to join {{course_name}}.\n\n"
                "DETAILS\n"
                "-------\n"
                "Course      : {{course_name}}\n"
                "Invited By  : {{inviter_name}}\n\n"
                "Accept the invitation to start learning.\n\n"
                "ACTION: Accept invitation → {{registration_url}}"
            ),
            "variables": ["recipient_name", "inviter_name", "course_name", "registration_url"],
        },
        {
            "notification_type": "enrollment_request_approved_rejected",
            "subject": "Enrollment Request {{status}} — {{course_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "Your enrollment request for {{course_name}} has been {{status}}.\n\n"
                "DETAILS\n"
                "-------\n"
                "Course   : {{course_name}}\n"
                "Status   : {{status}}\n"
                "Reason   : {{reason}}\n\n"
                "ACTION: View course → {{course_url}}"
            ),
            "variables": ["recipient_name", "course_name", "status", "reason", "course_url"],
        },
        {
            "notification_type": "welcome_new_enrollment",
            "subject": "🚀 Welcome to {{course_name}}!",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "Welcome! Your learning journey in {{course_name}} begins now.\n\n"
                "DETAILS\n"
                "-------\n"
                "Course      : {{course_name}}\n"
                "Instructor  : {{instructor_name}}\n\n"
                "Tip: Set a regular study schedule and track your progress on the dashboard.\n\n"
                "ACTION: Start first lesson → {{first_lesson_url}}"
            ),
            "variables": ["recipient_name", "course_name", "instructor_name", "first_lesson_url"],
        },

        # ═══════════════════════════════════════════════════════════════════
        # 2. ASSIGNMENTS & GRADING
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "assignment_submitted_instructor",
            "subject": "📝 New Submission — {{assignment_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "{{student_name}} has submitted an assignment for your review.\n\n"
                "DETAILS\n"
                "-------\n"
                "Student     : {{student_name}}\n"
                "Course      : {{course_name}}\n"
                "Assignment  : {{assignment_name}}\n"
                "Submitted   : {{submitted_at}}\n\n"
                "ACTION: Review submission → {{submission_url}}"
            ),
            "variables": ["recipient_name", "student_name", "course_name", "assignment_name", "submitted_at", "submission_url"],
        },
        {
            "notification_type": "assignment_graded_student",
            "subject": "✅ Assignment Graded — {{assignment_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "Your assignment has been graded. Check your result below.\n\n"
                "DETAILS\n"
                "-------\n"
                "Assignment  : {{assignment_name}}\n"
                "Course      : {{course_name}}\n"
                "Grade       : {{grade}} / {{max_grade}}\n"
                "Feedback    : {{feedback}}\n\n"
                "ACTION: View feedback → {{submission_url}}"
            ),
            "variables": ["recipient_name", "assignment_name", "course_name", "grade", "max_grade", "feedback", "submission_url"],
        },
        {
            "notification_type": "assignment_submitted_late_instructor",
            "subject": "⚠️ Late Submission — {{assignment_name}} by {{student_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "A late assignment submission has been received.\n\n"
                "DETAILS\n"
                "-------\n"
                "Student     : {{student_name}}\n"
                "Course      : {{course_name}}\n"
                "Assignment  : {{assignment_name}}\n"
                "Due Date    : {{due_date}}\n"
                "Submitted   : {{submitted_at}}\n"
                "Delay       : {{delay}}\n\n"
                "ACTION: Review submission → {{submission_url}}"
            ),
            "variables": ["recipient_name", "student_name", "course_name", "assignment_name", "due_date", "submitted_at", "delay", "submission_url"],
        },
        {
            "notification_type": "submission_comment_added",
            "subject": "💬 New Comment on Submission — {{assignment_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "{{commenter_name}} left a comment on the submission for {{assignment_name}}.\n\n"
                "DETAILS\n"
                "-------\n"
                "Course      : {{course_name}}\n"
                "Assignment  : {{assignment_name}}\n"
                "Comment By  : {{commenter_name}}\n"
                "Preview     : \"{{comment_preview}}\"\n\n"
                "ACTION: View full comment → {{submission_url}}"
            ),
            "variables": ["recipient_name", "commenter_name", "course_name", "assignment_name", "comment_preview", "submission_url"],
        },
        {
            "notification_type": "essay_question_graded",
            "subject": "📝 Essay / Question Graded — {{lesson_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "Your essay or lesson question has been reviewed and graded.\n\n"
                "DETAILS\n"
                "-------\n"
                "Course    : {{course_name}}\n"
                "Lesson    : {{lesson_name}}\n"
                "Grade     : {{grade}} / {{max_grade}}\n"
                "Feedback  : {{feedback}}\n\n"
                "ACTION: View graded work → {{lesson_url}}"
            ),
            "variables": ["recipient_name", "course_name", "lesson_name", "grade", "max_grade", "feedback", "lesson_url"],
        },

        # ═══════════════════════════════════════════════════════════════════
        # 3. DEADLINES & REMINDERS
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "upcoming_due_date_reminder",
            "subject": "⏰ Due Soon — {{assignment_name}} in {{time_until_due}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "Reminder: {{assignment_name}} is due in {{time_until_due}}.\n\n"
                "DETAILS\n"
                "-------\n"
                "Assignment      : {{assignment_name}}\n"
                "Course          : {{course_name}}\n"
                "Due Date        : {{due_date}}\n"
                "Time Remaining  : {{time_until_due}}\n\n"
                "Submit early to avoid last-minute issues.\n\n"
                "ACTION: Submit now → {{submission_url}}"
            ),
            "variables": ["recipient_name", "assignment_name", "course_name", "due_date", "time_until_due", "submission_url"],
        },
        {
            "notification_type": "past_due_date_reminder",
            "subject": "🔴 Overdue — {{assignment_name}} ({{overdue_by}} late)",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "The deadline for {{assignment_name}} has passed.\n\n"
                "DETAILS\n"
                "-------\n"
                "Assignment   : {{assignment_name}}\n"
                "Course       : {{course_name}}\n"
                "Was Due      : {{due_date}}\n"
                "Overdue By   : {{overdue_by}}\n\n"
                "Contact your instructor if you have extenuating circumstances.\n\n"
                "ACTION: View assignment → {{submission_url}}"
            ),
            "variables": ["recipient_name", "assignment_name", "course_name", "due_date", "overdue_by", "submission_url"],
        },
        {
            "notification_type": "quiz_attempt_overdue_warning",
            "subject": "⚠️ Quiz Attempt Overdue — {{quiz_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "Your quiz attempt window for {{quiz_name}} has expired.\n\n"
                "DETAILS\n"
                "-------\n"
                "Quiz    : {{quiz_name}}\n"
                "Course  : {{course_name}}\n"
                "Was Due : {{due_date}}\n\n"
                "Please contact your instructor if you need assistance.\n\n"
                "ACTION: View quiz → {{quiz_url}}"
            ),
            "variables": ["recipient_name", "quiz_name", "course_name", "due_date", "quiz_url"],
        },

        # ═══════════════════════════════════════════════════════════════════
        # 4. QUIZZES & TESTS
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "quiz_submission_confirmation_student",
            "subject": "✅ Quiz Submitted — {{quiz_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "Your quiz has been submitted successfully.\n\n"
                "DETAILS\n"
                "-------\n"
                "Quiz             : {{quiz_name}}\n"
                "Course           : {{course_name}}\n"
                "Submitted At     : {{submitted_at}}\n"
                "Total Questions  : {{total_questions}}\n\n"
                "Your results will be available once grading is complete.\n\n"
                "ACTION: View submission → {{quiz_url}}"
            ),
            "variables": ["recipient_name", "quiz_name", "course_name", "submitted_at", "total_questions", "quiz_url"],
        },
        {
            "notification_type": "quiz_submission_notification_instructor",
            "subject": "📝 Quiz Submitted by {{student_name}} — {{quiz_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "A student has submitted a quiz that may require manual grading.\n\n"
                "DETAILS\n"
                "-------\n"
                "Student     : {{student_name}}\n"
                "Quiz        : {{quiz_name}}\n"
                "Course      : {{course_name}}\n"
                "Submitted   : {{submitted_at}}\n\n"
                "ACTION: Grade quiz → {{submission_url}}"
            ),
            "variables": ["recipient_name", "student_name", "quiz_name", "course_name", "submitted_at", "submission_url"],
        },
        {
            "notification_type": "quiz_graded_notification",
            "subject": "🏆 Quiz Result Available — {{quiz_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "Your quiz result for {{quiz_name}} is now ready.\n\n"
                "DETAILS\n"
                "-------\n"
                "Quiz        : {{quiz_name}}\n"
                "Course      : {{course_name}}\n"
                "Score       : {{score}} / {{max_score}} ({{percentage}}%)\n"
                "Result      : {{passed}}\n\n"
                "ACTION: View result → {{quiz_url}}"
            ),
            "variables": ["recipient_name", "quiz_name", "course_name", "score", "max_score", "percentage", "passed", "quiz_url"],
        },

        # ═══════════════════════════════════════════════════════════════════
        # 5. ACHIEVEMENTS & FEEDBACK
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "badge_awarded",
            "subject": "🏅 Badge Earned — {{badge_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "Congratulations! You've earned a new badge for your outstanding performance.\n\n"
                "DETAILS\n"
                "-------\n"
                "Badge        : {{badge_name}}\n"
                "Description  : {{badge_description}}\n"
                "Earned In    : {{course_name}}\n"
                "Awarded At   : {{awarded_at}}\n\n"
                "Keep it up and collect more badges!\n\n"
                "ACTION: View all badges → {{badges_url}}"
            ),
            "variables": ["recipient_name", "badge_name", "badge_description", "course_name", "awarded_at", "badges_url"],
        },
        {
            "notification_type": "course_completion_certificate",
            "subject": "🎓 Course Completed — Certificate Ready",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "Congratulations! You have successfully completed {{course_name}}. "
                "Your certificate is ready to download.\n\n"
                "DETAILS\n"
                "-------\n"
                "Course           : {{course_name}}\n"
                "Completed On     : {{completion_date}}\n"
                "Certificate ID   : {{certificate_id}}\n\n"
                "Share your achievement with the world!\n\n"
                "ACTION: Download certificate → {{certificate_url}}"
            ),
            "variables": ["recipient_name", "course_name", "completion_date", "certificate_id", "certificate_url"],
        },
        {
            "notification_type": "ceus_earned",
            "subject": "📚 {{ceu_credits}} CEU(s) Earned — {{course_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "You have earned {{ceu_credits}} Continuing Education Unit(s) for your activity in {{course_name}}.\n\n"
                "DETAILS\n"
                "-------\n"
                "Credits Earned  : {{ceu_credits}}\n"
                "Course          : {{course_name}}\n"
                "Total CEUs      : {{total_ceus}}\n\n"
                "ACTION: View CEU transcript → {{ceus_url}}"
            ),
            "variables": ["recipient_name", "ceu_credits", "course_name", "total_ceus", "ceus_url"],
        },
        {
            "notification_type": "new_badge_created",
            "subject": "🏅 New Badge Created — {{badge_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "A new badge has been created on the platform.\n\n"
                "DETAILS\n"
                "-------\n"
                "Badge Name    : {{badge_name}}\n"
                "Description   : {{badge_description}}\n"
                "Created By    : {{created_by}}\n"
                "For Course    : {{course_name}}\n\n"
                "ACTION: View badge → {{badge_url}}"
            ),
            "variables": ["recipient_name", "badge_name", "badge_description", "created_by", "course_name", "badge_url"],
        },
        {
            "notification_type": "feedback_review_submission",
            "subject": "⭐ New Review — {{course_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "{{reviewer_name}} submitted a new review for {{course_name}}.\n\n"
                "DETAILS\n"
                "-------\n"
                "Course    : {{course_name}}\n"
                "Reviewer  : {{reviewer_name}}\n"
                "Rating    : {{rating}} / 5\n"
                "Preview   : \"{{review_preview}}\"\n\n"
                "ACTION: Read full review → {{review_url}}"
            ),
            "variables": ["recipient_name", "reviewer_name", "course_name", "rating", "review_preview", "review_url"],
        },

        # ═══════════════════════════════════════════════════════════════════
        # 6. COMMUNICATION & COLLABORATION
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "new_forum_post_reply",
            "subject": "💬 New Reply — {{forum_topic}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "{{poster_name}} replied to the forum discussion '{{forum_topic}}' in {{course_name}}.\n\n"
                "REPLY PREVIEW\n"
                "-------------\n"
                "\"{{reply_preview}}\"\n\n"
                "ACTION: Join discussion → {{forum_url}}"
            ),
            "variables": ["recipient_name", "poster_name", "forum_topic", "course_name", "reply_preview", "forum_url"],
        },
        {
            "notification_type": "new_personal_message",
            "subject": "✉️ New Message from {{sender_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "You have a new personal message from {{sender_name}}.\n\n"
                "MESSAGE PREVIEW\n"
                "---------------\n"
                "\"{{message_preview}}\"\n\n"
                "ACTION: Read message → {{message_url}}"
            ),
            "variables": ["recipient_name", "sender_name", "message_preview", "message_url"],
        },
        {
            "notification_type": "user_added_to_conversation",
            "subject": "💬 Added to Conversation — {{conversation_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "{{added_by}} has added you to the conversation '{{conversation_name}}'.\n\n"
                "DETAILS\n"
                "-------\n"
                "Conversation   : {{conversation_name}}\n"
                "Participants   : {{participants}}\n\n"
                "ACTION: Join conversation → {{conversation_url}}"
            ),
            "variables": ["recipient_name", "added_by", "conversation_name", "participants", "conversation_url"],
        },
        {
            "notification_type": "new_course_announcement",
            "subject": "📢 New Announcement — {{course_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "{{posted_by}} posted a new announcement in {{course_name}}.\n\n"
                "ANNOUNCEMENT\n"
                "------------\n"
                "Title    : {{announcement_title}}\n"
                "Preview  : {{announcement_preview}}\n\n"
                "ACTION: Read full announcement → {{announcement_url}}"
            ),
            "variables": ["recipient_name", "course_name", "posted_by", "announcement_title", "announcement_preview", "announcement_url"],
        },
        {
            "notification_type": "comment_learning_plan",
            "subject": "💬 New Comment on Your Learning Plan",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "{{commenter_name}} commented on your learning plan '{{learning_plan_name}}'.\n\n"
                "COMMENT PREVIEW\n"
                "---------------\n"
                "\"{{comment_preview}}\"\n\n"
                "ACTION: View comment → {{plan_url}}"
            ),
            "variables": ["recipient_name", "commenter_name", "learning_plan_name", "comment_preview", "plan_url"],
        },

        # ═══════════════════════════════════════════════════════════════════
        # 7. ADMINISTRATIVE & SYSTEM
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "site_backup_status",
            "subject": "🔒 Backup {{backup_status}} — {{backup_date}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "The scheduled site backup completed with status: {{backup_status}}.\n\n"
                "DETAILS\n"
                "-------\n"
                "Date           : {{backup_date}}\n"
                "Backup Size    : {{backup_size}}\n"
                "Duration       : {{backup_duration}}\n"
                "Error (if any) : {{error_message}}\n\n"
                "ACTION: View admin panel → {{admin_url}}"
            ),
            "variables": ["recipient_name", "backup_status", "backup_date", "backup_size", "backup_duration", "error_message", "admin_url"],
        },
        {
            "notification_type": "new_software_update",
            "subject": "🔄 Software Update Available — v{{version}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "A new software update (v{{version}}) is available for the LMS Platform.\n\n"
                "DETAILS\n"
                "-------\n"
                "Version                : {{version}}\n"
                "Release Notes          : {{release_notes}}\n"
                "Scheduled Maintenance  : {{scheduled_maintenance}}\n\n"
                "ACTION: View update details → {{update_url}}"
            ),
            "variables": ["recipient_name", "version", "release_notes", "scheduled_maintenance", "update_url"],
        },
        {
            "notification_type": "critical_site_error",
            "subject": "🚨 CRITICAL ERROR DETECTED",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "A critical error has been detected on the platform and requires IMMEDIATE attention.\n\n"
                "ERROR REPORT\n"
                "------------\n"
                "Error Type         : {{error_type}}\n"
                "Message            : {{error_message}}\n"
                "Time               : {{error_time}}\n"
                "Affected Service   : {{affected_service}}\n\n"
                "Please investigate and resolve this issue as soon as possible.\n\n"
                "ACTION: View error details → {{error_url}}"
            ),
            "variables": ["recipient_name", "error_type", "error_message", "error_time", "affected_service", "error_url"],
        },
        {
            "notification_type": "suspicious_login_alert",
            "subject": "⚠️ New Login Detected on Your Account",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "A new login was detected on your account. If this was you, no action is needed. "
                "If not, please secure your account immediately.\n\n"
                "LOGIN DETAILS\n"
                "-------------\n"
                "Time       : {{login_time}}\n"
                "IP Address : {{ip_address}}\n"
                "Location   : {{location}}\n"
                "Device     : {{device}}\n\n"
                "ACTION: Secure my account → {{secure_url}}"
            ),
            "variables": ["recipient_name", "login_time", "ip_address", "location", "device", "secure_url"],
        },

        # ═══════════════════════════════════════════════════════════════════
        # 8. MENTORING & REVIEWS
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "mentor_connection_request",
            "subject": "🤝 Mentor Connection Request from {{requester_name}}",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "{{requester_name}} ({{requester_role}}) sent you a mentor connection request.\n\n"
                "THEIR MESSAGE\n"
                "-------------\n"
                "\"{{message}}\"\n\n"
                "ACTION: Respond to request → {{request_url}}"
            ),
            "variables": ["recipient_name", "requester_name", "requester_role", "message", "request_url"],
        },

        # ═══════════════════════════════════════════════════════════════════
        # 9. ACCOUNT & AUTHENTICATION
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "welcome_message",
            "subject": "👋 Welcome to the LMS Platform!",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "Welcome aboard! Your account has been successfully created and you're ready to start learning.\n\n"
                "GET STARTED\n"
                "-----------\n"
                "🎓  Browse available courses\n"
                "📚  Set up your learning profile\n"
                "🏆  Track your achievements\n"
                "📅  Join upcoming live sessions\n\n"
                "ACTION: Go to Dashboard → {{dashboard_url}}"
            ),
            "variables": ["recipient_name", "dashboard_url"],
        },
        {
            "notification_type": "password_reset_confirmation",
            "subject": "✅ Password Reset Successfully",
            "template_text": (
                "Hi {{recipient_name}},\n\n"
                "Your account password was successfully changed on {{reset_time}}.\n\n"
                "SECURITY NOTICE\n"
                "---------------\n"
                "✔  If you made this change, no further action is required.\n"
                "⚠  If you did NOT make this change, contact support immediately.\n\n"
                "ACTION: Contact Support → {{support_url}}"
            ),
            "variables": ["recipient_name", "reset_time", "support_url"],
        },
    ]


# ---------------------------------------------------------------------------
# Alembic table reference
# ---------------------------------------------------------------------------
_tbl = table(
    "notification_templates",
    column("template_id", sa.String(36)),
    column("notification_type", sa.String(100)),
    column("channel", sa.String(50)),
    column("subject", sa.String(255)),
    column("template_html", sa.Text),
    column("template_text", sa.Text),
    column("variables", sa.JSON),
    column("version", sa.Integer),
    column("is_active", sa.Boolean),
    column("created_at", sa.DateTime),
    column("updated_at", sa.DateTime),
)


def upgrade():
    now = datetime.utcnow()
    rows = []
    for tpl in _templates():
        rows.append(
            {
                "template_id": str(uuid.uuid4()),
                "notification_type": tpl["notification_type"],
                "channel": "in_app",
                "subject": tpl["subject"],
                "template_html": None,
                "template_text": tpl["template_text"],
                "variables": tpl.get("variables", []),
                "version": 1,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
        )
    op.bulk_insert(_tbl, rows)


def downgrade():
    op.execute(
        "DELETE FROM notification_templates WHERE channel = 'in_app' AND version = 1"
    )
