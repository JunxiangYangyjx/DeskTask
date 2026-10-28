# 邮件加入 DeskTask

扩展 0.3.0 提供 Outlook、Gmail、QQ 邮箱及网易 163/126/yeah 网页适配。支持的主机集中在 `providers.js`；浏览器扩展与本地接收端均校验来源。Gmail 和 QQ 新版已在真实页面核对，用户于 2026-10-28 确认实际使用正常；网易及 QQ 旧版目前通过的是模拟页面测试，仍待真实邮箱验证。
点击右下角“加入 DeskTask”，核对事项、日期、提醒时间和地点，确认后通过 Chrome Native Messaging 发送到本地程序。不使用邮件 API、邮箱密码或外部服务器。日期提取使用本地规则，不是 AI 语义识别；中文月日及英文月份日期没有年份时，按电脑本地当前年份补全并在预览中提示，不会因日期已过自动改成明年。明确年份保持原样；多日期、转发邮件和跨时区活动仍需核对。

支持同源 iframe 中的邮件正文；受限的跨源 iframe、附件和图片文字可通过手动粘贴摘录补充。保存来源链接时会过滤 `sid`、`token` 等已知登录参数。过滤后的 QQ/网易链接可能只能回到邮箱入口，打开原邮件前仍需登录。

## 一个日程的多个子事项

0.2.0 起可根据日期附近的报名、提交幻灯片、培训、比赛等关键词，识别带日期的子事项。确认界面可修改名称、日期、开始/提醒时间和结束时间，也可取消纳入某一项或手动添加。编辑摘录后可点击“重新识别子事项”；没有明确给出的时间保持空白。

所有子事项保存为同一条 DeskTask 日程的 `milestones`，不会拆成独立任务。主日程显示最早未完成的子事项；打开任务详情可逐项勾选，全部完成后主日程才完成。每个明确填写了时间的子事项分别提醒，提醒弹出本身不会将其标记完成。重复导入保留已有子事项的完成进度；先前导入的单事项可在再次导入时升级为多子事项日程。

从旧版升级后，需要重新加载 Chrome 扩展并退出、重启 DeskTask，以加载新的桌面子事项功能。

## 安装

1. 在项目根目录运行 `powershell -ExecutionPolicy Bypass -File scripts/install_outlook_bridge.ps1`，注册当前用户的本地接收程序。不需要提升管理员权限。默认任务文件是项目根目录的 daily_tasks.json；其他数据文件可用 `-DataPath` 指定。
2. Chrome 打开 `chrome://extensions`，启用“开发者模式”，点击“加载已解压的扩展程序”，选择本文件所在目录 `extensions/outlook`。
3. 刷新邮箱网页，打开一封邮件，点击右下角“加入 DeskTask”。首次使用先核对主题和摘录确实来自目标邮件。

从 Outlook 专用版升级时，重新加载原扩展，确认 Chrome 要求的新邮箱站点权限，并退出、重启 DeskTask。扩展名称改为“邮件加入 DeskTask”；原目录 `extensions/outlook`、扩展 ID、本地通信主机名和 `outlook_inbox` 队列保持不变，已有配置和日程继续使用。

扩展固定 ID：`nmknpdikgjjjdmpcnlnehgbnbhdojkjj`。学校管理的 Chrome 若禁止本地扩展或 Native Messaging，需要管理员允许；本实现不会修改学校或 Chrome 的策略。

原邮件入口保存当前网页链接；在会话视图中该链接可能指向整个会话。需要精确指定正文时，先选中当前邮件中的文字。附件、图片中的文字和未展开的邮件不会被解析。

## 数据与卸载

本地接收程序将确认过的内容写入任务文件同目录的 `outlook_inbox` 队列，DeskTask 在 GUI 线程中导入并去重。程序未运行时接收程序会启动源码版 DeskTask；源码目录及 `.venv` 需保持原位。同一正文、主题和链接的重复导入不会产生第二条未删除的任务。

在 Chrome 中移除扩展后，可删除当前用户注册表项 `HKCU\Software\Google\Chrome\NativeMessagingHosts\com.desktask.outlook` 以及项目 `build/outlook-native` 生成目录。已有任务会保留。

参考：[Chrome Native Messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging)、[加载本地扩展](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world#load-unpacked)。
