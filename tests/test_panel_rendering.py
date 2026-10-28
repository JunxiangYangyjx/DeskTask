import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PanelRenderingTests(unittest.TestCase):
    def test_scrolling_repaints_the_translucent_panel_without_changing_tasks(self):
        script = """
import os
from pathlib import Path
import sys
from unittest.mock import patch
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QScrollArea
from daily_task import app

app.SINGLE_INSTANCE_SERVER = 'DeskTask.Rendering.Test.' + str(os.getpid())
original_exec = QApplication.exec
errors = []

def bounded_exec(self):
    def exercise():
        try:
            window = next(w for w in self.topLevelWidgets() if hasattr(w, 'rows_for_panel'))
            window.clock.stop()
            window.outlook_timer.stop()
            scroll = window.findChild(QScrollArea)
            shell = scroll.parentWidget()
            bar = scroll.verticalScrollBar()
            assert bar.maximum() > 200, bar.maximum()
            viewport = scroll.viewport()
            with patch.object(viewport, 'update', wraps=viewport.update) as viewport_update, patch.object(shell, 'update', wraps=shell.update) as shell_update:
                for position in [75, 150, 225, 150, 75, 0, bar.maximum(), 0]:
                    viewport_update.reset_mock()
                    shell_update.reset_mock()
                    bar.setValue(position)
                    self.processEvents()
                    assert viewport_update.called, 'Scroll did not invalidate the full viewport'
                    assert shell_update.called, 'Scroll did not invalidate the shadowed panel'
            image = viewport.grab().toImage()
            assert image.width() > 100 and image.height() > 100
            # A horizontal white artifact cuts across cards, gaps and checkboxes alike.
            for y in range(2, image.height() - 2):
                white = sum(image.pixelColor(x, y).name() == '#ffffff' for x in range(10, image.width() - 20))
                assert white < (image.width() - 30) * 0.95, f'White stripe at row {y}'
            print('Scroll repaint and pixel checks passed')
        except Exception as error:
            errors.append(repr(error))
        finally:
            self.quit()
    QTimer.singleShot(100, exercise)
    QTimer.singleShot(10000, self.quit)
    result = original_exec()
    assert not errors, errors
    return result

QApplication.exec = bounded_exec
raise SystemExit(app.run_gui(Path(sys.argv[1]), Path(sys.argv[2])))
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_path = root / "daily_tasks.json"
            settings_path = root / "settings.json"
            data_path.write_text(json.dumps({"tasks": [
                {"id": f"task-{index}", "title": f"Rendering check {index}", "priority": "medium", "status": "todo", "due_label": "No deadline"}
                for index in range(24)
            ], "settings": {"morning_reminder": "", "evening_reminder": ""}}), encoding="utf-8")
            original_data = data_path.read_bytes()
            for theme, scale in [("light", "1"), ("light", "1.25"), ("dark", "1.5")]:
                with self.subTest(theme=theme, scale=scale):
                    settings_path.write_text(json.dumps({"theme": theme, "view": "panel", "panel_height": 450, "panel_width": 450}), encoding="utf-8")
                    result = subprocess.run([sys.executable, "-c", script, str(data_path), str(settings_path)],
                        env={**os.environ, "QT_QPA_PLATFORM": "offscreen", "QT_SCALE_FACTOR": scale,
                            "PYTHONPATH": str(ROOT / "src"), "PYTHONIOENCODING": "utf-8"},
                        capture_output=True, text=True, timeout=20)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn("Scroll repaint and pixel checks passed", result.stdout)
                    self.assertEqual(data_path.read_bytes(), original_data)


if __name__ == "__main__":
    unittest.main()
