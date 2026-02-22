from collections import defaultdict


def load_template(path):
    """Read and return a template file as a string."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def render(template_str, contact_dict):
    """Replace all {placeholder} values using str.format_map with a defaultdict fallback.

    Missing keys render as empty strings instead of raising KeyError.
    """
    safe_dict = defaultdict(str, contact_dict)
    return template_str.format_map(safe_dict)


def get_subject(template_str):
    """Extract the Subject line from the first line of the template.

    Expects the first line to be in the format 'Subject: ...'
    """
    first_line = template_str.strip().split("\n")[0]
    if first_line.lower().startswith("subject:"):
        return first_line.split(":", 1)[1].strip()
    return first_line.strip()


def get_body(template_str):
    """Return everything after the Subject line, stripped of leading blank lines."""
    lines = template_str.strip().split("\n")
    body_lines = lines[1:]
    body = "\n".join(body_lines).strip()
    return body
