import os
import json
from datetime import datetime, timedelta, timezone
from . import config

_service = None

def _token_path():
    return os.path.join(config.DATA_DIR, "gcal_token.json")

def _creds_path():
    import sys
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "client_secret.json")

def is_available():
    try:
        from google.oauth2.credentials import Credentials
        return True
    except ImportError:
        return False

def setup():
    global _service
    if not is_available():
        return False
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
        creds = None
        tp = _token_path()

        if os.path.exists(tp):
            try:
                creds = Credentials.from_authorized_user_file(tp, SCOPES)
            except Exception:
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None
            if not creds:
                cp = _creds_path()
                if not os.path.exists(cp):
                    return False
                flow = InstalledAppFlow.from_client_secrets_file(cp, SCOPES)
                creds = flow.run_local_server(port=0)

            config.ensure_data_dir()
            with open(tp, "w") as f:
                f.write(creds.to_json())

        _service = build("calendar", "v3", credentials=creds)
        return True
    except Exception:
        _service = None
        return False

def create_event(aim, duration_min):
    if not _service:
        return None
    try:
        now = datetime.now(timezone.utc)
        event = {
            "summary": aim or "Self-Remembering Session",
            "description": aim or "",
            "start": {"dateTime": now.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": (now + timedelta(minutes=duration_min)).isoformat(), "timeZone": "UTC"},
        }
        r = _service.events().insert(calendarId="primary", body=event).execute()
        return r.get("id")
    except Exception:
        return None

def patch_end(event_id):
    if not _service or not event_id:
        return
    try:
        now = datetime.now(timezone.utc)
        _service.events().patch(
            calendarId="primary",
            eventId=event_id,
            body={"end": {"dateTime": now.isoformat(), "timeZone": "UTC"}},
        ).execute()
    except Exception:
        pass
