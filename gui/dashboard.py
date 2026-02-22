import csv
import os
import random
import threading
import time
from datetime import datetime
from tkinter import filedialog

import customtkinter as ctk

from core import auto_lookup, database, template_engine
from core.followup import send_followups
from core.limiter import DailyLimiter
from core.reply_checker import check_replies
from core.sender import send_email

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))


class SmartOutreachApp(ctk.CTk):
    """Main application window for the SmartOutreach cold email tool."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.title("SmartOutreach")
        self.geometry("1100x750")
        self.minsize(900, 650)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.contacts = []
        self.limiter = DailyLimiter(config.get("DAILY_LIMIT", 40))
        self.template_str = ""
        self._load_template()

        self._build_ui()

    def _load_template(self):
        """Load the email template from the data directory."""
        tpl_path = os.path.join(PROJECT_ROOT, "data", "template.txt")
        if os.path.exists(tpl_path):
            self.template_str = template_engine.load_template(tpl_path)

    # ── UI Construction ──────────────────────────────────────────────

    def _build_ui(self):
        """Construct the full application layout."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)

        self._build_header()
        self._build_main_area()
        self._build_action_bar()
        self._build_console()

    def _build_header(self):
        """Build the top header bar with title and daily counter."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            header, text="SmartOutreach", font=ctk.CTkFont(size=22, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w")

        self.counter_label = ctk.CTkLabel(
            header,
            text=f"Daily: {self.limiter.count} / {self.limiter.limit}",
            font=ctk.CTkFont(size=14),
        )
        self.counter_label.grid(row=0, column=2, sticky="e")

    def _build_main_area(self):
        """Build the central area containing the contact table and email preview."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=4)
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(1, weight=1)

        # ── Left panel ──
        load_btn = ctk.CTkButton(
            main_frame, text="Load CSV", command=self._load_csv, width=120
        )
        load_btn.grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.table_frame = ctk.CTkScrollableFrame(main_frame, label_text="Contacts")
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        self.table_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._draw_table_headers()

        # ── Right panel ──
        preview_label = ctk.CTkLabel(
            main_frame, text="EMAIL PREVIEW", font=ctk.CTkFont(size=13, weight="bold")
        )
        preview_label.grid(row=0, column=1, sticky="w", pady=(0, 6))

        self.preview_box = ctk.CTkTextbox(main_frame, state="disabled", wrap="word")
        self.preview_box.grid(row=1, column=1, sticky="nsew")

    def _draw_table_headers(self):
        """Draw column headers in the contact table."""
        headers = ["Name", "Email", "Company", "Status"]
        for col_idx, header_text in enumerate(headers):
            lbl = ctk.CTkLabel(
                self.table_frame,
                text=header_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
            )
            lbl.grid(row=0, column=col_idx, sticky="ew", padx=4, pady=(0, 4))

    def _build_action_bar(self):
        """Build the action button row and progress bar."""
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=6)
        action_frame.grid_columnconfigure(3, weight=1)

        self.send_all_btn = ctk.CTkButton(
            action_frame, text="Send All", command=self._on_send_all, width=120
        )
        self.send_all_btn.grid(row=0, column=0, padx=(0, 8))

        self.check_replies_btn = ctk.CTkButton(
            action_frame,
            text="Check Replies",
            command=self._on_check_replies,
            width=130,
        )
        self.check_replies_btn.grid(row=0, column=1, padx=(0, 8))

        self.followup_btn = ctk.CTkButton(
            action_frame,
            text="Send Followups",
            command=self._on_send_followups,
            width=140,
        )
        self.followup_btn.grid(row=0, column=2, padx=(0, 8))

        self.progress = ctk.CTkProgressBar(action_frame)
        self.progress.grid(row=0, column=3, sticky="ew", padx=(12, 0))
        self.progress.set(0)

    def _build_console(self):
        """Build the status console at the bottom."""
        console_label = ctk.CTkLabel(
            self, text="STATUS CONSOLE", font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
        )
        console_label.grid(row=3, column=0, sticky="w", padx=16, pady=(4, 0))

        self.console = ctk.CTkTextbox(self, height=150, state="disabled")
        self.console.grid(row=4, column=0, sticky="nsew", padx=16, pady=(2, 12))
        self.grid_rowconfigure(4, weight=0, minsize=150)

    # ── Logging ──────────────────────────────────────────────────────

    def _log(self, message):
        """Append a timestamped message to the status console (thread-safe)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"

        def _append():
            self.console.configure(state="normal")
            self.console.insert("end", line)
            self.console.see("end")
            self.console.configure(state="disabled")

        self.after(0, _append)

    def _update_counter(self):
        """Refresh the daily counter label (thread-safe)."""
        def _update():
            self.counter_label.configure(
                text=f"Daily: {self.limiter.count} / {self.limiter.limit}"
            )

        self.after(0, _update)

    # ── CSV Loading ──────────────────────────────────────────────────

    def _load_csv(self):
        """Open a file dialog, parse the selected CSV, and populate the contact table."""
        filepath = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        self.contacts = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    contact = {k: (v or "") for k, v in row.items()}
                    if self.config.get("AUTO", False):
                        contact = auto_lookup.enrich_contact(contact, self.config)
                    self.contacts.append(contact)
        except Exception as e:
            self._log(f"Error loading CSV: {e}")
            return

        self._populate_table()
        self._log(f"Loaded {len(self.contacts)} contacts from {os.path.basename(filepath)}.")

    def _populate_table(self):
        """Clear and repopulate the contact table with loaded contacts."""
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        self._draw_table_headers()

        for idx, contact in enumerate(self.contacts):
            row_num = idx + 1
            sent = database.is_sent(contact.get("email", ""))
            status = "Sent" if sent else "Pending"

            name_lbl = ctk.CTkLabel(
                self.table_frame, text=contact.get("name", ""), anchor="w"
            )
            name_lbl.grid(row=row_num, column=0, sticky="ew", padx=4, pady=1)

            email_lbl = ctk.CTkLabel(
                self.table_frame, text=contact.get("email", ""), anchor="w"
            )
            email_lbl.grid(row=row_num, column=1, sticky="ew", padx=4, pady=1)

            company_lbl = ctk.CTkLabel(
                self.table_frame, text=contact.get("company", ""), anchor="w"
            )
            company_lbl.grid(row=row_num, column=2, sticky="ew", padx=4, pady=1)

            status_lbl = ctk.CTkLabel(self.table_frame, text=status, anchor="w")
            status_lbl.grid(row=row_num, column=3, sticky="ew", padx=4, pady=1)

            for lbl in (name_lbl, email_lbl, company_lbl, status_lbl):
                lbl.bind("<Button-1>", lambda e, i=idx: self._preview_email(i))

    def _preview_email(self, contact_idx):
        """Render and display the email preview for the selected contact."""
        contact = self.contacts[contact_idx]
        if not self.template_str:
            self._log("No template loaded.")
            return

        rendered = template_engine.render(self.template_str, contact)
        subject = template_engine.get_subject(rendered)
        body = template_engine.get_body(rendered)
        preview = f"Subject: {subject}\n{'─' * 40}\n{body}"

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        self.preview_box.insert("1.0", preview)
        self.preview_box.configure(state="disabled")

    # ── Send All ─────────────────────────────────────────────────────

    def _on_send_all(self):
        """Launch the send-all operation in a background thread."""
        if not self.contacts:
            self._log("No contacts loaded. Please load a CSV first.")
            return
        self.send_all_btn.configure(state="disabled")
        t = threading.Thread(target=self._send_all_worker, daemon=True)
        t.start()

    def _send_all_worker(self):
        """Background worker that iterates contacts and sends emails."""
        total = len(self.contacts)
        sent_count = 0

        for idx, contact in enumerate(self.contacts):
            email_addr = contact.get("email", "").strip()
            name = contact.get("name", "").strip()

            if not email_addr:
                self._log(f"Skipping row {idx + 1} — no email address.")
                self._set_progress((idx + 1) / total)
                continue

            if database.is_sent(email_addr):
                self._log(f"Skipping {email_addr} — already sent.")
                self._set_progress((idx + 1) / total)
                continue

            if not self.limiter.can_send():
                self._log("Daily limit reached — stopping.")
                break

            rendered = template_engine.render(self.template_str, contact)
            subject = template_engine.get_subject(rendered)
            body = template_engine.get_body(rendered)

            success = send_email(self.config, email_addr, subject, body, log_callback=self._log)

            if success:
                sent_time = datetime.now().isoformat()
                database.mark_sent(email_addr, name, sent_time)
                self.limiter.increment()
                self._update_counter()
                sent_count += 1
                self._update_row_status(idx, "Sent")

            self._set_progress((idx + 1) / total)

            if idx < total - 1 and self.limiter.can_send():
                delay = random.randint(
                    self.config.get("MIN_DELAY", 35),
                    self.config.get("MAX_DELAY", 90),
                )
                self._log(f"Waiting {delay}s before next email...")
                time.sleep(delay)

        self._log(f"Send round complete. {sent_count}/{total} emails sent.")
        self.after(0, lambda: self.send_all_btn.configure(state="normal"))

    def _set_progress(self, value):
        """Update the progress bar (thread-safe)."""
        self.after(0, lambda: self.progress.set(value))

    def _update_row_status(self, contact_idx, status_text):
        """Update the status column for a specific row (thread-safe)."""
        def _update():
            row_num = contact_idx + 1
            col = 3
            for widget in self.table_frame.winfo_children():
                info = widget.grid_info()
                if int(info.get("row", -1)) == row_num and int(info.get("column", -1)) == col:
                    widget.configure(text=status_text)
                    break

        self.after(0, _update)

    # ── Check Replies ────────────────────────────────────────────────

    def _on_check_replies(self):
        """Launch reply checking in a background thread."""
        self.check_replies_btn.configure(state="disabled")
        t = threading.Thread(target=self._check_replies_worker, daemon=True)
        t.start()

    def _check_replies_worker(self):
        """Background worker that checks for inbox replies."""
        self._log("Starting reply check...")
        count = check_replies(self.config, log_callback=self._log)
        self._log(f"Reply check finished. {count} new replies found.")
        self.after(0, lambda: self.check_replies_btn.configure(state="normal"))

    # ── Send Follow-ups ──────────────────────────────────────────────

    def _on_send_followups(self):
        """Launch follow-up sending in a background thread."""
        self.followup_btn.configure(state="disabled")
        t = threading.Thread(target=self._send_followups_worker, daemon=True)
        t.start()

    def _send_followups_worker(self):
        """Background worker that sends follow-up emails."""
        self._log("Starting follow-up round...")
        send_followups(self.config, self.limiter, log_callback=self._log)
        self._update_counter()
        self._log("Follow-up round finished.")
        self.after(0, lambda: self.followup_btn.configure(state="normal"))
