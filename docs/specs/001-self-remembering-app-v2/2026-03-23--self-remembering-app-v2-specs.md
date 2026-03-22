# Functional Specification: Self-Remembering App v2

| Field         | Value                          |
|---------------|-------------------------------|
| Spec ID       | 001-self-remembering-app-v2   |
| Date          | 2026-03-23                    |
| Status        | Draft                         |
| Version       | 2.0                           |
| Supersedes    | v1 (no formal spec)           |

---

## Table of Contents

1. [Overview](#1-overview)
2. [Problem Statement](#2-problem-statement)
3. [Goals and Non-Goals](#3-goals-and-non-goals)
4. [Users and Context](#4-users-and-context)
5. [Operating Modes](#5-operating-modes)
6. [System Tray Behavior](#6-system-tray-behavior)
7. [System-Wide Idle Detection](#7-system-wide-idle-detection)
8. [Bell and Quote System](#8-bell-and-quote-system)
9. [Configuration Persistence](#9-configuration-persistence)
10. [Session History and Statistics](#10-session-history-and-statistics)
11. [Google Calendar Integration](#11-google-calendar-integration)
12. [Security and Credential Handling](#12-security-and-credential-handling)
13. [User Interaction Flows](#13-user-interaction-flows)
14. [Edge Case Handling](#14-edge-case-handling)
15. [Integration Requirements](#15-integration-requirements)
16. [Acceptance Criteria](#16-acceptance-criteria)
17. [Out of Scope](#17-out-of-scope)
18. [Open Questions](#18-open-questions)

---

## 0. Business Context

Self-Remembering App is built for an internal team that practices Gurdjieff's Fourth Way self-remembering discipline during computer work. v1 proved the concept but low daily adoption (due to manual session management friction) limits its value. v2 eliminates that friction so the tool becomes ambient infrastructure — always running, always prompting.

**Why v2 now:** The team has grown and new members need a zero-setup path to begin the practice. The current app requires too much deliberate interaction to be sustainable.

**Success criterion:** All 10 specified features are implemented and working. The app is installable and functional on all three target platforms (Windows, macOS, Linux) without per-platform workarounds.

---

## 1. Overview

Self-Remembering App v2 is a standalone desktop mindfulness tool rooted in Gurdjieff's Fourth Way tradition. It runs as a persistent system tray application and periodically interrupts the user's workflow with an auditory cue (a Tibetan singing bowl sound) and a displayed wisdom quote, prompting a moment of conscious self-awareness.

v2 eliminates the manual session management burden of v1. The app operates automatically from startup, requires no active window management, and now tracks usage history with statistics. It also gains system-wide idle detection, ensuring timer accuracy regardless of which application has focus.

---

## 2. Problem Statement

### v1 Limitations

| Problem | Impact |
|---|---|
| User must manually open the app and start a timer to receive bells | High friction reduces daily adoption |
| Idle detection only works when the app window has focus | Timer continues running while user is away from computer |
| No session history or statistics | No feedback loop; no sense of progress or continuity |
| No persistence between sessions | Settings reset; no memory of previous use |
| No system tray presence | App is not ambient; requires deliberate interaction |

### Core Need

The app must require zero deliberate interaction to deliver value. Opening the computer should be sufficient for mindfulness prompts to begin. The user should only need to engage when they want active session features or want to review their history.

---

## 3. Goals and Non-Goals

### Goals

- Deliver auditory and textual mindfulness prompts at configurable intervals with no required setup after first launch
- Accurately track active vs. idle computer time across the full OS
- Persist all user preferences and session history across restarts
- Support both passive (ambient) and active (focus session) usage patterns within the same application
- Provide a lightweight weekly progress view to reinforce the practice
- Run without modification on Windows, macOS, and Linux

### Non-Goals

- No web or server component of any kind
- No mobile support
- No team dashboards or real-time sync in this version
- No custom sound uploads
- No auto-update mechanism

---

## 4. Users and Context

### Target Users

Internal team members who:
- Practice or want to practice self-remembering (Gurdjieff Fourth Way tradition)
- Want mindfulness prompts during computer work hours
- Range from highly technical to minimally technical

### Operating Environment

- Desktop computers running Windows 10+, macOS 12+, or Ubuntu 22.04+
- App runs alongside normal workday applications
- No network requirement for core functionality (Google Calendar integration is optional and degradable)
- App is not the primary application — it is ambient infrastructure

### Design Constraints

- Must not demand attention or interrupt flow beyond a brief notification
- Must not require the user to remember to start it
- Must be dismissible and non-blocking at all times

---

## 5. Operating Modes

The app supports two distinct modes. The user selects their preferred mode on first launch, and the choice persists. Modes can be switched at any time via the tray menu.

### 5.1 Passive Mode

Passive mode is the ambient, always-on mode. The app runs silently in the system tray from startup. No session needs to be started.

**Behavior:**
- Timer runs continuously from the moment the app starts
- At each configured bell interval, a bowl sound plays and a quote notification appears
- Tray tooltip displays elapsed time since the last bell (or since app start)
- Idle detection is active: if no OS-level input is detected for the idle threshold, the timer pauses and tray shows "Paused"
- Timer resumes automatically on any OS-level input after an idle period
- Every bell event is logged to the local database

**Default interval:** 60 minutes

### 5.2 Active Mode

Active mode is the intentional focus session mode. The user explicitly starts and stops sessions.

**Behavior:**
- No bells fire outside of an explicit session
- User starts a session by selecting a duration preset and optionally entering an aim (a brief intention statement)
- Bowl rings at session start
- Bell fires at each configured interval during the session
- Bowl rings at session end
- Tray tooltip displays remaining session time during an active session
- User can pause and resume a session via the tray menu
- User can stop a session early; the session is still logged with actual duration and marked incomplete
- Each completed session is logged to the local database

**Duration presets:** 5, 15, 25, 30, 45, 60 minutes

### 5.3 Mode Selection Persistence

- First launch: a welcome screen presents the mode choice
- Selection is written to config immediately
- Subsequent launches skip the welcome screen and load the configured mode
- Mode can be changed at any time via tray menu; change takes effect immediately and persists

---

## 6. System Tray Behavior

The system tray icon is the primary interface. The app has no persistent main window.

### 6.1 Tray Icon

- Always visible in the system tray when the app is running
- Displays a tooltip with contextual status:
  - Passive mode, active: elapsed time since last bell (e.g., "43 min since last bell")
  - Passive mode, paused: "Paused — idle"
  - Active mode, session running: remaining session time (e.g., "18 min remaining")
  - Active mode, no session: "No active session"

### 6.2 Right-Click Context Menu

The context menu is the primary control surface. Menu items vary by mode and session state.

**Always present:**
- Switch Mode (submenu: Passive / Active)
- View Stats
- Settings
- Quit

**Passive mode additions:**
- Adjust Bell Interval (submenu: 15 / 30 / 45 / 60 min)

**Active mode additions — no session running:**
- New Session

**Active mode additions — session running:**
- Pause Session / Resume Session (toggles based on state)
- Stop Session

---

## 7. System-Wide Idle Detection

Idle detection must operate at the OS level, monitoring mouse and keyboard activity across all applications, not just within the app's own window.

### 7.1 Idle Threshold

- Configurable by the user (default: 5 minutes)
- If no mouse movement or key press is detected for the full threshold duration, the system is considered idle

### 7.2 Idle Behavior

- When idle threshold is reached: timer pauses, tray tooltip updates to "Paused — idle"
- When any OS-level input is detected after an idle period: timer resumes within 2 seconds
- Paused time is not counted toward bell interval or session duration
- The idle state is reflected in the tray but does not generate a notification

### 7.3 OS Sleep/Wake

- When the OS enters sleep or hibernate: timer pauses
- When the OS wakes: timer resumes, treating the sleep period the same as idle

---

## 8. Bell and Quote System

### 8.1 Bell Interval

- Configurable: 15, 30, 45, or 60 minutes
- Applies in both modes
- In passive mode: interval resets after each bell
- In active mode: interval resets after each bell within the session; additional bell fires at session start and session end regardless of interval position

### 8.2 Audio

- Bell plays a Tibetan singing bowl sound at each bell event
- If no audio output device is available or the sound cannot be played, the bell event is silently skipped (quote notification still displays)
- No user action is required to dismiss or acknowledge the sound

### 8.3 Quote System

**Quote library:**
- Minimum 75 curated quotes
- Sources include: Gurdjieff, Ouspensky, Rumi, Kabir, Meher Baba, Lao-Tzu, William Blake, and others in the mystic/Fourth Way tradition
- Each quote is tagged with a teacher/tradition category

**Category filtering:**
- User selects which categories are active in Settings
- All categories are selected by default
- Only quotes from active categories are shown at bell time
- Selected categories persist in config

**Rotation logic:**
- Quotes are selected at random from the active category pool
- The same quote must not appear on two consecutive bells (no immediate repeats)
- Beyond that constraint, selection is random with no mandatory full-cycle requirement

**Display:**
- Quote appears as a desktop notification or overlay at each bell event
- Notification is dismissible and non-blocking
- Notification does not require user acknowledgment to continue app operation

---

## 9. Configuration Persistence

All user preferences are saved to a config file in a directory that is private to the current OS user account, appropriate for user-specific application data, and persistent across app restarts.

### 9.1 Persisted Fields

| Field | Default |
|---|---|
| Operating mode | Passive |
| Bell interval (minutes) | 60 |
| Idle detection threshold (minutes) | 5 |
| Selected quote categories | All |
| Aim history (last N aims, for autocomplete) | Empty |
| Main window / stats window position | OS default |
| Google Calendar enabled | False |

### 9.2 Behavior

- Config is loaded on every app startup
- Config is written immediately when any setting changes (no explicit save button)
- If the config file is absent or corrupted on startup, the app resets to defaults and notifies the user once with a non-blocking message

---

## 10. Session History and Statistics

### 10.1 Local Database

All session and bell events are logged to a local database file in the user's application data directory.

**Session record fields:**

| Field | Description |
|---|---|
| id | Unique record identifier |
| user_id | Local machine name (default); reserved for future team sync |
| timestamp_start | UTC timestamp of session or bell event start |
| timestamp_end | UTC timestamp of session end (null for in-progress) |
| mode | "passive" or "active" |
| duration_seconds | Actual elapsed active (non-idle) time |
| aim_text | Intention text entered by user (active mode only; null otherwise) |
| completed | Boolean; false if session stopped early or interrupted |

**Bell event record fields (passive mode):**

| Field | Description |
|---|---|
| id | Unique record identifier |
| user_id | Local machine name |
| timestamp | UTC timestamp of bell |
| mode | "passive" |
| quote_shown | Text of quote displayed |

### 10.2 Stats View

Accessible from the tray context menu. Opens a non-modal window.

**Weekly summary panel:**
- Total sessions started (active mode)
- Total mindful minutes (sum of active, non-idle time across sessions and passive bell periods)
- Current streak (consecutive days with at least one bell or session)
- Most-used aim texts (top 3, active mode only)

**Session list panel:**
- Chronological list of recent records
- Columns: date, mode, duration, aim (if any), completed status
- Filterable by date range

**Data integrity:** All totals displayed must match raw records in the database. No caching that could produce stale counts.

### 10.3 Future-Proofing

- The `user_id` field on all records is present from v2 launch to support a future team sync feature
- See Section 15.6 for data export requirements

---

## 11. Google Calendar Integration

Google Calendar integration is entirely optional and disabled by default. The app must function fully without it.

### 11.1 Opt-In Flow

1. User navigates to Settings and toggles "Google Calendar" on
2. App initiates the authentication flow (browser-based or embedded, depending on OS)
3. On successful authentication, credentials are stored in the user's app data directory
4. Setting persists as enabled in config

### 11.2 Behavior When Enabled

- When an active mode session starts: a calendar event is created with the session's start time, aim text (if any), and estimated end time based on selected duration
- When a session ends (normally or early): the calendar event is patched with the actual end time
- Only active mode sessions generate calendar events; passive mode bells do not

### 11.3 Failure Handling

If Google Calendar is enabled but the auth flow fails, credentials are missing, or a token is expired or invalid:
- The failure is logged internally
- The app continues operating without calendar functionality
- No error dialog, popup, or notification is shown to the user
- The calendar toggle remains enabled in Settings; the user may re-authenticate at any time

---

## 12. Security and Credential Handling

- No credentials, API keys, or tokens are stored in the application repository or source distribution
- Authentication tokens are stored exclusively in the user's application data directory
- Token files must have restrictive file permissions (readable only by the owning OS user account)
- The authentication flow for Google Calendar must not block or gate any core app functionality

---

## 13. User Interaction Flows

### 13.1 First Launch Flow

```
App opens
  → Welcome screen displayed
  → User selects mode: Passive or Active
  → User optionally selects quote categories (all pre-selected)
  → Config file created with selections
  → App minimizes to system tray
  → Begins operating in selected mode
```

No welcome screen on subsequent launches.

### 13.2 Passive Mode — Normal Operation

```
App running in tray
  → Timer counting toward next bell interval
  → [At bell interval]
      → Bowl sound plays
      → Quote notification displayed
      → Bell event logged to database
      → Timer resets
  → [If user idle beyond threshold]
      → Timer pauses
      → Tray: "Paused — idle"
  → [On next OS input after idle]
      → Timer resumes within 2 seconds
      → Tray returns to elapsed time display
```

### 13.3 Active Mode — Session Lifecycle

```
User: right-click tray → "New Session"
  → Duration selection screen appears
  → User selects duration preset
  → User optionally enters aim text
  → User confirms start
  → Bowl rings
  → Session record created in database (start time, aim)
  → Tray: shows countdown

  [During session — at each bell interval]
    → Bowl rings
    → Quote notification displayed

  [Session end — timer reaches zero]
    → Bowl rings
    → Session record updated: end time, duration, completed = true
    → Tray: returns to "No active session"

  [Early stop — user: right-click → "Stop Session"]
    → Bowl rings (optional — see Open Questions)
    → Session record updated: actual duration, completed = false
    → Tray: returns to "No active session"

  [Pause — user: right-click → "Pause Session"]
    → Timer pauses
    → Tray: "Session paused — X min remaining"
    → Menu item switches to "Resume Session"

  [Resume — user: right-click → "Resume Session"]
    → Timer resumes
    → Tray: countdown resumes
    → Menu item switches to "Pause Session"
```

### 13.4 Stats View Flow

```
User: right-click tray → "View Stats"
  → Stats window opens (non-modal)
  → Weekly summary displayed
  → Session list displayed (most recent first)
  → User optionally adjusts date range filter
  → User closes window
  → App continues tray operation unaffected
```

### 13.5 Settings Flow

```
User: right-click tray → "Settings"
  → Settings window opens (non-modal)
  → User modifies any setting
  → Change saved to config immediately on modification
  → User closes window
  → New settings take effect immediately
```

---

## 14. Edge Case Handling

| Scenario | Required Behavior |
|---|---|
| Second app instance launched | New instance detects existing instance is running, brings focus to tray icon area, exits immediately without opening a second tray icon |
| OS sleep during active session | Timer pauses at sleep; resumes on wake; sleep duration excluded from session time |
| OS sleep during passive mode | Timer pauses at sleep; resumes on wake |
| No audio output device available | Bell sound skipped silently; quote notification still displayed; no error shown |
| Config file missing on startup | App resets to defaults; displays a single non-blocking notification informing the user of the reset |
| Config file corrupted on startup | Same as missing: reset to defaults, single notification |
| Database file missing or corrupted | App creates a fresh database; logs a warning internally; existing history is lost but app continues operating |
| Quote category filter results in empty pool | App falls back to full quote library for that bell; logs a warning |
| Active session running when OS shuts down | Session logged with duration up to shutdown time, marked incomplete |

---

## 15. Integration Requirements

These are behavioral requirements on the app's interactions with the operating system and external services. They do not prescribe implementation approach.

### 15.1 Operating System

| Requirement | Description |
|---|---|
| System-wide input monitoring | Must detect mouse movement and keyboard input from any application, not only when the app window has focus |
| System tray registration | Must place a persistent tray icon with tooltip text and a right-click context menu |
| Single-instance enforcement | Must detect if an instance is already running and prevent a second instance from fully launching |
| Sleep/wake detection | Must receive OS notifications for sleep entry and wake events to pause and resume timers |
| Cross-platform compatibility | Must function without modification on Windows 10+, macOS 12+, and Ubuntu 22.04+ |

### 15.2 Audio

| Requirement | Description |
|---|---|
| Sound playback | Must play a bundled Tibetan singing bowl audio file on bell events |
| Graceful audio failure | If audio device is unavailable, bell event proceeds silently without error or interruption |

### 15.3 File System

| Requirement | Description |
|---|---|
| Config file location | Must resolve to the correct OS-specific user application data directory on all platforms |
| Database file location | Same directory as config |
| Token storage location | Same directory; tokens must have OS-enforced read permissions restricted to the current user |
| Path resolution | All file and directory paths must resolve correctly on all supported operating systems |

### 15.4 Google Calendar

| Requirement | Description |
|---|---|
| Authentication | App must guide the user through an authentication flow, store resulting credentials locally, and use those credentials for subsequent calendar operations without requiring re-authentication unless credentials expire or are revoked |
| Token refresh | App must refresh tokens automatically without user interaction when possible |
| Event creation | On active session start: create a calendar event with title, aim text, and estimated end time |
| Event update | On active session end or early stop: update the calendar event with actual end time |
| Silent degradation | All calendar operations must fail silently if credentials are absent, expired, or the request fails |

### 15.5 Desktop Notifications

| Requirement | Description |
|---|---|
| Quote display | At each bell event, a notification or overlay must display the selected quote |
| Non-blocking | Notification must not require user interaction to dismiss before the app continues |
| Dismissible | User must be able to dismiss the notification manually |

### 15.6 Data Export

| Requirement | Description |
|---|---|
| JSON export | All session and bell event records must be exportable to a JSON file on user request |
| Schema stability | Record schema must remain backward-compatible across v2 minor releases |

---

## 16. Acceptance Criteria

| ID | Criterion | Pass Condition |
|---|---|---|
| AC-01 | Passive mode bell timing | Bowl sound plays within ±5 seconds of the configured interval |
| AC-02 | Active session lifecycle | User can start, pause, resume, and stop a session; each state change is reflected in the tray tooltip and context menu |
| AC-03 | First-launch welcome screen | On first run (no config file present), welcome screen appears; after mode selection, config file exists with the chosen mode |
| AC-04 | System-wide idle detection | Timer pauses when no OS-level mouse or keyboard input is detected for the full idle threshold duration, even when another application has focus |
| AC-05 | Idle resume latency | Timer resumes within 2 seconds of detecting OS-level input following an idle pause |
| AC-06 | Config persistence across restarts | All settings survive an app restart; a changed setting is present with its new value after restart |
| AC-07 | Active session database logging | After completing an active session, one record exists in the database with correct start timestamp, duration, aim text, and completed = true |
| AC-08 | Passive bell event logging | Each bell ring in passive mode produces one record in the database with correct timestamp |
| AC-09 | Weekly stats accuracy | All totals in the stats view match the raw record count and sum in the database |
| AC-10 | Quote category filtering | With only "Gurdjieff" selected, only quotes tagged with the Gurdjieff category appear at bell events |
| AC-11 | No consecutive quote repeats | The same quote does not appear on two consecutive bell events |
| AC-12 | Google Calendar opt-in behavior | With GCal disabled: no auth prompts, no errors; with GCal enabled and authenticated: an active session start creates a calendar event |
| AC-13 | GCal auth failure — silent degradation | If GCal token is expired or invalid: app logs warning internally, continues all core operations, shows no user-facing error |
| AC-14 | Single instance enforcement | Launching a second instance while the first is running results in no additional tray icon appearing; the second process exits within 3 seconds; the first instance continues operating without interruption |
| AC-15 | Cross-platform operation | App runs on Windows 10+, macOS 12+, and Ubuntu 22.04+ without platform-specific modification |
| AC-16 | Tray tooltip content | Passive mode: tooltip shows elapsed time since last bell; active mode with session: tooltip shows remaining session time |
| AC-17 | Early stop logging | Stopping an active session before its scheduled end logs the actual elapsed duration and sets completed = false |
| AC-18 | Corrupted config recovery | Deleting or corrupting the config file before launch causes the app to reset to defaults on next launch and display a one-time notification |
| AC-19 | OS sleep/wake timer pause | On OS sleep entry, the timer pauses; on OS wake, the timer resumes; sleep duration is not counted toward bell interval or session duration |

---

## 17. Out of Scope

The following are explicitly excluded from v2 and deferred to future versions:

- Web backend or server component of any kind
- Mobile platform support (iOS, Android)
- Custom sound upload or sound library selection
- Team sync, shared dashboards, or multi-user features
- Auto-update mechanism
- Onboarding tutorial beyond the initial mode selection screen
- Sync of aim history across devices

---

## 18. Open Questions

These questions require resolution before implementation begins. They are not blockers for spec approval.

| # | Question | Options | Impact |
|---|---|---|---|
| OQ-1 | Weekly summary reset day | Monday (ISO week standard) vs. Sunday (US convention) | Affects streak calculation and weekly totals boundary |
| OQ-2 | Maximum aim text length | 140 characters (tweet-length) vs. 280 vs. unconstrained | UI layout in stats view, database field sizing |
| OQ-3 | Quote notification auto-dismiss duration | Auto-dismiss is confirmed (per Section 8.3: non-blocking, no acknowledgment required). What is N seconds? Should N be configurable? | Affects notification UX; default recommendation: 10 seconds, configurable |

---

*Spec ID: 001-self-remembering-app-v2 — v2.0 — 2026-03-23*
