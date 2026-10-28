importScripts('providers.js');
chrome.runtime.onMessage.addListener((message, sender, reply) => {
  let sourceUrl;
  try { sourceUrl = DeskTaskMailProviders.safeUrl(sender.url); } catch { return false; }
  if (sender.id !== chrome.runtime.id || message?.type !== "desktask-import") return false;
  const payload = {...message.payload, url:sourceUrl};
  chrome.runtime.sendNativeMessage("com.desktask.outlook", payload, (result) => {
    const error = chrome.runtime.lastError;
    reply(error ? {ok: false, error: "本地连接不可用，请先运行 DeskTask 的邮件连接安装脚本。"} : result);
  });
  return true;
});
