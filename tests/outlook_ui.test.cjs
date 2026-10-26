// Optional UI QA: npm install --prefix build/outlook-qa playwright
const {test} = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const {multiDateMail} = require('./outlook_fixtures.cjs');
const {chromium} = require('../build/outlook-qa/node_modules/playwright');
const root = path.join(__dirname, '..');
test('Outlook preview, confirmed payload, and desktop/mobile layout', async () => {
  const browser = await chromium.launch({channel:'chrome', headless:true});
  try {
    for (const {domain, viewport} of [
      {domain:'outlook.office.com',viewport:{width:1280,height:800}},
      {domain:'outlook.cloud.microsoft',viewport:{width:1280,height:800}},
      {domain:'outlook.cloud.microsoft',viewport:{width:390,height:844}},
    ]) {
      const page = await browser.newPage({viewport});
      await page.route('**/*', route => route.fulfill({contentType:'text/html', body:`<!doctype html><html><head><meta charset="utf-8"><title>Annual meeting - Outlook</title></head><body><main role="main"><h1>IEEE 年会</h1><div role="document">Date: 3 December 2026<br>Time: 6:00 pm<br>Venue: Melati Ballroom<br>请参加年会。</div></main></body></html>`}));
      await page.goto(`https://${domain}/mail/inbox/id/fixture`);
      await page.evaluate(() => {
        const attach = Element.prototype.attachShadow;
        Element.prototype.attachShadow = function(options) { return attach.call(this,{...options,mode:'open'}); };
        window.chrome = {runtime:{sendMessage: async message => { window.sentImport=message; return {ok:true,queued:true}; }}};
      });
      await page.addScriptTag({path:path.join(root,'extensions/outlook/extract.js')});
      await page.addScriptTag({path:path.join(root,'extensions/outlook/content.js')});
      await page.getByRole('button',{name:'加入 DeskTask',exact:true}).click();
      assert.equal(await page.getByLabel('事项',{exact:true}).inputValue(),'IEEE 年会');
      assert.equal(await page.locator('input[name="date"]').inputValue(),'2026-12-03');
      assert.equal(await page.getByLabel('提醒时间（本地时区）',{exact:true}).inputValue(),'18:00');
      assert.equal(await page.getByLabel('地点',{exact:true}).inputValue(),'Melati Ballroom');
      const bounds = await page.getByRole('dialog').boundingBox();
      assert.ok(bounds.x >= 0 && bounds.y >= 0 && bounds.x+bounds.width <= viewport.width && bounds.y+bounds.height <= viewport.height);
      fs.mkdirSync(path.join(root,'build/outlook-qa'),{recursive:true});
      await page.screenshot({path:path.join(root,`build/outlook-qa/preview-${viewport.width}.png`)});
      await page.getByRole('button',{name:'确认加入',exact:true}).click();
      await page.getByRole('status').filter({hasText:'已发送至 DeskTask'}).waitFor();
      const sent = await page.evaluate(() => window.sentImport);
      assert.equal(sent.payload.title,'IEEE 年会');
      assert.equal(sent.payload.due_date,'2026-12-03');
      assert.equal(sent.payload.time,'18:00');
      assert.equal(new URL(sent.payload.url).hostname,domain);
      await page.getByRole('button',{name:'关闭',exact:true}).click();
      assert.equal(await page.getByRole('dialog').count(),0);
      await page.close();
    }
    for (const bodyMarkup of [
      '<div role="document" aria-label="邮件正文">Date: 17 November 2026<br>Registration closes 2 November 2026<br>Venue: LT25</div><h3>发件人：Forwarder</h3><div role="document" aria-label="邮件正文"></div>',
      '<div role="document" aria-label="邮件正文"></div>',
    ]) {
      const page = await browser.newPage();
      await page.route('**/*', route => route.fulfill({contentType:'text/html',body:`<!doctype html><html><head><meta charset="utf-8"><title>邮件 - User - Outlook</title></head><body><aside><h2>导航窗格</h2></aside><main role="main" aria-label="阅读窗格"><h3>3MT Heat</h3><h3>发件人：Sender</h3>${bodyMarkup}</main></body></html>`}));
      await page.goto('https://outlook.cloud.microsoft/mail/inbox/id/conversation');
      await page.evaluate(() => {
        const attach = Element.prototype.attachShadow;
        Element.prototype.attachShadow = function(options) { return attach.call(this,{...options,mode:'open'}); };
        window.chrome = {runtime:{sendMessage:async()=>({ok:true})}};
      });
      await page.addScriptTag({path:path.join(root,'extensions/outlook/extract.js')});
      await page.addScriptTag({path:path.join(root,'extensions/outlook/content.js')});
      await page.getByRole('button',{name:'加入 DeskTask',exact:true}).click();
      assert.equal(await page.getByLabel('事项',{exact:true}).inputValue(),'3MT Heat');
      if (bodyMarkup.includes('17 November')) {
        assert.match(await page.getByLabel('邮件摘录',{exact:true}).inputValue(),/17 November 2026/);
        assert.equal(await page.getByLabel('地点',{exact:true}).inputValue(),'LT25');
        assert.equal(await page.locator('input[name="date"]').inputValue(),'');
        assert.equal(await page.locator('.step').count(),2);
      } else {
        await page.getByText('未识别到邮件正文，可在下方粘贴正文并填写事项。',{exact:true}).waitFor();
        await page.getByLabel('邮件摘录',{exact:true}).fill('手动补充正文');
      }
      await page.close();
    }
  } finally { await browser.close(); }
});

