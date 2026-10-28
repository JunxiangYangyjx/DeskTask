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
- Chrome extension with Outlook, Gmail, QQ and NetEase webmail adapters
- One schedule with multiple dated checklist items and independent reminders
- Single-instance launch and a dedicated hide-to-tray button

## Screenshots

Screenshots will be added in a later release.

## Download And Run

1. Download the latest `DeskTask-*-win64.zip` from the release page.
2. Extract the zip file to a normal folder.
3. Open the extracted folder.
4. Double-click `DeskTask.exe`.

Do not run the app directly inside the zip preview.
Keep the extracted `_internal` folder next to `DeskTask.exe`.

## Installer

The Windows installer is named `DeskTaskSetup-*-beta.exe`.

It installs DeskTask for the current Windows user and does not require administrator permission. The first installer build uses an English setup wizard.

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

## Local Development Shortcut

Create a desktop shortcut that opens the local development version:

```powershell
.\scripts\create_dev_shortcut.ps1
```

The shortcut runs `src\daily_task\app.py` with the project's virtual environment and uses the local project JSON data.

## Webmail Import

The mail bridge currently requires the source checkout and its `.venv`; the Windows installer alone does not install the bridge.

1. Follow **Install From Source** above.
2. Run `powershell -ExecutionPolicy Bypass -File scripts\install_outlook_bridge.ps1` from the project folder.
3. In Chrome, open `chrome://extensions`, enable Developer mode, and load the unpacked `extensions/outlook` folder.
4. Refresh webmail, open an email, and click **加入 DeskTask** to review and import it.

Supported hosts include `outlook.office.com`, `outlook.office365.com`, `outlook.live.com`, and `outlook.cloud.microsoft`. The extension uses a local native-messaging bridge, not Microsoft Graph or an external AI service. Browser policies may restrict local extensions or native messaging.

Extension 0.3.0 adds Gmail (`mail.google.com`), QQ (`mail.qq.com` / `wx.mail.qq.com`), and NetEase 163/126/yeah adapters. The user confirmed Gmail and the current QQ webmail version work on 2026-10-28; NetEase and legacy QQ layouts still need live verification. Same-origin message frames are supported; inaccessible cross-origin frames can use manual paste. Known session parameters such as `sid` and `token` are removed from saved source links, which may then open the mailbox rather than a specific message. Existing extension IDs, installation paths and native host configuration remain compatible.

Chinese month/day and English month-name dates without a year default to the computer's local current year, with a preview notice. Explicit years are preserved, and past dates show a warning rather than rolling forward to next year. Combined `Date & Time` lines are supported, including a date before the clock.

An email can become one schedule containing registration, slide submission, training, and event milestones. Review the extracted dates and times before importing; missing times stay blank. Each milestone can be completed separately in task details. Milestone reminder popups do not mark the schedule complete. Existing single reminder tasks retain their automatic-completion behavior.

See [extension setup and limitations](extensions/outlook/README.md). After upgrading, reload the extension and restart DeskTask.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_outlook_import.py -v
node --test tests\outlook_extract.test.cjs tests\outlook_background.test.cjs tests\mail_providers.test.cjs
```

Optional browser UI checks require Node.js, Chrome, and Playwright:

```powershell
npm install --prefix build/outlook-qa --no-package-lock playwright
node --test tests\outlook_ui.test.cjs tests\mail_providers_ui.test.cjs
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

The `outlook_inbox/` queue and generated bridge configuration under `build/` also remain local and are ignored by Git.

If `daily_tasks.json` is missing, DeskTask creates it from the example file.

Packaged releases store user data under `%LOCALAPPDATA%\DeskTask`, so schedules survive upgrades. On first launch, DeskTask also tries to migrate older `daily_tasks.json` and `app_settings.json` files from older extracted or installed folders. You can also use `+` -> `Import old schedule` from the app menu.

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

## Build The Windows Installer

Install Inno Setup 6 first:

```powershell
winget install --id JRSoftware.InnoSetup -e
```

Build:

```powershell
.\scripts\build_installer.ps1
```

The installer will be created under `release/`.

## Roadmap

- Installer
- Startup-at-login option
- Better recurrence rules
- Optional external push channels such as email or WeChat
- Import/export task files

## License

MIT License.
