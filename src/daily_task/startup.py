"""Current-user Windows startup registration for DeskTask."""

import subprocess
import sys
from pathlib import Path

try:
    import winreg
except ImportError:
    winreg = None

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "DeskTask"


def startup_command(data_path: Path, settings_path: Path) -> str:
    root = Path(__file__).resolve().parents[2]
    if getattr(sys, "frozen", False):
        command = [sys.executable]
    else:
        pythonw = root / ".venv" / "Scripts" / "pythonw.exe"
        if not pythonw.is_file():
            pythonw = Path(sys.executable).with_name("pythonw.exe")
        if not pythonw.is_file():
            raise FileNotFoundError("找不到 pythonw.exe，请检查 DeskTask 的 Python 环境。")
        command = [str(pythonw), str(root / "src" / "daily_task" / "app.py")]
    command.extend(["--data", str(data_path.resolve()), "--settings", str(settings_path.resolve())])
    return subprocess.list2cmdline(command)


def is_enabled() -> bool:
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, VALUE_NAME)
            return bool(value)
    except FileNotFoundError:
        return False


def set_enabled(enabled: bool, data_path: Path, settings_path: Path) -> None:
    if winreg is None:
        raise OSError("开机自启动仅支持 Windows。")
    if enabled:
        command = startup_command(data_path, settings_path)
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, command)
    else:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, VALUE_NAME)
        except FileNotFoundError:
            pass
