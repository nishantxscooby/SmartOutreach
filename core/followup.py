import os
import random
import time
from datetime import datetime

from core import database, sender, template_engine


def send_followups(config, limiter, log_callback=None):
    """Send follow-up emails to contacts who haven't replied within the configured window.

    Iterates through the sent database and sends a follow-up to each contact
    where: replied is False, followup_sent is False, and enough days have
    elapsed since the original email was sent.

    Respects the daily limiter and applies a random delay between sends.
    """
    def _log(msg):
        if log_callback:
            log_callback(msg)

    db = database.get_all()
    if not db:
        _log("No sent emails in database — nothing to follow up on.")
        return

    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "followup_template.txt"
    )
    template_str = template_engine.load_template(template_path)
    followup_days = config.get("FOLLOWUP_AFTER_DAYS", 4)
    sent_count = 0

    for email_addr, entry in db.items():
        if entry.get("replied", False):
            continue
        if entry.get("followup_sent", False):
            continue

        try:
            sent_time = datetime.fromisoformat(entry["sent_time"])
        except (KeyError, ValueError):
            _log(f"Skipping {email_addr} — invalid sent_time.")
            continue

        days_elapsed = (datetime.now() - sent_time).days
        if days_elapsed < followup_days:
            continue

        if not limiter.can_send():
            _log("Daily send limit reached — stopping follow-ups.")
            break

        contact_data = {
            "name": entry.get("name", ""),
            "email": email_addr,
            "company": entry.get("company", ""),
            "company_description": entry.get("company_description", ""),
        }

        rendered = template_engine.render(template_str, contact_data)
        subject = template_engine.get_subject(rendered)
        body = template_engine.get_body(rendered)

        _log(f"Sending follow-up to {email_addr}...")
        success = sender.send_email(config, email_addr, subject, body, log_callback=_log)

        if success:
            database.mark_followup_sent(email_addr)
            limiter.increment()
            sent_count += 1
            _log(f"Follow-up sent to {email_addr} ({limiter.remaining()} remaining today).")

        delay = random.randint(config.get("MIN_DELAY", 35), config.get("MAX_DELAY", 90))
        _log(f"Waiting {delay}s before next follow-up...")
        time.sleep(delay)

    _log(f"Follow-up round complete. {sent_count} follow-ups sent.")
