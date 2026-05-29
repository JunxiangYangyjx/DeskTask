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
