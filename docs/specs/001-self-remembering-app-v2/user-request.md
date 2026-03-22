# User Request

**Original Input**: Redesign and enhance the self-remembering app (https://github.com/JKDasondee/self-remembering-app) for internal team use.

**Key Requirements Mentioned**:
1. Passive mode (Awareness-style) — background system tray app, rings bowl every N minutes
2. System-wide idle detection — OS-level input monitoring, not app-window-only
3. System tray integration — elapsed time display, right-click menu
4. Periodic bell during active sessions — configurable interval
5. Config persistence — ~/.mindapp/config.json
6. Session history & stats — local SQLite, structured for future team sync
7. Graceful Google Calendar fallback — optional plugin, silent on failure
8. Cross-platform support — Windows + macOS + Linux
9. Code cleanup — strip docstrings, fix set() dedup, split monolith into modules
10. Security fixes — remove token.pickle from repo, audit OAuth flow

**Constraints**:
- Internal team use (not public distribution)
- Single developer (Jay Dasondee)
- Python/PyQt6 tech stack
- All 10 features must be implemented (feature-complete is success criteria)
- First-launch mode selection, persisted
- Curated quotes with category filtering by teacher/tradition
- Google Calendar as opt-in, not core
- Local data first, schema ready for future team sync
