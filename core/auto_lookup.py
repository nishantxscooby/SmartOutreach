FREE_DOMAINS = [
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "protonmail.com",
]


def enrich_contact(contact, config):
    """Enrich a contact dictionary by auto-filling missing company and description fields.

    Extracts domain from the email address and uses it to populate empty fields.
    Never overwrites fields that already have values.
    If IGNORE_FREE_DOMAINS is enabled and the domain is a free email provider,
    returns the contact unchanged.
    """
    contact = dict(contact)
    email = contact.get("email", "")
    if not email or "@" not in email:
        return contact

    domain = email.split("@")[1].strip().lower()

    if config.get("IGNORE_FREE_DOMAINS", True) and domain in FREE_DOMAINS:
        return contact

    if not contact.get("company", "").strip():
        contact["company"] = domain.split(".")[0].capitalize()

    if not contact.get("company_description", "").strip():
        contact["company_description"] = f"a company operating under {domain}"

    return contact
