import json
import os
import sys


def load_config():
    """Load application configuration from config.json."""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    config = load_config()

    storage_dir = os.path.join(os.path.dirname(__file__), "storage")
    os.makedirs(storage_dir, exist_ok=True)

    db_path = os.path.join(storage_dir, "sent_db.json")
    if not os.path.exists(db_path):
        with open(db_path, "w", encoding="utf-8") as f:
            f.write("{}")

    logs_path = os.path.join(storage_dir, "logs.txt")
    if not os.path.exists(logs_path):
        with open(logs_path, "w", encoding="utf-8") as f:
            pass

    from gui.dashboard import SmartOutreachApp

    app = SmartOutreachApp(config)
    app.mainloop()


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    main()
