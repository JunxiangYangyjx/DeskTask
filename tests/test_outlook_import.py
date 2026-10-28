import io
import json
from pathlib import Path
import struct
import subprocess
import os
import tempfile
import unittest
from unittest.mock import patch
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from daily_task.outlook_import import consume_imports, enqueue_import, validate_import
from daily_task.milestones import due_milestone_reminders, refresh_milestone_task
from datetime import datetime


def save(data, path):
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class OutlookImportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "daily_tasks.json"
        self.data = {"tasks": [{"id": "existing", "title": "Keep this task"}]}
        self.payload = {
            "title": "参加年会", "subject": "Annual meeting",
            "url": "https://outlook.office.com/mail/inbox/id/example",
            "body": "Date: 3 December 2026\nTime: 6:00 pm\nVenue: Singapore",
            "due_date": "2026-12-03", "time": "18:00", "location": "Singapore",
        }

    def test_preserves_existing_and_deduplicates(self):
        enqueue_import(self.payload, self.path)
        self.assertEqual(consume_imports(self.data, self.path, save), 1)
        enqueue_import(self.payload, self.path)
        self.assertEqual(consume_imports(self.data, self.path, save), 0)
        self.assertEqual(len(self.data["tasks"]), 2)
        task = self.data["tasks"][-1]
        self.assertEqual(task["reminder_at"], "2026-12-03 18:00")
        self.assertIn("地点：Singapore", task["note"])
        self.assertEqual(self.data["tasks"][0]["id"], "existing")

    def test_optional_date(self):
        task = validate_import({**self.payload, "due_date": "", "time": ""})
        self.assertIsNone(task["due_date"])
        self.assertIsNone(task["reminder_at"])

    def test_other_providers_round_trip_without_session_credentials(self):
        for url, expected in [
            ("https://mail.google.com/mail/u/0/#inbox/message123", "gmail-web"),
            ("https://mail.qq.com/cgi-bin/readmail?sid=PRIVATE&mailid=123", "qq-web"),
            ("https://wx.mail.qq.com/#/read/123?token=PRIVATE", "qq-web"),
            ("https://mail.163.com/js6/main.jsp?sid=PRIVATE#/read?mid=123", "netease-web"),
            ("https://hw.mail.126.com/js6/main.jsp?sid=PRIVATE#/read?mid=123", "netease-web"),
        ]:
            with self.subTest(url=url):
                payload = {**self.payload, "url": url}
                identity = enqueue_import(payload, self.path)
                self.assertTrue(identity.startswith("mail-"))
                self.assertEqual(consume_imports(self.data, self.path, save), 1)
                task = self.data["tasks"][-1]
                self.assertEqual(task["source"]["type"], expected)
                self.assertNotIn("PRIVATE", task["source"]["url"])
                self.assertNotIn("PRIVATE", task["note"])
                enqueue_import(payload, self.path)
                self.assertEqual(consume_imports(self.data, self.path, save), 0)

    def test_cloud_domain_is_imported_and_lookalikes_are_rejected(self):
        payload = {**self.payload, "url": "https://outlook.cloud.microsoft/mail/inbox/id/example"}
        enqueue_import(payload, self.path)
        self.assertEqual(consume_imports(self.data, self.path, save), 1)
        self.assertEqual(self.data["tasks"][-1]["source"]["url"], payload["url"])
        with self.assertRaises(ValueError):
            validate_import({**payload, "url": "https://outlook.cloud.microsoft.attacker.example/mail"})

    def test_rejects_invalid_inputs(self):
        for changes in [
            {"title": ""}, {"due_date": "2026-02-30"}, {"time": "25:00"},
            {"time": "18:00", "due_date": ""}, {"priority": "bogus"},
            {"url": "https://outlook.office.com.attacker.example/mail"},
            {"url": "http://outlook.office.com/mail"},
        ]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_import({**self.payload, **changes})

    def test_failed_save_leaves_queue_for_retry(self):
        enqueue_import(self.payload, self.path)
        with self.assertRaises(OSError):
            consume_imports(self.data, self.path, lambda *_: (_ for _ in ()).throw(OSError("locked")))
        self.assertEqual(len(self.data["tasks"]), 1)
        self.assertEqual(consume_imports(self.data, self.path, save), 1)

    def test_bad_queue_is_quarantined(self):
        queue = self.path.parent / "outlook_inbox"
        queue.mkdir()
        (queue / "outlook-invalid.json").write_text('{"bad":true}', encoding="utf-8")
        self.assertEqual(consume_imports(self.data, self.path, save), 0)
        self.assertTrue((queue / "outlook-invalid.rejected").exists())

    def grouped_payload(self):
        return {**self.payload, "due_date": "", "time": "", "milestones": [
            {"id": "registration", "title": "报名", "due_date": "2026-11-02", "time": "16:00"},
            {"id": "training", "title": "培训", "due_date": "2026-11-04"},
            {"id": "slides", "title": "交 PPT", "due_date": "2026-11-09", "time": "16:00"},
            {"id": "event", "title": "比赛", "due_date": "2026-11-17", "time": "13:00", "end_time": "16:00"},
        ]}

    def test_group_is_one_task_and_advances_to_next_pending_step(self):
        enqueue_import(self.grouped_payload(), self.path)
        self.assertEqual(consume_imports(self.data, self.path, save), 1)
        self.assertEqual(len(self.data["tasks"]), 2)
        task = self.data["tasks"][-1]
        self.assertEqual(len(task["milestones"]), 4)
        self.assertEqual(task["due_date"], "2026-11-02")
        task["milestones"][0]["status"] = "done"
        refresh_milestone_task(task)
        self.assertEqual(task["due_date"], "2026-11-04")
        self.assertIsNone(task["reminder_at"])
        self.assertNotIn("completed_on", task)
        enqueue_import(self.grouped_payload(), self.path)
        self.assertEqual(consume_imports(self.data, self.path, save), 0)
        self.assertEqual(task["milestones"][0]["status"], "done")
        enqueue_import({**self.grouped_payload(), "body": "Edited excerpt from the same email"}, self.path)
        self.assertEqual(consume_imports(self.data, self.path, save), 0)
        self.assertEqual(len(self.data["tasks"]), 2)

    def test_invalid_group_never_queues_a_partial_schedule(self):
        payload = self.grouped_payload()
        payload["milestones"][-1]["end_time"] = "12:00"
        with self.assertRaises(ValueError):
            enqueue_import(payload, self.path)
        self.assertFalse((self.path.parent / "outlook_inbox").exists())
        for steps in [[], [payload["milestones"][0]] * 2]:
            with self.assertRaises(ValueError):
                validate_import({**payload, "milestones": steps})

    def test_group_save_failure_rolls_back_all_steps(self):
        enqueue_import(self.grouped_payload(), self.path)
        with self.assertRaises(OSError):
            consume_imports(self.data, self.path, lambda *_: (_ for _ in ()).throw(OSError("locked")))
        self.assertEqual(len(self.data["tasks"]), 1)
        self.assertEqual(consume_imports(self.data, self.path, save), 1)
        self.assertEqual(len(self.data["tasks"][-1]["milestones"]), 4)

    def test_reimport_upgrades_existing_single_task(self):
        enqueue_import(self.payload, self.path)
        consume_imports(self.data, self.path, save)
        enqueue_import(self.grouped_payload(), self.path)
        self.assertEqual(consume_imports(self.data, self.path, save), 1)
        self.assertEqual(len(self.data["tasks"]), 2)
        self.assertEqual(len(self.data["tasks"][-1]["milestones"]), 4)

    def test_reminders_do_not_mark_steps_or_parent_complete(self):
        task = validate_import(self.grouped_payload())
        now = datetime(2026, 11, 2, 16, 0)
        due = due_milestone_reminders(task, now)
        self.assertEqual([step["title"] for step in due], ["报名"])
        due[0]["last_reminded_at"] = now.strftime("%Y-%m-%d %H:%M")
        self.assertEqual(due_milestone_reminders(task, now), [])
        self.assertEqual(task["milestones"][0]["status"], "todo")
        self.assertNotIn("completed_on", task)
        for step in task["milestones"]:
            step["status"] = "done"
        refresh_milestone_task(task)
        self.assertEqual(task["status"], "done")
        self.assertIn("completed_on", task)

    def test_native_protocol_unicode_and_launch(self):
        spec = importlib.util.spec_from_file_location("native_host", ROOT / "scripts" / "outlook_native_host.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        native_root = self.path.parent / "build" / "outlook-native"
        native_root.mkdir(parents=True)
        (native_root / "config.json").write_text(json.dumps({"data_path": str(self.path)}), encoding="utf-8")
        raw = json.dumps(self.payload, ensure_ascii=False).encode("utf-8")
        incoming = type("Input", (), {"buffer": io.BytesIO(struct.pack("<I", len(raw)) + raw)})()
        outgoing = type("Output", (), {"buffer": io.BytesIO()})()
        with patch.object(module, "ROOT", self.path.parent), patch.object(module.sys, "stdin", incoming), patch.object(module.sys, "stdout", outgoing), patch.object(module.sys, "platform", "test"), patch.object(module.subprocess, "Popen") as launch:
            module.main()
        framed = outgoing.buffer.getvalue()
        self.assertEqual(struct.unpack("<I", framed[:4])[0], len(framed[4:]))
        self.assertTrue(json.loads(framed[4:])["ok"])
        launch.assert_called_once()
        self.assertEqual(consume_imports(self.data, self.path, save), 1)

    def test_gui_consumes_queue_on_startup(self):
        save({"tasks": [], "settings": {"morning_reminder": "", "evening_reminder": ""}}, self.path)
        settings = self.path.parent / "settings.json"
        settings.write_text("{}", encoding="utf-8")
        enqueue_import(self.payload, self.path)
        script = """
import sys
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from daily_task import app
app.SINGLE_INSTANCE_SERVER = 'DeskTask.Outlook.Test.' + str(__import__('os').getpid())
original_exec = QApplication.exec
def bounded_exec(self):
    QTimer.singleShot(2500, self.quit)
    return original_exec()
QApplication.exec = bounded_exec
raise SystemExit(app.run_gui(Path(sys.argv[1]), Path(sys.argv[2])))
"""
        result = subprocess.run([sys.executable, "-c", script, str(self.path), str(settings)],
            env={**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONPATH": str(ROOT / "src"), "PYTHONIOENCODING": "utf-8"},
            capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        tasks = json.loads(self.path.read_text(encoding="utf-8"))["tasks"]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["title"], self.payload["title"])

    def test_gui_group_reminder_and_individual_completion(self):
        save({"tasks": [], "settings": {"morning_reminder": "", "evening_reminder": ""}}, self.path)
        settings = self.path.parent / "settings.json"
        settings.write_text("{}", encoding="utf-8")
        identity = enqueue_import(self.grouped_payload(), self.path)
        script = """
import sys, os
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QDialogButtonBox, QMessageBox
from daily_task import app
app.SINGLE_INSTANCE_SERVER = 'DeskTask.Group.Test.' + str(os.getpid())
original_exec = QApplication.exec
errors = []
def bounded_exec(self):
    def exercise():
        try:
            window = next(w for w in QApplication.topLevelWidgets() if hasattr(w, 'open_task_detail_dialog'))
            alerts = []
            QMessageBox.information = lambda *args: alerts.append(args[1])
            window.show_due_task_reminders(datetime(2026,11,2,16,0))
            window.show_due_task_reminders(datetime(2026,11,2,16,0))
            assert len(alerts) == 1, alerts
            assert 'completed_on' not in window.data['tasks'][0]
            def finish_dialog():
                try:
                    dialog = next(w for w in QApplication.topLevelWidgets() if isinstance(w,QDialog))
                    checkbox = next(c for c in dialog.findChildren(QCheckBox) if c.text().startswith('报名  '))
                    checkbox.setChecked(True)
                    window.on_clock()
                    dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok).click()
                except Exception as error:
                    errors.append(repr(error))
                    self.quit()
            QTimer.singleShot(100,finish_dialog)
            window.open_task_detail_dialog(sys.argv[3])
        except Exception as error:
            errors.append(repr(error))
    QTimer.singleShot(300,exercise)
    QTimer.singleShot(1500,self.quit)
    code = original_exec()
    assert not errors, errors
    return code
QApplication.exec = bounded_exec
raise SystemExit(app.run_gui(Path(sys.argv[1]),Path(sys.argv[2])))
"""
        result = subprocess.run([sys.executable, "-c", script, str(self.path), str(settings), identity],
            env={**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONPATH": str(ROOT / "src"), "PYTHONIOENCODING": "utf-8"},
            capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        task = json.loads(self.path.read_text(encoding="utf-8"))["tasks"][0]
        self.assertEqual(task["milestones"][0]["status"], "done")
        self.assertEqual(task["milestones"][1]["status"], "todo")
        self.assertEqual(task["due_date"], "2026-11-04")
        self.assertNotIn("completed_on", task)


if __name__ == "__main__":
    unittest.main()
