# DeskTask v0.1.3-beta

Schedule migration and local development launch improvements.

中文版本见下方。

## Highlights

- Packaged releases now store user data under `%LOCALAPPDATA%\DeskTask`, so schedules survive zip-folder or installer upgrades.
- First launch automatically migrates old `daily_tasks.json` and `app_settings.json` files from previous extracted or installed DeskTask folders when possible.
- Added `+` -> `导入旧版日程` for manually importing an old `daily_tasks.json`.
- Added `scripts\create_dev_shortcut.ps1` to create a desktop shortcut for opening the local development version.

---

# DeskTask v0.1.3-beta 中文说明

这个版本加入日程迁移和本地开发版快捷打开能力。

## 主要变化

- 打包发布版现在把用户数据保存在 `%LOCALAPPDATA%\DeskTask`，因此 zip 解压目录变化或安装器升级后，日程仍会保留。
- 首次启动时，如果能找到旧版解压目录或旧安装目录中的 `daily_tasks.json` / `app_settings.json`，会自动迁移。
- 右上角 `+` 菜单新增“导入旧版日程”，可以手动选择旧版 `daily_tasks.json`。
- 新增 `scripts\create_dev_shortcut.ps1`，用于创建打开本地开发版的桌面快捷方式。

---

# DeskTask v0.1.2-beta

Small UI polish release.

中文版本见下方。

## Fixes

- Replaced the top-right `+` text button with a drawn icon.
- Hid the default Qt menu arrow that overlapped with the `+` button.
- The action menu button no longer depends on the user's installed font rendering.

## Installer

- Added an Inno Setup based Windows installer: `DeskTaskSetup-0.1.2-beta.exe`.
- The installer uses current-user installation and does not require administrator permission.
- The first installer build uses an English setup wizard.

---

# DeskTask v0.1.2-beta 中文说明

这是一个小型界面修复版本。

## 修复内容

- 将右上角 `+` 文字按钮改成绘制图标。
- 隐藏 Qt 默认下拉箭头，避免它和 `+` 按钮重叠。
- 操作菜单按钮不再依赖用户电脑上的字体渲染效果。

## 安装器

- 新增基于 Inno Setup 的 Windows 安装器：`DeskTaskSetup-0.1.2-beta.exe`。
- 安装器采用当前用户安装模式，不需要管理员权限。
- 当前安装向导暂时使用英文界面。

---

# DeskTask v0.1.1-beta

Runtime packaging fix for the first public beta.

中文版本见下方。

## Fixes

- Changed the Windows release zip to contain one complete top-level app folder.
- Pins PySide6 to `6.7.3` for reproducible Windows packaging.
- Explicitly checks PySide6 / Qt runtime loading during packaging.
- Adds the bundled PySide6 and shiboken6 directories to the Windows DLL search path at startup.
- Added a startup diagnostic message when Qt runtime loading fails.
- Added a build-time GUI smoke test.

## How to Run

1. Download `DeskTask-0.1.1-beta-win64.zip`.
2. Extract the zip file to a normal folder.
3. Double-click `DeskTask.exe`.

Do not run the app directly inside the zip preview.
Keep the extracted `_internal` folder next to `DeskTask.exe`.

---

# DeskTask v0.1.1-beta 中文说明

这是针对第一个公开 beta 版本的运行时打包修复。

## 修复内容

- 将 Windows 发布 zip 调整为包含一个完整顶层程序文件夹。
- 将 PySide6 固定为 `6.7.3`，保证 Windows 打包可复现。
- 打包时显式检查 PySide6 / Qt 运行时是否可加载。
- 启动时将随包附带的 PySide6 和 shiboken6 目录加入 Windows DLL 搜索路径。
- 当 Qt 运行时加载失败时，显示更清晰的启动诊断信息。
- 构建时增加 GUI 导入 smoke test。

## 如何运行

1. 下载 `DeskTask-0.1.1-beta-win64.zip`。
2. 将 zip 文件完整解压到普通文件夹。
3. 双击运行 `DeskTask.exe`。

不要直接在压缩包预览窗口中运行程序。
请保留解压后的 `_internal` 文件夹，它需要和 `DeskTask.exe` 放在同一目录。

---

# DeskTask v0.1.0-beta

Initial public beta. This release is provided as a portable Windows zip package.

中文版本见下方。

## Highlights

- Floating Windows desktop task panel
- Quick task editing by clicking task cards
- Full task table view
- Five task types with distinct colors
- Local reminder popups
- Recurring task cleanup behavior
- Daily cleanup checkpoints at `00:00` and `09:00`
- Local JSON data storage

## Privacy

User task data is local. The repository does not include personal `daily_tasks.json` or `app_settings.json`; only example files are included.

## Known Limitations

- Windows-focused beta
- Reminder delivery is local popup only
- WeChat and email push are not integrated yet
- Recurrence rules are stored as text; automatic recurrence scheduling is still planned
- No installer yet; this release is distributed as a portable zip

---

# DeskTask v0.1.0-beta 中文说明

这是 DeskTask 的第一个公开 beta 版本。本版本以 Windows 便携压缩包形式发布。

## 主要功能

- Windows 桌面悬浮任务面板
- 点击任务卡片即可快速编辑任务详情
- 支持完整任务表格视图
- 五种任务类型，并使用不同颜色区分：
  - 高优先级
  - 中优先级
  - 低优先级
  - 循环任务
  - 定时提醒
- 支持本地弹窗提醒
- 支持循环任务的每日重置逻辑
- 每天 `00:00` 和 `09:00` 自动检查已完成任务
- 任务数据保存在本地 JSON 文件中

## 隐私说明

用户的真实任务数据只保存在本地。公开仓库不包含个人的 `daily_tasks.json` 或 `app_settings.json`，只包含可公开的示例文件。

## 已知限制

- 当前版本主要面向 Windows
- 提醒方式目前仅支持本地弹窗
- 尚未接入微信或邮件推送
- 循环规则目前以文本形式保存，自动周期调度仍在后续计划中
- 暂无安装器，本版本以便携 zip 包发布
