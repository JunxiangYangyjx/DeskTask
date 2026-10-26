"""Dated checklist items belonging to one task."""

from datetime import date, datetime


def validate_milestones(values: list) -> list[dict]:
    if not isinstance(values, list) or not 1 <= len(values) <= 32:
        raise ValueError("A schedule must contain 1-32 milestones")
    result = []
    identifiers = set()
    for index, value in enumerate(values):
        if not isinstance(value, dict):
            raise ValueError("Invalid milestone")
        title = str(value.get("title", "")).strip()
        if not title or len(title) > 200:
            raise ValueError("Milestone title must contain 1-200 characters")
        due = str(value.get("due_date") or "")
        if due:
            date.fromisoformat(due)
        clock = str(value.get("time") or "")
        end = str(value.get("end_time") or "")
        for timestamp in (clock, end):
            if timestamp:
                datetime.strptime(timestamp, "%H:%M")
                if not due:
                    raise ValueError("A milestone time requires a date")
        if end and (not clock or end <= clock):
            raise ValueError("End time must be after start time on the same day")
        identity = str(value.get("id") or f"step-{index + 1}")
        if identity in identifiers or len(identity) > 100 or not identity.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Invalid or duplicate milestone identity")
        identifiers.add(identity)
        result.append({
            "id": identity, "title": title, "due_date": due or None,
            "time": clock, "end_time": end,
            "status": "done" if value.get("status") == "done" else "todo",
            "evidence": str(value.get("evidence") or "")[:1000],
        })
    return result


def milestone_date_label(step: dict) -> str:
    label = step.get("due_date") or "日期待定"
    if step.get("time"):
        label += " " + step["time"]
    if step.get("end_time"):
        label += "-" + step["end_time"]
    return label


def refresh_milestone_task(task: dict, today: date | None = None) -> None:
    steps = task.get("milestones")
    if not steps:
        return
    today = today or date.today()
    pending = [step for step in steps if step.get("status") != "done"]
    if not pending:
        task["status"] = "done"
        task["completed_on"] = task.get("completed_on") or today.isoformat()
        task["due_label"] = f"子事项已全部完成（{len(steps)}/{len(steps)}）"
        task.pop("reminder_at", None)
        return
    upcoming = min(pending, key=lambda step: (step.get("due_date") or "9999-12-31", step.get("time") or "23:59"))
    task["status"] = "todo" if task.get("status") == "done" else task.get("status", "todo")
    task.pop("completed_on", None)
    task["due_date"] = upcoming.get("due_date")
    task["due_label"] = f"{upcoming['title']}：{milestone_date_label(upcoming)}（完成 {len(steps) - len(pending)}/{len(steps)}）"
    task["reminder_at"] = f"{upcoming['due_date']} {upcoming['time']}" if upcoming.get("due_date") and upcoming.get("time") else None


def milestone_summary(task: dict) -> str:
    return "\n".join(
        f"[{'x' if step.get('status') == 'done' else ' '}] {step['title']}：{milestone_date_label(step)}"
        for step in task.get("milestones", [])
    )


def due_milestone_reminders(task: dict, now: datetime) -> list[dict]:
    stamp = now.strftime("%Y-%m-%d %H:%M")
    return [step for step in task.get("milestones", [])
            if step.get("status") != "done" and step.get("time")
            and f"{step.get('due_date')} {step['time']}" == stamp
            and step.get("last_reminded_at") != stamp]
