import json
import os
import socket

DATA_DIR = os.path.join(os.path.expanduser("~"), ".mindapp")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
DB_PATH = os.path.join(DATA_DIR, "sessions.db")

DEFAULTS = {
    "mode": "passive",
    "bell_interval": 60,
    "idle_threshold": 5,
    "quote_categories": [],
    "aim_history": [],
    "gcal_enabled": False,
    "notification_duration": 10,
    "user_id": socket.gethostname(),
}

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load():
    ensure_data_dir()
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
        merged = {**DEFAULTS, **data}
        return merged
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return dict(DEFAULTS)

def save(cfg):
    ensure_data_dir()
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

def is_first_launch():
    return not os.path.exists(CONFIG_PATH)

def add_aim(cfg, aim):
    if not aim or aim == "Engaged in activity":
        return
    history = cfg.get("aim_history", [])
    if aim in history:
        history.remove(aim)
    history.insert(0, aim)
    cfg["aim_history"] = history[:20]
    save(cfg)
