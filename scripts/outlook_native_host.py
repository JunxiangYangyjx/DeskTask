"""Chrome native messaging entry point. stdout is reserved for framed JSON."""

import json
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from daily_task.outlook_import import enqueue_import


def main():
    if sys.platform == "win32":
        import msvcrt
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    try:
        header = sys.stdin.buffer.read(4)
        if len(header) != 4:
            return
        length = struct.unpack("<I", header)[0]
        if length > 131072:
            raise ValueError("Import exceeds 128 KB")
        raw = sys.stdin.buffer.read(length)
        if len(raw) != length:
            raise ValueError("Incomplete request")
        payload = json.loads(raw.decode("utf-8"))
        config = json.loads((ROOT / "build" / "outlook-native" / "config.json").read_text(encoding="utf-8"))
        task_id = enqueue_import(payload, Path(config["data_path"]))
        subprocess.Popen([
            str(ROOT / ".venv" / "Scripts" / "pythonw.exe"),
            str(ROOT / "src" / "daily_task" / "app.py"),
            "--data", config["data_path"],
        ], cwd=str(ROOT), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        result = {"ok": True, "queued": True, "id": task_id}
    except Exception as error:
        result = {"ok": False, "error": str(error)}
    encoded = json.dumps(result, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(encoded)) + encoded)
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
