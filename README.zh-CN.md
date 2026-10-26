# DeskTask

[English](README.md) | [简体中文](README.zh-CN.md)

DeskTask 是一个基于 PySide6 / Qt 构建的 Windows 桌面任务面板。它以小型悬浮窗口的形式停留在桌面上，支持快速编辑任务，并可以显示本地弹窗提醒。

## 功能

- 圆角桌面悬浮任务面板
- 支持调整面板大小和完整表格视图
- 点击任务卡片即可编辑详情
- 五种任务类型，并用不同颜色区分：
  - 高优先级
  - 中优先级
  - 低优先级
  - 循环任务
  - 定时提醒
- 支持 `YYYY-MM-DD HH:MM` 格式的本地弹窗提醒
- 每天 `00:00` 和 `09:00` 自动清理已完成任务
- 非循环任务完成后会在清理时被移除
- 循环任务完成后会保留，并在下次清理后重新变为未完成
- 支持从 `+` 菜单更换字体
- 任务数据保存在本地
- Chrome 扩展，可将当前 Outlook 网页邮件导入待办
- 同一条日程支持多个带日期的子事项，分别完成和提醒
- 单实例运行，并提供独立的隐藏到托盘按钮

## 截图

截图将在后续版本中补充。

## 下载并运行

1. 从 Release 页面下载最新的 `DeskTask-*-win64.zip`。
2. 将 zip 文件完整解压到普通文件夹。
3. 打开解压后的文件夹。
4. 双击运行 `DeskTask.exe`。

不要直接在压缩包预览窗口中运行程序。
请保留解压后的 `_internal` 文件夹，它需要和 `DeskTask.exe` 放在同一目录。

## 安装器

Windows 安装器文件名为 `DeskTaskSetup-*-beta.exe`。

它会为当前 Windows 用户安装 DeskTask，不需要管理员权限。当前安装向导暂时使用英文界面。

## 从源码运行

```powershell
git clone https://github.com/JunxiangYangyjx/DeskTask.git
cd DeskTask
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\pythonw.exe src\daily_task\app.py
```

## 无控制台运行

```powershell
.\.venv\Scripts\pythonw.exe src\daily_task\app.py
```

## 本地开发版快捷方式

创建一个桌面快捷方式，用来打开本地开发版：

```powershell
.\scripts\create_dev_shortcut.ps1
```

这个快捷方式会使用项目虚拟环境运行 `src\daily_task\app.py`，并读取本地项目里的 JSON 数据。

## 从 Outlook 网页导入

目前 Outlook 连接需要保留源码目录和 `.venv`，Windows 安装器本身不会安装此连接。

1. 先按上文“从源码运行”配置环境。
2. 在项目目录执行 `powershell -ExecutionPolicy Bypass -File scripts\install_outlook_bridge.ps1`。
3. Chrome 打开 `chrome://extensions`，启用开发者模式，加载已解压的 `extensions/outlook` 文件夹。
4. 刷新 Outlook，打开邮件，点击“加入 DeskTask”，核对后导入。

支持 `outlook.office.com`、`outlook.office365.com`、`outlook.live.com` 和 `outlook.cloud.microsoft`。邮件通过 Chrome 本地通信交给桌面程序，不使用 Microsoft Graph，也不上传至外部 AI 服务。受管理的浏览器可能限制本地扩展或本地通信。

同一封邮件可以保存为一条日程，包含报名、交 PPT、培训、比赛等子事项。日期识别采用本地规则，导入前需要核对；未明确给出的时间保持空白。在任务详情中可以逐项勾选完成。子事项弹出提醒时不会自动完成整条日程；原有单次提醒仍保留弹窗后自动完成的行为。

详见[扩展安装与限制说明](extensions/outlook/README.md)。升级后请重新加载扩展，并退出、重启 DeskTask。

## 测试

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_outlook_import.py -v
node --test tests\outlook_extract.test.cjs tests\outlook_background.test.cjs
```

可选的浏览器界面测试需要 Node.js、Chrome 和 Playwright：

```powershell
npm install --prefix build/outlook-qa --no-package-lock playwright
node --test tests\outlook_ui.test.cjs
```

## 校验数据

```powershell
.\.venv\Scripts\python.exe src\daily_task\app.py --check
```

## 本地数据

DeskTask 会把用户数据保存在本地 JSON 文件中：

- `daily_tasks.json`
- `app_settings.json`

这些文件会被 Git 忽略，不会提交到公开仓库。仓库中只包含安全的示例文件：

- `daily_tasks.example.json`
- `app_settings.example.json`

`outlook_inbox/` 邮件导入队列和 `build/` 内生成的本地连接配置也会被 Git 忽略。

如果 `daily_tasks.json` 不存在，DeskTask 会根据示例文件自动创建。

打包发布版会把用户数据保存在 `%LOCALAPPDATA%\DeskTask`，因此升级后日程会保留。首次启动时，DeskTask 也会尝试从旧版解压目录或旧安装目录自动迁移 `daily_tasks.json` 和 `app_settings.json`。你也可以在软件右上角 `+` 菜单中选择“导入旧版日程”。

## 任务行为

提醒任务：

- 将任务类型设置为 `Reminder`
- 将提醒时间填写为 `YYYY-MM-DD HH:MM`
- DeskTask 会在设定时间显示本地弹窗
- 弹窗触发后，该任务会自动标记为已完成

循环任务：

- 将任务类型设置为 `Recurring`
- 在循环规则中填写说明，例如 `Every Friday`
- 点击完成后，任务会继续保留
- 到清理时间后，任务会重新变成未完成

其他任务类型：

- 标记完成后，会在下一个清理检查点被移除

## 构建 Windows Zip

先在项目虚拟环境中安装 PyInstaller：

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
```

执行构建：

```powershell
.\scripts\build_windows.ps1
```

生成的 zip 文件会放在 `release/` 目录下。

## 构建 Windows 安装器

先安装 Inno Setup 6：

```powershell
winget install --id JRSoftware.InnoSetup -e
```

执行构建：

```powershell
.\scripts\build_installer.ps1
```

生成的安装器会放在 `release/` 目录下。

## 后续计划

- 安装器
- 开机自启动选项
- 更完善的循环规则
- 可选的外部推送渠道，例如邮件或微信
- 任务文件导入和导出

## 许可证

MIT License.
