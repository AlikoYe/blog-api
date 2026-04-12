import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation
from apps.users.models import DEFAULT_LANGUAGE, User

logger = logging.getLogger(__name__)


EMAIL_FROM = "noreply@blogapi.com"
SUPPORTED_EMAIL_LANGUAGES = ("en", "ru", "kk")


def send_welcome_email(user: User) -> None:
    lang = (
        user.language
        if user.language in SUPPORTED_EMAIL_LANGUAGES
        else DEFAULT_LANGUAGE
    )
    subject_template = f"emails/welcome/subject_{lang}.txt"
    body_template = f"emails/welcome/body_{lang}.html"
    context = {"user": user}
    current_language = translation.get_language()

    try:
        translation.activate(lang)
        subject = render_to_string(subject_template, context).strip()
        html_body = render_to_string(body_template, context)
    except Exception:
        logger.exception("Failed to render welcome email template for lang=%s", lang)
        return
    finally:
        translation.activate(current_language)

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=html_body,
            from_email=EMAIL_FROM,
            to=[user.email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send()

        logger.info("Welcome email sent to %s in language %s", user.email, lang)
    except Exception:
        logger.exception("Failed to send welcome email to %s", user.email)
