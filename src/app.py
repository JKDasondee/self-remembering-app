import sys
import os
import time

from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QDialog, QFormLayout,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QGroupBox, QScrollArea, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QFont, QAction

from . import config, db, bell, quotes
from .idle import IdleDetector
from . import calendar_plugin

def _icon_path():
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "icons", "selfremembering.ico")


class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Self Remembering App")
        self.setMinimumWidth(380)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Welcome to Self Remembering App"))

        layout.addWidget(QLabel("Choose your default mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["passive", "active"])
        layout.addWidget(self.mode_combo)

        layout.addWidget(QLabel("Select quote categories:"))
        self.cat_checks = {}
        cats = quotes.get_categories()
        for cat in cats:
            cb = QCheckBox(cat)
            cb.setChecked(True)
            self.cat_checks[cat] = cb
            layout.addWidget(cb)

        btn = QPushButton("Start")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
        self.setLayout(layout)

    def get_config(self):
        cats = [c for c, cb in self.cat_checks.items() if cb.isChecked()]
        return {
            "mode": self.mode_combo.currentText(),
            "quote_categories": cats,
        }


class SessionDialog(QDialog):
    def __init__(self, aim_history=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Session")
        self.setMinimumWidth(350)
        layout = QFormLayout()

        self.duration_combo = QComboBox()
        self.duration_combo.addItems(["5 min", "15 min", "25 min", "30 min", "45 min", "60 min"])
        self.duration_combo.setCurrentIndex(2)
        layout.addRow("Duration:", self.duration_combo)

        self.aim_input = QLineEdit()
        self.aim_input.setPlaceholderText("Enter your aim...")
        layout.addRow("Aim:", self.aim_input)

        btn = QPushButton("Start Session")
        btn.clicked.connect(self.accept)
        layout.addRow(btn)
        self.setLayout(layout)

    def get_values(self):
        txt = self.duration_combo.currentText().replace(" min", "")
        return {
            "duration": int(txt),
            "aim": self.aim_input.text().strip() or None,
        }


class StatsWindow(QWidget):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Session Stats")
        self.setMinimumSize(500, 400)
        self._uid = user_id
        layout = QVBoxLayout()

        self.summary = QLabel()
        self.summary.setFont(QFont("Arial", 11))
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "Mode", "Duration", "Aim", "Completed"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        btn = QPushButton("Export JSON")
        btn.clicked.connect(self._export)
        layout.addWidget(btn)

        self.setLayout(layout)
        self.refresh()

    def refresh(self):
        s = db.weekly_stats(self._uid)
        aims_str = ", ".join(f"{a['aim']} ({a['count']})" for a in s["top_aims"]) or "none"
        self.summary.setText(
            f"This week: {s['sessions']} sessions, {s['minutes']} min, "
            f"{s['bells']} bells, streak {s['streak']}d\n"
            f"Top aims: {aims_str}"
        )
        rows = db.recent_sessions(self._uid)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r["ts_start"][:16]))
            self.table.setItem(i, 1, QTableWidgetItem(r["mode"]))
            self.table.setItem(i, 2, QTableWidgetItem(f"{r['duration_seconds'] // 60}m"))
            self.table.setItem(i, 3, QTableWidgetItem(r.get("aim_text") or ""))
            self.table.setItem(i, 4, QTableWidgetItem("Yes" if r["completed"] else "No"))

    def _export(self):
        data = db.export_json(self._uid)
        p = os.path.join(config.DATA_DIR, "export.json")
        with open(p, "w") as f:
            f.write(data)
        QMessageBox.information(self, "Exported", f"Saved to {p}")


class SettingsDialog(QDialog):
    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        self._cfg = cfg
        layout = QVBoxLayout()

        form = QFormLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["passive", "active"])
        self.mode_combo.setCurrentText(cfg.get("mode", "passive"))
        form.addRow("Mode:", self.mode_combo)

        self.bell_spin = QSpinBox()
        self.bell_spin.setRange(5, 120)
        self.bell_spin.setValue(cfg.get("bell_interval", 60))
        self.bell_spin.setSuffix(" min")
        form.addRow("Bell Interval:", self.bell_spin)

        self.idle_spin = QSpinBox()
        self.idle_spin.setRange(1, 30)
        self.idle_spin.setValue(cfg.get("idle_threshold", 5))
        self.idle_spin.setSuffix(" min")
        form.addRow("Idle Threshold:", self.idle_spin)

        layout.addLayout(form)

        grp = QGroupBox("Quote Categories")
        grp_layout = QVBoxLayout()
        self.cat_checks = {}
        active_cats = cfg.get("quote_categories", [])
        for cat in quotes.get_categories():
            cb = QCheckBox(cat)
            cb.setChecked(not active_cats or cat in active_cats)
            self.cat_checks[cat] = cb
            grp_layout.addWidget(cb)
        grp.setLayout(grp_layout)
        layout.addWidget(grp)

        self.gcal_check = QCheckBox("Enable Google Calendar")
        self.gcal_check.setChecked(cfg.get("gcal_enabled", False))
        layout.addWidget(self.gcal_check)

        btn = QPushButton("Save")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
        self.setLayout(layout)

    def get_config(self):
        cats = [c for c, cb in self.cat_checks.items() if cb.isChecked()]
        return {
            "mode": self.mode_combo.currentText(),
            "bell_interval": self.bell_spin.value(),
            "idle_threshold": self.idle_spin.value(),
            "quote_categories": cats,
            "gcal_enabled": self.gcal_check.isChecked(),
        }


class TrayApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        icon_path = _icon_path()
        self.icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        self.app.setWindowIcon(self.icon)

        self._first_launch = config.is_first_launch()
        self.cfg = config.load()

        db.init()
        bell.init()

        self.rotator = quotes.QuoteRotator(self.cfg.get("quote_categories") or None)
        self.idle = IdleDetector(self.cfg.get("idle_threshold", 5))
        self.idle.on_state_change(self._on_idle_change)

        self._mode = self.cfg.get("mode", "passive")
        self._session_running = False
        self._session_paused = False
        self._session_id = None
        self._session_elapsed = 0
        self._session_total = 0
        self._session_aim = None
        self._event_id = None
        self._passive_elapsed = 0
        self._idle_paused = False
        self._bell_counter = 0

        self._stats_win = None

        self.tray = QSystemTrayIcon(self.icon)
        self.tray.setToolTip("Self Remembering App")
        self._build_menu()
        self.tray.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)

        if self._first_launch:
            self._show_welcome()

        if self.cfg.get("gcal_enabled"):
            calendar_plugin.setup()

        self.idle.start()

    def _show_welcome(self):
        dlg = WelcomeDialog()
        if dlg.exec():
            vals = dlg.get_config()
            self.cfg.update(vals)
            self._mode = vals["mode"]
            self.rotator.set_categories(vals.get("quote_categories"))
            config.save(self.cfg)
            self._build_menu()

    def _build_menu(self):
        menu = QMenu()

        mode_menu = menu.addMenu("Mode")
        for m in ["passive", "active"]:
            a = QAction(m.capitalize(), menu)
            a.setCheckable(True)
            a.setChecked(m == self._mode)
            a.triggered.connect(lambda checked, mode=m: self._switch_mode(mode))
            mode_menu.addAction(a)

        menu.addSeparator()

        if self._mode == "passive":
            iv_menu = menu.addMenu("Bell Interval")
            for mins in [15, 30, 45, 60]:
                a = QAction(f"{mins} min", menu)
                a.setCheckable(True)
                a.setChecked(self.cfg.get("bell_interval", 60) == mins)
                a.triggered.connect(lambda checked, m=mins: self._set_interval(m))
                iv_menu.addAction(a)

        if self._mode == "active":
            if not self._session_running and not self._session_paused:
                a = menu.addAction("New Session")
                a.triggered.connect(self._new_session)
            if self._session_running and not self._session_paused:
                a = menu.addAction("Pause Session")
                a.triggered.connect(self._pause_session)
            if self._session_paused:
                a = menu.addAction("Resume Session")
                a.triggered.connect(self._resume_session)
            if self._session_running or self._session_paused:
                a = menu.addAction("Stop Session")
                a.triggered.connect(self._stop_session)

        menu.addSeparator()
        menu.addAction("View Stats").triggered.connect(self._show_stats)
        menu.addAction("Settings").triggered.connect(self._show_settings)
        menu.addSeparator()
        menu.addAction("Quit").triggered.connect(self._quit)

        self.tray.setContextMenu(menu)

    def _switch_mode(self, mode):
        if self._session_running or self._session_paused:
            self._stop_session()
        self._mode = mode
        self.cfg["mode"] = mode
        config.save(self.cfg)
        self._passive_elapsed = 0
        self._bell_counter = 0
        self._build_menu()

    def _set_interval(self, mins):
        self.cfg["bell_interval"] = mins
        config.save(self.cfg)
        self._bell_counter = 0
        self._build_menu()

    def _new_session(self):
        dlg = SessionDialog(self.cfg.get("aim_history"))
        if dlg.exec():
            vals = dlg.get_values()
            self._session_aim = vals["aim"]
            self._session_total = vals["duration"] * 60
            self._session_elapsed = 0
            self._session_running = True
            self._session_paused = False
            self._bell_counter = 0
            self._session_id = db.log_session_start(
                self.cfg.get("user_id", "local"), "active", self._session_aim
            )
            if self._session_aim:
                config.add_aim(self.cfg, self._session_aim)
            bell.play()
            self._show_quote()
            if self.cfg.get("gcal_enabled") and calendar_plugin._service:
                self._event_id = calendar_plugin.create_event(self._session_aim, vals["duration"])
            self._build_menu()

    def _pause_session(self):
        self._session_paused = True
        self._session_running = False
        self._build_menu()
        self.tray.setToolTip(f"Session paused — {(self._session_total - self._session_elapsed) // 60}m remaining")

    def _resume_session(self):
        self._session_paused = False
        self._session_running = True
        bell.play()
        self._build_menu()

    def _stop_session(self):
        if self._session_id:
            db.log_session_end(
                self._session_id,
                self._session_elapsed,
                self._session_elapsed >= self._session_total,
            )
        bell.play()
        if self._event_id:
            calendar_plugin.patch_end(self._event_id)
        self._session_running = False
        self._session_paused = False
        self._session_id = None
        self._session_elapsed = 0
        self._session_total = 0
        self._session_aim = None
        self._event_id = None
        self._bell_counter = 0
        self._build_menu()
        self.tray.setToolTip("No active session")

    def _tick(self):
        if self._idle_paused:
            return

        interval_sec = self.cfg.get("bell_interval", 60) * 60

        if self._mode == "passive":
            self._passive_elapsed += 1
            self._bell_counter += 1
            if self._bell_counter >= interval_sec:
                self._fire_bell("passive")
                self._bell_counter = 0
            mins = self._passive_elapsed // 60
            self.tray.setToolTip(f"{mins}m since start")

        elif self._mode == "active" and self._session_running and not self._session_paused:
            self._session_elapsed += 1
            self._bell_counter += 1
            remaining = self._session_total - self._session_elapsed
            if remaining <= 0:
                self._fire_bell("active")
                self._stop_session()
                return
            if self._bell_counter >= interval_sec:
                self._fire_bell("active")
                self._bell_counter = 0
            self.tray.setToolTip(f"{remaining // 60}m {remaining % 60}s remaining")

    def _fire_bell(self, mode):
        bell.play()
        q = self.rotator.next()
        txt = self.rotator.format(q)
        db.log_bell(self.cfg.get("user_id", "local"), mode, txt)
        self.tray.showMessage("Self Remembering", txt, QSystemTrayIcon.MessageIcon.Information,
                              self.cfg.get("notification_duration", 10) * 1000)

    def _show_quote(self):
        q = self.rotator.next()
        txt = self.rotator.format(q)
        self.tray.showMessage("Self Remembering", txt, QSystemTrayIcon.MessageIcon.Information, 8000)

    def _on_idle_change(self, is_idle):
        self._idle_paused = is_idle
        if is_idle:
            self.tray.setToolTip("Paused — idle")
        else:
            if self._mode == "passive":
                self.tray.setToolTip(f"{self._passive_elapsed // 60}m since start")

    def _show_stats(self):
        if self._stats_win:
            self._stats_win.refresh()
            self._stats_win.show()
            self._stats_win.raise_()
            return
        self._stats_win = StatsWindow(self.cfg.get("user_id", "local"))
        self._stats_win.show()

    def _show_settings(self):
        dlg = SettingsDialog(self.cfg)
        if dlg.exec():
            new_cfg = dlg.get_config()
            old_mode = self._mode
            self.cfg.update(new_cfg)
            config.save(self.cfg)
            self._mode = new_cfg["mode"]
            self.rotator.set_categories(new_cfg.get("quote_categories"))
            self.idle.set_threshold(new_cfg.get("idle_threshold", 5))
            if new_cfg.get("gcal_enabled") and not calendar_plugin._service:
                calendar_plugin.setup()
            if old_mode != self._mode:
                self._passive_elapsed = 0
                self._bell_counter = 0
            self._build_menu()

    def _quit(self):
        if self._session_running or self._session_paused:
            self._stop_session()
        self.idle.stop()
        self.tray.hide()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())
