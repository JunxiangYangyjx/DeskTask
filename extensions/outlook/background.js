chrome.runtime.onMessage.addListener((message, sender, reply) => {
  const allowed = new Set(["outlook.office.com", "outlook.office365.com", "outlook.live.com", "outlook.cloud.microsoft"]);
  let senderUrl;
  try { senderUrl = new URL(sender.url); } catch { return false; }
  if (sender.id !== chrome.runtime.id || senderUrl.protocol !== "https:" || !allowed.has(senderUrl.hostname) || message?.type !== "desktask-import") return false;
  const payload = {...message.payload, url: sender.url};
  chrome.runtime.sendNativeMessage("com.desktask.outlook", payload, (result) => {
    const error = chrome.runtime.lastError;
    reply(error ? {ok: false, error: "本地连接不可用，请先运行 DeskTask 的 Outlook 连接安装脚本。"} : result);
  });
  return true;
});
