# Brainstorming Notes

## Technical Decisions Discussed
- Python/PyQt6 stack retained from v1
- pygame for audio playback
- pynput for system-wide idle detection (replaces app-window-only mousePressEvent/keyPressEvent)
- QSystemTrayIcon for tray integration
- SQLite for local session history
- Google Calendar API remains but as optional plugin

## Architecture Direction
- Split monolith (~450 lines single file) into modules: core timer, bell engine, tray, stats/db, quotes, calendar plugin, config
- Config at ~/.mindapp/config.json
- Database at ~/.mindapp/sessions.db
- OAuth tokens at ~/.mindapp/

## Key Technical Concerns
- pynput requires accessibility permissions on macOS (System Preferences → Security & Privacy → Privacy → Accessibility)
- Linux idle detection may need X11/Wayland consideration
- PyInstaller builds needed for all 3 platforms (CI matrix)
- token.pickle must be removed from git history (not just .gitignore'd)
- pickle deserialization is a security risk — consider JSON-based token storage
- set() dedup on quotes destroys order — use random.sample() or Fisher-Yates shuffle

## Inspiration: Awareness App
- Zero-friction passive bell every hour
- System tray with elapsed time counter
- System-wide idle detection with auto-reset
- Built with C#/Mono — cross-platform via MonoMac + Windows.Forms
- Key insight: popularity comes from demanding nothing from the user

## Decisions Made During Brainstorming
- Target: internal team use
- Default mode: user chooses on first launch, persisted
- Data: local SQLite now, schema supports future team sync
- Google Calendar: optional plugin, not core
- Quotes: curated set with category filtering by teacher/tradition
- Platforms: Windows + macOS + Linux
- Success: feature-complete (all 10 features implemented)
