import sqlite3
import json
import os
from datetime import datetime, timezone, timedelta
from . import config

def _conn():
    config.ensure_data_dir()
    c = sqlite3.connect(config.DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c

def init():
    c = _conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            ts_start TEXT NOT NULL,
            ts_end TEXT,
            mode TEXT NOT NULL,
            duration_seconds INTEGER DEFAULT 0,
            aim_text TEXT,
            completed INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS bell_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            ts TEXT NOT NULL,
            mode TEXT NOT NULL,
            quote_shown TEXT
        );
    """)
    c.close()

def log_session_start(user_id, mode, aim=None):
    c = _conn()
    now = datetime.now(timezone.utc).isoformat()
    cur = c.execute(
        "INSERT INTO sessions (user_id, ts_start, mode, aim_text) VALUES (?,?,?,?)",
        (user_id, now, mode, aim),
    )
    sid = cur.lastrowid
    c.commit()
    c.close()
    return sid

def log_session_end(sid, duration, completed):
    c = _conn()
    now = datetime.now(timezone.utc).isoformat()
    c.execute(
        "UPDATE sessions SET ts_end=?, duration_seconds=?, completed=? WHERE id=?",
        (now, duration, int(completed), sid),
    )
    c.commit()
    c.close()

def log_bell(user_id, mode, quote_text):
    c = _conn()
    now = datetime.now(timezone.utc).isoformat()
    c.execute(
        "INSERT INTO bell_events (user_id, ts, mode, quote_shown) VALUES (?,?,?,?)",
        (user_id, now, mode, quote_text),
    )
    c.commit()
    c.close()

def weekly_stats(user_id):
    c = _conn()
    today = datetime.now(timezone.utc).date()
    monday = today - timedelta(days=today.weekday())
    start = datetime(monday.year, monday.month, monday.day, tzinfo=timezone.utc).isoformat()

    sessions = c.execute(
        "SELECT COUNT(*) as cnt, COALESCE(SUM(duration_seconds),0) as total_sec FROM sessions WHERE user_id=? AND ts_start>=? AND mode='active'",
        (user_id, start),
    ).fetchone()

    bells = c.execute(
        "SELECT COUNT(*) as cnt FROM bell_events WHERE user_id=? AND ts>=?",
        (user_id, start),
    ).fetchone()

    aims = c.execute(
        "SELECT aim_text, COUNT(*) as cnt FROM sessions WHERE user_id=? AND ts_start>=? AND aim_text IS NOT NULL AND aim_text != '' GROUP BY aim_text ORDER BY cnt DESC LIMIT 3",
        (user_id, start),
    ).fetchall()

    streak = _calc_streak(c, user_id)
    c.close()

    return {
        "sessions": sessions["cnt"],
        "minutes": sessions["total_sec"] // 60,
        "bells": bells["cnt"],
        "streak": streak,
        "top_aims": [{"aim": r["aim_text"], "count": r["cnt"]} for r in aims],
    }

def _calc_streak(c, user_id):
    today = datetime.now(timezone.utc).date()
    streak = 0
    for i in range(365):
        d = today - timedelta(days=i)
        ds = datetime(d.year, d.month, d.day, tzinfo=timezone.utc).isoformat()
        de = datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc).isoformat()
        r = c.execute(
            "SELECT COUNT(*) as cnt FROM (SELECT ts_start as t FROM sessions WHERE user_id=? AND t>=? AND t<=? UNION ALL SELECT ts FROM bell_events WHERE user_id=? AND ts>=? AND ts<=?)",
            (user_id, ds, de, user_id, ds, de),
        ).fetchone()
        if r["cnt"] > 0:
            streak += 1
        else:
            break
    return streak

def recent_sessions(user_id, limit=50):
    c = _conn()
    rows = c.execute(
        "SELECT * FROM sessions WHERE user_id=? ORDER BY ts_start DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]

def export_json(user_id):
    c = _conn()
    sessions = c.execute("SELECT * FROM sessions WHERE user_id=?", (user_id,)).fetchall()
    bells = c.execute("SELECT * FROM bell_events WHERE user_id=?", (user_id,)).fetchall()
    c.close()
    return json.dumps({
        "sessions": [dict(r) for r in sessions],
        "bell_events": [dict(r) for r in bells],
    }, indent=2)
