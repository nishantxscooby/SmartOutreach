# SmartOutreach — Intelligent Cold Email Automation Tool

A Python desktop application for managing and automating cold email outreach campaigns with follow-up tracking, reply detection, and daily send limits.

## Prerequisites

- **Python 3.10+**
- **pip** (Python package manager)

## Installation

```bash
cd smart_outreach
pip install -r requirements.txt
```

## Gmail App Password Setup

SmartOutreach uses Gmail's SMTP and IMAP servers. You must generate an **App Password** (regular passwords won't work with 2FA enabled):

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already enabled
3. Navigate to **Security → 2-Step Verification → App Passwords**
4. Select **Mail** and your device, then click **Generate**
5. Copy the 16-character app password (formatted as `xxxx xxxx xxxx xxxx`)

## Configuration

Edit `config.json` with your credentials and preferences:

| Key                  | Description                                          | Default              |
|----------------------|------------------------------------------------------|----------------------|
| `EMAIL`              | Your Gmail address                                   | `your@gmail.com`     |
| `APP_PASSWORD`       | Gmail App Password (see above)                       | `xxxx xxxx xxxx xxxx`|
| `AUTO`               | Auto-enrich contacts with missing company info       | `true`               |
| `ATTACH_RESUME`      | Attach a resume/PDF to outgoing emails               | `false`              |
| `RESUME_PATH`        | Path to the resume file                              | `data/resume.pdf`    |
| `DAILY_LIMIT`        | Maximum emails per day                               | `40`                 |
| `MIN_DELAY`          | Minimum delay between emails (seconds)               | `35`                 |
| `MAX_DELAY`          | Maximum delay between emails (seconds)               | `90`                 |
| `FOLLOWUP_AFTER_DAYS`| Days to wait before sending a follow-up              | `4`                  |
| `IGNORE_FREE_DOMAINS`| Skip auto-enrichment for free email providers        | `true`               |

## Preparing Contacts

Edit `data/contacts.csv` with your outreach targets:

```csv
name,email,company,first_line,about_them
Alice Johnson,alice@techcorp.com,TechCorp,I came across your engineering blog,"a fast-growing B2B SaaS company"
```

| Column       | Required | Description                                    |
|--------------|----------|------------------------------------------------|
| `name`       | Yes      | Contact's full name                            |
| `email`      | Yes      | Contact's email address                        |
| `company`    | No       | Company name (auto-filled from domain if empty)|
| `first_line` | No       | Personalized opening line                      |
| `about_them` | No       | Brief company/person description               |

## Running the Application

```bash
cd smart_outreach
python main.py
```

## Module Descriptions

| Module                    | Description                                               |
|---------------------------|-----------------------------------------------------------|
| `main.py`                 | Entry point — loads config and launches the GUI           |
| `gui/dashboard.py`        | CustomTkinter GUI with contact table, preview, and console|
| `core/sender.py`          | Sends emails via Gmail SMTP with optional attachments     |
| `core/template_engine.py` | Loads and renders email templates with placeholder support|
| `core/auto_lookup.py`     | Enriches contacts by extracting info from email domains   |
| `core/followup.py`        | Sends follow-up emails after a configurable delay         |
| `core/reply_checker.py`   | Checks inbox for replies from sent contacts via IMAP      |
| `core/limiter.py`         | Enforces daily sending limits                             |
| `core/database.py`        | JSON-based database for tracking sent emails and replies  |

## Template Placeholders

Use these placeholders in `data/template.txt` and `data/followup_template.txt`:

| Placeholder            | Source                                                 |
|------------------------|--------------------------------------------------------|
| `{name}`               | Contact name from CSV                                  |
| `{email}`              | Contact email from CSV                                 |
| `{company}`            | Company name (CSV or auto-enriched from domain)        |
| `{first_line}`         | Personalized opening line from CSV                     |
| `{about_them}`         | Company/person description from CSV                    |
| `{company_description}`| Auto-generated from email domain if not provided       |

Missing placeholders render as empty strings — no errors will occur.

## Safety Notes

- **Daily Limits**: The app enforces a configurable daily send limit (default: 40) to avoid triggering spam filters.
- **Random Delays**: A random delay (35–90 seconds by default) is applied between each email to mimic human sending patterns.
- **No Overwrites**: Auto-enrichment never overwrites existing CSV values.
- **Fail-Safe Sending**: If an individual email fails, the error is logged and the batch continues.
- **Follow-up Respect**: Follow-ups are only sent to contacts who haven't replied and haven't already received a follow-up.
