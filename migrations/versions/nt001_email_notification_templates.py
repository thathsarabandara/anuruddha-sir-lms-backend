"""Add Email Notification Templates

Revision ID: nt001_email
Revises:
Create Date: 2026-02-27

This migration seeds all email (HTML) notification templates into the
notification_templates table. Each template uses modern minimalistic HTML
with unique accent colours per category and Jinja2-style {{variable}} placeholders.
"""

import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import column, table

# ---------------------------------------------------------------------------
# Alembic revision metadata
# ---------------------------------------------------------------------------
revision = "nt001_email"
down_revision = None
branch_labels = ("notification_templates",)
depends_on = None

# ---------------------------------------------------------------------------
# Category accent colours
# ---------------------------------------------------------------------------
COLORS = {
    "enrollment": "#4F46E5",      # indigo
    "assignments": "#0891B2",     # cyan
    "deadlines": "#D97706",       # amber
    "quizzes": "#7C3AED",         # violet
    "achievements": "#059669",    # emerald
    "communication": "#2563EB",   # blue
    "admin": "#DC2626",           # red
    "ilt": "#0D9488",             # teal
    "mentoring": "#9333EA",       # purple
}

# ---------------------------------------------------------------------------
# HTML builder helper
# ---------------------------------------------------------------------------
def _build_html(color: str, icon: str, category: str, title: str, body_html: str, cta_html: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f8;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f8;">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);max-width:600px;">

          <!-- HEADER -->
          <tr>
            <td style="background:{color};padding:28px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <p style="margin:0;color:rgba(255,255,255,0.75);font-size:12px;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;">{category}</p>
                    <h1 style="margin:6px 0 0;color:#ffffff;font-size:22px;font-weight:700;line-height:1.3;">{icon}&nbsp;&nbsp;{title}</h1>
                  </td>
                  <td align="right" style="vertical-align:top;">
                    <p style="margin:0;color:rgba(255,255,255,0.60);font-size:12px;">Anuruddha Sir LMS Platform</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- BODY -->
          <tr>
            <td style="padding:36px 40px 28px;">
              {body_html}
            </td>
          </tr>

          <!-- CTA (optional) -->
          {"<tr><td style='padding:0 40px 36px;text-align:center;'>" + cta_html + "</td></tr>" if cta_html else ""}

          <!-- DIVIDER -->
          <tr>
            <td style="padding:0 40px;"><hr style="border:none;border-top:1px solid #eaeaea;margin:0;" /></td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="padding:24px 40px;background:#fafafa;">
              <p style="color:#aaaaaa;font-size:11px;margin:0 0 6px;line-height:1.6;">
                This is an automated notification from <strong style="color:#888;">Anuruddha Sir - LMS Platform</strong>.
                Please do not reply to this email.
              </p>
              <p style="color:#aaaaaa;font-size:11px;margin:0;line-height:1.6;">
                <a href="{{{{platform_url}}}}" style="color:{color};text-decoration:none;">Visit Platform</a>
                &nbsp;·&nbsp;
                <a href="{{{{unsubscribe_url}}}}" style="color:{color};text-decoration:none;">Unsubscribe</a>
                &nbsp;·&nbsp;
                <a href="{{{{preferences_url}}}}" style="color:{color};text-decoration:none;">Notification Preferences</a>
              </p>
            </td>
          </tr>

        </table>

        <!-- Bottom stamp -->
        <p style="color:#cccccc;font-size:10px;margin:20px 0 0;text-align:center;">
          &copy; {{{{current_year}}}} Anuruddha Sir - LMS Platform. All rights reserved.
        </p>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _cta_button(color: str, url: str, label: str) -> str:
    return (
        f'<a href="{url}" style="display:inline-block;background:{color};color:#ffffff;'
        f'text-decoration:none;font-size:15px;font-weight:600;padding:14px 36px;'
        f'border-radius:6px;margin-top:16px;">{label}</a>'
    )


# ---------------------------------------------------------------------------
# Salutation + signature reusable snippets
# ---------------------------------------------------------------------------
GREET = '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">Hi <strong>{{{{recipient_name}}}}</strong>,</p>'
SIG   = ('<p style="color:#777777;font-size:13px;line-height:1.6;margin:20px 0 0;">'
         'Warm regards,<br/><strong style="color:#444;">The Anuruddha Sir - LMS Platform Team</strong></p>')


# ---------------------------------------------------------------------------
# Template definitions  (type, subject, category_key, icon, title, body, cta)
# ---------------------------------------------------------------------------
def _templates():
    c = COLORS

    return [
        # ═══════════════════════════════════════════════════════════════════
        # 1. COURSE ENROLLMENT & ACCESS
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "enrollment_confirmation",
            "subject": "You're enrolled in {{course_name}}! 🎉",
            "category": "Course Enrollment & Access",
            "color": c["enrollment"],
            "icon": "🎓",
            "title": "Enrollment Confirmed",
            "variables": ["recipient_name", "course_name", "course_url", "start_date", "instructor_name", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Congratulations! Your enrollment in <strong>{{course_name}}</strong> has been successfully confirmed.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#f0f0ff;border-left:4px solid #4F46E5;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0 0 6px;color:#4F46E5;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;">Course Details</p>'
                '<p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '👤 <strong>Instructor:</strong> {{instructor_name}}<br/>'
                '📅 <strong>Start Date:</strong> {{start_date}}'
                '</p></td></tr></table>'
                '<p style="color:#555555;font-size:14px;line-height:1.7;margin:0 0 8px;">'
                'Head to your dashboard and start learning at your own pace. We hope you enjoy the course!</p>'
                + SIG
            ),
            "cta": _cta_button(c["enrollment"], "{{course_url}}", "Go to Course →"),
        },
        {
            "notification_type": "enrollment_expiration_warning",
            "subject": "⚠️ Your access to {{course_name}} expires in {{days_remaining}} days",
            "category": "Course Enrollment & Access",
            "color": c["enrollment"],
            "icon": "⏳",
            "title": "Enrollment Expiring Soon",
            "variables": ["recipient_name", "course_name", "days_remaining", "expiry_date", "course_url", "renew_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'This is a friendly reminder that your enrollment in <strong>{{course_name}}</strong> '
                'will expire in <strong>{{days_remaining}} days</strong> on <strong>{{expiry_date}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#fff8e1;border-left:4px solid #D97706;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#92400e;font-size:14px;line-height:1.7;">'
                '⚠️ Complete your remaining lessons before <strong>{{expiry_date}}</strong> to make the most of your enrollment. '
                'You can also renew your access to continue learning beyond that date.</p></td></tr></table>'
                '<p style="color:#555555;font-size:14px;line-height:1.7;margin:0 0 8px;">'
                'Any progress you have made will be saved even after expiry.</p>'
                + SIG
            ),
            "cta": _cta_button(c["enrollment"], "{{renew_url}}", "Renew Enrollment →"),
        },
        {
            "notification_type": "course_invitation_confirmation",
            "subject": "You've been invited to join {{course_name}} on LMS Platform",
            "category": "Course Enrollment & Access",
            "color": c["enrollment"],
            "icon": "✉️",
            "title": "Course Invitation",
            "variables": ["recipient_name", "course_name", "inviter_name", "course_url", "registration_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                '<strong>{{inviter_name}}</strong> has invited you to join <strong>{{course_name}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#f0f0ff;border-left:4px solid #4F46E5;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '👤 <strong>Invited by:</strong> {{inviter_name}}'
                '</p></td></tr></table>'
                '<p style="color:#555555;font-size:14px;line-height:1.7;margin:0 0 8px;">'
                'Click the button below to accept the invitation and get started. '
                'If this was unexpected, you may safely ignore this email.</p>'
                + SIG
            ),
            "cta": _cta_button(c["enrollment"], "{{registration_url}}", "Accept Invitation →"),
        },
        {
            "notification_type": "enrollment_request_admin",
            "subject": "📋 New Enrollment Request for {{course_name}} from {{student_name}}",
            "category": "Course Enrollment & Access",
            "color": c["enrollment"],
            "icon": "📋",
            "title": "New Enrollment Request",
            "variables": ["recipient_name", "student_name", "student_email", "course_name", "request_date", "review_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'A new enrollment request has been submitted and requires your review.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#f0f0ff;border-left:4px solid #4F46E5;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#4F46E5;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Request Details</p>'
                '<p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '👤 <strong>Student:</strong> {{student_name}} ({{student_email}})<br/>'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '📅 <strong>Requested on:</strong> {{request_date}}'
                '</p></td></tr></table>'
                '<p style="color:#555555;font-size:14px;line-height:1.7;margin:0 0 8px;">'
                'Please review and approve or reject the request from the admin panel.</p>'
                + SIG
            ),
            "cta": _cta_button(c["enrollment"], "{{review_url}}", "Review Request →"),
        },
        {
            "notification_type": "enrollment_request_approved_rejected",
            "subject": "Your enrollment request for {{course_name}} has been {{status}}",
            "category": "Course Enrollment & Access",
            "color": c["enrollment"],
            "icon": "📩",
            "title": "Enrollment Request Update",
            "variables": ["recipient_name", "course_name", "status", "reason", "course_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Your enrollment request for <strong>{{course_name}}</strong> has been <strong>{{status}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#f0f0ff;border-left:4px solid #4F46E5;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '✅ <strong>Status:</strong> {{status}}<br/>'
                '💬 <strong>Reason:</strong> {{reason}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["enrollment"], "{{course_url}}", "View Course →"),
        },
        {
            "notification_type": "welcome_new_enrollment",
            "subject": "Welcome to {{course_name}}! Let's begin 🚀",
            "category": "Course Enrollment & Access",
            "color": c["enrollment"],
            "icon": "🚀",
            "title": "Welcome to Your New Course",
            "variables": ["recipient_name", "course_name", "instructor_name", "course_url", "first_lesson_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Welcome aboard! We are thrilled to have you in <strong>{{course_name}}</strong>. '
                'Your learning journey begins now.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#f0f0ff;border-left:4px solid #4F46E5;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '👤 <strong>Instructor:</strong> {{instructor_name}}<br/>'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '🗺️ Start with your first lesson and keep the momentum going!'
                '</p></td></tr></table>'
                '<p style="color:#555555;font-size:14px;line-height:1.7;margin:0 0 8px;">'
                'Set a regular study schedule, track your progress, and reach out if you need any help.</p>'
                + SIG
            ),
            "cta": _cta_button(c["enrollment"], "{{first_lesson_url}}", "Start First Lesson →"),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 2. ASSIGNMENTS & GRADING
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "assignment_submitted_instructor",
            "subject": "📝 New Assignment Submission — {{student_name}} in {{course_name}}",
            "category": "Assignments & Grading",
            "color": c["assignments"],
            "icon": "📝",
            "title": "New Assignment Submission",
            "variables": ["recipient_name", "student_name", "course_name", "assignment_name", "submitted_at", "submission_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                '<strong>{{student_name}}</strong> has submitted an assignment for your review.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#e0f7fa;border-left:4px solid #0891B2;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#006064;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Submission Details</p>'
                '<p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '👤 <strong>Student:</strong> {{student_name}}<br/>'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '📄 <strong>Assignment:</strong> {{assignment_name}}<br/>'
                '🕐 <strong>Submitted:</strong> {{submitted_at}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["assignments"], "{{submission_url}}", "Review Submission →"),
        },
        {
            "notification_type": "assignment_graded_student",
            "subject": "Your assignment '{{assignment_name}}' has been graded ✅",
            "category": "Assignments & Grading",
            "color": c["assignments"],
            "icon": "✅",
            "title": "Assignment Graded",
            "variables": ["recipient_name", "assignment_name", "course_name", "grade", "max_grade", "feedback", "submission_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Great news! Your assignment <strong>{{assignment_name}}</strong> has been graded.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#e0f7fa;border-left:4px solid #0891B2;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '📄 <strong>Assignment:</strong> {{assignment_name}}<br/>'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '🏆 <strong>Grade:</strong> {{grade}} / {{max_grade}}<br/>'
                '💬 <strong>Feedback:</strong> {{feedback}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["assignments"], "{{submission_url}}", "View Feedback →"),
        },
        {
            "notification_type": "assignment_submitted_late_instructor",
            "subject": "⚠️ Late Submission Alert — {{student_name}} in {{course_name}}",
            "category": "Assignments & Grading",
            "color": c["assignments"],
            "icon": "⚠️",
            "title": "Late Assignment Submission",
            "variables": ["recipient_name", "student_name", "course_name", "assignment_name", "due_date", "submitted_at", "delay", "submission_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'A late submission has been received for your assignment.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#fff8e1;border-left:4px solid #D97706;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#92400e;font-size:14px;line-height:1.7;">'
                '👤 <strong>Student:</strong> {{student_name}}<br/>'
                '📄 <strong>Assignment:</strong> {{assignment_name}}<br/>'
                '📅 <strong>Due Date:</strong> {{due_date}}<br/>'
                '🕐 <strong>Submitted:</strong> {{submitted_at}}<br/>'
                '⏱️ <strong>Delay:</strong> {{delay}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["assignments"], "{{submission_url}}", "Review Submission →"),
        },
        {
            "notification_type": "submission_comment_added",
            "subject": "💬 New comment on your submission in {{course_name}}",
            "category": "Assignments & Grading",
            "color": c["assignments"],
            "icon": "💬",
            "title": "New Comment on Submission",
            "variables": ["recipient_name", "commenter_name", "course_name", "assignment_name", "comment_preview", "submission_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                '<strong>{{commenter_name}}</strong> left a comment on the submission for <strong>{{assignment_name}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#e0f7fa;border-left:4px solid #0891B2;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#006064;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Comment Preview</p>'
                '<p style="margin:0;color:#333;font-size:14px;line-height:1.7;font-style:italic;">"{{comment_preview}}"</p>'
                '</td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["assignments"], "{{submission_url}}", "View Full Comment →"),
        },
        {
            "notification_type": "essay_question_graded",
            "subject": "Your essay / lesson question has been graded 📝",
            "category": "Assignments & Grading",
            "color": c["assignments"],
            "icon": "📝",
            "title": "Essay / Question Graded",
            "variables": ["recipient_name", "course_name", "lesson_name", "grade", "max_grade", "feedback", "lesson_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Your essay / lesson question in <strong>{{lesson_name}}</strong> has been reviewed and graded.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#e0f7fa;border-left:4px solid #0891B2;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '📖 <strong>Lesson:</strong> {{lesson_name}}<br/>'
                '🏆 <strong>Grade:</strong> {{grade}} / {{max_grade}}<br/>'
                '💬 <strong>Feedback:</strong> {{feedback}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["assignments"], "{{lesson_url}}", "View Graded Work →"),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 3. DEADLINES & REMINDERS
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "upcoming_due_date_reminder",
            "subject": "⏰ Reminder: {{assignment_name}} is due in {{time_until_due}}",
            "category": "Deadlines & Reminders",
            "color": c["deadlines"],
            "icon": "⏰",
            "title": "Upcoming Due Date",
            "variables": ["recipient_name", "assignment_name", "course_name", "due_date", "time_until_due", "submission_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'This is a reminder that <strong>{{assignment_name}}</strong> is due in <strong>{{time_until_due}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#fff8e1;border-left:4px solid #D97706;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#92400e;font-size:14px;line-height:1.7;">'
                '📄 <strong>Assignment:</strong> {{assignment_name}}<br/>'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '📅 <strong>Due:</strong> {{due_date}}<br/>'
                '⏳ <strong>Time Remaining:</strong> {{time_until_due}}'
                '</p></td></tr></table>'
                '<p style="color:#555555;font-size:14px;line-height:1.7;margin:0 0 8px;">'
                'Don\'t leave it to the last minute — submit early to avoid technical issues.</p>'
                + SIG
            ),
            "cta": _cta_button(c["deadlines"], "{{submission_url}}", "Submit Now →"),
        },
        {
            "notification_type": "past_due_date_reminder",
            "subject": "🔴 Overdue: {{assignment_name}} was due {{overdue_by}} ago",
            "category": "Deadlines & Reminders",
            "color": c["deadlines"],
            "icon": "🔴",
            "title": "Past Due Date Alert",
            "variables": ["recipient_name", "assignment_name", "course_name", "due_date", "overdue_by", "submission_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'The deadline for <strong>{{assignment_name}}</strong> has passed.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#fff0f0;border-left:4px solid #DC2626;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#991b1b;font-size:14px;line-height:1.7;">'
                '📄 <strong>Assignment:</strong> {{assignment_name}}<br/>'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '📅 <strong>Was Due:</strong> {{due_date}}<br/>'
                '⏱️ <strong>Overdue By:</strong> {{overdue_by}}'
                '</p></td></tr></table>'
                '<p style="color:#555555;font-size:14px;line-height:1.7;margin:0 0 8px;">'
                'If you have extenuating circumstances, please contact your instructor immediately.</p>'
                + SIG
            ),
            "cta": _cta_button(c["deadlines"], "{{submission_url}}", "Submit Now →"),
        },
        {
            "notification_type": "activity_start_date_reminder",
            "subject": "📅 Activity '{{activity_name}}' starts {{time_until_start}}",
            "category": "Deadlines & Reminders",
            "color": c["deadlines"],
            "icon": "📅",
            "title": "Activity Starting Soon",
            "variables": ["recipient_name", "activity_name", "course_name", "start_date", "time_until_start", "activity_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'A course activity you are enrolled in is starting soon.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#fff8e1;border-left:4px solid #D97706;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#92400e;font-size:14px;line-height:1.7;">'
                '🎯 <strong>Activity:</strong> {{activity_name}}<br/>'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '📅 <strong>Starts:</strong> {{start_date}}<br/>'
                '⏳ <strong>Time Until Start:</strong> {{time_until_start}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["deadlines"], "{{activity_url}}", "View Activity →"),
        },
        {
            "notification_type": "quiz_attempt_overdue_warning",
            "subject": "⚠️ Quiz attempt for '{{quiz_name}}' is overdue",
            "category": "Deadlines & Reminders",
            "color": c["deadlines"],
            "icon": "⚠️",
            "title": "Quiz Attempt Overdue",
            "variables": ["recipient_name", "quiz_name", "course_name", "due_date", "quiz_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Your quiz attempt deadline for <strong>{{quiz_name}}</strong> has passed. '
                'Please contact your instructor if you believe this is an error.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#fff0f0;border-left:4px solid #DC2626;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#991b1b;font-size:14px;line-height:1.7;">'
                '📝 <strong>Quiz:</strong> {{quiz_name}}<br/>'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '📅 <strong>Was Due:</strong> {{due_date}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["deadlines"], "{{quiz_url}}", "View Quiz →"),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 4. QUIZZES & TESTS
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "quiz_submission_confirmation_student",
            "subject": "✅ Quiz '{{quiz_name}}' submitted successfully",
            "category": "Quizzes & Tests",
            "color": c["quizzes"],
            "icon": "✅",
            "title": "Quiz Submitted",
            "variables": ["recipient_name", "quiz_name", "course_name", "submitted_at", "total_questions", "quiz_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Your quiz has been successfully submitted. Well done for completing it!</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#f3f0ff;border-left:4px solid #7C3AED;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '📝 <strong>Quiz:</strong> {{quiz_name}}<br/>'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '🕐 <strong>Submitted:</strong> {{submitted_at}}<br/>'
                '❓ <strong>Total Questions:</strong> {{total_questions}}'
                '</p></td></tr></table>'
                '<p style="color:#555555;font-size:14px;line-height:1.7;margin:0 0 8px;">'
                'Your results will be available once grading is complete.</p>'
                + SIG
            ),
            "cta": _cta_button(c["quizzes"], "{{quiz_url}}", "View Submission →"),
        },
        {
            "notification_type": "quiz_submission_notification_instructor",
            "subject": "📝 Quiz submitted by {{student_name}} — {{quiz_name}}",
            "category": "Quizzes & Tests",
            "color": c["quizzes"],
            "icon": "📝",
            "title": "Student Quiz Submitted",
            "variables": ["recipient_name", "student_name", "quiz_name", "course_name", "submitted_at", "submission_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                '<strong>{{student_name}}</strong> has submitted <strong>{{quiz_name}}</strong> and it may require manual grading.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#f3f0ff;border-left:4px solid #7C3AED;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '👤 <strong>Student:</strong> {{student_name}}<br/>'
                '📝 <strong>Quiz:</strong> {{quiz_name}}<br/>'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '🕐 <strong>Submitted:</strong> {{submitted_at}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["quizzes"], "{{submission_url}}", "Grade Quiz →"),
        },
        {
            "notification_type": "quiz_graded_notification",
            "subject": "🏆 Your quiz '{{quiz_name}}' result is ready",
            "category": "Quizzes & Tests",
            "color": c["quizzes"],
            "icon": "🏆",
            "title": "Quiz Result Available",
            "variables": ["recipient_name", "quiz_name", "course_name", "score", "max_score", "percentage", "passed", "quiz_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Your result for <strong>{{quiz_name}}</strong> is now available.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#f3f0ff;border-left:4px solid #7C3AED;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '📝 <strong>Quiz:</strong> {{quiz_name}}<br/>'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '🏆 <strong>Score:</strong> {{score}} / {{max_score}} ({{percentage}}%)<br/>'
                '✅ <strong>Result:</strong> {{passed}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["quizzes"], "{{quiz_url}}", "View Result →"),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 5. ACHIEVEMENTS & FEEDBACK
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "badge_awarded",
            "subject": "🏅 You've earned the '{{badge_name}}' badge!",
            "category": "Achievements & Feedback",
            "color": c["achievements"],
            "icon": "🏅",
            "title": "Badge Awarded",
            "variables": ["recipient_name", "badge_name", "badge_description", "course_name", "awarded_at", "badges_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Congratulations! You have earned a new badge for your outstanding performance.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#ecfdf5;border-left:4px solid #059669;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#065f46;font-size:16px;font-weight:700;margin-bottom:6px;">🏅 {{badge_name}}</p>'
                '<p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '📝 <strong>Description:</strong> {{badge_description}}<br/>'
                '📘 <strong>Earned in:</strong> {{course_name}}<br/>'
                '📅 <strong>Awarded:</strong> {{awarded_at}}'
                '</p></td></tr></table>'
                '<p style="color:#555555;font-size:14px;line-height:1.7;margin:0 0 8px;">'
                'Keep up the great work and continue collecting badges!</p>'
                + SIG
            ),
            "cta": _cta_button(c["achievements"], "{{badges_url}}", "View All Badges →"),
        },
        {
            "notification_type": "course_completion_certificate",
            "subject": "🎉 Congratulations! You completed {{course_name}} — Certificate Ready",
            "category": "Achievements & Feedback",
            "color": c["achievements"],
            "icon": "🎓",
            "title": "Course Completed — Certificate Awarded",
            "variables": ["recipient_name", "course_name", "completion_date", "certificate_url", "certificate_id", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'You have successfully completed <strong>{{course_name}}</strong>! '
                'Your certificate is now ready to download and share.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#ecfdf5;border-left:4px solid #059669;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '📅 <strong>Completed On:</strong> {{completion_date}}<br/>'
                '🔖 <strong>Certificate ID:</strong> {{certificate_id}}'
                '</p></td></tr></table>'
                '<p style="color:#555555;font-size:14px;line-height:1.7;margin:0 0 8px;">'
                'Share your achievement on LinkedIn or with your employer. You deserve it!</p>'
                + SIG
            ),
            "cta": _cta_button(c["achievements"], "{{certificate_url}}", "Download Certificate →"),
        },
        {
            "notification_type": "ceus_earned",
            "subject": "📚 You've earned {{ceu_credits}} Continuing Education Units",
            "category": "Achievements & Feedback",
            "color": c["achievements"],
            "icon": "📚",
            "title": "CEUs Earned",
            "variables": ["recipient_name", "ceu_credits", "course_name", "total_ceus", "ceus_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'You have earned <strong>{{ceu_credits}} CEU(s)</strong> for completing activities in <strong>{{course_name}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#ecfdf5;border-left:4px solid #059669;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '📚 <strong>Credits Earned:</strong> {{ceu_credits}}<br/>'
                '📘 <strong>Course:</strong> {{course_name}}<br/>'
                '🏆 <strong>Total CEUs:</strong> {{total_ceus}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["achievements"], "{{ceus_url}}", "View CEU Transcript →"),
        },
        {
            "notification_type": "new_badge_created",
            "subject": "🏅 New Badge Created: {{badge_name}}",
            "category": "Achievements & Feedback",
            "color": c["achievements"],
            "icon": "🏅",
            "title": "New Badge Created",
            "variables": ["recipient_name", "badge_name", "badge_description", "created_by", "course_name", "badge_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'A new badge has been created on the platform.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#ecfdf5;border-left:4px solid #059669;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '🏅 <strong>Badge Name:</strong> {{badge_name}}<br/>'
                '📝 <strong>Description:</strong> {{badge_description}}<br/>'
                '👤 <strong>Created By:</strong> {{created_by}}<br/>'
                '📘 <strong>For Course:</strong> {{course_name}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["achievements"], "{{badge_url}}", "View Badge →"),
        },
        {
            "notification_type": "feedback_review_submission",
            "subject": "⭐ New review submitted for {{course_name}}",
            "category": "Achievements & Feedback",
            "color": c["achievements"],
            "icon": "⭐",
            "title": "New Course Review",
            "variables": ["recipient_name", "reviewer_name", "course_name", "rating", "review_preview", "review_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                '<strong>{{reviewer_name}}</strong> has submitted a review for <strong>{{course_name}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#ecfdf5;border-left:4px solid #059669;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#065f46;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Review Preview</p>'
                '<p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '⭐ <strong>Rating:</strong> {{rating}} / 5<br/>'
                '💬 "{{review_preview}}"'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["achievements"], "{{review_url}}", "Read Full Review →"),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 6. COMMUNICATION & COLLABORATION
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "new_forum_post_reply",
            "subject": "💬 New reply in '{{forum_topic}}' — {{course_name}}",
            "category": "Communication & Collaboration",
            "color": c["communication"],
            "icon": "💬",
            "title": "New Forum Reply",
            "variables": ["recipient_name", "poster_name", "forum_topic", "course_name", "reply_preview", "forum_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                '<strong>{{poster_name}}</strong> replied to the discussion <strong>{{forum_topic}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#eff6ff;border-left:4px solid #2563EB;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#1e40af;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Reply Preview</p>'
                '<p style="margin:0;color:#333;font-size:14px;line-height:1.7;font-style:italic;">"{{reply_preview}}"</p>'
                '</td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["communication"], "{{forum_url}}", "Join Discussion →"),
        },
        {
            "notification_type": "daily_forum_digest",
            "subject": "📰 Your Daily Forum Digest — {{digest_date}}",
            "category": "Communication & Collaboration",
            "color": c["communication"],
            "icon": "📰",
            "title": "Daily Forum Digest",
            "variables": ["recipient_name", "digest_date", "new_topics_count", "new_replies_count", "top_topics", "forum_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Here\'s your daily summary of forum activity for <strong>{{digest_date}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#eff6ff;border-left:4px solid #2563EB;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '🆕 <strong>New Topics:</strong> {{new_topics_count}}<br/>'
                '💬 <strong>New Replies:</strong> {{new_replies_count}}<br/>'
                '🔥 <strong>Top Discussions:</strong> {{top_topics}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["communication"], "{{forum_url}}", "Visit Forum →"),
        },
        {
            "notification_type": "new_personal_message",
            "subject": "✉️ New message from {{sender_name}}",
            "category": "Communication & Collaboration",
            "color": c["communication"],
            "icon": "✉️",
            "title": "New Personal Message",
            "variables": ["recipient_name", "sender_name", "message_preview", "message_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'You have received a new personal message from <strong>{{sender_name}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#eff6ff;border-left:4px solid #2563EB;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#1e40af;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Message Preview</p>'
                '<p style="margin:0;color:#333;font-size:14px;line-height:1.7;font-style:italic;">"{{message_preview}}"</p>'
                '</td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["communication"], "{{message_url}}", "Read Message →"),
        },
        {
            "notification_type": "user_added_to_conversation",
            "subject": "💬 You've been added to a conversation — {{conversation_name}}",
            "category": "Communication & Collaboration",
            "color": c["communication"],
            "icon": "💬",
            "title": "Added to Conversation",
            "variables": ["recipient_name", "added_by", "conversation_name", "participants", "conversation_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                '<strong>{{added_by}}</strong> has added you to the conversation <strong>{{conversation_name}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#eff6ff;border-left:4px solid #2563EB;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '💬 <strong>Conversation:</strong> {{conversation_name}}<br/>'
                '👥 <strong>Participants:</strong> {{participants}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["communication"], "{{conversation_url}}", "Join Conversation →"),
        },
        {
            "notification_type": "new_course_announcement",
            "subject": "📢 Announcement in {{course_name}}: {{announcement_title}}",
            "category": "Communication & Collaboration",
            "color": c["communication"],
            "icon": "📢",
            "title": "New Course Announcement",
            "variables": ["recipient_name", "course_name", "announcement_title", "announcement_preview", "posted_by", "announcement_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'A new announcement has been posted in <strong>{{course_name}}</strong> by <strong>{{posted_by}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#eff6ff;border-left:4px solid #2563EB;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#1e40af;font-size:15px;font-weight:700;margin-bottom:8px;">{{announcement_title}}</p>'
                '<p style="margin:0;color:#333;font-size:14px;line-height:1.7;">{{announcement_preview}}</p>'
                '</td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["communication"], "{{announcement_url}}", "Read Announcement →"),
        },
        {
            "notification_type": "comment_learning_plan",
            "subject": "💬 New comment on your learning plan / competency",
            "category": "Communication & Collaboration",
            "color": c["communication"],
            "icon": "💬",
            "title": "New Comment on Learning Plan",
            "variables": ["recipient_name", "commenter_name", "learning_plan_name", "comment_preview", "plan_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                '<strong>{{commenter_name}}</strong> commented on your learning plan <strong>{{learning_plan_name}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#eff6ff;border-left:4px solid #2563EB;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;font-style:italic;">"{{comment_preview}}"</p>'
                '</td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["communication"], "{{plan_url}}", "View Comment →"),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 7. ADMINISTRATIVE & SYSTEM
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "site_backup_status",
            "subject": "🔒 Site Backup {{backup_status}} — {{backup_date}}",
            "category": "Administrative & System",
            "color": c["admin"],
            "icon": "🔒",
            "title": "Site Backup Report",
            "variables": ["recipient_name", "backup_status", "backup_date", "backup_size", "backup_duration", "error_message", "admin_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'The scheduled site backup completed with status: <strong>{{backup_status}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#fff0f0;border-left:4px solid #DC2626;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '📅 <strong>Date:</strong> {{backup_date}}<br/>'
                '💾 <strong>Backup Size:</strong> {{backup_size}}<br/>'
                '⏱️ <strong>Duration:</strong> {{backup_duration}}<br/>'
                '⚠️ <strong>Error (if any):</strong> {{error_message}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["admin"], "{{admin_url}}", "View Admin Panel →"),
        },
        {
            "notification_type": "new_software_update",
            "subject": "🔄 Software Update Available — v{{version}}",
            "category": "Administrative & System",
            "color": c["admin"],
            "icon": "🔄",
            "title": "New Software Update Available",
            "variables": ["recipient_name", "version", "release_notes", "update_url", "scheduled_maintenance", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'A new software update (v{{version}}) is available for the LMS Platform.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#fff0f0;border-left:4px solid #DC2626;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '🔄 <strong>Version:</strong> {{version}}<br/>'
                '📋 <strong>Release Notes:</strong> {{release_notes}}<br/>'
                '🛠️ <strong>Scheduled Maintenance:</strong> {{scheduled_maintenance}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["admin"], "{{update_url}}", "View Update Details →"),
        },
        {
            "notification_type": "critical_site_error",
            "subject": "🚨 CRITICAL ALERT — Site Error Detected",
            "category": "Administrative & System",
            "color": c["admin"],
            "icon": "🚨",
            "title": "Critical Site Error",
            "variables": ["recipient_name", "error_type", "error_message", "error_time", "affected_service", "error_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#991b1b;font-size:15px;font-weight:700;line-height:1.7;margin:0 0 14px;">'
                '⚠️ A critical error has been detected on the platform and requires immediate attention.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#fff0f0;border-left:4px solid #DC2626;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#991b1b;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Error Report</p>'
                '<p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '❌ <strong>Error Type:</strong> {{error_type}}<br/>'
                '📋 <strong>Message:</strong> {{error_message}}<br/>'
                '🕐 <strong>Time:</strong> {{error_time}}<br/>'
                '🔧 <strong>Affected Service:</strong> {{affected_service}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["admin"], "{{error_url}}", "View Error Details →"),
        },
        {
            "notification_type": "batch_user_upload_summary",
            "subject": "📊 Batch User Upload Summary — {{upload_date}}",
            "category": "Administrative & System",
            "color": c["admin"],
            "icon": "📊",
            "title": "Batch Upload Summary",
            "variables": ["recipient_name", "upload_date", "total_users", "successful", "failed", "errors_summary", "report_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'The batch user upload process completed on <strong>{{upload_date}}</strong>. Here is the summary:</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#fff0f0;border-left:4px solid #DC2626;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '👥 <strong>Total Users:</strong> {{total_users}}<br/>'
                '✅ <strong>Successful:</strong> {{successful}}<br/>'
                '❌ <strong>Failed:</strong> {{failed}}<br/>'
                '⚠️ <strong>Errors:</strong> {{errors_summary}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["admin"], "{{report_url}}", "View Full Report →"),
        },
        {
            "notification_type": "password_reset_request",
            "subject": "🔐 Password Reset Request — LMS Platform",
            "category": "Administrative & System",
            "color": c["admin"],
            "icon": "🔐",
            "title": "Password Reset Request",
            "variables": ["recipient_name", "reset_url", "expiry_time", "ip_address", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'We received a request to reset the password for your LMS Platform account. '
                'Click the button below to create a new password.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#fff8e1;border-left:4px solid #D97706;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#92400e;font-size:14px;line-height:1.7;">'
                '⏳ This link will expire in <strong>{{expiry_time}}</strong>.<br/>'
                '🌐 Request came from IP: <strong>{{ip_address}}</strong>.<br/>'
                'If you did not request this, please ignore this email and your password will remain unchanged.'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["admin"], "{{reset_url}}", "Reset Password →"),
        },
        {
            "notification_type": "suspicious_login_alert",
            "subject": "⚠️ New Login Detected on Your Account",
            "category": "Administrative & System",
            "color": c["admin"],
            "icon": "⚠️",
            "title": "New Login Detected",
            "variables": ["recipient_name", "login_time", "ip_address", "location", "device", "secure_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'We detected a new login to your account. If this was you, no action is needed. '
                'If not, please secure your account immediately.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#fff0f0;border-left:4px solid #DC2626;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '🕐 <strong>Time:</strong> {{login_time}}<br/>'
                '🌐 <strong>IP Address:</strong> {{ip_address}}<br/>'
                '📍 <strong>Location:</strong> {{location}}<br/>'
                '💻 <strong>Device:</strong> {{device}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["admin"], "{{secure_url}}", "Secure My Account →"),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 8. INSTRUCTOR-LED TRAINING (ILT)
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "ilt_booking_confirmation",
            "subject": "✅ Booking {{booking_status}} — {{session_name}}",
            "category": "Instructor-Led Training",
            "color": c["ilt"],
            "icon": "✅",
            "title": "ILT Booking Update",
            "variables": ["recipient_name", "booking_status", "session_name", "session_date", "session_time", "venue", "instructor_name", "booking_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Your booking for <strong>{{session_name}}</strong> has been <strong>{{booking_status}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#f0fdfa;border-left:4px solid #0D9488;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '🎯 <strong>Session:</strong> {{session_name}}<br/>'
                '📅 <strong>Date:</strong> {{session_date}}<br/>'
                '🕐 <strong>Time:</strong> {{session_time}}<br/>'
                '📍 <strong>Venue:</strong> {{venue}}<br/>'
                '👤 <strong>Instructor:</strong> {{instructor_name}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["ilt"], "{{booking_url}}", "View Booking →"),
        },
        {
            "notification_type": "ilt_session_start_reminder",
            "subject": "📅 Reminder: Your session '{{session_name}}' starts {{time_until}}",
            "category": "Instructor-Led Training",
            "color": c["ilt"],
            "icon": "📅",
            "title": "Session Starting Soon",
            "variables": ["recipient_name", "session_name", "session_date", "session_time", "time_until", "venue", "join_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Your instructor-led training session is coming up soon. Please make sure you are prepared!</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#f0fdfa;border-left:4px solid #0D9488;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '🎯 <strong>Session:</strong> {{session_name}}<br/>'
                '📅 <strong>Date:</strong> {{session_date}}<br/>'
                '🕐 <strong>Time:</strong> {{session_time}}<br/>'
                '⏳ <strong>Starting In:</strong> {{time_until}}<br/>'
                '📍 <strong>Venue:</strong> {{venue}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["ilt"], "{{join_url}}", "Join Session →"),
        },
        {
            "notification_type": "ilt_session_joining_instructions",
            "subject": "📋 Joining Instructions for {{session_name}}",
            "category": "Instructor-Led Training",
            "color": c["ilt"],
            "icon": "📋",
            "title": "Session Joining Instructions",
            "variables": ["recipient_name", "session_name", "session_date", "session_time", "venue", "join_url", "meeting_id", "passcode", "instructions", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Here are the joining instructions for your upcoming session <strong>{{session_name}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#f0fdfa;border-left:4px solid #0D9488;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '📅 <strong>Date & Time:</strong> {{session_date}} at {{session_time}}<br/>'
                '📍 <strong>Venue / Link:</strong> {{venue}}<br/>'
                '🔑 <strong>Meeting ID:</strong> {{meeting_id}}<br/>'
                '🔐 <strong>Passcode:</strong> {{passcode}}<br/>'
                '📋 <strong>Instructions:</strong> {{instructions}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["ilt"], "{{join_url}}", "Join Now →"),
        },
        {
            "notification_type": "ilt_waitlist_update",
            "subject": "📋 Waitlist Update for {{session_name}}",
            "category": "Instructor-Led Training",
            "color": c["ilt"],
            "icon": "📋",
            "title": "Waitlist Status Update",
            "variables": ["recipient_name", "session_name", "waitlist_status", "waitlist_position", "session_date", "session_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Your waitlist status for <strong>{{session_name}}</strong> has been updated.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#f0fdfa;border-left:4px solid #0D9488;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '🎯 <strong>Session:</strong> {{session_name}}<br/>'
                '📋 <strong>Status:</strong> {{waitlist_status}}<br/>'
                '🔢 <strong>Position:</strong> {{waitlist_position}}<br/>'
                '📅 <strong>Session Date:</strong> {{session_date}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["ilt"], "{{session_url}}", "View Session →"),
        },
        {
            "notification_type": "ilt_signup_prompt",
            "subject": "🎯 Don't miss out — Sign up for {{session_name}}",
            "category": "Instructor-Led Training",
            "color": c["ilt"],
            "icon": "🎯",
            "title": "Sign Up for Instructor-Led Training",
            "variables": ["recipient_name", "session_name", "session_date", "available_seats", "session_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'An instructor-led training session is available and has limited seats. Register now to secure your spot!</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#f0fdfa;border-left:4px solid #0D9488;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '🎯 <strong>Session:</strong> {{session_name}}<br/>'
                '📅 <strong>Date:</strong> {{session_date}}<br/>'
                '💺 <strong>Available Seats:</strong> {{available_seats}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["ilt"], "{{session_url}}", "Register Now →"),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 9. MENTORING & REVIEWS
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "mentor_connection_request",
            "subject": "🤝 Mentor Connection Request — {{requester_name}}",
            "category": "Mentoring & Reviews",
            "color": c["mentoring"],
            "icon": "🤝",
            "title": "Mentor Connection Request",
            "variables": ["recipient_name", "requester_name", "requester_role", "message", "request_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                '<strong>{{requester_name}}</strong> ({{requester_role}}) has sent you a mentor connection request.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#faf5ff;border-left:4px solid #9333EA;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#6b21a8;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Their Message</p>'
                '<p style="margin:0;color:#333;font-size:14px;line-height:1.7;font-style:italic;">"{{message}}"</p>'
                '</td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["mentoring"], "{{request_url}}", "Respond to Request →"),
        },
        {
            "notification_type": "performance_review_reminder",
            "subject": "📊 Performance Review Due — {{review_period}}",
            "category": "Mentoring & Reviews",
            "color": c["mentoring"],
            "icon": "📊",
            "title": "Performance Review Reminder",
            "variables": ["recipient_name", "review_period", "due_date", "reviewee_name", "review_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'This is a reminder that a performance review is due for the period <strong>{{review_period}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#faf5ff;border-left:4px solid #9333EA;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#333;font-size:14px;line-height:1.7;">'
                '📅 <strong>Review Period:</strong> {{review_period}}<br/>'
                '📅 <strong>Due Date:</strong> {{due_date}}<br/>'
                '👤 <strong>Reviewee:</strong> {{reviewee_name}}'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["mentoring"], "{{review_url}}", "Complete Review →"),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 10. ACCOUNT & AUTHENTICATION
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "welcome_message",
            "subject": "Welcome to LMS Platform, {{recipient_name}}! 🎉",
            "category": "Account & Authentication",
            "color": c["achievements"],
            "icon": "👋",
            "title": "Welcome to the Platform",
            "variables": ["recipient_name", "dashboard_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                "We're thrilled to have you on board! Your account has been successfully created and you're all set to begin your learning journey.</p>"
                '<table cellpadding="0" cellspacing="0" style="background:#ecfdf5;border-left:4px solid #059669;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#065f46;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;">Get Started</p>'
                '<p style="margin:0;color:#333;font-size:14px;line-height:1.9;">'
                '🎓&nbsp; Browse available courses<br/>'
                '📚&nbsp; Set up your learning profile<br/>'
                '🏆&nbsp; Track your achievements<br/>'
                '📅&nbsp; Join upcoming live sessions'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["achievements"], "{{dashboard_url}}", "Go to Dashboard →"),
        },
        {
            "notification_type": "otp_verification",
            "subject": "Your Verification Code — {{otp_code}}",
            "category": "Account & Authentication",
            "color": c["admin"],
            "icon": "🔐",
            "title": "Email Verification OTP",
            "variables": ["recipient_name", "otp_code", "expires_in", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Please use the One-Time Password (OTP) below to verify your identity. '
                'This code is valid for <strong>{{expires_in}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" width="100%" style="margin:24px 0;">'
                '<tr><td align="center">'
                '<div style="display:inline-block;background:#fff5f5;border:2px solid #DC2626;border-radius:10px;padding:20px 48px;">'
                '<p style="margin:0 0 8px;color:#DC2626;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;">Your OTP Code</p>'
                '<p style="margin:0;color:#DC2626;font-size:38px;font-weight:800;letter-spacing:14px;font-family:monospace;">{{otp_code}}</p>'
                '</div>'
                '</td></tr></table>'
                '<p style="color:#777777;font-size:13px;line-height:1.6;margin:8px 0 0;">'
                '⚠️ Never share this code with anyone. If you did not request this, please ignore this email.'
                '</p>'
                + SIG
            ),
        },
        {
            "notification_type": "forgot_password_otp",
            "subject": "Password Reset OTP — {{otp_code}}",
            "category": "Account & Authentication",
            "color": c["admin"],
            "icon": "🔑",
            "title": "Password Reset OTP",
            "variables": ["recipient_name", "otp_code", "expires_in", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'We received a request to reset the password for your account. '
                'Use the OTP below to proceed. This code expires in <strong>{{expires_in}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" width="100%" style="margin:24px 0;">'
                '<tr><td align="center">'
                '<div style="display:inline-block;background:#fff5f5;border:2px solid #DC2626;border-radius:10px;padding:20px 48px;">'
                '<p style="margin:0 0 8px;color:#DC2626;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;">Password Reset OTP</p>'
                '<p style="margin:0;color:#DC2626;font-size:38px;font-weight:800;letter-spacing:14px;font-family:monospace;">{{otp_code}}</p>'
                '</div>'
                '</td></tr></table>'
                '<p style="color:#777777;font-size:13px;line-height:1.6;margin:8px 0 0;">'
                '⚠️ If you did not request a password reset, please ignore this email or contact support immediately.'
                '</p>'
                + SIG
            ),
        },
        {
            "notification_type": "password_reset_confirmation",
            "subject": "✅ Your Password Has Been Reset Successfully",
            "category": "Account & Authentication",
            "color": c["communication"],
            "icon": "✅",
            "title": "Password Changed Successfully",
            "variables": ["recipient_name", "reset_time", "support_url", "platform_url", "unsubscribe_url", "preferences_url", "current_year"],
            "body": (
                GREET +
                '<p style="color:#333333;font-size:15px;line-height:1.7;margin:0 0 14px;">'
                'Your account password has been changed successfully on <strong>{{reset_time}}</strong>.</p>'
                '<table cellpadding="0" cellspacing="0" style="background:#eff6ff;border-left:4px solid #2563EB;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0;width:100%;">'
                '<tr><td><p style="margin:0;color:#1e40af;font-size:14px;line-height:1.8;">'
                '🔒&nbsp; Your account is now secured with your new password.<br/>'
                '⚠️&nbsp; If you did not make this change, contact our support team immediately.'
                '</p></td></tr></table>'
                + SIG
            ),
            "cta": _cta_button(c["communication"], "{{support_url}}", "Contact Support →"),
        },
    ]


# ---------------------------------------------------------------------------
# Alembic table reference (no ORM model import needed in migrations)
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
                "channel": "email",
                "subject": tpl["subject"],
                "template_html": _build_html(
                    color=tpl["color"],
                    icon=tpl["icon"],
                    category=tpl["category"],
                    title=tpl["title"],
                    body_html=tpl["body"],
                    cta_html=tpl.get("cta", ""),
                ),
                "template_text": None,
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
        "DELETE FROM notification_templates WHERE channel = 'email' AND version = 1"
    )
