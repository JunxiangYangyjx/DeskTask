from __future__ import annotations

import argparse
import copy
import json
import sys
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


def application_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


APP_ROOT = application_root()
DEFAULT_DATA_PATH = APP_ROOT / "daily_tasks.json"
DEFAULT_SETTINGS_PATH = APP_ROOT / "app_settings.json"
DEFAULT_EXAMPLE_DATA_PATH = APP_ROOT / "daily_tasks.example.json"
DEFAULT_EXAMPLE_SETTINGS_PATH = APP_ROOT / "app_settings.example.json"

GROUP_MUST = "今天必须做"
GROUP_NEXT = "可以推进"
GROUP_LATER = "可选或等待"

STATUS_LABELS = {
    "todo": "未开始",
    "doing": "进行中",
    "done": "完成",
    "blocked": "阻塞",
    "waiting": "等待",
    "scheduled": "已安排",
}

TASK_TYPE_LABELS = {
    "high": "高优先级",
    "medium": "中优先级",
    "low": "低优先级",
    "recurring": "循环",
    "reminder": "提醒",
}

TASK_TYPE_OPTIONS = [
    ("high", "高优先级"),
    ("medium", "中优先级"),
    ("low", "低优先级"),
    ("recurring", "循环"),
    ("reminder", "提醒"),
]

DEFAULT_SETTINGS = {
    "view": "panel",
    "x": None,
    "y": 96,
    "panel_width": 390,
    "panel_height": None,
    "panel_max_height": 680,
    "table_width": 1120,
    "table_height": 640,
    "topmost": True,
    "locked": False,
    "theme": "light",
    "show_done_in_panel": True,
    "daily_reset_time": "00:00",
    "last_reset_date": "",
    "last_completion_clear_00_date": "",
    "last_completion_clear_09_date": "",
    "font_family": "",
    "font_file": "",
}

THEMES = {
    "light": {
        "window": "#f2f5f9",
        "surface": "#ffffff",
        "surface_2": "#f7f9fc",
        "surface_3": "#eef3f8",
        "border": "#dbe3ee",
        "text": "#162033",
        "muted": "#667085",
        "muted_2": "#98a2b3",
        "must": "#e5484d",
        "next": "#2563eb",
        "later": "#64748b",
        "done": "#98a2b3",
        "type_high": "#e5484d",
        "type_medium": "#2563eb",
        "type_low": "#64748b",
        "type_recurring": "#7c3aed",
        "type_reminder": "#d97706",
        "type_high_bg": "#fff4f5",
        "type_medium_bg": "#eff6ff",
        "type_low_bg": "#f8fafc",
        "type_recurring_bg": "#f5f3ff",
        "type_reminder_bg": "#fffbeb",
        "type_high_border": "#ffd6dc",
        "type_medium_border": "#bfdbfe",
        "type_low_border": "#dbe3ee",
        "type_recurring_border": "#ddd6fe",
        "type_reminder_border": "#fde68a",
        "must_bg": "#fff4f5",
        "next_bg": "#eff6ff",
        "later_bg": "#f8fafc",
        "done_bg": "#f1f5f9",
        "must_border": "#ffd6dc",
        "next_border": "#bfdbfe",
        "later_border": "#dbe3ee",
        "done_border": "#dbe3ee",
        "shadow": "#000000",
        "button": "#eef3f8",
        "button_hover": "#e1e8f0",
    },
    "dark": {
        "window": "#111827",
        "surface": "#1f2937",
        "surface_2": "#273449",
        "surface_3": "#334155",
        "border": "#475569",
        "text": "#f8fafc",
        "muted": "#cbd5e1",
        "muted_2": "#94a3b8",
        "must": "#fb7185",
        "next": "#60a5fa",
        "later": "#cbd5e1",
        "done": "#94a3b8",
        "type_high": "#fb7185",
        "type_medium": "#60a5fa",
        "type_low": "#cbd5e1",
        "type_recurring": "#a78bfa",
        "type_reminder": "#fbbf24",
        "type_high_bg": "#3a2029",
        "type_medium_bg": "#1d314f",
        "type_low_bg": "#273449",
        "type_recurring_bg": "#2e254a",
        "type_reminder_bg": "#3a2a12",
        "type_high_border": "#5f2f3b",
        "type_medium_border": "#2f4f7c",
        "type_low_border": "#475569",
        "type_recurring_border": "#5b4b8a",
        "type_reminder_border": "#725315",
        "must_bg": "#3a2029",
        "next_bg": "#1d314f",
        "later_bg": "#273449",
        "done_bg": "#334155",
        "must_border": "#5f2f3b",
        "next_border": "#2f4f7c",
        "later_border": "#475569",
        "done_border": "#475569",
        "shadow": "#000000",
        "button": "#334155",
        "button_hover": "#475569",
    },
}


@dataclass
class Task:
    id: str
    title: str
    status: str
    priority: str
    due_date: str | None
    due_label: str
    note: str
    depends_on: list[str]
    completed_on: str | None

    @property
    def due(self) -> date | None:
        if not self.due_date:
            return None
        try:
            return date.fromisoformat(self.due_date)
        except ValueError:
            return None

    @property
    def status_label(self) -> str:
        return STATUS_LABELS.get(self.status, self.status)


def load_data(path: Path = DEFAULT_DATA_PATH) -> dict[str, Any]:
    if not path.exists():
        if DEFAULT_EXAMPLE_DATA_PATH.exists():
            with DEFAULT_EXAMPLE_DATA_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"version": 1, "settings": {"timezone": "Asia/Shanghai", "morning_reminder": "09:00", "evening_reminder": "18:00"}, "tasks": []}
        save_data(data, path)
        return data
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: dict[str, Any], path: Path = DEFAULT_DATA_PATH) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_settings(path: Path = DEFAULT_SETTINGS_PATH) -> dict[str, Any]:
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    source_path = path if path.exists() else DEFAULT_EXAMPLE_SETTINGS_PATH
    if source_path.exists():
        with source_path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            settings.update(loaded)
    return settings


