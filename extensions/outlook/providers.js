(() => {
  const definitions = [
    {id:'outlook',name:'Outlook',hosts:['outlook.office.com','outlook.office365.com','outlook.live.com','outlook.cloud.microsoft'],
      bodies:['[role="document"]','.allowTextSelection [class*="Body"]','[data-testid="message-body"]'],
      subjects:['[data-testid="message-subject"]','[role="main"] [role="heading"]','main h1','main h2','main h3']},
    {id:'gmail',name:'Gmail',hosts:['mail.google.com'],
      bodies:['.a3s.aiL','[data-message-id] .a3s'],subjects:['h2.hP','[role="main"] h2']},
    {id:'qq',name:'QQ 邮箱',hosts:['mail.qq.com','wx.mail.qq.com'],
      bodies:['.mail-detail-content','#mailContentContainer','#mailContent','.mailcontent','.mail-content','[data-testid="mail-content"]'],
      subjects:['.mail-detail-subject .mail-subject-text','#subject','h1.mail-title','.mail-subject','.mail_title','[data-testid="mail-subject"]']},
    {id:'netease',name:'网易邮箱',hosts:['mail.163.com','mail.126.com','mail.yeah.net','email.163.com'],suffixes:['.mail.163.com','.mail.126.com','.mail.yeah.net'],
      bodies:['.mailContent','.mail-content','.nui-scroll .js-component-email-body','[data-testid="mail-content"]'],
      subjects:['.readMsgSubject','.mail-subject','.nui-fIBlock .nui-fIBlock-text','[data-testid="mail-subject"]']},
  ];
  function provider(host) {
    return definitions.find(item=>item.hosts.includes(host) || item.suffixes?.some(suffix=>host.endsWith(suffix)));
  }
  const sensitive = new Set(['sid','session','sessionid','session_id','token','access_token','auth_token','code','skey','ticket','auth','authorization','password']);
  function cleanQuery(query) {
    const parameters = new URLSearchParams(query);
    for (const key of [...parameters.keys()]) if (sensitive.has(key.toLowerCase())) parameters.delete(key);
    return parameters.toString();
  }
  function safeUrl(value) {
    const url = new URL(value);
    if (url.protocol !== 'https:' || url.username || url.password || (url.port && url.port !== '443') || !provider(url.hostname)) throw new Error('不支持此邮箱地址');
    url.search = cleanQuery(url.search);
    const hash = url.hash.slice(1);
    const separator = hash.indexOf('?');
    if (separator >= 0) {
      const query = cleanQuery(hash.slice(separator+1));
      url.hash = hash.slice(0,separator) + (query ? '?' + query : '');
    }
    return url.href;
  }
  function visible(node) {
    const view = node.ownerDocument.defaultView;
    return node.getClientRects().length > 0 && view.getComputedStyle(node).visibility !== 'hidden';
  }
  function documents(top) {
    const result = [{doc:top,frame:null}];
    const visit = (doc,depth) => {
      if (depth > 4) return;
      for (const frame of doc.querySelectorAll('iframe,frame')) {
        if (!visible(frame)) continue;
        try {
          const child = frame.contentDocument;
          if (child?.body && !result.some(item=>item.doc===child)) {result.push({doc:child,frame});visit(child,depth+1);}
        } catch { /* Cross-origin frames require a separate permission; use manual paste. */ }
      }
    };
    visit(top,0);
    return result;
  }
  function firstText(doc,selectors) {
    for (const selector of selectors) {
      const node = [...doc.querySelectorAll(selector)].find(node=>visible(node) && node.innerText.trim());
      if (node) return node.innerText.trim();
    }
    return '';
  }
  function readMail(doc = document) {
    const site = provider(location.hostname);
    if (!site) throw new Error('当前网站不在已支持的邮箱列表中');
    const scopes = documents(doc);
    const matches = [];
    let selected = '';
    for (const {doc:scope,frame} of scopes) {
      selected ||= scope.getSelection()?.toString().trim() || '';
      let nodes = [...scope.querySelectorAll(site.bodies.join(','))].filter(node=>visible(node) && node.innerText.trim());
      // QQ/NetEase may render the message directly in an otherwise unlabelled frame.
      if (!nodes.length && frame && /(?:mail|message|content|read|正文)/i.test([frame.id,frame.name,frame.title,frame.className].join(' '))
          && scope.body.innerText.trim() && !scope.querySelector('input[type="password"]')) nodes = [scope.body];
      for (const node of nodes) if (!matches.some(item=>item.node===node)) matches.push({node,scope});
    }
    const chosen = matches.at(-1);
    const body = (selected || chosen?.node.innerText || '').trim().slice(0,20000);
    let subject = firstText(doc,site.subjects);
    if (!subject && chosen?.scope !== doc && chosen?.scope) subject = firstText(chosen.scope,site.subjects);
    return {title:subject || '邮件待办',subject:subject || '邮件待办',body,url:safeUrl(location.href),provider:site.id,
      extractionWarning:body?'':'未识别到邮件正文，可在下方粘贴正文并填写事项。'};
  }
  globalThis.DeskTaskMailProviders = {definitions,provider,safeUrl,readMail};
})();
