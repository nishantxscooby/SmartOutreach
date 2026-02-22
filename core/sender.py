import os
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "logs.txt")


def _log_to_file(message):
    """Append a timestamped log line to the logs file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def send_email(config, to_email, subject, body, log_callback=None):
    """Send an email via Gmail SMTP with optional resume attachment.

    Connects to smtp.gmail.com:587 using STARTTLS, authenticates with the
    configured credentials, and sends the message. Optionally attaches a
    resume file if ATTACH_RESUME is enabled and the file exists.

    Returns True on success, False on failure. Errors are logged but never
    re-raised so that one failed email does not halt the batch.
    """
    def _log(msg):
        if log_callback:
            log_callback(msg)

    try:
        _log(f"Connecting to SMTP server for {to_email}...")

        msg = MIMEMultipart("alternative")
        msg["From"] = config["EMAIL"]
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        if config.get("ATTACH_RESUME", False):
            resume_path = config.get("RESUME_PATH", "")
            if resume_path and os.path.exists(resume_path):
                _log("Attaching resume...")
                with open(resume_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(resume_path)}",
                )
                msg.attach(part)
            else:
                _log("Resume file not found — skipping attachment.")

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(config["EMAIL"], config["APP_PASSWORD"])
            server.sendmail(config["EMAIL"], to_email, msg.as_string())

        success_msg = f"Email sent successfully to {to_email}"
        _log(success_msg)
        _log_to_file(success_msg)
        return True

    except Exception as e:
        error_msg = f"Failed to send email to {to_email}: {e}"
        _log(error_msg)
        _log_to_file(f"ERROR: {error_msg}")
        return False
