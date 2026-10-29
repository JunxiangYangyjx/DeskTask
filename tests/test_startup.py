import subprocess
import sys
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from daily_task import startup


class StartupTests(unittest.TestCase):
    def test_source_command_preserves_paths_with_spaces(self):
        data = Path("C:/Example folder/my tasks.json")
        settings = Path("C:/Example folder/my settings.json")
        with patch.object(startup.sys, "frozen", False, create=True), patch.object(Path, "is_file", return_value=True):
            command = startup.startup_command(data, settings)
        expected = [str(ROOT / ".venv" / "Scripts" / "pythonw.exe"), str(ROOT / "src" / "daily_task" / "app.py"),
                    "--data", str(data.resolve()), "--settings", str(settings.resolve())]
        self.assertEqual(command, subprocess.list2cmdline(expected))

    def test_packaged_command_uses_executable(self):
        data, settings = Path("data.json"), Path("settings.json")
        with patch.object(startup.sys, "frozen", True, create=True), patch.object(startup.sys, "executable", "C:/Program Files/DeskTask/DeskTask.exe"):
            command = startup.startup_command(data, settings)
        self.assertEqual(command, subprocess.list2cmdline(["C:/Program Files/DeskTask/DeskTask.exe", "--data", str(data.resolve()), "--settings", str(settings.resolve())]))

    def test_enable_disable_and_registry_errors(self):
        registry = MagicMock()
        registry.HKEY_CURRENT_USER = object()
        registry.KEY_READ = 1
        registry.KEY_SET_VALUE = 2
        registry.REG_SZ = 1
        registry.QueryValueEx.return_value = ("command", registry.REG_SZ)
        data, settings = Path("data.json"), Path("settings.json")
        with patch.object(startup, "winreg", registry), patch.object(startup, "startup_command", return_value="quoted command"):
            self.assertTrue(startup.is_enabled())
            startup.set_enabled(True, data, settings)
            registry.SetValueEx.assert_called_once_with(registry.CreateKeyEx.return_value.__enter__.return_value, startup.VALUE_NAME, 0, registry.REG_SZ, "quoted command")
            startup.set_enabled(False, data, settings)
            registry.DeleteValue.assert_called_once_with(registry.OpenKey.return_value.__enter__.return_value, startup.VALUE_NAME)
            registry.OpenKey.side_effect = FileNotFoundError()
            self.assertFalse(startup.is_enabled())
            startup.set_enabled(False, data, settings)
            registry.OpenKey.side_effect = PermissionError("denied")
            with self.assertRaises(PermissionError):
                startup.is_enabled()
            with self.assertRaises(PermissionError):
                startup.set_enabled(False, data, settings)

    def test_unsupported_platform_does_not_enable(self):
        with patch.object(startup, "winreg", None):
            self.assertFalse(startup.is_enabled())
            with self.assertRaises(OSError):
                startup.set_enabled(True, Path("data"), Path("settings"))

    def test_settings_menu_toggles_without_touching_the_real_registry(self):
        script = r'''
import os, sys
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from daily_task import app
app.SINGLE_INSTANCE_SERVER = 'DeskTask.Startup.Test.' + str(os.getpid())
changes = []
app.startup.is_enabled = lambda: False
app.startup.set_enabled = lambda enabled, data, settings: changes.append((enabled, data, settings))
original_exec = QApplication.exec
def bounded_exec(qapp):
    errors = []
    def exercise():
        try:
            window = next(w for w in qapp.topLevelWidgets() if hasattr(w, 'more_menu'))
            menu = window.more_menu()
            assert not any(action.text() == '设置' for action in menu.actions())
            action = next(action for action in menu.actions() if action.text() == '开机自启动')
            assert action.isCheckable() and not action.isChecked()
            action.trigger()
            action.trigger()
            assert [change[0] for change in changes] == [True, False], changes
            assert changes[0][1:] == (Path(sys.argv[1]), Path(sys.argv[2]))
        except Exception:
            import traceback
            errors.append(traceback.format_exc())
        finally:
            qapp.quit()
    QTimer.singleShot(100, exercise)
    QTimer.singleShot(5000, qapp.quit)
    result = original_exec()
    assert not errors, errors
    return result
QApplication.exec = bounded_exec
raise SystemExit(app.run_gui(Path(sys.argv[1]), Path(sys.argv[2])))
'''
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / "daily_tasks.json"
            settings = Path(directory) / "settings.json"
            data.write_text(json.dumps({"tasks": [], "settings": {"morning_reminder": "", "evening_reminder": ""}}), encoding="utf-8")
            settings.write_text("{}", encoding="utf-8")
            result = subprocess.run([sys.executable, "-c", script, str(data), str(settings)],
                env={**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONPATH": str(ROOT / "src"), "PYTHONIOENCODING": "utf-8"},
                capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
