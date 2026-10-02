import os
import smtplib
from email.message import EmailMessage
from urllib.parse import quote

from dotenv import load_dotenv


load_dotenv()

MAIL_HOST = os.getenv("MAIL_HOST")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USERNAME)

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://127.0.0.1:8000"
)


def send_verification_email(
    recipient_email: str,
    username: str,
    verification_token: str
):
    """
    Send an email verification link to a newly registered user.
    """

    if not MAIL_HOST:
        raise ValueError("MAIL_HOST is not configured in .env")

    if not MAIL_USERNAME:
        raise ValueError("MAIL_USERNAME is not configured in .env")

    if not MAIL_PASSWORD:
        raise ValueError("MAIL_PASSWORD is not configured in .env")

    # URL-encode both values so a "+", "/", "=" or "#" anywhere in
    # the token or email can never corrupt or truncate the query string.
    safe_token = quote(verification_token, safe="")
    safe_email = quote(recipient_email, safe="")

    verification_url = (
        f"{FRONTEND_URL}/verify-email.html"
        f"?token={safe_token}"
        f"&email={safe_email}"
    )

    message = EmailMessage()
    message["Subject"] = "Verify your SnapDrive account"
    message["From"] = MAIL_FROM
    message["To"] = recipient_email

    # Plain-text fallback for clients that render it.
    message.set_content(
        f"""Hello {username},

Welcome to SnapDrive!

Thank you for creating your SnapDrive account.

Please verify your email address by opening the following link:

{verification_url}

This verification link will expire in 30 minutes.

If you did not create a SnapDrive account, you can ignore this email.

Regards,
SnapDrive Team
"""
    )

    # HTML alternative — the link lives inside an href attribute,
    # so it can't be broken by plain-text line wrapping, and most
    # clients render it as a clickable button/link.
    message.add_alternative(
        f"""\
<html>
  <body style="font-family: Arial, sans-serif; color: #111827;">
    <p>Hello {username},</p>
    <p>Welcome to SnapDrive! Please verify your email address:</p>
    <p>
      <a href="{verification_url}"
         style="display:inline-block;padding:10px 20px;
                background:#111827;color:#ffffff;
                border-radius:6px;text-decoration:none;">
        Verify Email
      </a>
    </p>
    <p>Or paste this link into your browser:</p>
    <p style="word-break: break-all;">{verification_url}</p>
    <p>This link will expire in 30 minutes.</p>
    <p>If you did not create a SnapDrive account, you can ignore this email.</p>
    <p>Regards,<br>SnapDrive Team</p>
  </body>
</html>
""",
        subtype="html"
    )

    try:
        with smtplib.SMTP(MAIL_HOST, MAIL_PORT, timeout=20) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.send_message(message)

        print(f"Verification email sent successfully to {recipient_email}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print("SMTP AUTHENTICATION ERROR")
        print("Check your Gmail address and App Password.")
        print(e)
        raise Exception(
            "Email authentication failed. Check MAIL_USERNAME and MAIL_PASSWORD."
        )

    except smtplib.SMTPConnectError as e:
        print("SMTP CONNECTION ERROR")
        print(e)
        raise Exception("Could not connect to the email server.")

    except Exception as e:
        print("EMAIL SENDING ERROR")
        print(type(e).__name__)
        print(e)
        raise Exception(f"Verification email could not be sent: {e}")