def save_settings(settings: dict[str, Any], path: Path = DEFAULT_SETTINGS_PATH) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
        f.write("\n")


def parse_tasks(data: dict[str, Any]) -> list[Task]:
    tasks = []
    for item in data.get("tasks", []):
        tasks.append(
            Task(
                id=item["id"],
                title=item["title"],
                status=item.get("status", "todo"),
                priority=item.get("priority", "medium"),
                due_date=item.get("due_date"),
                due_label=item.get("due_label") or item.get("due_date") or "",
                note=item.get("note", ""),
                depends_on=list(item.get("depends_on", [])),
                completed_on=item.get("completed_on"),
            )
        )
    return tasks


def is_completed_today(task: Task, today: date | None = None) -> bool:
    today = today or date.today()
    return task.completed_on == today.isoformat()


def clear_stale_completions(data: dict[str, Any], today: date | None = None) -> bool:
    today = today or date.today()
    changed = False
    for item in data.get("tasks", []):
        completed_on = item.get("completed_on")
        if completed_on and completed_on != today.isoformat() and task_type(item.get("priority")) == "recurring":
            item.pop("completed_on", None)
            changed = True
    return changed


def cleanup_completed_tasks_at_checkpoint(data: dict[str, Any]) -> bool:
    changed = False
    kept_tasks = []
    for item in data.get("tasks", []):
        if item.get("completed_on"):
            if task_type(item.get("priority")) == "recurring":
                item.pop("completed_on", None)
                kept_tasks.append(item)
            changed = True
        else:
            kept_tasks.append(item)
    if changed:
        data["tasks"] = kept_tasks
    return changed


def days_until(task: Task, today: date) -> int | None:
    due = task.due
    if due is None:
        return None
    return (due - today).days


def task_type(value: str | None) -> str:
    if value in TASK_TYPE_LABELS:
        return value
    return "medium"


def task_type_label(value: str | None) -> str:
    return TASK_TYPE_LABELS.get(task_type(value), TASK_TYPE_LABELS["medium"])


def parse_reminder_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip().replace("T", " ")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


GENERIC_REASONS = {"中优先级", "低优先级或长期任务"}


def normalize_detail_text(value: str) -> str:
    return re.sub(r"[\s·，,。；;：:/\-()（）]", "", value)


def compact_detail_text(due_label: str, reason: str) -> str:
    due = (due_label or "").strip()
    reason = (reason or "").strip()

    if not due:
        return reason
    if not reason or reason in GENERIC_REASONS:
        return due

    if due.endswith("6 月前") and reason.startswith("6 月前完成"):
        reason = reason.replace("6 月前完成，", "", 1).strip()
    if due.startswith("ECCE 论文已拒") and reason.startswith("ECCE 已拒，"):
        reason = reason.replace("ECCE 已拒，", "", 1).strip()
    if due.startswith("今天") and reason == "今天截止":
        return due

    due_normalized = normalize_detail_text(due)
    reason_normalized = normalize_detail_text(reason)
    if not reason_normalized or reason_normalized in due_normalized:
        return due
    if due_normalized in reason_normalized:
        return reason

    return f"{due} · {reason}"


def classify_task(task: Task, today: date) -> tuple[str, int, str]:
    if is_completed_today(task, today):
        return (GROUP_LATER, 900, "今天已完成")

    days = days_until(task, today)

    if task.id == "zoom-seminar-procrastination":
        if task.due == today:
            return (GROUP_MUST, 0, "今天 12:00-13:15 参加 Zoom seminar")
        if days is not None and days < 0:
            return (GROUP_LATER, 95, "已过期，可更新或移除")
        return (GROUP_LATER, 70, "5 月 26 日当天参加，提前 10 分钟进入 Zoom")

    if task.id == "ecce-paper-revise-resubmit":
        return (GROUP_MUST, 1, "根据拒稿意见改成 APEC 版本")

    if task.id == "canada-visa-materials" and "暂缓" in task.due_label:
        return (GROUP_LATER, 85, "等待新的录用或签证触发条件")

    if task.id == "canada-visa-materials" and today >= date(2026, 5, 22):
        return (GROUP_MUST, 1, "先确认 ECCE 录取结果，再决定签证材料优先级")

    if task.id in {"3d-printer-research", "pesa-paper-draft"} and today <= date(2026, 5, 31):
        return (GROUP_MUST, 2, "当前应推进")

    if task.id == "pr-application":
        return (GROUP_MUST, 3, "依赖家里人协助")

    if task.id == "submit-reimbursement":
        return (GROUP_NEXT, 45, "整理票据和附件")

    if days is not None:
        if days < 0:
            return (GROUP_MUST, 4, "已超过目标日期，需要处理或更新")
        if days == 0:
            return (GROUP_MUST, 5, "今天截止")
        if days <= 7:
            return (GROUP_MUST, 5, f"还有 {days} 天")
        if days <= 30:
            return (GROUP_NEXT, 20 + days, f"还有 {days} 天")

    current_type = task_type(task.priority)

    if current_type == "high":
        return (GROUP_NEXT, 40, "高优先级，但没有硬截止")

    if current_type == "reminder":
        return (GROUP_NEXT, 42, "提醒事项")

    if current_type == "recurring":
        return (GROUP_NEXT, 50, "循环任务")

    if current_type == "medium":
        return (GROUP_NEXT, 55, "中优先级")

    return (GROUP_LATER, 80, "低优先级或长期任务")


PRIORITY_ORDER = {"high": 0, "reminder": 1, "recurring": 2, "medium": 3, "low": 4}


def row_sort_key(row: dict[str, Any], today: date) -> tuple[Any, ...]:
    task: Task = row["task"]
    if is_completed_today(task, today):
        return (9, 9999, row["rank"], task.title)

    days = days_until(task, today)
    priority_rank = PRIORITY_ORDER.get(task_type(task.priority), 3)

    if row["group"] == GROUP_MUST:
        if days is not None:
            return (0, max(days, -999), priority_rank, row["rank"], task.title)
        return (1, priority_rank, row["rank"], task.title)

    if row["group"] == GROUP_NEXT:
        if days is not None and days <= 30:
            return (2, max(days, -999), priority_rank, row["rank"], task.title)
        if days is None:
            return (3, priority_rank, row["rank"], task.title)
        return (4, days, priority_rank, row["rank"], task.title)

    if days is not None and days >= 0:
        return (5, days, priority_rank, row["rank"], task.title)
    return (6, priority_rank, row["rank"], task.title)


