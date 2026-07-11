from django.core.mail import send_mail
from django.template.loader import render_to_string
from mjml import mjml_to_html
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_otp_email(email, otp):
    try:
        logger.info(f"Preparing to send OTP email to {email}")
        context = {
            "email": email,
            "otp": otp
        }

        email_body = render_to_string("account/otp_email.mjml", context)
        logger.info("Rendered body %s", email_body)
        result = mjml_to_html(email_body)
        if result.errors:
            logger.error(f"MJML conversion errors: {result.errors}")
            raise ValueError(f"MJML rendering failed: {result.errors}")
        html_content = result.html

        logger.info("Converted MJML to HTML for %s", email)
        send_mail(
            subject="Your OTP Code",
            message="",
            from_email=settings.EMAIL_SENDER_USER,
            recipient_list=[email],
            html_message=html_content
        )
    except Exception as e:
        logger.info(f"Error sending OTP email to {email}")
        logger.error(str(e))