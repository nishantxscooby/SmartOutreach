import email
import imaplib
import re

from core import database


def check_replies(config, log_callback=None):
    """Check the Gmail INBOX for replies from previously contacted addresses.

    Connects to imap.gmail.com via SSL, iterates through inbox messages,
    and cross-references sender addresses against the sent database.
    Marks matching entries as replied.

    Returns the count of newly detected replies.
    """
    def _log(msg):
        if log_callback:
            log_callback(msg)

    new_replies = 0

    try:
        _log("Connecting to IMAP server...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(config["EMAIL"], config["APP_PASSWORD"])
        mail.select("INBOX")

        db = database.get_all()
        sent_emails = {addr.lower() for addr in db.keys()}

        if not sent_emails:
            _log("No sent emails in database — nothing to check.")
            mail.logout()
            return 0

        _log(f"Checking replies against {len(sent_emails)} sent contacts...")
        status, message_ids = mail.search(None, "ALL")

        if status != "OK" or not message_ids[0]:
            _log("No messages found in inbox.")
            mail.logout()
            return 0

        for msg_id in message_ids[0].split():
            status, msg_data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            from_header = msg.get("From", "")

            match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", from_header)
            if not match:
                continue

            sender_addr = match.group(0).lower()

            if sender_addr in sent_emails:
                entry = db.get(sender_addr, {})
                if not entry.get("replied", False):
                    database.mark_replied(sender_addr)
                    new_replies += 1
                    _log(f"Reply detected from {sender_addr}")

        mail.logout()
        _log(f"Reply check complete. {new_replies} new replies detected.")

    except Exception as e:
        _log(f"Error checking replies: {e}")

    return new_replies