test('Edit and import four milestones as one schedule, including mobile layout', async () => {
  const browser = await chromium.launch({channel:'chrome',headless:true});
  try {
    for (const viewport of [{width:1280,height:900},{width:390,height:844}]) {
      const page = await browser.newPage({viewport});
      await page.route('**/*',route=>route.fulfill({contentType:'text/html',body:`<!doctype html><html><head><meta charset="utf-8"></head><body><main role="main"><h3>3MT Heat</h3><div role="document">${multiDateMail.replaceAll('\n','<br>')}</div><div role="document"></div></main></body></html>`}));
      await page.goto('https://outlook.cloud.microsoft/mail/inbox/id/multi-date');
      await page.evaluate(()=>{
        const attach=Element.prototype.attachShadow;
        Element.prototype.attachShadow=function(options){return attach.call(this,{...options,mode:'open'});};
        window.chrome={runtime:{sendMessage:async message=>{window.sentImport=message;return {ok:true};}}};
      });
      await page.addScriptTag({path:path.join(root,'extensions/outlook/extract.js')});
      await page.addScriptTag({path:path.join(root,'extensions/outlook/content.js')});
      await page.getByRole('button',{name:'加入 DeskTask',exact:true}).click();
      assert.equal(await page.getByLabel('同一日程，多个子事项',{exact:true}).isChecked(),true);
      assert.equal(await page.locator('.step').count(),4);
      assert.deepEqual(await page.locator('.step-title').evaluateAll(nodes=>nodes.map(n=>n.value)),['报名','培训','交 PPT','比赛']);
      const training=page.locator('.step').nth(1);
      assert.equal(await training.locator('.step-time').inputValue(),'');
      await training.locator('.step-time').fill('10:00');
      const bounds=await page.getByRole('dialog').boundingBox();
      assert.ok(bounds.x>=0 && bounds.x+bounds.width<=viewport.width && bounds.y>=0);
      assert.equal(await page.locator('.step').evaluateAll(nodes=>nodes.every(n=>n.scrollWidth<=n.clientWidth)),true);
      await page.screenshot({path:path.join(root,`build/outlook-qa/milestones-${viewport.width}.png`)});
      await page.getByRole('button',{name:'确认加入',exact:true}).click();
      await page.getByRole('status').filter({hasText:'1 条日程，4 个子事项'}).waitFor();
      const payload=await page.evaluate(()=>window.sentImport.payload);
      assert.equal(payload.title,'3MT Heat');
      assert.equal(payload.milestones.length,4);
      assert.equal(payload.milestones[1].time,'10:00');
      await page.close();
    }
  } finally {await browser.close();}
});
