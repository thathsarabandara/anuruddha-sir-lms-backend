"""Add WhatsApp Notification Templates

Revision ID: nt003_whatsapp
Revises: nt002_inapp
Create Date: 2026-02-27

This migration seeds all WhatsApp notification templates into the
notification_templates table. Every template is bilingual:
  - English  : friendly, casual, modern tone
  - Singlish : natural mixed Sinhala + English (the way Sri Lankans text)

Jinja2-style {{variable}} placeholders are used throughout.
WhatsApp formatting used: *bold*, _italic_, ━ dividers, emojis.
"""

import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import column, table

# ---------------------------------------------------------------------------
# Alembic revision metadata
# ---------------------------------------------------------------------------
revision = "nt003_whatsapp"
down_revision = "nt002_inapp"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
DIVIDER = "━━━━━━━━━━━━━━━━━━━━"

def _wa(english_block: str, singlish_block: str) -> str:
    """Wrap English + Singlish blocks in a consistent WhatsApp template layout."""
    return (
        f"{DIVIDER}\n"
        f"🎓 *Anuruddha Sir - LMS Platform*\n"
        f"{DIVIDER}\n\n"
        f"{english_block}\n\n"
        f"{DIVIDER}\n"
        f"🇱🇰 *සිංහල*\n"
        f"{DIVIDER}\n\n"
        f"{singlish_block}\n\n"
        f"{DIVIDER}"
    )


# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------
def _templates():
    return [
        # ═══════════════════════════════════════════════════════════════════
        # 1. COURSE ENROLLMENT & ACCESS
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "enrollment_confirmation",
            "subject": "Enrollment Confirmed — {{course_name}}",
            "variables": ["recipient_name", "course_name", "instructor_name", "start_date", "course_url"],
            "template_text": _wa(
                english_block=(
                    "Hey, Son {{recipient_name}}! 👋\n\n"
                    "Great news — you're officially enrolled in *{{course_name}}*! 🎉\n\n"
                    "📘 *Course:* {{course_name}}\n"
                    "👤 *Instructor:* {{instructor_name}}\n"
                    "📅 *Start Date:* {{start_date}}\n\n"
                    "Head over to the platform and start your learning journey today!\n"
                    "🔗 {{course_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}}! ට 🎉\n\n"
                    "ඔබ *{{course_name}}* පාඨමාලාවට ලියාපදිංචි වූ බව තහවුරු කෙරිණ! 🙌\n\n"
                    "📘 *පාඨමාලාව:* {{course_name}}\n"
                    "👤 *ගුරුවරයා:* {{instructor_name}}\n"
                    "📅 *ආරම්භ දිනය:* {{start_date}}\n\n"
                    "ඉගෙනීම ආරම්භ කිරීමට ප්ලැට්ෆෝමයට ලොග් වන්න! 💪\n"
                    "🔗 {{course_url}}"
                ),
            ),
        },
        {
            "notification_type": "enrollment_expiration_warning",
            "subject": "Enrollment Expiring in {{days_remaining}} Days — {{course_name}}",
            "variables": ["recipient_name", "course_name", "expiry_date", "days_remaining"],
            "template_text": _wa(
                english_block=(
                    "Hey {{recipient_name}}! ⏳\n\n"
                    "Just a heads-up — your access to *{{course_name}}* expires in *{{days_remaining}} days* ({{expiry_date}}).\n\n"
                    "Finish your lessons.\n\n"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! ⚠️\n\n"
                    "ඔබගේ *{{course_name}}* ප්‍රවේශය *{{days_remaining}} දිනකින්* ({{expiry_date}}) කල් ඉකුත් වේ.\n\n"
                    "ඉක්මනින් ක්‍රියා කරන්න! පාඩම් සම්පූර්ණ කරන්න,.\n\n"
                ),
            ),
        },
        {
            "notification_type": "course_invitation_confirmation",
            "subject": "You're Invited to Join {{course_name}}",
            "variables": ["recipient_name", "inviter_name", "course_name", "registration_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! ✉️\n\n"
                    "*{{inviter_name}}* has invited you to join *{{course_name}}*Anuruddha Sir on LMS Platform.\n\n"
                    "Tap the link below to accept the invitation and get started!\n\n"
                    "✅ *Accept here:* {{registration_url}}\n\n"
                    "_If this invitation wasn't for you, simply ignore this message._"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට 📨\n\n"
                    "*{{inviter_name}}* ඔබව *{{course_name}}* පාඨමාලාවට ආරාධනා කළේ! 🎓\n\n"
                    "ආරාධනාව පිළිගැනීමට සබැඳිය ක්ලික් කරන්න!\n\n"
                    "✅ *පිළිගැනීමට:* {{registration_url}}\n\n"
                    "_ඔබ වෙනුවෙන් ආරාධනාවක් නොමැති නම් නොසලකා හරින්න._"
                ),
            ),
        },
        {
            "notification_type": "enrollment_request_approved_rejected",
            "subject": "Enrollment Request {{status}} — {{course_name}}",
            "variables": ["recipient_name", "course_name", "status", "reason", "course_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! 📩\n\n"
                    "Your enrollment request for *{{course_name}}* has been *{{status}}*.\n\n"
                    "📘 *Course:* {{course_name}}\n"
                    "✅ *Status:* {{status}}\n"
                    "💬 *Reason:* {{reason}}\n\n"
                    "🔗 *View course:* {{course_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට 📩\n\n"
                    "ඔබගේ *{{course_name}}* ලියාපදිංචි ඉල්ලීම *{{status}}* විය! 📋\n\n"
                    "📘 *පාඨමාලාව:* {{course_name}}\n"
                    "✅ *තත්ත්වය:* {{status}}\n"
                    "💬 *හේතුව:* {{reason}}\n\n"
                    "🔗 *පාඨමාලාව බලන්න:* {{course_url}}"
                ),
            ),
        },
        {
            "notification_type": "welcome_new_enrollment",
            "subject": "Welcome to {{course_name}}! 🚀",
            "variables": ["recipient_name", "course_name", "instructor_name", "first_lesson_url"],
            "template_text": _wa(
                english_block=(
                    "Welcome aboard, {{recipient_name}}! 🚀\n\n"
                    "We're so glad to have you in *{{course_name}}*. Your journey starts now — let's make it count!\n\n"
                    "👤 *Instructor:* {{instructor_name}}\n\n"
                    "💡 Tip: Stay consistent, track your progress, and don't hesitate to ask questions.\n\n"
                    "▶️ *Start your first lesson:* {{first_lesson_url}}"
                ),
                singlish_block=(
                    "ආයුබෝවන් {{recipient_name}}! 🎉\n\n"
                    "ඔබ *{{course_name}}* පාඨමාලාවට සම්බන්ධ වීම ගැන අපි ගොඩක් සතුටු වෙනවා. 🙌\n\n"
                    "👤 *ගුරුවරයා:* {{instructor_name}}\n\n"
                    "💡 ඉඟිය: දිනපතා කාලසටහනක් සකසා ඉගෙනීම ඉදිරියට ගෙන යන්න. 😄\n\n"
                    "▶️ *පළමු පාඩමට යන්න:* {{first_lesson_url}}"
                ),
            ),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 2. ASSIGNMENTS & GRADING
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "assignment_submitted_instructor",
            "subject": "New Submission — {{assignment_name}} by {{student_name}}",
            "variables": ["recipient_name", "student_name", "course_name", "assignment_name", "submitted_at", "submission_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! 📝\n\n"
                    "*{{student_name}}* just submitted *{{assignment_name}}* for your review.\n\n"
                    "📘 *Course:* {{course_name}}\n"
                    "🕐 *Submitted:* {{submitted_at}}\n\n"
                    "🔗 *Review submission:* {{submission_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! 📋\n\n"
                    "*ඔබගේ අධ්‍යයනය සඳහා{{student_name}}* *{{assignment_name}}* පැවරුම ඉදිරිපත් කළා..\n\n"
                    "📘 *පාඨමාලාව:* {{course_name}}\n"
                    "📄 *පැවරුම:* {{assignment_name}}\n"
                    "🕐 *ඉදිරිපත් කළ:* {{submitted_at}}\n\n"
                    "🔗 *අධ්‍යයනය කරන්න:* {{submission_url}}"
                ),
            ),
        },
        {
            "notification_type": "assignment_graded_student",
            "subject": "Assignment Graded — {{assignment_name}}",
            "variables": ["recipient_name", "assignment_name", "course_name", "grade", "max_grade", "feedback", "submission_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! ✅\n\n"
                    "Your assignment *{{assignment_name}}* has been graded. Check out your result!\n\n"
                    "📘 *Course:* {{course_name}}\n"
                    "🏆 *Grade:* {{grade}} / {{max_grade}}\n"
                    "💬 *Feedback:* {{feedback}}\n\n"
                    "🔗 *View feedback:* {{submission_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! 🎉\n\n"
                    "ඔබගේ *{{assignment_name}}* පැවරුම ශ්‍රේණිගත කෙරිණ! ප්‍රතිඵල බලන්න!\n\n"
                    "📘 *පාඨමාලාව:* {{course_name}}\n"
                    "🏆 *ලකුණු:* {{grade}} / {{max_grade}}\n"
                    "💬 *ප්‍රතිපෝෂණය:* {{feedback}}\n\n"
                    "🔗 *බලන්න:* {{submission_url}}"
                ),
            ),
        },
        {
            "notification_type": "assignment_submitted_late_instructor",
            "subject": "⚠️ Late Submission — {{assignment_name}} by {{student_name}}",
            "variables": ["recipient_name", "student_name", "course_name", "assignment_name", "due_date", "submitted_at", "delay", "submission_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! ⚠️\n\n"
                    "A *late submission* was received from *{{student_name}}* for *{{assignment_name}}*.\n\n"
                    "📅 *Due Date:* {{due_date}}\n"
                    "🕐 *Submitted:* {{submitted_at}}\n"
                    "⏱️ *Late By:* {{delay}}\n\n"
                    "🔗 *Review submission:* {{submission_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! ⚠️\n\n"
                    "*{{student_name}}* ගෙන් *{{assignment_name}}* ප්‍රමාද වූ ඉදිරිපත් කිරීමක් ලැබුණි.!\n\n"
                    "📅 *කාලසීමාව:* {{due_date}}\n"
                    "🕐 *ඉදිරිපත් කළ:* {{submitted_at}}\n"
                    "⏱️ *ප්‍රමාදය:* {{delay}}\n\n"
                    "🔗 *අධ්‍යයනය කරන්න:* {{submission_url}}"
                ),
            ),
        },
        {
            "notification_type": "submission_comment_added",
            "subject": "New Comment on Submission — {{assignment_name}}",
            "variables": ["recipient_name", "commenter_name", "course_name", "assignment_name", "comment_preview", "submission_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! 💬\n\n"
                    "*{{commenter_name}}* left a comment on the submission for *{{assignment_name}}*.\n\n"
                    "_\"{{comment_preview}}\"_\n\n"
                    "🔗 *View full comment:* {{submission_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! 💬\n\n"
                    "*{{commenter_name}}* ඔබගේ *{{assignment_name}}* ඉදිරිපත් කිරීම ගැන අදහසක් දැක්වීය!\n\n"
                    "_\"{{comment_preview}}\"_\n\n"
                    "🔗 *අදහස බලන්න:* {{submission_url}}"
                ),
            ),
        },
        {
            "notification_type": "essay_question_graded",
            "subject": "Essay / Question Graded — {{lesson_name}}",
            "variables": ["recipient_name", "course_name", "lesson_name", "grade", "max_grade", "feedback", "lesson_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! 📝\n\n"
                    "Your essay / lesson question in *{{lesson_name}}* has been graded.\n\n"
                    "📘 *Course:* {{course_name}}\n"
                    "📖 *Lesson:* {{lesson_name}}\n"
                    "🏆 *Grade:* {{grade}} / {{max_grade}}\n"
                    "💬 *Feedback:* {{feedback}}\n\n"
                    "🔗 *View graded work:* {{lesson_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! 📝\n\n"
                    "*{{lesson_name}}* හි ඔබගේ පාඩම් ප්‍රශ්නය ශ්‍රේණිගත කර ඇත.!\n\n"
                    "📘 *පාඨමාලාව:* {{course_name}}\n"
                    "🏆 *ලකුණු:* {{grade}} / {{max_grade}}\n"
                    "💬 *ප්‍රතිපෝෂණය:* {{feedback}}\n\n"
                    "🔗 *බලන්න:* {{lesson_url}}"
                ),
            ),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 3. DEADLINES & REMINDERS
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "upcoming_due_date_reminder",
            "subject": "⏰ Due Soon — {{assignment_name}}",
            "variables": ["recipient_name", "assignment_name", "course_name", "due_date", "time_until_due", "submission_url"],
            "template_text": _wa(
                english_block=(
                    "Hey {{recipient_name}}! ⏰\n\n"
                    "Friendly reminder — *{{assignment_name}}* is due in *{{time_until_due}}*.\n\n"
                    "📘 *Course:* {{course_name}}\n"
                    "📅 *Due:* {{due_date}}\n"
                    "⏳ *Time Left:* {{time_until_due}}\n\n"
                    "Don't leave it to the last minute! Submit early. 🙏\n\n"
                    "🔗 *Submit now:* {{submission_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! ⏰\n\n"
                    "*{{assignment_name}}* කාලසීමාව ළං වෙමින් ඇත! *{{time_until_due}}* ක් ඉතිරිව ඇත!\n\n"
                    "📘 *පාඨමාලාව:* {{course_name}}\n"
                    "📅 *කාලසීමාව:* {{due_date}}\n\n"
                    "ඉක්මනින් ඉදිරිපත් කරන්න! 🙏\n\n"
                    "🔗 *ඉදිරිපත් කිරීමට:* {{submission_url}}"
                ),
            ),
        },
        {
            "notification_type": "past_due_date_reminder",
            "subject": "🔴 Overdue — {{assignment_name}}",
            "variables": ["recipient_name", "assignment_name", "course_name", "due_date", "overdue_by", "submission_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}} 😟\n\n"
                    "The deadline for *{{assignment_name}}* has already passed.\n\n"
                    "📘 *Course:* {{course_name}}\n"
                    "📅 *Was Due:* {{due_date}}\n"
                    "⏱️ *Overdue By:* {{overdue_by}}\n\n"
                    "Please contact your instructor if you need an extension.\n\n"
                    "🔗 *Submit anyway:* {{submission_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! 😟\n\n"
                    "*{{assignment_name}}* කාලසීමාව ඉකුත් විය! *{{overdue_by}}* ක් ප්‍රමාදයෙන් ඇත!\n\n"
                    "📘 *පාඨමාලාව:* {{course_name}}\n"
                    "📅 *කාලසීමාව:* {{due_date}}\n\n"
                    "දිගු කිරීමක් අවශ්‍ය නම් ගුරුවරයාගෙන් ඉල්ලන්න. 🙏\n\n"
                    "🔗 *අධ්‍යයනයට:* {{submission_url}}"
                ),
            ),
        },
        {
            "notification_type": "activity_start_date_reminder",
            "subject": "📅 Activity Starting Soon — {{activity_name}}",
            "variables": ["recipient_name", "activity_name", "course_name", "start_date", "time_until_start", "activity_url"],
            "template_text": _wa(
                english_block=(
                    "Hey {{recipient_name}}! 📅\n\n"
                    "Your course activity *{{activity_name}}* is starting very soon!\n\n"
                    "📘 *Course:* {{course_name}}\n"
                    "🎯 *Activity:* {{activity_name}}\n"
                    "📅 *Starts:* {{start_date}}\n"
                    "⏳ *Starts In:* {{time_until_start}}\n\n"
                    "Get ready and be on time! 🙌\n\n"
                    "🔗 *View activity:* {{activity_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! 📅\n\n"
                    "*{{activity_name}}* පන්තිය ළං වෙමින් ඇත! සූදානම් වන්න!\n\n"
                    "📘 *පාඨමාලාව:* {{course_name}}\n"
                    "🎯 *පන්තිය:* {{activity_name}}\n"
                    "📅 *ආරම්භ:* {{start_date}}\n"
                    "⏳ *ඉතිරි කාලය:* {{time_until_start}}\n\n"
                    "ප්‍රමාද නොවෙන්න! 😄\n\n"
                    "🔗 *බලන්න:* {{activity_url}}"
                ),
            ),
        },
        {
            "notification_type": "quiz_attempt_overdue_warning",
            "subject": "⚠️ Quiz Attempt Overdue — {{quiz_name}}",
            "variables": ["recipient_name", "quiz_name", "course_name", "due_date", "quiz_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! ⚠️\n\n"
                    "Your quiz attempt window for *{{quiz_name}}* has expired.\n\n"
                    "📘 *Course:* {{course_name}}\n"
                    "📅 *Was Due:* {{due_date}}\n\n"
                    "Please contact your instructor if you believe this is an error.\n\n"
                    "🔗 *View quiz:* {{quiz_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! ⚠️\n\n"
                    "*{{quiz_name}}* ප්‍රශ්නාවලිය ආරම්භ කිරීමේ කාලසීමාව ඉකුත් විය!\n\n"
                    "📘 *පාඨමාලාව:* {{course_name}}\n"
                    "📅 *කාලසීමාව:* {{due_date}}\n\n"
                    "ගැටළුවක් ඇත්නම් ගුරුවරයාගෙන් අහන්න! 🙏\n\n"
                    "🔗 *ප්‍රශ්නාවලිය බලන්න:* {{quiz_url}}"
                ),
            ),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 4. QUIZZES & TESTS
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "quiz_submission_confirmation_student",
            "subject": "✅ Quiz Submitted — {{quiz_name}}",
            "variables": ["recipient_name", "quiz_name", "course_name", "submitted_at", "total_questions", "quiz_url"],
            "template_text": _wa(
                english_block=(
                    "Well done, {{recipient_name}}! ✅\n\n"
                    "Your quiz *{{quiz_name}}* has been submitted successfully!\n\n"
                    "📘 *Course:* {{course_name}}\n"
                    "🕐 *Submitted:* {{submitted_at}}\n"
                    "❓ *Total Questions:* {{total_questions}}\n\n"
                    "Results will be available once grading is complete. Good luck! 🤞\n\n"
                    "🔗 *View submission:* {{quiz_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට 🎉\n\n"
                    "*{{quiz_name}}* ප්‍රශ්නාවලිය සාර්ථකව ඉදිරිපත් කර ඇත!\n\n"
                    "📘 *පාඨමාලාව:* {{course_name}}\n"
                    "🕐 *ඉදිරිපත් කළ:* {{submitted_at}}\n\n"
                    "ප්‍රතිඵල ලැබූ සැනින් දැනුම් දෙනු ලැ‍බේ. ශුභ පැතුම්! 🤞\n\n"
                    "🔗 *බලන්න:* {{quiz_url}}"
                ),
            ),
        },
        {
            "notification_type": "quiz_submission_notification_instructor",
            "subject": "Quiz Submitted by {{student_name}} — {{quiz_name}}",
            "variables": ["recipient_name", "student_name", "quiz_name", "course_name", "submitted_at", "submission_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! 📝\n\n"
                    "*{{student_name}}* completed and submitted *{{quiz_name}}*. It may need manual grading.\n\n"
                    "📘 *Course:* {{course_name}}\n"
                    "🕐 *Submitted:* {{submitted_at}}\n\n"
                    "🔗 *Grade quiz:* {{submission_url}}"
                ),
                singlish_block=(
                    "ගුරු {{recipient_name}} ට! 📝\n\n"
                    "*{{student_name}}*  ප්‍රශ්නාවලිය ඉදිරිපත් කරනා ලදී! *{{quiz_name}}* ශ්‍රේණිගත කිරීම අවශ්‍ය විය හැකිය!\n\n"
                    "📘 *පාඨමාලාව:* {{course_name}}\n"
                    "🕐 *ඉදිරිපත් කළ:* {{submitted_at}}\n\n"
                    "🔗 *ශ්‍රේණිගත කිරීමට:* {{submission_url}}"
                ),
            ),
        },
        {
            "notification_type": "quiz_graded_notification",
            "subject": "🏆 Quiz Result Ready — {{quiz_name}}",
            "variables": ["recipient_name", "quiz_name", "course_name", "score", "max_score", "percentage", "passed", "quiz_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! 🏆\n\n"
                    "Your result for *{{quiz_name}}* is now available!\n\n"
                    "📘 *Course:* {{course_name}}\n"
                    "🏆 *Score:* {{score}} / {{max_score}} ({{percentage}}%)\n"
                    "✅ *Result:* {{passed}}\n\n"
                    "Keep it up — you're doing great! 💪\n\n"
                    "🔗 *View result:* {{quiz_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! 🏆\n\n"
                    "*{{quiz_name}}* ප්‍රශ්නාවලිය ප්‍රතිඵල ලැබිණ! බලන්න!\n\n"
                    "📘 *පාඨමාලාව:* {{course_name}}\n"
                    "🏆 *ලකුණු:* {{score}} / {{max_score}} ({{percentage}}%)\n"
                    "✅ *ප්‍රතිඵලය:* {{passed}}\n\n"
                    "ඒක දිගටම කරගෙන යන්න — ඔයා නියමයි! 💪\n\n"
                    "🔗 *ප්‍රතිඵලය බලන්න:* {{quiz_url}}"
                ),
            ),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 5. ACHIEVEMENTS & FEEDBACK
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "badge_awarded",
            "subject": "🏅 Badge Earned — {{badge_name}}",
            "variables": ["recipient_name", "badge_name", "badge_description", "course_name", "awarded_at", "badges_url"],
            "template_text": _wa(
                english_block=(
                    "Congratulations, {{recipient_name}}! 🏅\n\n"
                    "You've earned the *{{badge_name}}* badge — amazing achievement!\n\n"
                    "📝 *Description:* {{badge_description}}\n"
                    "📘 *Earned In:* {{course_name}}\n"
                    "📅 *Awarded:* {{awarded_at}}\n\n"
                    "Keep up the fantastic work and collect more badges! 🌟\n\n"
                    "🔗 *View badges:* {{badges_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට සුභ පැතුම් 🏅🎉\n\n"
                    "ඔබට *{{badge_name}}* ත්‍යාගය ලැබිණ! විශ්මිත ජයග්‍රහණයක්! 💪\n\n"
                    "📝 *විස්තරය:* {{badge_description}}\n"
                    "📘 *ලැබිණේ:* {{course_name}} හිදී\n"
                    "📅 *ලැබිණ:* {{awarded_at}}\n\n"
                    "අපූරු වැඩ දිගටම කරගෙන ගොස් තවත් ලාංඡන එකතු කරන්න පුළුවන්! 😄🌟\n\n"
                    "🔗 *ත්‍යාග බලන්න:* {{badges_url}}"
                ),
            ),
        },
        {
            "notification_type": "course_completion_certificate",
            "subject": "🎓 Course Completed — Certificate Ready!",
            "variables": ["recipient_name", "course_name", "completion_date", "certificate_url", "certificate_id"],
            "template_text": _wa(
                english_block=(
                    "Amazing job, {{recipient_name}}! 🎓🎉\n\n"
                    "You successfully completed *{{course_name}}*! Your certificate is ready to download.\n\n"
                    "📅 *Completed On:* {{completion_date}}\n"
                    "🔖 *Certificate ID:* {{certificate_id}}\n\n"
                    "you deserve the recognition! 🌟\n\n"
                    "🔗 *Download certificate:* {{certificate_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}}!! 🎓🎉\n\n"
                    "ඔබ *{{course_name}}* පාඨමාලාව සාර්ථකව සම්පූර්ණ කළා! ඔබගේ සහතිකය බාගත කිරීමට සූදානම්.\n\n"
                    "📅 *සම්පූර්ණ කළ:* {{completion_date}}\n"
                    "🔖 *සහතිකය ID:* {{certificate_id}}\n\n"
                    "ඔබ පිළිගැනීමට සුදුසුයි! 💪🌟\n\n"
                    "🔗 *සහතිකය බාගත:* {{certificate_url}}"
                ),
            ),
        },
        {
            "notification_type": "feedback_review_submission",
            "subject": "⭐ New Review for {{course_name}}",
            "variables": ["recipient_name", "reviewer_name", "course_name", "rating", "review_preview", "review_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! ⭐\n\n"
                    "*{{reviewer_name}}* submitted a new review for *{{course_name}}*.\n\n"
                    "⭐ *Rating:* {{rating}} / 5\n"
                    "💬 *Preview:* _\"{{review_preview}}\"_\n\n"
                    "🔗 *Read full review:* {{review_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! ⭐\n\n"
                    "*{{reviewer_name}}* *{{course_name}}* සඳහා නව සමාලෝචනයක් ඉදිරිපත් කරන ලදී!\n\n"
                    "⭐ *ශ්‍රේණිය:* {{rating}} / 5\n"
                    "💬 *සමාලෝචනය:* _\"{{review_preview}}\"_\n\n"
                    "🔗 *සම්පූර්ණ සමාලෝචනය:* {{review_url}}"
                ),
            ),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 6. COMMUNICATION & COLLABORATION
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "new_forum_post_reply",
            "subject": "💬 New Forum Reply — {{forum_topic}}",
            "variables": ["recipient_name", "poster_name", "forum_topic", "course_name", "reply_preview", "forum_url"],
            "template_text": _wa(
                english_block=(
                    "Hey {{recipient_name}}! 💬\n\n"
                    "*{{poster_name}}* replied to *{{forum_topic}}* in {{course_name}}.\n\n"
                    "_\"{{reply_preview}}\"_\n\n"
                    "🔗 *Join the discussion:* {{forum_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! 💬\n\n"
                    "*{{poster_name}}* *{{course_name}}* හි *{{forum_topic}}* ගැන පිළිතුරක් ලියූ!\n\n"
                    "_\"{{reply_preview}}\"_\n\n"
                    "ඔබේ අදහසද දක්වන්න! 😄\n\n"
                    "🔗 *සාකච්ඡාව:* {{forum_url}}"
                ),
            ),
        },
        {
            "notification_type": "new_personal_message",
            "subject": "✉️ New Message from {{sender_name}}",
            "variables": ["recipient_name", "sender_name", "message_preview", "message_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! ✉️\n\n"
                    "You've got a new message from *{{sender_name}}*.\n\n"
                    "_\"{{message_preview}}\"_\n\n"
                    "🔗 *Read message:* {{message_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! ✉️\n\n"
                    "*{{sender_name}}* ඔබට නව පණිවිඩයක් යැව්වා!\n\n"
                    "_\"{{message_preview}}\"_\n\n"
                    "🔗 *පණිවිඩය:* {{message_url}}"
                ),
            ),
        },
        {
            "notification_type": "user_added_to_conversation",
            "subject": "You've Been Added to a Conversation — {{conversation_name}}",
            "variables": ["recipient_name", "added_by", "conversation_name", "participants", "conversation_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! 💬\n\n"
                    "*{{added_by}}* added you to the conversation *{{conversation_name}}*.\n\n"
                    "👥 *Participants:* {{participants}}\n\n"
                    "🔗 *Join conversation:* {{conversation_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! 👋\n\n"
                    "*{{added_by}}* ඔබව *{{conversation_name}}* කතාබහට එකතු කළේ!\n\n"
                    "👥 *සහභාගිවන්නෝ:* {{participants}}\n\n"
                    "🔗 *කතාබහ:* {{conversation_url}}"
                ),
            ),
        },
        {
            "notification_type": "new_course_announcement",
            "subject": "📢 New Announcement — {{course_name}}",
            "variables": ["recipient_name", "course_name", "posted_by", "announcement_title", "announcement_preview", "announcement_url"],
            "template_text": _wa(
                english_block=(
                    "📢 Attention {{recipient_name}}!\n\n"
                    "*{{posted_by}}* made a new announcement in *{{course_name}}*.\n\n"
                    "📌 *{{announcement_title}}*\n"
                    "_{{announcement_preview}}_\n\n"
                    "🔗 *Read full announcement:* {{announcement_url}}"
                ),
                singlish_block=(
                    "📢 ආදරණීය පුතා/දියණිය {{recipient_name}} ට!\n\n"
                    "*{{posted_by}}* *{{course_name}}* ගෙන නිවේදනයක් ලියූ!\n\n"
                    "📌 *{{announcement_title}}*\n"
                    "_{{announcement_preview}}_\n\n"
                    "කරුණාකර කියවා ගන්න. 🙏\n\n"
                    "🔗 *සම්පූර්ණ නිවේදනය:* {{announcement_url}}"
                ),
            ),
        },
        {
            "notification_type": "comment_learning_plan",
            "subject": "💬 New Comment on Your Learning Plan",
            "variables": ["recipient_name", "commenter_name", "learning_plan_name", "comment_preview", "plan_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! 💬\n\n"
                    "*{{commenter_name}}* commented on your learning plan *{{learning_plan_name}}*.\n\n"
                    "_\"{{comment_preview}}\"_\n\n"
                    "🔗 *View comment:* {{plan_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! 💬\n\n"
                    "*{{commenter_name}}* ඔබගේ *{{learning_plan_name}}* ඉගෙනීම් සැලැස්ම ගැන අදහසක් දැක්වීය!\n\n"
                    "_\"{{comment_preview}}\"_\n\n"
                    "🔗 *අදහස:* {{plan_url}}"
                ),
            ),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 7. INSTRUCTOR-LED TRAINING (ILT)
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "ilt_booking_confirmation",
            "subject": "ILT Booking {{booking_status}} — {{session_name}}",
            "variables": ["recipient_name", "booking_status", "session_name", "session_date", "session_time", "venue", "instructor_name", "booking_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! ✅\n\n"
                    "Your booking for *{{session_name}}* has been *{{booking_status}}*.\n\n"
                    "📅 *Date:* {{session_date}}\n"
                    "🕐 *Time:* {{session_time}}\n"
                    "📍 *Venue:* {{venue}}\n"
                    "👤 *Instructor:* {{instructor_name}}\n\n"
                    "🔗 *View booking:* {{booking_url}}"
                ),
                singlish_block=(
                    "{{recipient_name}} ට! ✅\n\n"
                    "*{{session_name}}* සත්කාරය සඳහා ඔබේ ලියාපදිංචිය *{{booking_status}}* විය!\n\n"
                    "📅 *දිනය:* {{session_date}}\n"
                    "🕐 *වේලාව:* {{session_time}}\n"
                    "📍 *ස්ථානය:* {{venue}}\n"
                    "👤 *ගුරුවරයා:* {{instructor_name}}\n\n"
                    "🔗 *ලියාපදිංචිය:* {{booking_url}}"
                ),
            ),
        },
        {
            "notification_type": "ilt_session_start_reminder",
            "subject": "Session Starting Soon — {{session_name}}",
            "variables": ["recipient_name", "session_name", "session_date", "session_time", "time_until", "venue", "join_url"],
            "template_text": _wa(
                english_block=(
                    "Hey {{recipient_name}}! ⏰\n\n"
                    "Your training session *{{session_name}}* is starting in *{{time_until}}*!\n\n"
                    "📅 *Date:* {{session_date}}\n"
                    "🕐 *Time:* {{session_time}}\n"
                    "📍 *Venue:* {{venue}}\n\n"
                    "Get ready and don't be late! 🙌\n\n"
                    "🔗 *Join session:* {{join_url}}"
                ),
                singlish_block=(
                    "{{recipient_name}} ට! ⏰\n\n"
                    "*{{session_name}}* පුහුණු සත්කාරය *{{time_until}}* ක් ඇතුළත ආරම්භ වේ!\n\n"
                    "📅 *දිනය:* {{session_date}}\n"
                    "🕐 *වේලාව:* {{session_time}}\n"
                    "📍 *ස්ථානය:* {{venue}}\n\n"
                    "සූදානම් වන්න! ප්‍රමාද නොවෙන්න! 🙌\n\n"
                    "🔗 *සත්කාරයට:* {{join_url}}"
                ),
            ),
        },
        {
            "notification_type": "ilt_signup_prompt",
            "subject": "🎯 Register Now — {{session_name}}",
            "variables": ["recipient_name", "session_name", "session_date", "available_seats", "session_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! 🎯\n\n"
                    "Don't miss out! *{{session_name}}* is open for registration.\n\n"
                    "📅 *Date:* {{session_date}}\n"
                    "💺 *Seats Available:* {{available_seats}}\n\n"
                    "Seats are limited, so sign up before they're gone! 🏃\n\n"
                    "🔗 *Register now:* {{session_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! 🎯\n\n"
                    "*{{session_name}}* සත්කාරය ලියාපදිංචිය සඳහා විවෘත!\n\n"
                    "📅 *දිනය:* {{session_date}}\n"
                    "💺 *ලබාගත හැකි ආසන:* {{available_seats}}\n\n"
                    "ආසන සීමිතයි! ඉක්මනින් ලියාපදිංචි වන්න! 🏃\n\n"
                    "🔗 *ලියාපදිංචිය:* {{session_url}}"
                ),
            ),
        },

        # ═══════════════════════════════════════════════════════════════════
        # 9. ACCOUNT & AUTHENTICATION
        # ═══════════════════════════════════════════════════════════════════
        {
            "notification_type": "welcome_message",
            "subject": "Welcome to LMS Platform",
            "variables": ["recipient_name", "dashboard_url"],
            "template_text": _wa(
                english_block=(
                    "Hey {{recipient_name}}! 👋\n\n"
                    "Welcome to *Anuruddha Sir - LMS Platform*! 🎉\n\n"
                    "Your account is ready. Here's what to explore:\n"
                    "🎓 Browse available courses\n"
                    "📚 Build your learning profile\n"
                    "🏆 Earn achievements & certifications\n"
                    "📅 Join upcoming live sessions\n\n"
                    "Start your learning journey now! 🚀\n\n"
                    "🔗 *Dashboard:* {{dashboard_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට ආයුබෝවන්! 👋\n\n"
                    "*Anuruddha Sir - LMS Platform* ට ඔබව සාදරයෙන් පිළිගනිමු! 🎉\n\n"
                    "ගිණුම සූදානම්! මේවා ගවේෂණය කරන්න:\n"
                    "🎓 පවතින පාඨමාලා පිරික්සන්න\n"
                    "📚 ඔබේ ඉගෙනුම් පැතිකඩ ගොඩනඟන්න\n"
                    "🏆 ජයග්‍රහණ සහ සහතික උපයන්න\n"
                    "📅 ඉදිරි සජීවී සැසිවලට සම්බන්ධ වන්න\n\n"
                    "දැන් ඉගෙනීම ආරම්භ කරන්න! 🚀\n\n"
                    "🔗 *ප්‍රධාන පුවරුව:* {{dashboard_url}}"
                ),
            ),
        },
        {
            "notification_type": "otp_verification",
            "subject": "Your OTP Verification Code",
            "variables": ["recipient_name", "otp_code", "expires_in"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! 🔐\n\n"
                    "Your email verification OTP is:\n\n"
                    "🔢 *{{otp_code}}*\n\n"
                    "⏳ Valid for *{{expires_in}}* only.\n\n"
                    "⚠️ Do NOT share this code with anyone.\n"
                    "If you didn't request this, ignore this message."
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! 🔐\n\n"
                    "ඔබගේ ඊමේල් සත්‍යාපන OTP:\n\n"
                    "🔢 *{{otp_code}}*\n\n"
                    "⏳ *{{expires_in}}* ක් පමණ ක්‍රියාත්මක.\n\n"
                    "⚠️ මෙම කේතය කිසිවකුට නොකියන්න.\n"
                    "ඔබ ඉල්ලා නොසිටියේ නම් නොසලකා හරින්න."
                ),
            ),
        },
        {
            "notification_type": "forgot_password_otp",
            "subject": "Password Reset OTP",
            "variables": ["recipient_name", "otp_code", "expires_in"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! 🔑\n\n"
                    "We received a password reset request for your account.\n\n"
                    "Your reset OTP is:\n\n"
                    "🔢 *{{otp_code}}*\n\n"
                    "⏳ Expires in *{{expires_in}}*.\n\n"
                    "⚠️ If you didn't request this, please ignore this message."
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! 🔑\n\n"
                    "ඔබේ ගිණුමේ මුරපදය නැවත සැකසීමේ ඉල්ලීමක් ලැබිණ.\n\n"
                    "නැවත සැකසීමේ OTP:\n\n"
                    "🔢 *{{otp_code}}*\n\n"
                    "⏳ *{{expires_in}}* ක් ඇතුලත කල් ඉකුත් වේ.\n\n"
                    "⚠️ ඔබ ඉල්ලා නොසිටියේ නම් නොසලකා හරින්න."
                ),
            ),
        },
        {
            "notification_type": "password_reset_confirmation",
            "subject": "Password Changed Successfully",
            "variables": ["recipient_name", "reset_time", "support_url"],
            "template_text": _wa(
                english_block=(
                    "Hi {{recipient_name}}! ✅\n\n"
                    "Your password was successfully changed at *{{reset_time}}*.\n\n"
                    "🔒 Your account is now secured with your new password.\n\n"
                    "⚠️ If you didn't do this, contact support immediately:\n"
                    "🔗 *Support:* {{support_url}}"
                ),
                singlish_block=(
                    "ආදරණීය පුතා/දියණිය {{recipient_name}} ට! ✅\n\n"
                    "*{{reset_time}}* දී ඔබේ මුරපදය සාර්ථකව වෙනස් කෙරිණ.\n\n"
                    "🔒 ඔබේ ගිණුම දැන් ආරක්ෂිතව ඇත.\n\n"
                    "⚠️ ඔබ මෙය නොකළේ නම් ඉක්මනින් සහාය ඇමතුම් කරන්න:\n"
                    "🔗 *සහාය:* {{support_url}}"
                ),
            ),
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
                "channel": "whatsapp",
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
        "DELETE FROM notification_templates WHERE channel = 'whatsapp' AND version = 1"
    )
