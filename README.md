# DeskTask

[English](README.md) | [简体中文](README.zh-CN.md)

DeskTask is a small Windows desktop task panel built with PySide6 / Qt. It stays as a compact floating widget, supports quick task editing, and can show local reminder popups.

## Features

- Compact rounded desktop task panel
- Resizable panel and full table view
- Click a task card to edit details
- Five task types with distinct colors:
  - High priority
  - Medium priority
  - Low priority
  - Recurring
  - Reminder
- Local popup reminders with `YYYY-MM-DD HH:MM`
- Daily cleanup at `00:00` and `09:00`
- Completed non-recurring tasks are removed during cleanup
- Completed recurring tasks stay in the list and become incomplete again
- Font replacement from the `+` menu
- Data is stored locally

## Screenshots

Screenshots will be added in a later release.

## Download And Run

1. Download `DeskTask-0.1.0-beta-win64.zip` from the release page.
2. Extract the zip file to a normal folder.
3. Open the extracted folder.
4. Double-click `DeskTask.exe`.

Do not run the app directly inside the zip preview. Keep the `_internal` folder next to `DeskTask.exe`.

## Install From Source

```powershell
git clone https://github.com/JunxiangYangyjx/DeskTask.git
cd DeskTask
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\pythonw.exe src\daily_task\app.py
```

## Run Without Console

```powershell
.\.venv\Scripts\pythonw.exe src\daily_task\app.py
```

## Validate Data

```powershell
.\.venv\Scripts\python.exe src\daily_task\app.py --check
```

## Local Data

DeskTask keeps user data in local JSON files:

- `daily_tasks.json`
- `app_settings.json`

These files are intentionally ignored by Git. The repository includes safe examples:

- `daily_tasks.example.json`
- `app_settings.example.json`

If `daily_tasks.json` is missing, DeskTask creates it from the example file.

## Task Behavior

Reminder tasks:

- Set task type to `Reminder`
- Fill `Reminder time` as `YYYY-MM-DD HH:MM`
- DeskTask shows a local popup at that time
- After the popup, the task is automatically marked completed

Recurring tasks:

- Set task type to `Recurring`
- Fill a recurrence note such as `Every Friday`
- When completed, the task is kept
- At cleanup time it becomes incomplete again

Other task types:

- When completed, the task is removed at the next cleanup checkpoint

## Build A Windows Zip

Install PyInstaller in the project virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
```

Build:

```powershell
.\scripts\build_windows.ps1
```

The release zip will be created under `release/`.

## Roadmap

- Installer
- Startup-at-login option
- Better recurrence rules
- Optional external push channels such as email or WeChat
- Import/export task files

## License

MIT License.