def build_rows(tasks: list[Task], today: date | None = None) -> list[dict[str, Any]]:
    today = today or date.today()
    rows = []
    for task in tasks:
        group, rank, reason = classify_task(task, today)
        rows.append({"group": group, "rank": rank, "reason": reason, "task": task})
    return sorted(rows, key=lambda row: row_sort_key(row, today))


def check_data(path: Path) -> int:
    data = load_data(path)
    clear_stale_completions(data)
    rows = build_rows(parse_tasks(data))
    print(f"Data file: {path}")
    print(f"Tasks: {len(rows)}")
    for row in rows:
        task = row["task"]
        completed = "today-done" if is_completed_today(task) else "open"
        print(f"- [{row['group']}] {task.title} | {completed} | {task.due_label} | {row['reason']}")
    return 0


def run_gui(data_path: Path, settings_path: Path = DEFAULT_SETTINGS_PATH) -> int:
    from PySide6.QtCore import QPoint, Qt, QTimer
    from PySide6.QtGui import QAction, QColor, QFont, QFontDatabase, QIcon, QPainter, QPen, QPixmap
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QFrame,
        QFileDialog,
        QFontComboBox,
        QGraphicsDropShadowEffect,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QMenu,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSizeGrip,
        QSystemTrayIcon,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    class DesktopTaskWindow(QWidget):
        def __init__(self) -> None:
            super().__init__(
                None,
                Qt.FramelessWindowHint
                | Qt.Tool
                | Qt.WindowStaysOnTopHint
                | Qt.NoDropShadowWindowHint,
            )
            self.data_path = data_path
            self.settings_path = settings_path
            self.settings = load_settings(self.settings_path)
            self.data = load_data(self.data_path)
            if clear_stale_completions(self.data):
                save_data(self.data, self.data_path)
            self.drag_offset: QPoint | None = None
            self.is_rendering = False
            self.last_reminders: set[str] = set()
            self.tray_icon: QSystemTrayIcon | None = None

            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setWindowTitle("DeskTask")
            self.apply_app_font()
            self.apply_geometry()
            self.build_tray()
            self.render()

            self.clock = QTimer(self)
            self.clock.timeout.connect(self.on_clock)
            self.clock.start(30_000)
            QTimer.singleShot(0, self.on_clock)

        @property
        def theme(self) -> dict[str, str]:
            return THEMES.get(self.settings.get("theme", "light"), THEMES["light"])

        def apply_app_font(self) -> None:
            app = QApplication.instance()
            family = self.settings.get("font_family") or ""
            font_file = self.settings.get("font_file") or ""
            if font_file:
                font_path = Path(font_file)
                if not font_path.is_absolute():
                    font_path = APP_ROOT / font_path
                if font_path.exists():
                    font_id = QFontDatabase.addApplicationFont(str(font_path))
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    if families:
                        family = families[0]
            if not family:
                available = set(QFontDatabase.families())
                for candidate in ["MiSans", "HarmonyOS Sans SC", "Noto Sans SC", "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI"]:
                    if candidate in available:
                        family = candidate
                        break
            app.setFont(QFont(family or "Segoe UI", 10))

        def icon(self) -> QIcon:
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor("#2563eb"))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(8, 8, 48, 48, 14, 14)
            pen = QPen(QColor("#ffffff"), 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(20, 34, 29, 43)
            painter.drawLine(29, 43, 45, 23)
            painter.end()
            return QIcon(pixmap)

        def build_tray(self) -> None:
            if not QSystemTrayIcon.isSystemTrayAvailable():
                return
            self.tray_icon = QSystemTrayIcon(self.icon(), self)
            menu = QMenu()
            add_task = QAction("增加任务", self)
            add_task.triggered.connect(self.open_add_task_dialog)
            show_panel = QAction("显示小面板", self)
            show_panel.triggered.connect(lambda: self.show_view("panel"))
            show_table = QAction("打开完整表格", self)
            show_table.triggered.connect(lambda: self.show_view("table"))
            quit_action = QAction("退出", self)
            quit_action.triggered.connect(QApplication.instance().quit)
            menu.addAction(add_task)
            menu.addSeparator()
            menu.addAction(show_panel)
            menu.addAction(show_table)
            menu.addSeparator()
            menu.addAction(quit_action)
            self.tray_icon.setContextMenu(menu)
            self.tray_icon.activated.connect(self.on_tray_activated)
            self.tray_icon.show()

        def on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
            if reason in {QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick}:
                self.show_view("panel")

        def render(self) -> None:
            self.is_rendering = True
            try:
                self.data = load_data(self.data_path)
                if clear_stale_completions(self.data):
                    save_data(self.data, self.data_path)
                while self.layout() and self.layout().count():
                    item = self.layout().takeAt(0)
                    widget = item.widget()
                    if widget:
                        self.dispose_widget(widget)
                if self.layout() is None:
                    root_layout = QVBoxLayout(self)
                    root_layout.setContentsMargins(16, 16, 16, 16)
                self.layout().setSpacing(0)
                if self.settings.get("view") == "table":
                    self.render_table()
                else:
                    self.render_panel()
                self.apply_geometry()
            finally:
                self.is_rendering = False

        def dispose_widget(self, widget: QWidget) -> None:
            widget.blockSignals(True)
            for child in widget.findChildren(QWidget):
                child.blockSignals(True)
            widget.deleteLater()

        def card_shell(self) -> QFrame:
            shell = QFrame()
            shell.setObjectName("shell")
            shell.setStyleSheet(
                f"""
                QFrame#shell {{
                    background: {self.theme['surface']};
                    border: 1px solid {self.theme['border']};
                    border-radius: 24px;
                }}
                QLabel {{
                    color: {self.theme['text']};
                }}
                QPushButton {{
                    background: {self.theme['button']};
                    color: {self.theme['text']};
                    border: none;
                    border-radius: 12px;
                    padding: 6px 10px;
                }}
                QPushButton:hover {{
                    background: {self.theme['button_hover']};
                }}
                QScrollArea {{
                    border: none;
                    background: transparent;
                }}
                QScrollBar:vertical {{
                    background: transparent;
                    width: 8px;
                    margin: 8px 0 8px 0;
                }}
                QScrollBar::handle:vertical {{
                    background: {self.theme['border']};
                    border-radius: 4px;
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0;
                }}
                """
            )
            shadow = QGraphicsDropShadowEffect(shell)
            shadow.setBlurRadius(28)
            shadow.setColor(QColor(0, 0, 0, 48))
            shadow.setOffset(0, 10)
            shell.setGraphicsEffect(shadow)
            self.layout().addWidget(shell)
            return shell

        def header(self, parent_layout: QVBoxLayout, title: str, subtitle: str = "") -> None:
            header = QHBoxLayout()
            header.setContentsMargins(18, 16, 18, 10)
            left = QVBoxLayout()
            left.setSpacing(2)
            title_label = QLabel(title)
            title_label.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {self.theme['text']};")
            left.addWidget(title_label)
            if subtitle:
                subtitle_label = QLabel(subtitle)
                subtitle_label.setStyleSheet(f"font-size: 12px; color: {self.theme['muted']};")
                left.addWidget(subtitle_label)
            header.addLayout(left, 1)

            more = QPushButton("+")
            more.setFixedSize(36, 36)
            more.setObjectName("moreButton")
            more.setStyleSheet(
                f"""
                QPushButton#moreButton {{
                    background: {self.theme['button']};
                    color: {self.theme['text']};
                    border: none;
                    border-radius: 18px;
                    font-size: 22px;
                    font-weight: 500;
                    padding-bottom: 3px;
                }}
                QPushButton#moreButton:hover {{
                    background: {self.theme['button_hover']};
                }}
                """
            )
            more.setMenu(self.more_menu())
            header.addWidget(more, 0, Qt.AlignTop)
            parent_layout.addLayout(header)

        def more_menu(self) -> QMenu:
            menu = QMenu(self)
            menu.setStyleSheet(
                f"""
                QMenu {{
                    background: {self.theme['surface']};
                    color: {self.theme['text']};
                    border: 1px solid {self.theme['border']};
                    border-radius: 10px;
                    padding: 6px;
                }}
                QMenu::item {{
                    padding: 8px 28px 8px 12px;
                    border-radius: 8px;
                }}
                QMenu::item:selected {{
                    background: {self.theme['surface_2']};
                }}
                """
            )
            refresh_action = QAction("刷新", self)
            refresh_action.triggered.connect(self.refresh_data)
            add_action = QAction("增加任务", self)
            add_action.triggered.connect(self.open_add_task_dialog)
            font_action = QAction("修改字体", self)
            font_action.triggered.connect(self.open_font_dialog)
            view_action = QAction("打开完整任务表" if self.settings.get("view") != "table" else "回到小面板", self)
            view_action.triggered.connect(lambda: self.show_view("table" if self.settings.get("view") != "table" else "panel"))
            lock_action = QAction("解锁位置" if self.settings.get("locked") else "锁定位置", self)
            lock_action.triggered.connect(self.toggle_locked)
            theme_action = QAction("浅色模式" if self.settings.get("theme") == "dark" else "深色模式", self)
            theme_action.triggered.connect(self.toggle_theme)
            hide_action = QAction("隐藏到托盘", self)
            hide_action.triggered.connect(self.hide)
            quit_action = QAction("退出", self)
            quit_action.triggered.connect(QApplication.instance().quit)
            for action in [refresh_action, add_action, font_action, view_action, lock_action, theme_action, hide_action]:
                menu.addAction(action)
            menu.addSeparator()
            menu.addAction(quit_action)
            return menu

        def rows_for_panel(self) -> list[dict[str, Any]]:
            rows = build_rows(parse_tasks(self.data))
            active = [row for row in rows if not is_completed_today(row["task"])]
            completed = [row for row in rows if is_completed_today(row["task"])]
            priority = [row for row in active if row["group"] in {GROUP_MUST, GROUP_NEXT}]
            return (priority or active) + completed

        def refresh_data(self) -> None:
            self.data = load_data(self.data_path)
            if clear_stale_completions(self.data):
                save_data(self.data, self.data_path)
            self.render()

        def find_task_item(self, task_id: str) -> dict[str, Any] | None:
            self.data = load_data(self.data_path)
            for item in self.data.get("tasks", []):
                if item.get("id") == task_id:
                    return item
            return None

        def render_panel(self) -> None:
            shell = self.card_shell()
            shell_layout = QVBoxLayout(shell)
            shell_layout.setContentsMargins(0, 0, 0, 0)
            shell_layout.setSpacing(0)
            rows = self.rows_for_panel()
            self.header(shell_layout, "DeskTask", f"{datetime.now():%Y-%m-%d}")

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            content_layout = QVBoxLayout(content)
            content_layout.setContentsMargins(18, 12, 18, 16)
            content_layout.setSpacing(10)
            for row in rows:
                content_layout.addWidget(self.task_card(row))
            content_layout.addStretch(1)
            scroll.setWidget(content)
            shell_layout.addWidget(scroll, 1)

            grip_row = QHBoxLayout()
            grip_row.setContentsMargins(0, 0, 10, 10)
            grip_row.addStretch(1)
            grip_row.addWidget(QSizeGrip(shell), 0, Qt.AlignRight | Qt.AlignBottom)
            shell_layout.addLayout(grip_row)

            width = int(self.settings["panel_width"])
            saved_height = self.settings.get("panel_height")
            row_height = 96
            auto_height = min(int(self.settings["panel_max_height"]), 118 + max(1, len(rows)) * row_height)
            height = int(saved_height or auto_height)
            self.resize(width + 32, height + 32)

        def task_card(self, row: dict[str, Any]) -> QFrame:
            task: Task = row["task"]
            completed = is_completed_today(task)
            current_type = task_type(task.priority)
            accent = self.theme[f"type_{current_type}"]
            card_bg = self.theme["done_bg"] if completed else self.theme[f"type_{current_type}_bg"]
            card_border = self.theme["done_border"] if completed else self.theme[f"type_{current_type}_border"]
            card = QFrame()
            card.setObjectName("taskCard")
            card.setCursor(Qt.PointingHandCursor)
            card.setStyleSheet(
                f"""
                QFrame#taskCard {{
                    background: {card_bg};
                    border-radius: 18px;
                    border: 1px solid {card_border};
                }}
                QCheckBox::indicator {{
                    width: 20px;
                    height: 20px;
                    border-radius: 10px;
                    border: 2px solid {accent};
                    background: transparent;
                }}
                QCheckBox::indicator:checked {{
                    background: {accent};
                    border: 2px solid {accent};
                }}
                """
            )
            layout = QHBoxLayout(card)
            layout.setContentsMargins(12, 10, 12, 10)
            layout.setSpacing(10)

            checkbox = QCheckBox()
            checkbox.setChecked(completed)
            checkbox.toggled.connect(lambda checked, task_id=task.id: self.set_task_completed(task_id, checked))
            layout.addWidget(checkbox, 0, Qt.AlignVCenter)

            text_layout = QVBoxLayout()
            text_layout.setSpacing(4)
            title = QLabel(task.title)
            title.setWordWrap(True)
            title_font = title.font()
            title_font.setPointSize(11)
            title_font.setBold(True)
            title_font.setStrikeOut(completed)
            title.setFont(title_font)
            title.setStyleSheet(f"color: {self.theme['done'] if completed else self.theme['text']};")
            text_layout.addWidget(title)

            detail = QLabel(compact_detail_text(task.due_label, row["reason"]))
            detail.setWordWrap(True)
            detail.setStyleSheet(f"font-size: 12px; color: {self.theme['muted']};")
            text_layout.addWidget(detail)
            layout.addLayout(text_layout, 1)
            card.mousePressEvent = lambda event, task_id=task.id: self.open_task_detail_dialog(task_id)

            return card

        def render_table(self) -> None:
            shell = self.card_shell()
            shell_layout = QVBoxLayout(shell)
            shell_layout.setContentsMargins(0, 0, 0, 0)
            shell_layout.setSpacing(0)
            rows = build_rows(parse_tasks(self.data))
            self.header(shell_layout, "完整任务表")

            table = QTableWidget(len(rows), 6)
            table.setHorizontalHeaderLabels(["完成", "类型", "任务", "截止/窗口", "提醒原因", "备注"])
            table.verticalHeader().setVisible(False)
            table.setShowGrid(False)
            table.setWordWrap(True)
            table.setAlternatingRowColors(False)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.cellDoubleClicked.connect(lambda row_index, _column: self.open_task_detail_dialog(rows[row_index]["task"].id))
            table.setStyleSheet(
                f"""
                QTableWidget {{
                    background: {self.theme['surface']};
                    color: {self.theme['text']};
                    border: none;
                    gridline-color: transparent;
                }}
                QHeaderView::section {{
                    background: {self.theme['surface_2']};
                    color: {self.theme['muted']};
                    border: none;
                    padding: 8px;
                    font-weight: 600;
                }}
                QTableWidget::item {{
                    padding: 8px;
                    border-bottom: 1px solid {self.theme['border']};
                }}
                """
            )

            for row_index, row in enumerate(rows):
                task: Task = row["task"]
                completed = is_completed_today(task)
                checkbox = QCheckBox()
                checkbox.setChecked(completed)
                checkbox.toggled.connect(lambda checked, task_id=task.id: self.set_task_completed(task_id, checked))
                checkbox_wrap = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_wrap)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                checkbox_layout.addWidget(checkbox, 0, Qt.AlignCenter)
                table.setCellWidget(row_index, 0, checkbox_wrap)

                values = [task_type_label(task.priority), task.title, task.due_label, row["reason"], task.note]
                for column, value in enumerate(values, start=1):
                    item = QTableWidgetItem(value)
                    item.setForeground(QColor(self.theme["done"] if completed else self.theme["text"]))
                    table.setItem(row_index, column, item)

            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
            table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            shell_layout.addWidget(table, 1)
            grip_row = QHBoxLayout()
            grip_row.setContentsMargins(0, 0, 10, 10)
            grip_row.addStretch(1)
            grip_row.addWidget(QSizeGrip(shell), 0, Qt.AlignRight | Qt.AlignBottom)
            shell_layout.addLayout(grip_row)
            self.resize(int(self.settings["table_width"]) + 32, int(self.settings["table_height"]) + 32)

        def open_task_detail_dialog(self, task_id: str) -> None:
            item = self.find_task_item(task_id)
            if item is None:
                QMessageBox.warning(self, "任务不存在", "这个任务可能已经被移动或删除。")
                self.render()
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("任务详情")
            dialog.setModal(True)
            dialog.setStyleSheet(
                f"""
                QDialog {{
                    background: {self.theme['surface']};
                    color: {self.theme['text']};
                }}
                QLabel, QCheckBox {{
                    color: {self.theme['text']};
                }}
                QLineEdit, QTextEdit, QComboBox {{
                    background: {self.theme['surface_2']};
                    color: {self.theme['text']};
                    border: 1px solid {self.theme['border']};
                    border-radius: 8px;
                    padding: 7px;
                }}
                QPushButton {{
                    background: {self.theme['button']};
                    color: {self.theme['text']};
                    border: none;
                    border-radius: 8px;
                    padding: 7px 14px;
                }}
                QPushButton:hover {{
                    background: {self.theme['button_hover']};
                }}
                """
            )

            layout = QVBoxLayout(dialog)
            form = QFormLayout()

            title_input = QLineEdit(item.get("title", ""))

            status_input = QComboBox()
            status_order = ["todo", "doing", "waiting", "blocked", "scheduled", "done"]
            for status in status_order:
                status_input.addItem(STATUS_LABELS.get(status, status), status)
            current_status = item.get("status", "todo")
            status_index = status_input.findData(current_status)
            if status_index < 0:
                status_input.addItem(current_status, current_status)
                status_index = status_input.findData(current_status)
            status_input.setCurrentIndex(status_index)

            priority_input = QComboBox()
            for value, label in TASK_TYPE_OPTIONS:
                priority_input.addItem(label, value)
            priority_index = priority_input.findData(task_type(item.get("priority", "medium")))
            priority_input.setCurrentIndex(priority_index if priority_index >= 0 else 1)

            due_date_input = QLineEdit(item.get("due_date") or "")
            due_date_input.setPlaceholderText("YYYY-MM-DD，可留空")
            due_label_input = QLineEdit(item.get("due_label") or "")
            reminder_at_input = QLineEdit(item.get("reminder_at") or "")
            reminder_at_input.setPlaceholderText("YYYY-MM-DD HH:MM，仅提醒类型需要")
            recurrence_input = QLineEdit(item.get("recurrence") or "")
            recurrence_input.setPlaceholderText("例如：每周五 / 每月一次，仅循环类型需要")
            note_input = QTextEdit(item.get("note") or "")
            note_input.setMinimumHeight(120)

            completed_today = QCheckBox("今天已完成")
            completed_today.setChecked(item.get("completed_on") == date.today().isoformat())

            form.addRow("任务名", title_input)
            form.addRow("状态", status_input)
            form.addRow("类型", priority_input)
            form.addRow("截止日期", due_date_input)
            form.addRow("显示说明", due_label_input)
            form.addRow("提醒时间", reminder_at_input)
            form.addRow("循环规则", recurrence_input)
            form.addRow("描述", note_input)
            form.addRow("", completed_today)
            layout.addLayout(form)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.button(QDialogButtonBox.Ok).setText("保存")
            buttons.button(QDialogButtonBox.Cancel).setText("取消")
            delete_button = buttons.addButton(
                "清除循环任务" if task_type(item.get("priority")) == "recurring" else "删除任务",
                QDialogButtonBox.DestructiveRole,
            )
            layout.addWidget(buttons)

            def save_task_detail() -> None:
                title = title_input.text().strip()
                if not title:
                    QMessageBox.warning(dialog, "缺少任务名", "任务名不能为空。")
                    return

                due_date = due_date_input.text().strip() or None
                if due_date:
                    try:
                        date.fromisoformat(due_date)
                    except ValueError:
                        QMessageBox.warning(dialog, "日期格式错误", "截止日期请使用 YYYY-MM-DD，或留空。")
                        return
                reminder_at = reminder_at_input.text().strip()
                if reminder_at and parse_reminder_datetime(reminder_at) is None:
                    QMessageBox.warning(dialog, "提醒时间格式错误", "提醒时间请使用 YYYY-MM-DD HH:MM，或留空。")
                    return

                item["title"] = title
                item["status"] = status_input.currentData()
                item["priority"] = priority_input.currentData()
                item["due_date"] = due_date
                item["due_label"] = due_label_input.text().strip() or due_date or "无固定截止"
                item["note"] = note_input.toPlainText().strip()
                if reminder_at:
                    item["reminder_at"] = reminder_at
                else:
                    item.pop("reminder_at", None)
                recurrence = recurrence_input.text().strip()
                if recurrence:
                    item["recurrence"] = recurrence
                else:
                    item.pop("recurrence", None)
                if completed_today.isChecked():
                    item["completed_on"] = date.today().isoformat()
                else:
                    item.pop("completed_on", None)

                save_data(self.data, self.data_path)
                self.render()
                dialog.accept()

            def delete_task() -> None:
                title = item.get("title", "这个任务")
                reply = QMessageBox.question(
                    dialog,
                    "确认删除",
                    f"确定要删除“{title}”吗？这会从任务列表中移除该任务。",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return
                self.data = load_data(self.data_path)
                self.data["tasks"] = [task for task in self.data.get("tasks", []) if task.get("id") != task_id]
                save_data(self.data, self.data_path)
                self.render()
                dialog.accept()

            buttons.accepted.connect(save_task_detail)
            buttons.rejected.connect(dialog.reject)
            delete_button.clicked.connect(delete_task)
            dialog.resize(640, 540)
            dialog.exec()

        def open_font_dialog(self) -> None:
            dialog = QDialog(self)
            dialog.setWindowTitle("修改字体")
            dialog.setModal(True)
            dialog.setStyleSheet(
                f"""
                QDialog {{
                    background: {self.theme['surface']};
                    color: {self.theme['text']};
                }}
                QLabel {{
                    color: {self.theme['text']};
                }}
                QLineEdit, QFontComboBox {{
                    background: {self.theme['surface_2']};
                    color: {self.theme['text']};
                    border: 1px solid {self.theme['border']};
                    border-radius: 8px;
                    padding: 7px;
                }}
                QPushButton {{
                    background: {self.theme['button']};
                    color: {self.theme['text']};
                    border: none;
                    border-radius: 8px;
                    padding: 7px 14px;
                }}
                QPushButton:hover {{
                    background: {self.theme['button_hover']};
                }}
                """
            )

            layout = QVBoxLayout(dialog)
            form = QFormLayout()
            font_combo = QFontComboBox()
            current_family = self.settings.get("font_family") or QApplication.instance().font().family()
            font_combo.setCurrentFont(QFont(current_family))

            font_file = QLineEdit(self.settings.get("font_file") or "")
            browse = QPushButton("选择文件")
            clear_file = QPushButton("清除")
            file_row = QHBoxLayout()
            file_row.addWidget(font_file, 1)
            file_row.addWidget(browse)
            file_row.addWidget(clear_file)

            def browse_font_file() -> None:
                path, _ = QFileDialog.getOpenFileName(
                    dialog,
                    "选择字体文件",
                    str(APP_ROOT),
                    "Font files (*.ttf *.otf *.ttc *.otc);;All files (*)",
                )
                if path:
                    font_file.setText(path)

            browse.clicked.connect(browse_font_file)
            clear_file.clicked.connect(font_file.clear)

            form.addRow("已安装字体", font_combo)
            form.addRow("本地字体文件", file_row)
            layout.addLayout(form)

            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            reset_button = button_box.addButton("恢复默认", QDialogButtonBox.ResetRole)
            layout.addWidget(button_box)

            def reset_font_settings() -> None:
                self.settings["font_family"] = ""
                self.settings["font_file"] = ""
                save_settings(self.settings, self.settings_path)
                self.apply_app_font()
                self.render()
                dialog.accept()

            def save_font_settings() -> None:
                selected_file = font_file.text().strip()
                if selected_file:
                    font_path = Path(selected_file)
                    if not font_path.exists():
                        QMessageBox.warning(dialog, "字体文件不存在", "请选择一个存在的字体文件。")
                        return
                    self.settings["font_family"] = ""
                    self.settings["font_file"] = selected_file
                else:
                    self.settings["font_family"] = font_combo.currentFont().family().strip()
                    self.settings["font_file"] = ""
                save_settings(self.settings, self.settings_path)
                self.apply_app_font()
                self.render()
                dialog.accept()

            reset_button.clicked.connect(reset_font_settings)
            button_box.accepted.connect(save_font_settings)
            button_box.rejected.connect(dialog.reject)
            dialog.resize(520, 150)
            dialog.exec()

        def open_add_task_dialog(self) -> None:
            dialog = QDialog(self)
            dialog.setWindowTitle("增加任务")
            dialog.setModal(True)
            dialog.setStyleSheet(
                f"""
                QDialog {{
                    background: {self.theme['surface']};
                    color: {self.theme['text']};
                }}
                QLabel {{
                    color: {self.theme['text']};
                }}
                QLineEdit, QTextEdit, QComboBox {{
                    background: {self.theme['surface_2']};
                    color: {self.theme['text']};
                    border: 1px solid {self.theme['border']};
                    border-radius: 8px;
                    padding: 7px;
                }}
                QPushButton {{
                    background: {self.theme['button']};
                    color: {self.theme['text']};
                    border: none;
                    border-radius: 8px;
                    padding: 7px 14px;
                }}
                QPushButton:hover {{
                    background: {self.theme['button_hover']};
                }}
                """
            )
            layout = QVBoxLayout(dialog)
            form = QFormLayout()
            title_input = QLineEdit()
            title_input.setPlaceholderText("例如：整理 ECCE demo abstract")
            priority_input = QComboBox()
            for value, label in TASK_TYPE_OPTIONS:
                priority_input.addItem(label, value)
            priority_input.setCurrentIndex(priority_input.findData("medium"))
            due_date_input = QLineEdit()
            due_date_input.setPlaceholderText("YYYY-MM-DD，可留空")
            due_label_input = QLineEdit()
            due_label_input.setPlaceholderText("例如：六月前 / 下周三 / 无固定截止")
            reminder_at_input = QLineEdit()
            reminder_at_input.setPlaceholderText("YYYY-MM-DD HH:MM，仅提醒类型需要")
            recurrence_input = QLineEdit()
            recurrence_input.setPlaceholderText("例如：每周五 / 每月一次，仅循环类型需要")
            note_input = QTextEdit()
            note_input.setPlaceholderText("备注、依赖、下一步动作")
            note_input.setFixedHeight(96)

            form.addRow("任务名", title_input)
            form.addRow("类型", priority_input)
            form.addRow("截止日期", due_date_input)
            form.addRow("截止说明", due_label_input)
            form.addRow("提醒时间", reminder_at_input)
            form.addRow("循环规则", recurrence_input)
            form.addRow("备注", note_input)
            layout.addLayout(form)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.button(QDialogButtonBox.Ok).setText("添加")
            buttons.button(QDialogButtonBox.Cancel).setText("取消")
            layout.addWidget(buttons)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)

            if dialog.exec() != QDialog.Accepted:
                return

            title = title_input.text().strip()
            if not title:
                QMessageBox.warning(self, "缺少任务名", "请先填写任务名。")
                return
            due_date = due_date_input.text().strip() or None
            if due_date:
                try:
                    date.fromisoformat(due_date)
                except ValueError:
                    QMessageBox.warning(self, "日期格式错误", "截止日期请使用 YYYY-MM-DD，或留空。")
                    return
            reminder_at = reminder_at_input.text().strip()
            if reminder_at and parse_reminder_datetime(reminder_at) is None:
                QMessageBox.warning(self, "提醒时间格式错误", "提醒时间请使用 YYYY-MM-DD HH:MM，或留空。")
                return

            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:36]
            task_id = f"task-{datetime.now():%Y%m%d%H%M%S}"
            if slug:
                task_id = f"{task_id}-{slug}"
            new_task = {
                "id": task_id,
                "title": title,
                "status": "todo",
                "priority": priority_input.currentData(),
                "due_date": due_date,
                "due_label": due_label_input.text().strip() or due_date or "无固定截止",
                "note": note_input.toPlainText().strip(),
                "depends_on": [],
            }
            if reminder_at:
                new_task["reminder_at"] = reminder_at
            recurrence = recurrence_input.text().strip()
            if recurrence:
                new_task["recurrence"] = recurrence
            self.data = load_data(self.data_path)
            self.data.setdefault("tasks", []).append(new_task)
            save_data(self.data, self.data_path)
            self.render()

        def set_task_completed(self, task_id: str, checked: bool) -> None:
            if self.is_rendering:
                return
            today = date.today().isoformat()
            self.data = load_data(self.data_path)
            if clear_stale_completions(self.data):
                save_data(self.data, self.data_path)
            for item in self.data.get("tasks", []):
                if item.get("id") == task_id:
                    if checked:
                        item["completed_on"] = today
                    else:
                        item.pop("completed_on", None)
                    save_data(self.data, self.data_path)
                    self.render()
                    return

        def apply_geometry(self) -> None:
            width = self.width() or int(self.settings["panel_width"])
            x = self.settings.get("x")
            if x is None:
                screen = QApplication.primaryScreen().availableGeometry()
                x = screen.right() - width - 24
            y = int(self.settings.get("y") or 96)
            self.move(int(x), y)

        def resizeEvent(self, event: Any) -> None:
            super().resizeEvent(event)
            if self.settings.get("view") == "table":
                self.settings["table_width"] = max(720, self.width() - 32)
                self.settings["table_height"] = max(420, self.height() - 32)
            else:
                self.settings["panel_width"] = max(300, self.width() - 32)
                self.settings["panel_height"] = max(260, self.height() - 32)
            save_settings(self.settings, self.settings_path)

        def mousePressEvent(self, event: Any) -> None:
            if event.button() == Qt.LeftButton and not self.settings.get("locked"):
                self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(self, event: Any) -> None:
            if self.drag_offset is not None and not self.settings.get("locked"):
                self.move(event.globalPosition().toPoint() - self.drag_offset)
                event.accept()

        def mouseReleaseEvent(self, event: Any) -> None:
            if self.drag_offset is not None:
                self.settings["x"] = self.x()
                self.settings["y"] = self.y()
                save_settings(self.settings, self.settings_path)
            self.drag_offset = None
            event.accept()

        def show_view(self, view: str) -> None:
            self.settings["view"] = view
            save_settings(self.settings, self.settings_path)
            self.show()
            self.raise_()
            self.activateWindow()
            self.render()

        def toggle_locked(self) -> None:
            self.settings["locked"] = not bool(self.settings.get("locked"))
            save_settings(self.settings, self.settings_path)
            self.render()

        def toggle_theme(self) -> None:
            self.settings["theme"] = "dark" if self.settings.get("theme") == "light" else "light"
            save_settings(self.settings, self.settings_path)
            self.render()

        def show_due_task_reminders(self, now: datetime) -> None:
            current_minute = now.replace(second=0, microsecond=0)
            for item in self.data.get("tasks", []):
                if task_type(item.get("priority")) != "reminder":
                    continue
                if item.get("completed_on") == now.date().isoformat():
                    continue
                reminder_at = parse_reminder_datetime(item.get("reminder_at"))
                if reminder_at is None:
                    continue
                reminder_minute = reminder_at.replace(second=0, microsecond=0)
                if reminder_minute != current_minute:
                    continue
                reminder_key = f"task-reminder-{item.get('id')}-{current_minute.isoformat()}"
                if reminder_key in self.last_reminders:
                    continue
                self.last_reminders.add(reminder_key)
                title = item.get("title", "任务提醒")
                message = item.get("note") or item.get("due_label") or "该处理这个提醒事项了。"
                item["completed_on"] = now.date().isoformat()
                save_data(self.data, self.data_path)
                if self.tray_icon:
                    self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 8000)
                QMessageBox.information(self, title, message)
                self.render()

        def run_completion_clear_checkpoint(self, key: str, today_key: str) -> bool:
            setting_key = f"last_completion_clear_{key}_date"
            if self.settings.get(setting_key) == today_key:
                return False
            changed = cleanup_completed_tasks_at_checkpoint(self.data)
            self.settings[setting_key] = today_key
            save_settings(self.settings, self.settings_path)
            if changed:
                save_data(self.data, self.data_path)
            return changed

        def on_clock(self) -> None:
            now = datetime.now()
            current = now.strftime("%H:%M")
            today_key = now.strftime("%Y-%m-%d")
            self.data = load_data(self.data_path)
            should_render = False
            if clear_stale_completions(self.data):
                save_data(self.data, self.data_path)
                should_render = True
            reset_time = self.settings.get("daily_reset_time", "00:00")
            if current == reset_time and self.settings.get("last_reset_date") != today_key:
                self.settings["last_reset_date"] = today_key
                save_settings(self.settings, self.settings_path)
            if current >= "00:00" and self.run_completion_clear_checkpoint("00", today_key):
                should_render = True
            if current >= "09:00" and self.run_completion_clear_checkpoint("09", today_key):
                should_render = True
            if should_render:
                self.render()

            self.show_due_task_reminders(now)

            reminder_key = f"{today_key}-{current}"
            if reminder_key in self.last_reminders:
                return
            reminder_settings = self.data.get("settings", {})
            if current == reminder_settings.get("morning_reminder", "09:00"):
                self.last_reminders.add(reminder_key)
                self.show_morning_reminder()
            elif current == reminder_settings.get("evening_reminder", "18:00"):
                self.last_reminders.add(reminder_key)
                self.show_evening_reminder()

        def show_morning_reminder(self) -> None:
            rows = build_rows(parse_tasks(self.data))
            must = [row["task"].title for row in rows if row["group"] == GROUP_MUST and not is_completed_today(row["task"])]
            message = "今天必须做：\n" + "\n".join(f"- {title}" for title in must[:6])
            if not must:
                message = "今天没有必须处理项。请选择 2-3 项可以推进的任务。"
            QMessageBox.information(self, "早上 9:00 任务提醒", message)

        def show_evening_reminder(self) -> None:
            QMessageBox.information(
                self,
                "晚上 18:00 任务复盘",
                "请复盘今天完成了哪些、哪些没完成。\n已完成的普通任务会在清理点删除；循环任务会保留并在第二天重新变成未完成。",
            )

        def closeEvent(self, event: Any) -> None:
            self.hide()
            event.ignore()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = DesktopTaskWindow()
    window.show()
    return app.exec()


def main() -> int:
    parser = argparse.ArgumentParser(description="DeskTask desktop task panel.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help="Path to daily_tasks.json")
    parser.add_argument("--settings", type=Path, default=DEFAULT_SETTINGS_PATH, help="Path to app_settings.json")
    parser.add_argument("--check", action="store_true", help="Validate and print the current task plan without opening GUI")
    args = parser.parse_args()

    if args.check:
        return check_data(args.data)
    return run_gui(args.data, args.settings)


if __name__ == "__main__":
    raise SystemExit(main())
