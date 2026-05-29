# GitHub Publishing Checklist

## Repository

- Repository name: `DeskTask`
- Visibility: public
- License: MIT
- Initial version: `v0.1.0-beta`

## Files To Commit

- `.gitignore`
- `LICENSE`
- `README.md`
- `RELEASE_NOTES.md`
- `pyproject.toml`
- `daily_tasks.example.json`
- `app_settings.example.json`
- `scripts/build_windows.ps1`
- `src/`

## Files Not To Commit

- `.venv/`
- `daily_tasks.json`
- `app_settings.json`
- `build/`
- `dist/`
- `release/`
- `*.spec`
- `*.log`

## First Release

Upload this asset to GitHub Releases:

- `release/DeskTask-0.1.0-beta-win64.zip`

Use `RELEASE_NOTES.md` as the release description.

## Suggested Git Commands

```powershell
cd "D:\software\Daily task"
git init
git add .
git commit -m "Initial public beta"
git branch -M main
git remote add origin https://github.com/<your-username>/DeskTask.git
git push -u origin main
```

Then create a release on GitHub:

- Tag: `v0.1.0-beta`
- Title: `DeskTask v0.1.0-beta`
- Description: content from `RELEASE_NOTES.md`
- Asset: `release/DeskTask-0.1.0-beta-win64.zip`
