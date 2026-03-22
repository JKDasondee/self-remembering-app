import sys
import os
import time

from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QDialog, QFormLayout,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QGroupBox, QScrollArea, QMessageBox, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QIcon, QFont, QAction, QPixmap

from . import config, db, bell, quotes
from .idle import IdleDetector
from . import calendar_plugin


def _base_path():
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _icon_path():
    return os.path.join(_base_path(), "icons", "selfremembering.ico")


class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Self Remembering App")
        self.setMinimumWidth(380)
        layout = QVBoxLayout()

        title = QLabel("Welcome to Self Remembering App")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(QLabel("Choose your default mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["passive", "active"])
        layout.addWidget(self.mode_combo)

        layout.addWidget(QLabel("Select quote categories:"))
        self.cat_checks = {}
        for cat in quotes.get_categories():
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
        return {"mode": self.mode_combo.currentText(), "quote_categories": cats}


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
        return {"duration": int(txt), "aim": self.aim_input.text().strip() or None}


class StatsWindow(QWidget):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Session Stats")
        self.setMinimumSize(550, 420)
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


class MainWindow(QWidget):
    def __init__(self, tray_app):
        super().__init__()
        self._app = tray_app
        self.setWindowTitle("Self Remembering App")
        self.setMinimumSize(440, 520)
        icon_path = _icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.mode_label = QLabel()
        self.mode_label.setFont(QFont("Arial", 10))
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.mode_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        form = QFormLayout()
        form.setSpacing(10)
        self.aim_input = QLineEdit()
        self.aim_input.setPlaceholderText("Enter your aim for this session...")
        self.aim_input.setFont(QFont("Arial", 10))
        form.addRow(QLabel("Aim:"), self.aim_input)

        self.duration_combo = QComboBox()
        self.duration_combo.addItems(["5 min", "15 min", "25 min", "30 min", "45 min", "60 min"])
        self.duration_combo.setCurrentIndex(2)
        self.duration_combo.setFont(QFont("Arial", 10))
        form.addRow(QLabel("Duration:"), self.duration_combo)
        layout.addLayout(form)

        self.timer_display = QLabel("0:00")
        self.timer_display.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        self.timer_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.timer_display)

        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Arial", 9))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)

        self.quote_label = QLabel()
        self.quote_label.setFont(QFont("Arial", 10, italic=True))
        self.quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quote_label.setWordWrap(True)
        self.quote_label.setMinimumHeight(60)
        layout.addWidget(self.quote_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_path = os.path.join(_base_path(), "icons", "picture.jpg")
        if os.path.exists(img_path):
            px = QPixmap(img_path).scaled(QSize(300, 150), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(px)
        layout.addWidget(self.image_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.start_btn = QPushButton("Start")
        self.start_btn.setFont(QFont("Arial", 10))
        self.start_btn.clicked.connect(self._start)
        btn_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setFont(QFont("Arial", 10))
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self._pause)
        btn_layout.addWidget(self.pause_btn)

        self.resume_btn = QPushButton("Resume")
        self.resume_btn.setFont(QFont("Arial", 10))
        self.resume_btn.setEnabled(False)
        self.resume_btn.clicked.connect(self._resume)
        btn_layout.addWidget(self.resume_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFont(QFont("Arial", 10))
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop)
        btn_layout.addWidget(self.stop_btn)

        layout.addLayout(btn_layout)

        bottom = QHBoxLayout()
        stats_btn = QPushButton("Stats")
        stats_btn.clicked.connect(self._app._show_stats)
        bottom.addWidget(stats_btn)
        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self._app._show_settings)
        bottom.addWidget(settings_btn)
        layout.addLayout(bottom)

        self.setLayout(layout)
        self._show_random_quote()

    def _show_random_quote(self):
        q = self._app.rotator.next()
        self.quote_label.setText(f"<i>{q['text']}</i>\n— {q['author']}")

    def update_display(self):
        a = self._app
        if a._mode == "passive":
            self.mode_label.setText(f"Mode: Passive  |  Bell every {a.cfg.get('bell_interval', 60)} min")
            mins = a._passive_elapsed // 60
            secs = a._passive_elapsed % 60
            self.timer_display.setText(f"{mins}:{secs:02d}")
            if a._idle_paused:
                self.status_label.setText("Paused — idle")
            else:
                self.status_label.setText(f"{mins}m since start")
            self.aim_input.setEnabled(False)
            self.duration_combo.setEnabled(False)
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)

        elif a._mode == "active":
            self.mode_label.setText("Mode: Active")
            if a._session_running or a._session_paused:
                remaining = a._session_total - a._session_elapsed
                mins = max(0, remaining) // 60
                secs = max(0, remaining) % 60
                self.timer_display.setText(f"{mins}:{secs:02d}")
                aim_txt = a._session_aim or ""
                if a._session_paused:
                    self.status_label.setText(f"Session paused | Aim: {aim_txt}")
                elif a._idle_paused:
                    self.status_label.setText("Paused — idle")
                else:
                    self.status_label.setText(f"Session active | Aim: {aim_txt}")
                self.aim_input.setEnabled(False)
                self.duration_combo.setEnabled(False)
                self.start_btn.setEnabled(False)
                self.pause_btn.setEnabled(a._session_running and not a._session_paused)
                self.resume_btn.setEnabled(a._session_paused)
                self.stop_btn.setEnabled(True)
            else:
                self.timer_display.setText("0:00")
                self.status_label.setText("No active session")
                self.aim_input.setEnabled(True)
                self.duration_combo.setEnabled(True)
                self.start_btn.setEnabled(True)
                self.pause_btn.setEnabled(False)
                self.resume_btn.setEnabled(False)
                self.stop_btn.setEnabled(False)

    def show_quote_on_bell(self, q):
        self.quote_label.setText(f"<i>{q['text']}</i>\n— {q['author']}")

    def _start(self):
        a = self._app
        aim = self.aim_input.text().strip() or None
        txt = self.duration_combo.currentText().replace(" min", "")
        dur = int(txt)

        a._session_aim = aim
        a._session_total = dur * 60
        a._session_elapsed = 0
        a._session_running = True
        a._session_paused = False
        a._bell_counter = 0
        a._session_id = db.log_session_start(a.cfg.get("user_id", "local"), "active", aim)
        if aim:
            config.add_aim(a.cfg, aim)
        bell.play()
        self._show_random_quote()
        if a.cfg.get("gcal_enabled") and calendar_plugin._service:
            a._event_id = calendar_plugin.create_event(aim, dur)
        a._build_menu()

    def _pause(self):
        self._app._pause_session()

    def _resume(self):
        self._app._resume_session()

    def _stop(self):
        self._app._stop_session()
        self._show_random_quote()

    def closeEvent(self, event):
        event.ignore()
        self.hide()


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
        self._main_win = None

        self.tray = QSystemTrayIcon(self.icon)
        self.tray.setToolTip("Self Remembering App")
        self.tray.activated.connect(self._tray_activated)
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

        self._main_win = MainWindow(self)
        self._main_win.update_display()
        self._main_win.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self._main_win:
                if self._main_win.isVisible():
                    self._main_win.raise_()
                    self._main_win.activateWindow()
                else:
                    self._main_win.show()
                    self._main_win.raise_()

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

        a = menu.addAction("Open Window")
        a.triggered.connect(lambda: self._main_win and self._main_win.show() and self._main_win.raise_())

        menu.addSeparator()

        mode_menu = menu.addMenu("Mode")
        for m in ["passive", "active"]:
            act = QAction(m.capitalize(), menu)
            act.setCheckable(True)
            act.setChecked(m == self._mode)
            act.triggered.connect(lambda checked, mode=m: self._switch_mode(mode))
            mode_menu.addAction(act)

        menu.addSeparator()

        if self._mode == "passive":
            iv_menu = menu.addMenu("Bell Interval")
            for mins in [15, 30, 45, 60]:
                act = QAction(f"{mins} min", menu)
                act.setCheckable(True)
                act.setChecked(self.cfg.get("bell_interval", 60) == mins)
                act.triggered.connect(lambda checked, m=mins: self._set_interval(m))
                iv_menu.addAction(act)

        if self._mode == "active":
            if not self._session_running and not self._session_paused:
                act = menu.addAction("New Session")
                act.triggered.connect(self._new_session)
            if self._session_running and not self._session_paused:
                act = menu.addAction("Pause Session")
                act.triggered.connect(self._pause_session)
            if self._session_paused:
                act = menu.addAction("Resume Session")
                act.triggered.connect(self._resume_session)
            if self._session_running or self._session_paused:
                act = menu.addAction("Stop Session")
                act.triggered.connect(self._stop_session)

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
        if self._main_win:
            self._main_win.update_display()

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
                self._session_id, self._session_elapsed,
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
            if self._main_win:
                self._main_win.update_display()
            return

        interval_sec = self.cfg.get("bell_interval", 60) * 60

        if self._mode == "passive":
            self._passive_elapsed += 1
            self._bell_counter += 1
            if self._bell_counter >= interval_sec:
                self._fire_bell("passive")
                self._bell_counter = 0
            self.tray.setToolTip(f"{self._passive_elapsed // 60}m since start")

        elif self._mode == "active" and self._session_running and not self._session_paused:
            self._session_elapsed += 1
            self._bell_counter += 1
            remaining = self._session_total - self._session_elapsed
            if remaining <= 0:
                self._fire_bell("active")
                self._stop_session()
                if self._main_win:
                    self._main_win._show_random_quote()
                    self._main_win.update_display()
                return
            if self._bell_counter >= interval_sec:
                self._fire_bell("active")
                self._bell_counter = 0
            self.tray.setToolTip(f"{remaining // 60}m {remaining % 60}s remaining")

        if self._main_win:
            self._main_win.update_display()

    def _fire_bell(self, mode):
        bell.play()
        q = self.rotator.next()
        txt = self.rotator.format(q)
        db.log_bell(self.cfg.get("user_id", "local"), mode, txt)
        self.tray.showMessage("Self Remembering", txt, QSystemTrayIcon.MessageIcon.Information,
                              self.cfg.get("notification_duration", 10) * 1000)
        if self._main_win:
            self._main_win.show_quote_on_bell(q)

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
            if self._main_win:
                self._main_win.update_display()

    def _quit(self):
        if self._session_running or self._session_paused:
            self._stop_session()
        self.idle.stop()
        self.tray.hide()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())
