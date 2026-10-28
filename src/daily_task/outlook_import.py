"""Validated, durable handoff from Chrome to the GUI's task writer."""

import hashlib
import json
import os
import uuid
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

try:
    from daily_task.milestones import refresh_milestone_task, validate_milestones
except ModuleNotFoundError:
    from milestones import refresh_milestone_task, validate_milestones


MAIL_PROVIDERS = {
    "outlook": {"outlook.office.com", "outlook.office365.com", "outlook.live.com", "outlook.cloud.microsoft"},
    "gmail": {"mail.google.com"},
    "qq": {"mail.qq.com", "wx.mail.qq.com"},
    "netease": {"mail.163.com", "mail.126.com", "mail.yeah.net", "email.163.com"},
}
MAIL_SUFFIXES = (".mail.163.com", ".mail.126.com", ".mail.yeah.net")
SENSITIVE_PARAMETERS = {"sid", "session", "sessionid", "session_id", "token", "access_token", "auth_token", "code", "skey", "ticket", "auth", "authorization", "password"}


def mail_source_url(value: str) -> tuple[str, str]:
    parsed = urlsplit(value)
    provider = next((name for name, hosts in MAIL_PROVIDERS.items() if parsed.hostname in hosts), None)
    if not provider and (parsed.hostname or "").endswith(MAIL_SUFFIXES):
        provider = "netease"
    if parsed.scheme != "https" or not provider or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("Only supported webmail HTTPS links are accepted")
    def clean_query(query):
        return urlencode([(key, val) for key, val in parse_qsl(query, keep_blank_values=True) if key.lower() not in SENSITIVE_PARAMETERS])
    fragment = parsed.fragment
    if "?" in fragment:
        route, query = fragment.split("?", 1)
        cleaned = clean_query(query)
        fragment = route + ("?" + cleaned if cleaned else "")
    return provider, urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", clean_query(parsed.query), fragment))


def validate_import(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Invalid import request")
    title = str(payload.get("title", "")).strip()
    if not title or len(title) > 500:
        raise ValueError("Title must contain 1-500 characters")
    url = str(payload.get("url", ""))
    if len(url) > 8192:
        raise ValueError("Mail link is too long")
    provider, url = mail_source_url(url)
    due = str(payload.get("due_date", "") or "")
    if due:
        date.fromisoformat(due)
    clock = str(payload.get("time", "") or "")
    if clock:
        datetime.strptime(clock, "%H:%M")
        if not due:
            raise ValueError("A reminder time requires a date")
    priority = payload.get("priority", "reminder")
    if priority not in {"high", "medium", "low", "reminder"}:
        raise ValueError("Invalid priority")
    body = str(payload.get("body", ""))[:20000]
    location = str(payload.get("location", "")).strip()[:1000]
    identity = hashlib.sha256((url + "\n" + str(payload.get("subject", title)) + "\n" + body).encode("utf-8")).hexdigest()[:24]
    note = "\n".join(part for part in [f"地点：{location}" if location else "", f"原邮件：{url}", body] if part)
    task = {
        "id": f"{'outlook' if provider == 'outlook' else 'mail'}-{identity}", "title": title, "status": "todo",
        "priority": priority, "due_date": due or None,
        "due_label": f"{due} {clock}".strip() if due else "无固定截止",
        "note": note, "depends_on": [],
        "reminder_at": f"{due} {clock}" if due and clock else None,
        "source": {"type": f"{provider}-web", "url": url, "subject": str(payload.get("subject", title))[:500], "imported_at": datetime.now().isoformat(timespec="seconds")},
    }
    if "milestones" in payload:
        task["milestones"] = validate_milestones(payload["milestones"])
        refresh_milestone_task(task)
    return task


def enqueue_import(payload: dict, data_path: Path) -> str:
    task = validate_import(payload)
    queue = data_path.parent / "outlook_inbox"
    queue.mkdir(parents=True, exist_ok=True)
    temporary = queue / f"{uuid.uuid4().hex}.tmp"
    try:
        temporary.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        os.replace(temporary, queue / f"{task['id']}.json")
    finally:
        temporary.unlink(missing_ok=True)
    return task["id"]


def consume_imports(data: dict, data_path: Path, save) -> int:
    """Called on the GUI thread so browser imports cannot race GUI edits."""
    queue = data_path.parent / "outlook_inbox"
    if not queue.is_dir():
        return 0
    count = 0
    for path in sorted(queue.glob("*.json")):
        try:
            task = json.loads(path.read_text(encoding="utf-8"))
            # Revalidate queued data instead of trusting files left by another process.
            queued_payload = {
                "title": task["title"], "url": task["source"]["url"],
                "due_date": task.get("due_date"),
                "time": (task.get("reminder_at") or "").split(" ")[-1],
                "priority": task["priority"],
                "subject": task["source"].get("subject",task["title"]),
            }
            if "milestones" in task:
                queued_payload["milestones"] = task["milestones"]
            checked = validate_import(queued_payload)
            if task["id"] != path.stem or not task["id"].startswith(("outlook-", "mail-")):
                raise ValueError("Invalid task identity")
            checked["source"]["imported_at"] = str(task["source"].get("imported_at", checked["source"]["imported_at"]))[:40]
            checked.update(id=task["id"], note=str(task.get("note", ""))[:30000])
        except (ValueError, KeyError, TypeError):
            path.replace(path.with_suffix(".rejected"))
            continue
        existing = next((item for item in data.get("tasks", []) if item.get("id") == checked["id"]), None)
        if existing is None and "milestones" in checked:
            existing = next((item for item in data.get("tasks", [])
                if item.get("source", {}).get("url") == checked["source"]["url"]
                and (item.get("source", {}).get("subject") or item.get("title")) == checked["source"].get("subject")), None)
        upgrade = existing is not None and "milestones" not in existing and "milestones" in checked
        if existing is None or upgrade:
            previous = existing.copy() if upgrade else None
            if upgrade:
                checked["id"] = existing["id"]
                existing.update(checked)
            else:
                data.setdefault("tasks", []).append(checked)
            try:
                save(data, data_path)
            except Exception:
                if upgrade:
                    existing.clear()
                    existing.update(previous)
                else:
                    data["tasks"].pop()
                raise
            count += 1
        path.unlink(missing_ok=True)
    return count
